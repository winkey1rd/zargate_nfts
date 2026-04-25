from abc import ABC, abstractmethod
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import logging

from nft.config import COLLECTIONS, COLLECTIONS_BY_ADDRESS
from backend.app.models import OpeningORM
from backend.app.models import NftBaseORM


from getgems.api import get_getgems_nft_history
from ton.api.events import get_event_details
from ton.parser.event import parse_open_event
from utility.converter import convert_address_to_uq

logger = logging.getLogger(__name__)


class CollectionHandler(ABC):
    """Base class for handling different NFT collection types with bulk operations."""

    def __init__(self, collection_address: str, db_session: AsyncSession, api_session):
        self.collection_address = collection_address
        self.db_session = db_session
        self.api_session = api_session
        self.collection_name = COLLECTIONS_BY_ADDRESS.get(collection_address)
        self.collection_config = COLLECTIONS.get(self.collection_name, {})
        self.nft_objects: List[NftBaseORM] = []
        self.nft_updates: List[Dict[str, Any]] = []
        self.opening_objects: List[OpeningORM] = []
        self.specific_objects: List[Any] = []

    async def process_nft(self, item: Dict[str, Any]) -> None:
        """Process a single NFT item and collect objects for bulk insert."""
        try:
            nft_address = convert_address_to_uq(item["address"])

            # Always parse basic NFT info
            nft_info = self._parse_nft_info(item)

            # Check if NFT already exists
            existing_nft = get_nft_by_address(self.db_session, nft_address)
            
            if existing_nft:
                # Get nft_info dict from existing model
                existing_nft_info = {
                    "address": existing_nft.address,
                    "name": existing_nft.name,
                    "price": existing_nft.price,
                    "owner_wallet_address": existing_nft.owner_wallet_address,
                    "sale_type": existing_nft.sale_type,
                    "finish_at": existing_nft.finish_at,
                }
                
                # Compare with parsed info
                if existing_nft_info == nft_info:
                    # No changes
                    logger.debug(f"NFT {nft_address} unchanged, skipping")
                    return
                
                # If changed - collect updates
                changes = {}
                if existing_nft.price != nft_info.get("price"):
                    changes["price"] = nft_info.get("price")
                    logger.debug(f"NFT {nft_address} price changed: {existing_nft.price} -> {nft_info.get('price')}")
                
                if existing_nft.owner_wallet_address != nft_info.get("owner_wallet_address"):
                    changes["owner_wallet_address"] = nft_info.get("owner_wallet_address")
                    logger.debug(f"NFT {nft_address} owner changed")
                
                if existing_nft.sale_type != nft_info.get("sale_type"):
                    changes["sale_type"] = nft_info.get("sale_type")
                    logger.debug(f"NFT {nft_address} sale_type changed: {existing_nft.sale_type} -> {nft_info.get('sale_type')}")
                
                if existing_nft.finish_at != nft_info.get("finish_at"):
                    changes["finish_at"] = nft_info.get("finish_at")
                    logger.debug(f"NFT {nft_address} finish_at changed")
                
                if changes:
                    changes["address"] = existing_nft.address
                    self.nft_updates.append(changes)
                    logger.info(f"NFT {nft_address} changed: {list(changes.keys())}")
                
                return

            # New NFT - proceed with mint info and opening
            mint_info = await self._get_mint_info(nft_info.get("address"))

            # Get open data
            open_data = await self._get_open_data(nft_info, mint_info)

            # Create base NFT (collect, not add immediately)
            nft = NftBaseORM(
                **nft_info,
                collection_address=self.collection_address,
                mint_wallet_address=open_data.get("open_wallet_address"),
                mint_at=mint_info["time"]
            )
            self.nft_objects.append(nft)

            # Add opening if it's a box collection
            if self.collection_config.get("box_collection"):
                opening = OpeningORM(
                    **open_data,
                    nft_address=nft_info.get("address"),
                    open_at=mint_info["time"]
                )
                self.opening_objects.append(opening)

            # Process specific collection type (collects objects)
            await self._process_specific(nft_info, nft_address, item)

        except Exception as e:
            logger.error(f"Error processing NFT {item.get('address', 'unknown')}: {e}")

    async def bulk_save(self) -> bool:
        """Save all collected objects in bulk. Returns True if successful."""
        try:
            if self.nft_objects:
                await self.db_session.bulk_save_objects(self.nft_objects)
                logger.info(f"Inserted {len(self.nft_objects)} NFT objects")

            if self.nft_updates:
                from sqlalchemy import select
                for update_data in self.nft_updates:
                    nft_address = update_data.pop('address')
                    stmt = select(NftBaseORM).where(NftBaseORM.address == nft_address)
                    result = await self.db_session.execute(stmt)
                    nft = result.scalar()
                    if nft:
                        for key, value in update_data.items():
                            if hasattr(nft, key):
                                setattr(nft, key, value)
                logger.info(f"Updated {len(self.nft_updates)} NFT objects")

            if self.opening_objects:
                await self.db_session.bulk_save_objects(self.opening_objects)
                logger.info(f"Inserted {len(self.opening_objects)} opening objects")

            if self.specific_objects:
                await self.db_session.bulk_save_objects(self.specific_objects)
                logger.info(f"Inserted {len(self.specific_objects)} specific objects")

            # Clear lists for next batch
            self.nft_objects.clear()
            self.nft_updates.clear()
            self.opening_objects.clear()
            self.specific_objects.clear()

            return True
        except Exception as e:
            logger.error(f"Error during bulk save: {e}")
            await self.db_session.rollback()
            return False

    @abstractmethod
    async def _process_specific(self, nft_info: Dict[str, Any], nft_address: str, item: Dict[str, Any]) -> None:
        """Process collection-specific logic (e.g., stickers, boxes)."""
        pass

    @staticmethod
    def _parse_nft_info(item: Dict[str, Any]) -> Dict[str, Any]:
        """Parse basic NFT info from item."""
        from ton.parser.collection import parse_ton_collection_nft_item
        return parse_ton_collection_nft_item(item)

    async def _get_mint_info(self, nft_address: str) -> Dict[str, Any]:
        """Get mint information from GetGems."""
        try:
            nft_mint_info = await get_getgems_nft_history(self.api_session, nft_address, types='mint')
            mint_info = nft_mint_info["response"]["items"][0]
            mint_time = datetime.fromisoformat(mint_info.get("time").replace("Z", "+00:00"))
            return {
                "hash": mint_info.get("hash"),
                "time": mint_time
            }
        except Exception as e:
            logger.error(f"Error getting mint info for {nft_address}: {e}")
            raise

    async def _get_open_data(self, nft_info: Dict[str, Any], mint_info: Dict[str, Any]) -> Dict[str, Any]:
        """Get open data, either from NFT info or event details."""
        open_data = {"open_wallet_address": nft_info.get("open_wallet_address")}
        if self.collection_config.get("box_collection"):
            try:
                open_event_data = await get_event_details(self.api_session, mint_info["hash"])
                open_data = parse_open_event(open_event_data)
            except Exception as e:
                logger.warning(f"Error getting open data: {e}, using default")
        return open_data