from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from nft_shared.crud.base import BaseRepository
from nft_shared.models.nft import NftBaseORM
from nft_shared.models.sticker import AttributeORM
from nft_shared.models.extra import OpeningORM


class NftRepository(BaseRepository[NftBaseORM]):
    model = NftBaseORM

    async def get_by_address(self, address: str) -> Optional[NftBaseORM]:
        stmt = select(NftBaseORM).where(NftBaseORM.address == address)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_owner(self, owner_address: str) -> List[NftBaseORM]:
        stmt = select(NftBaseORM).where(NftBaseORM.owner_wallet_address == owner_address)
        result = await self.session.execute(stmt)
        return list(result.scalars())

    async def get_by_owners(self, owner_addresses: List[str]) -> List[NftBaseORM]:
        stmt = select(NftBaseORM).where(
            NftBaseORM.owner_wallet_address.in_(owner_addresses)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars())

    async def get_attribute_by_value(
        self, trait_type: str, value: str
    ) -> Optional[AttributeORM]:
        stmt = select(AttributeORM).where(
            AttributeORM.trait_type == trait_type,
            AttributeORM.value == value,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_attribute(
        self,
        trait_type: str,
        value: str,
        attribute_group: str,
        attribute_value: int,
    ) -> AttributeORM:
        """INSERT ... ON CONFLICT DO NOTHING, затем SELECT."""
        stmt = (
            pg_insert(AttributeORM)
            .values(
                trait_type=trait_type,
                value=value,
                attribute_group=attribute_group,
                attribute_value=attribute_value,
            )
            .on_conflict_do_nothing(constraint="uq_attribute_trait_value")
        )
        await self.session.execute(stmt)
        return await self.get_attribute_by_value(trait_type, value)

    async def get_opening_by_hash(self, event_hash: str) -> Optional[OpeningORM]:
        stmt = select(OpeningORM).where(OpeningORM.hash == event_hash)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def merge_nft(self, nft: NftBaseORM) -> NftBaseORM:
        """Полное обновление через session.merge — SQLAlchemy генерирует UPDATE только изменившихся полей."""
        merged = await self.session.merge(nft)
        await self.session.flush()
        return merged
