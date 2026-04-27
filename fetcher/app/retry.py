import asyncio
import logging
from enum import Enum
from typing import Callable, TypeVar

logger = logging.getLogger(__name__)
T = TypeVar("T")


class ErrorKind(Enum):
    RATE_LIMIT = "rate_limit"   # 429
    SERVER     = "server"       # 5xx
    NETWORK    = "network"      # таймаут / обрыв соединения
    FATAL      = "fatal"        # прочее — не повторяем


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
    from fetcher.app.settings import settings
    return {
        ErrorKind.RATE_LIMIT: settings.retry.seconds_429,
        ErrorKind.SERVER:     settings.retry.seconds_5xx,
        ErrorKind.NETWORK:    settings.retry.seconds_network,
        ErrorKind.FATAL:      0.0,
    }[kind]


async def with_retry(coro_fn: Callable, *args, task_name: str = "task", **kwargs):
    from fetcher.app.settings import settings
    max_attempts = settings.retry.max_attempts

    for attempt in range(1, max_attempts + 1):
        try:
            return await coro_fn(*args, **kwargs)
        except Exception as exc:
            kind = classify_error(exc)
            delay = get_delay(kind)

            if kind == ErrorKind.FATAL or attempt == max_attempts:
                logger.error(
                    f"[{task_name}] attempt {attempt}/{max_attempts} "
                    f"fatal ({kind.value}): {exc}"
                )
                raise

            logger.warning(
                f"[{task_name}] attempt {attempt}/{max_attempts} "
                f"failed ({kind.value}): {exc}. Retry in {delay}s."
            )
            await asyncio.sleep(delay)