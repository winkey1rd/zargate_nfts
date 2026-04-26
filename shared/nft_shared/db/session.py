from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def build_engine(db_url: str, pool_size: int = 10, max_overflow: int = 5):
    return create_async_engine(
        db_url,
        pool_size=pool_size,
        max_overflow=max_overflow,
        echo=False,
    )


def build_session_factory(engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )


# FastAPI dependency — импортируется в backend после инициализации engine
async def get_session(session_factory: async_sessionmaker[AsyncSession]) -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        yield session