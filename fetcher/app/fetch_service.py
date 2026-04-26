import asyncio
import logging
from typing import List

import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from nft_shared.config.collections import COLLECTIONS, COLLECTIONS_BY_ADDRESS
from nft_shared.crud.nft_repository import NftRepository
from nft_shared.handlers.base_handler import CollectionHandler
from nft_shared.handlers.stickers_handler import StickersCollectionHandler
from nft_shared.handlers.boxes_handler import BoxesCollectionHandler
from nft_shared.ton.client import get_ton_collection_nft, get_ton_items, get_ton_cursor
from nft_shared.utility.calculator import get_attribute_values_for_collection
from fetcher.app.retry import with_retry
from fetcher.app.settings import settings

logger = logging.getLogger(__name__)

HANDLER_MAP = {
    "Unstoppable Tribe from ZarGates": StickersCollectionHandler,
    "ZarGates GiftBoxes":              BoxesCollectionHandler,
    "ZarGates StickerBoxes":           BoxesCollectionHandler,
}


async def fetch_collection(
    collection_address: str,
    session_factory: async_sessionmaker[AsyncSession],
    api_session: aiohttp.ClientSession,
    semaphore: asyncio.Semaphore,
) -> int:
    """
    Загружает все NFT одной коллекции постранично.
    Каждый батч сохраняется транзакционно.
    Возвращает общее количество обработанных NFT.
    """
    collection_name = COLLECTIONS_BY_ADDRESS.get(collection_address)
    if not collection_name:
        logger.warning(f"Unknown collection address: {collection_address}")
        return 0

    handler_class = HANDLER_MAP.get(collection_name)
    if not handler_class:
        logger.warning(f"No handler for collection: {collection_name}")
        return 0

    attribute_values = get_attribute_values_for_collection(collection_address)
    total = 0
    cursor = ""

    async with session_factory() as db_session:
        nft_repo = NftRepository(db_session)
        handler: CollectionHandler = handler_class(
            collection_address=collection_address,
            db_session=db_session,
            api_session=api_session,
            attribute_values=attribute_values,
            nft_repository=nft_repo,
        )

        while True:
            async with semaphore:
                data = await with_retry(
                    get_ton_collection_nft,
                    api_session,
                    collection_address,
                    cursor,
                    task_name=f"fetch_page:{collection_name}",
                )

            if not data:
                break

            items = get_ton_items(data)
            if not items:
                break

            # Параллельная обработка NFT внутри батча
            await asyncio.gather(
                *[handler.process_nft(item) for item in items],
                return_exceptions=True,
            )

            saved = await handler.bulk_save()
            if not saved:
                logger.error(f"Bulk save failed for {collection_name}, rolling back")
                await db_session.rollback()
                break

            await db_session.commit()
            total += len(items)
            logger.info(f"[{collection_name}] committed {len(items)} (total: {total})")

            cursor = get_ton_cursor(data, cursor)
            if not cursor:
                break

    logger.info(f"[{collection_name}] fetch complete: {total} NFTs")
    return total


async def fetch_all_collections(session_factory: async_sessionmaker[AsyncSession]) -> None:
    """Запускает fetch всех коллекций параллельно с общим semaphore."""
    semaphore = asyncio.Semaphore(settings.fetch_semaphore_size)

    async with aiohttp.ClientSession() as api_session:
        tasks = [
            fetch_collection(info["address"], session_factory, api_session, semaphore)
            for info in COLLECTIONS.values()
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    for name, result in zip(COLLECTIONS.keys(), results):
        if isinstance(result, Exception):
            logger.error(f"Collection {name} failed: {result}")
        else:
            logger.info(f"Collection {name}: {result} NFTs processed")
