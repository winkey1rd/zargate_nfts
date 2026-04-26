from abc import ABC, abstractmethod
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import logging

from nft_shared.config.config import COLLECTIONS, COLLECTIONS_BY_ADDRESS
from backend.app.models import OpeningORM, NftBaseORM
from nft_shared.crud.nft_repository import NftRepository

from nft_shared.getgems import get_getgems_nft_history
from nft_shared.ton.api import get_event_details
from nft_shared.ton.parser import parse_open_event
from nft_shared.utility import convert_address_to_uq

logger = logging.getLogger(__name__)


class CollectionHandler(ABC):
    """Base class for handling different NFT collection types with bulk operations."""

    def __init__(
        self,
        collection_address: str,
        db_session: AsyncSession,
        api_session,
        nft_repository: NftRepository,
    ):
        self.collection_address = collection_address
        self.db_session = db_session
        self.api_session = api_session

        # Repositories
        self.nft_repository = nft_repository
        self.special_repository = self._build_special_repository()

        # Collection metadata
        self.collection_name = COLLECTIONS_BY_ADDRESS.get(collection_address)
        self.collection_config = COLLECTIONS.get(self.collection_name, {})

        # In-flight batch buffers
        self.nft_objects: List[NftBaseORM] = []
        self.nft_updates: List[Dict[str, Any]] = []
        self.opening_objects: List[OpeningORM] = []
        self.specific_objects: List[Any] = []

    def _build_special_repository(self):
        """Override in subclasses to return the specialised repository instance."""
        return None

    async def process_nft(self, item: Dict[str, Any]) -> None:
        """Process a single NFT item and collect objects for bulk insert."""
        try:
            nft_address = convert_address_to_uq(item["address"])
            nft_info = self._parse_nft_info(item)

            existing_nft = await self.nft_repository.get_by_address(nft_address)

            if existing_nft:
                changes = self._diff(existing_nft, nft_info)
                if changes:
                    changes["address"] = existing_nft.address
                    self.nft_updates.append(changes)
                    logger.info(f"NFT {nft_address} changed: {list(changes.keys())}")
                return

            mint_info = await self._get_mint_info(nft_info.get("address"))
            open_data = await self._get_open_data(nft_info, mint_info)

            nft = NftBaseORM(
                **nft_info,
                collection_address=self.collection_address,
                mint_wallet_address=open_data.get("open_wallet_address"),
                mint_at=mint_info["time"],
            )
            self.nft_objects.append(nft)

            if self.collection_config.get("box_collection"):
                opening = OpeningORM(
                    **open_data,
                    nft_address=nft_info.get("address"),
                    open_at=mint_info["time"],
                )
                self.opening_objects.append(opening)

            await self._process_specific(nft_info, nft_address, item)

        except Exception as e:
            logger.error(f"Error processing NFT {item.get('address', 'unknown')}: {e}")

    # ------------------------------------------------------------------
    # Bulk save
    # ------------------------------------------------------------------

    async def bulk_save(self) -> bool:
        """Persist all buffered objects in one flush, then clear buffers."""
        try:
            # 1. New NFTs
            if self.nft_objects:
                self.db_session.add_all(self.nft_objects)
                await self.db_session.flush()
                logger.info(f"Inserted {len(self.nft_objects)} NFT objects")

            # 2. Updated NFTs — load + patch individually (small list by design)
            if self.nft_updates:
                await self._apply_updates()
                logger.info(f"Updated {len(self.nft_updates)} NFT objects")

            # 3. Openings (depend on NFTs existing first)
            if self.opening_objects:
                self.db_session.add_all(self.opening_objects)
                await self.db_session.flush()
                logger.info(f"Inserted {len(self.opening_objects)} opening objects")

            # 4. Collection-specific rows (stickers, boxes, …)
            if self.specific_objects:
                self.db_session.add_all(self.specific_objects)
                await self.db_session.flush()
                logger.info(f"Inserted {len(self.specific_objects)} specific objects")

            self._clear_buffers()
            return True

        except Exception as e:
            logger.error(f"Error during bulk save: {e}")
            await self.db_session.rollback()
            return False

    async def _apply_updates(self) -> None:
        from sqlalchemy import select
        from backend.app.models import NftBaseORM

        addresses = [u["address"] for u in self.nft_updates]
        stmt = select(NftBaseORM).where(NftBaseORM.address.in_(addresses))
        result = await self.db_session.execute(stmt)
        nfts_by_address = {n.address: n for n in result.scalars()}

        for update_data in self.nft_updates:
            addr = update_data["address"]
            nft = nfts_by_address.get(addr)
            if not nft:
                continue
            for key, value in update_data.items():
                if key != "address" and hasattr(nft, key):
                    setattr(nft, key, value)

        await self.db_session.flush()

    def _clear_buffers(self) -> None:
        self.nft_objects.clear()
        self.nft_updates.clear()
        self.opening_objects.clear()
        self.specific_objects.clear()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _diff(existing: NftBaseORM, nft_info: Dict[str, Any]) -> Dict[str, Any]:
        """Return only the fields that actually changed."""
        fields = ("price", "owner_wallet_address", "sale_type", "finish_at")
        return {
            f: nft_info[f]
            for f in fields
            if f in nft_info and getattr(existing, f) != nft_info[f]
        }

    @staticmethod
    def _parse_nft_info(item: Dict[str, Any]) -> Dict[str, Any]:
        from nft_shared.ton.parser import parse_ton_collection_nft_item
        return parse_ton_collection_nft_item(item)

    async def _get_mint_info(self, nft_address: str) -> Dict[str, Any]:
        try:
            nft_mint_info = await get_getgems_nft_history(
                self.api_session, nft_address, types="mint"
            )
            mint_info = nft_mint_info["response"]["items"][0]
            mint_time = datetime.fromisoformat(
                mint_info.get("time").replace("Z", "+00:00")
            )
            return {"hash": mint_info.get("hash"), "time": mint_time}
        except Exception as e:
            logger.error(f"Error getting mint info for {nft_address}: {e}")
            raise

    async def _get_open_data(
        self, nft_info: Dict[str, Any], mint_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        open_data = {"open_wallet_address": nft_info.get("open_wallet_address")}
        if self.collection_config.get("box_collection"):
            try:
                open_event_data = await get_event_details(
                    self.api_session, mint_info["hash"]
                )
                open_data = parse_open_event(open_event_data)
            except Exception as e:
                logger.warning(f"Error getting open data: {e}, using default")
        return open_data

    @abstractmethod
    async def _process_specific(
        self, nft_info: Dict[str, Any], nft_address: str, item: Dict[str, Any]
    ) -> None:
        """Process collection-specific logic (e.g. stickers, boxes)."""
        pass