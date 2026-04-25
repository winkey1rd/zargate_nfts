from typing import Optional, List

from sqlalchemy import select, delete
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models import NftBaseORM, StickerORM
from backend.app.models.sticker import Sticker


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

    async def get_all_by_wallet_address(self, wallet_address: str) -> List[Sticker]:
        """Get all stickers for a wallet by address."""
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
            .where(NftBaseORM.owner_wallet_address == wallet_address)
        )
        result = await self.session.execute(stmt)
        data = result.all()
        # TODO: convert to list of Stickers
        return data

    async def clear_all(self):
        """Clear all stickers."""
        stmt = (delete(Sticker))
        result = await self.session.execute(stmt)
