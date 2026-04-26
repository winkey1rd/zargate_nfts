from typing import List, Optional

from sqlalchemy import select

from nft_shared.crud.base import BaseRepository

from nft_shared.models.extra import UserSession

class SessionRepository(BaseRepository[UserSession]):
    model = UserSession

    async def get_by_wallet(self, wallet_address: str) -> Optional[UserSession]:
        stmt = select(UserSession).where(UserSession.wallet_address == wallet_address)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert(self, wallet_address: str, wallets: List[str]) -> UserSession:
        existing = await self.get_by_wallet(wallet_address)
        if existing:
            existing.wallets = wallets
            await self.session.flush()
            return existing
        new = UserSession(wallet_address=wallet_address, wallets=wallets)
        self.session.add(new)
        await self.session.flush()
        return new
