import asyncio
import logging
from enum import Enum
from typing import Callable, TypeVar

from fetcher.app.settings import settings

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ErrorKind(Enum):
    RATE_LIMIT = "rate_limit"   # 429 — ждём долго
    SERVER = "server"           # 5xx — ждём средне
    NETWORK = "network"         # сетевая ошибка — ждём мало
    FATAL = "fatal"             # прочее — не повторяем


def classify_error(exc: Exception) -> ErrorKind:
    msg = str(exc).lower()
    if "429" in msg or "rate limit" in msg or "too many" in msg:
        return ErrorKind.RATE_LIMIT
    if any(code in msg for code in ("500", "502", "503", "504")):
        return ErrorKind.SERVER
    if any(k in msg for k in ("timeout", "connection", "network", "ssl")):
        return ErrorKind.NETWORK
    return ErrorKind.FATAL


def get_delay(kind: ErrorKind) -> float:
    return {
        ErrorKind.RATE_LIMIT: settings.retry_429_seconds,
        ErrorKind.SERVER:     settings.retry_5xx_seconds,
        ErrorKind.NETWORK:    settings.retry_network_seconds,
        ErrorKind.FATAL:      0.0,
    }[kind]


async def with_retry(coro_fn: Callable, *args, task_name: str = "task", **kwargs):
    """
    Выполняет корутину с retry-логикой по типу ошибки.
    FATAL-ошибки не повторяются — сразу поднимаются выше.
    """
    for attempt in range(1, settings.retry_max_attempts + 1):
        try:
            return await coro_fn(*args, **kwargs)
        except Exception as exc:
            kind = classify_error(exc)
            delay = get_delay(kind)

            if kind == ErrorKind.FATAL or attempt == settings.retry_max_attempts:
                logger.error(
                    f"[{task_name}] attempt {attempt}/{settings.retry_max_attempts} "
                    f"failed with {kind.value}: {exc}. No more retries."
                )
                raise

            logger.warning(
                f"[{task_name}] attempt {attempt}/{settings.retry_max_attempts} "
                f"failed with {kind.value}: {exc}. Retrying in {delay}s."
            )
            await asyncio.sleep(delay)