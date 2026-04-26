from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from nft_shared.db.session import build_engine, build_session_factory
from api.app.settings import settings

engine = build_engine(settings.db.url)
_session_factory = build_session_factory(engine)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with _session_factory() as session:
        yield session