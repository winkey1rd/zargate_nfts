from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models import NftBaseORM, StickerORM


class StickerRepository:
    """Repository for sticker-specific read operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_full_info(self, address: str) -> Optional[NftBaseORM]:
        """Load an NFT together with its sticker and all four attributes."""
        stmt = (
            select(NftBaseORM)
            .options(
                joinedload(NftBaseORM.stickers)
                    .joinedload(StickerORM.attr1),
                joinedload(NftBaseORM.stickers)
                    .joinedload(StickerORM.attr2),
                joinedload(NftBaseORM.stickers)
                    .joinedload(StickerORM.attr3),
                joinedload(NftBaseORM.stickers)
                    .joinedload(StickerORM.attr4),
            )
            .where(NftBaseORM.address == address)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def save_all(self, objects: list[StickerORM]) -> None:
        self.session.add_all(objects)
        await self.session.flush()