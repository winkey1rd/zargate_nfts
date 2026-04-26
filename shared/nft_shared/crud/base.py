from typing import Generic, Optional, Sequence, Type, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from nft_shared.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    model: Type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_pk(self, pk) -> Optional[ModelT]:
        return await self.session.get(self.model, pk)

    async def save_all(self, objects: Sequence[ModelT]) -> None:
        self.session.add_all(objects)
        await self.session.flush()

    async def delete(self, obj: ModelT) -> None:
        await self.session.delete(obj)
        await self.session.flush()