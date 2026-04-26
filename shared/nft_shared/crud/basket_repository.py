from typing import List, Optional

from sqlalchemy import select

from nft_shared.crud.base import BaseRepository

from nft_shared.models.basket import BasketItem, TradeItem



class BasketRepository(BaseRepository[BasketItem]):
    model = BasketItem

    async def get_by_sticker(self, sticker_address: str) -> Optional[BasketItem]:
        stmt = select(BasketItem).where(BasketItem.sticker_address == sticker_address)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_owner(self, owner_address: str) -> List[BasketItem]:
        stmt = select(BasketItem).where(BasketItem.owner_address == owner_address)
        result = await self.session.execute(stmt)
        return list(result.scalars())

    async def get_by_recipient(self, recipient_address: str) -> List[BasketItem]:
        stmt = select(BasketItem).where(BasketItem.recipient_address == recipient_address)
        result = await self.session.execute(stmt)
        return list(result.scalars())

    async def create(self, item: BasketItem) -> BasketItem:
        self.session.add(item)
        await self.session.flush()
        return item


class TradeRepository(BaseRepository[TradeItem]):
    model = TradeItem

    async def get_by_sticker(self, sticker_address: str) -> Optional[TradeItem]:
        stmt = select(TradeItem).where(TradeItem.sticker_address == sticker_address)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_wallet(self, wallet_address: str) -> List[TradeItem]:
        stmt = select(TradeItem).where(TradeItem.added_address == wallet_address)
        result = await self.session.execute(stmt)
        return list(result.scalars())

    async def create(self, item: TradeItem) -> TradeItem:
        self.session.add(item)
        await self.session.flush()
        return item
