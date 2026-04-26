from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import joinedload


from nft_shared.crud.base import BaseRepository
from nft_shared.models.nft import NftBaseORM
from nft_shared.models.sticker import StickerORM, AttributeORM

class StickerRepository(BaseRepository[StickerORM]):
    model = StickerORM

    async def get_full_info(self, address: str) -> Optional[NftBaseORM]:
        """NFT + стикер + все 4 атрибута за один запрос."""
        stmt = (
            select(NftBaseORM)
            .options(
                joinedload(NftBaseORM.stickers).joinedload(StickerORM.attr1),
                joinedload(NftBaseORM.stickers).joinedload(StickerORM.attr2),
                joinedload(NftBaseORM.stickers).joinedload(StickerORM.attr3),
                joinedload(NftBaseORM.stickers).joinedload(StickerORM.attr4),
            )
            .where(NftBaseORM.address == address)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_stickers_by_owners(
        self, owner_addresses: List[str]
    ) -> List[StickerORM]:
        """Все стикеры для списка кошельков — один запрос с JOIN."""
        stmt = (
            select(StickerORM)
            .join(NftBaseORM, StickerORM.nft_address == NftBaseORM.address)
            .options(
                joinedload(StickerORM.attr1),
                joinedload(StickerORM.attr2),
                joinedload(StickerORM.attr3),
                joinedload(StickerORM.attr4),
                joinedload(StickerORM.nft),
            )
            .where(NftBaseORM.owner_wallet_address.in_(owner_addresses))
        )
        result = await self.session.execute(stmt)
        return list(result.unique().scalars())

    async def load_all_attributes(self) -> dict[tuple, AttributeORM]:
        """Загрузить весь кэш атрибутов за один SELECT — используется в handler."""
        stmt = select(AttributeORM)
        result = await self.session.execute(stmt)
        return {(a.trait_type, a.value): a for a in result.scalars()}
