from datetime import datetime, timezone
from typing import Callable

from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from nft_shared.crud.wallet_repository import WalletRepository
from nft_shared.models.user import Wallet
from nft_shared.db import get_session


async def get_current_wallet(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> Wallet:
    """
    Извлекает кошелёк из заголовка X-Token.
    Обновляет last_query_at.
    Кладёт объект в request.state.wallet для последующих слоёв.
    """
    token = request.headers.get("X-Token")
    if not token:
        raise HTTPException(status_code=401, detail="X-Token header missing")

    repo = WalletRepository(session)
    wallet = await repo.get_by_token(token)
    if not wallet:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Обновляем время последнего запроса
    wallet.last_query_at = datetime.now(timezone.utc)
    await session.flush()

    request.state.wallet = wallet
    return wallet


def require_flag(flag_name: str) -> Callable:
    """
    Фабрика зависимостей: проверяет, что у кошелька включён нужный флаг.

    Использование:
        @router.get("/synergy", dependencies=[Depends(require_flag("is_synergy"))])
    """
    async def _check(wallet: Wallet = Depends(get_current_wallet)) -> Wallet:
        if not getattr(wallet, flag_name, False):
            raise HTTPException(
                status_code=403,
                detail=f"Access to this section is disabled (flag: {flag_name})",
            )
        return wallet

    _check.__name__ = f"require_{flag_name}"
    return _check