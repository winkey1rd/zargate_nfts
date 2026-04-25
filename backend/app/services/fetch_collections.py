from sqlalchemy.ext.asyncio import AsyncSession
import logging

from nft.config import COLLECTIONS, COLLECTIONS_BY_ADDRESS

from backend.app.models import NftCollectionORM
from backend.app.crud.nft_repository import NftRepository
from backend.ton.api import get_ton_collection_nft, get_ton_cursor, get_ton_items
from backend.utility.calculator import get_attribute_values_for_collection

from .stickers_handler import StickersCollectionHandler
from .boxes_handler import BoxesCollectionHandler

logger = logging.getLogger(__name__)


async def populate_collections(session: AsyncSession) -> None:
    """Insert collections into DB."""
    for name, info in COLLECTIONS.items():
        collection = NftCollectionORM(address=info.get("address"), name=name)
        session.add(collection)
    await session.commit()


async def fetch_and_insert_nfts(
    collection_address: str,
    db_session: AsyncSession,
    api_session,
) -> None:
    """Fetch NFTs from a collection and upsert them into the DB."""
    try:
        collection_name = COLLECTIONS_BY_ADDRESS.get(collection_address)
        if not collection_name:
            logger.warning(f"Unknown collection address: {collection_address}")
            return

        attribute_values = get_attribute_values_for_collection(collection_address)

        # Build shared NftRepository once — injected into every handler
        nft_repository = NftRepository(db_session)

        handler_class_map = {
            "Unstoppable Tribe from ZarGates": StickersCollectionHandler,
            "ZarGates GiftBoxes": BoxesCollectionHandler,
            "ZarGates StickerBoxes": BoxesCollectionHandler,
        }

        handler_class = handler_class_map.get(collection_name)
        if not handler_class:
            logger.warning(f"No handler found for collection: {collection_name}")
            return

        handler = handler_class(
            collection_address=collection_address,
            db_session=db_session,
            api_session=api_session,
            attribute_values=attribute_values,
            nft_repository=nft_repository,
        )

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

                if not await handler.bulk_save():
                    logger.error("Bulk save failed, rolling back")
                    await db_session.rollback()
                    return

                await db_session.commit()
                total_processed += len(items)
                logger.info(
                    f"Committed {len(items)} items (total: {total_processed})"
                )

                cursor = get_ton_cursor(data, cursor)
                if not cursor:
                    break

            except Exception as e:
                logger.error(f"Error processing batch: {e}")
                await db_session.rollback()
                raise

        logger.info(
            f"Finished: {total_processed} NFTs for {collection_address}"
        )

    except Exception as e:
        logger.error(f"Fatal error in fetch_and_insert_nfts: {e}")
        await db_session.rollback()
        raise