import logging
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import joinedload

from nft_shared.models.extra import MonitorRule, PriceSnapshot
from nft_shared.models.nft import NftBaseORM
from nft_shared.models.sticker import StickerORM
from monitor.app.filter_engine import matches_rule
from monitor.app.notifier import send_notification

logger = logging.getLogger(__name__)


async def run_all_checks(session_factory: async_sessionmaker[AsyncSession]) -> None:
    """
    Основной цикл мониторинга:
    1. Загружаем активные правила
    2. Для каждого правила находим подходящие стикеры
    3. Отправляем уведомления
    4. Сохраняем снапшоты цен
    """
    async with session_factory() as session:
        rules = await _load_active_rules(session)
        if not rules:
            return

        stickers = await _load_stickers_with_nft(session)
        logger.info(f"Checking {len(rules)} rules against {len(stickers)} stickers")

        for rule in rules:
            matches = []
            for sticker in stickers:
                nft = sticker.nft
                price = nft.price if nft else None
                if matches_rule(sticker, price, {"type": rule.rule_type, "filter_json": rule.filter_json}):
                    matches.append((sticker, nft))

            if matches:
                logger.info(f"Rule {rule.id} ({rule.rule_type}): {len(matches)} matches")
                await send_notification(rule.tg_chat_id, rule, matches)

        await _save_price_snapshots(session, stickers)
        await session.commit()


async def _load_active_rules(session: AsyncSession) -> List[MonitorRule]:
    stmt = select(MonitorRule).where(MonitorRule.is_active.is_(True))
    result = await session.execute(stmt)
    return list(result.scalars())


async def _load_stickers_with_nft(session: AsyncSession) -> List[StickerORM]:
    stmt = (
        select(StickerORM)
        .options(
            joinedload(StickerORM.nft),
            joinedload(StickerORM.attr1),
            joinedload(StickerORM.attr2),
            joinedload(StickerORM.attr3),
            joinedload(StickerORM.attr4),
        )
        .join(NftBaseORM, StickerORM.nft_address == NftBaseORM.address)
        .where(NftBaseORM.price.isnot(None))  # только выставленные на продажу
    )
    result = await session.execute(stmt)
    return list(result.unique().scalars())


async def _save_price_snapshots(
    session: AsyncSession, stickers: List[StickerORM]
) -> None:
    snapshots = [
        PriceSnapshot(nft_address=s.nft_address, price=s.nft.price)
        for s in stickers
        if s.nft and s.nft.price is not None
    ]
    session.add_all(snapshots)