from sqlalchemy.ext.asyncio import AsyncSession
import logging

from nft.config import COLLECTIONS, COLLECTIONS_BY_ADDRESS

from backend.app.models import NftCollectionORM

from ton.api.collection import get_ton_collection_nft, get_ton_cursor, get_ton_items

from utility.calculator import *

from .stickers_handler import StickersCollectionHandler
from .boxes_handler import BoxesCollectionHandler

logger = logging.getLogger(__name__)


async def populate_collections(session: AsyncSession):
    """Внести коллекции в БД."""
    for name, info in COLLECTIONS.items():
        collection = NftCollectionORM(address=info.get("address"), name=name)
        session.add(collection)
    session.commit()


async def fetch_and_insert_nfts(collection_address: str, db_session: AsyncSession, api_session):
    """Получить NFT из коллекции и вставить в БД."""
    try:
        # Get attribute values for stickers
        attribute_values = get_attribute_values_for_collection(collection_address)

        # Get collection name
        collection_name = COLLECTIONS_BY_ADDRESS.get(collection_address)
        if not collection_name:
            logger.warning(f"Unknown collection address: {collection_address}")
            return

        # Handler mapping
        handlers = {
            "Unstoppable Tribe from ZarGates": StickersCollectionHandler,
            "ZarGates GiftBoxes": BoxesCollectionHandler,
            "ZarGates StickerBoxes": BoxesCollectionHandler,
        }

        handler_class = handlers.get(collection_name)
        if not handler_class:
            logger.warning(f"No handler found for collection: {collection_name}")
            return

        handler = handler_class(collection_address, db_session, api_session, attribute_values)

        cursor = ""
        total_processed = 0
        
        while True:
            try:
                data = await get_ton_collection_nft(api_session, collection_address, cursor)
                if not data:
                    break
                items = get_ton_items(data)
                
                for item in items:
                    await handler.process_nft(item)
                
                # Bulk save after each batch
                if not await handler.bulk_save():
                    logger.error("Bulk save failed, rolling back transaction")
                    await db_session.rollback()
                    return
                
                # Commit after successful bulk save
                await db_session.commit()
                total_processed += len(items)
                logger.info(f"Processed and committed {len(items)} items (total: {total_processed})")

                cursor = get_ton_cursor(data, cursor)
                if not cursor:
                    break
                    
            except Exception as e:
                logger.error(f"Error processing batch: {e}")
                await db_session.rollback()
                raise
        
        logger.info(f"Successfully processed {total_processed} NFTs for collection {collection_address}")
        
    except Exception as e:
        logger.error(f"Fatal error in fetch_and_insert_nfts: {e}")
        await db_session.rollback()
        raise
