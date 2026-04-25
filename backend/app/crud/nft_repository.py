from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models import NftBaseORM, AttributeORM, OpeningORM


class NftRepository:
    """Repository for base NFT operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_address(self, address: str) -> Optional[NftBaseORM]:
        stmt = select(NftBaseORM).where(NftBaseORM.address == address)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_attribute_by_value(
        self,
        trait_type: str,
        value: str,
    ) -> Optional[AttributeORM]:
        stmt = select(AttributeORM).where(
            AttributeORM.trait_type == trait_type,
            AttributeORM.value == value,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_opening_by_hash(self, event_hash: str) -> Optional[OpeningORM]:
        stmt = select(OpeningORM).where(OpeningORM.hash == event_hash)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def save_all(self, objects: list) -> None:
        """Bulk-add a list of ORM objects and flush."""
        self.session.add_all(objects)
        await self.session.flush()