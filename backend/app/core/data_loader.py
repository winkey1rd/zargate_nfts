"""
Data loader module - handles loading stickers from API and storing in database.
Implements: fetch from API → store in DB → avoid duplicates
"""
from typing import Dict, List

from backend.getgems import get_getgems_owner_collection_nft
from transfer_app.db.repositories import WalletRepository, StickerRepository
from transfer_app.db.database import Database
from transfer_app.config.config import ATTRIBUTE_GROUPS
from transfer_app.utils.json_loader import load_collection_json
import logging

from backend.utility.calculator import calculate_nft_value, normalize_logo
from backend.utility import get_session

logger = logging.getLogger(__name__)

# Try to import async API fetcher; if missing, provide a safe fallback


class DataLoader:
    """
    Loads NFT data from API and stores in database.
    Handles deduplication by sticker address.
    """
    
    def __init__(self, database: Database):
        self.database = database
        # Do not keep long-lived sessions/repositories — create per-operation
        self.attribute_groups = ATTRIBUTE_GROUPS
    
    async def load_wallet(self, wallet_address: str, collection_address: str) -> int:
        """
        Load wallet stickers from API and save to database.
        Updates existing stickers, ignores duplicates.
        
        Args:
            wallet_address: Wallet address to load
            collection_address: Collection address
        
        Returns:
            Number of stickers loaded/updated
        """
        logger.info(f"Loading wallet: {wallet_address}")
        
        # Use a short-lived DB session and repositories for this load
        session = self.database.get_session()
        wallet_repo = WalletRepository(session)
        sticker_repo = StickerRepository(session)

        # Get or create wallet in DB
        wallet = wallet_repo.get_or_create(wallet_address)
        
        try:
            # Fetch from API in batches
            nfts = []
            cursor = None
            session = await get_session()
            while True:
                api_response = await get_getgems_owner_collection_nft(
                    session,
                    wallet_address,
                    collection_address,
                    cursor=cursor if cursor else ""
                )
                
                if not api_response:
                    logger.warning(f"No response from API for wallet {wallet_address}")
                    break
                
                # Extract NFTs from API response - GetGems API structure: response.items
                if isinstance(api_response, dict):
                    response_data = api_response.get('response', {})
                    batch_items = response_data.get('items', []) if isinstance(response_data, dict) else []
                    # batch_items = [item for item in batch_items if item.get("collectionAddress") == collection_address]
                    if not batch_items:
                        logger.debug(f"No items in response for {wallet_address}")
                        break
                    
                    nfts.extend(batch_items)
                    
                    # Check for pagination cursor
                    cursor = response_data.get('cursor') if isinstance(response_data, dict) else None
                    print(cursor)
                    if not cursor:
                        break
                else:
                    logger.error(f"API response is not dict: {type(api_response)}")
                    break
            
            if not nfts:
                logger.warning(f"No NFTs found for wallet {wallet_address}")
                return 0
            
            logger.info(f"Fetched {len(nfts)} NFTs from API for {wallet_address}")
            
            # Load attribute definitions
            attribute_values = load_collection_json(f"transfer_app/data/{collection_address}.json")
            
            # Process and store stickers
            stored_count = 0
            for nft in nfts:
                try:
                    sticker_data = self._prepare_sticker_data(
                        nft, 
                        wallet_address, 
                        attribute_values
                    )
                    sticker_repo.create_or_update(sticker_data)
                    stored_count += 1
                except Exception as e:
                    nft_addr = nft.get('address', '?') if isinstance(nft, dict) else str(nft)[:30]
                    logger.error(f"Error processing sticker {nft_addr}: {repr(e)}")
                    continue
            
            # Update wallet stats
            total_stickers = len(sticker_repo.get_by_wallet(wallet.id))
            total_value = sum(s.total_value for s in sticker_repo.get_by_wallet(wallet.id))
            wallet_repo.update_stats(wallet.id, total_stickers, total_value)
            
            logger.info(f"Loaded {stored_count} stickers for wallet {wallet_address[:20]}...")
            return stored_count
        
        except Exception as e:
            logger.error(f"Failed to load wallet {wallet_address}: {e}")
            raise
        finally:
            try:
                session.close()
            except Exception:
                pass
    
    async def load_multiple_wallets(self, wallet_addresses: List[str], collection_address: str) -> Dict[str, int]:
        """
        Load multiple wallets concurrently.
        
        Args:
            wallet_addresses: List of wallet addresses
            collection_address: Collection address
        
        Returns:
            Dictionary mapping wallet address to sticker count
        """
        results = {}
        for wallet in wallet_addresses:
            try:
                count = await self.load_wallet(wallet, collection_address)
                results[wallet] = count
            except Exception as e:
                logger.error(f"Failed to load {wallet}: {e}")
                results[wallet] = 0
        
        return results
    
    def _prepare_sticker_data(self, nft: Dict, wallet_address: str, attribute_values: Dict) -> Dict:
        """
        Prepare sticker data from API response for database storage.
        
        Args:
            nft: NFT data from API
            wallet_address: Owner wallet address
            attribute_values: Attribute definitions
        
        Returns:
            Dictionary ready for StickerRepository.create_or_update()
        """
        # Ensure NFT is a dict
        if isinstance(nft, str):
            logger.error(f"NFT data is string, not dict: {nft}")
            raise ValueError(f"Invalid NFT data format: {nft}")
        
        if not isinstance(nft, dict):
            logger.error(f"NFT data is {type(nft)}, expected dict: {nft}")
            raise ValueError(f"Invalid NFT data type: {type(nft)}")
        
        # Extract basic info
        nft_address = nft.get('address', '')
        if not nft_address:
            logger.warning(f"NFT has no address: {nft}")
            raise ValueError("NFT missing address field")
        
        nft_name = nft.get('name', 'Unknown')
        
        # Handle image URL
        image_url = nft.get('image', '')
        if isinstance(image_url, dict):
            image_url = image_url.get('url', '')
        
        # Extract attributes from API format: [{ traitType, value }, ...]
        attributes = {}
        skin_tone = None
        
        attributes_raw = nft.get('attributes', [])
        if not isinstance(attributes_raw, list):
            logger.warning(f"Attributes for {nft_address} is not list: {type(attributes_raw)}")
            attributes_raw = []
        
        for attr in attributes_raw:
            if not isinstance(attr, dict):
                continue
            
            trait_type = attr.get('traitType', attr.get('trait_type'))
            trait_value = attr.get('value')
            
            if not trait_type or not trait_value:
                continue
            
            # Extract skin tone
            if trait_type == 'Skin Tone':
                skin_tone = trait_value
                continue
            
            # Group attributes - find which group this trait belongs to
            group_name = None
            for gn, trait_names in self.attribute_groups.items():
                if trait_type in trait_names:
                    group_name = gn
                    break
            
            # If trait not found in any group, it's a Logo (default)
            if not group_name:
                group_name = "Logos"
            
            # Normalize logos
            if group_name == "Logos":
                trait_value = normalize_logo(trait_value)
            
            if group_name not in attributes:
                attributes[group_name] = []
            
            # if trait_value not in attributes[group_name]:
            attributes[group_name].append(trait_value)
        
        # Validate required fields
        if not skin_tone:
            logger.warning(f"NFT {nft_address} has no skin tone - skipping")
            raise ValueError("NFT missing skin tone")
        
        # Extract emotion from name
        from transfer_app.config.config import EMOTIONS
        emotion = next((e for e in EMOTIONS if e in nft_name), 'Neutral')
        
        # Calculate values using old logic
        attr_value, synergy_bonus, name_value, num_features = calculate_nft_value(
            attributes_raw, attribute_values, nft_name
        )
        total_value = attr_value + synergy_bonus + name_value
        
        return {
            'address': nft_address,
            'wallet_address': wallet_address,
            'name': nft_name,
            'image_url': image_url,
            'emotion': emotion,
            'skin_tone': skin_tone,
            'attributes': attributes,
            'attr_value': attr_value,
            'synergy_bonus': synergy_bonus,
            'name_value': name_value,
            'total_value': total_value
        }
