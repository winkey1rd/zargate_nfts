from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models import NftBaseORM, AttributeORM, OpeningORM

class NftRepository:
    """Repository for sticker operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_nft_by_address(self, address: str) -> Optional[NftBaseORM]:
        return self.session.query(NftBaseORM).filter_by(
            address=address
        ).first()

    def get_attributes_by_value(
        self,
        trait_type: str,
        value: str,
    ) -> Optional[AttributeORM]:
        """Получает коллекцию пользователя."""
        return self.session.query(AttributeORM).filter_by(
            trait_type=trait_type,
            value=value
        ).first()

    def get_open_event_by_hash(self, event_hash: str) -> Optional[OpeningORM]:
        return self.session.query(OpeningORM).filter_by(
            hash=event_hash
        ).first()
