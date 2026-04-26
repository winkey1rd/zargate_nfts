from typing import Optional

from sqlalchemy import select

from nft_shared.crud.base import BaseRepository
from nft_shared.models.user import Wallet


class WalletRepository(BaseRepository[Wallet]):
    model = Wallet

    async def get_by_token(self, token: str) -> Optional[Wallet]:
        stmt = select(Wallet).where(Wallet.token == token)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_address(self, address: str) -> Optional[Wallet]:
        stmt = select(Wallet).where(Wallet.address == address)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[Wallet]:
        stmt = select(Wallet).where(Wallet.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, wallet: Wallet) -> Wallet:
        self.session.add(wallet)
        await self.session.flush()
        return wallet