import logging
from typing import Dict

import aiohttp

logger = logging.getLogger(__name__)


async def get_session() -> aiohttp.ClientSession:
    """Получает или создает глобальную сессию aiohttp."""
    timeout = aiohttp.ClientTimeout(total=10)
    _session = aiohttp.ClientSession(timeout=timeout)
    return _session

async def close_session(_session):
    """Закрывает глобальную сессию aiohttp."""
    if _session and not _session.closed:
        await _session.close()
        _session = None

def get_headers(key, is_bearer: bool = True) -> Dict[str, str]:
    """
    Получает заголовки для запросов к API с авторизацией.

    Returns:
        Словарь с заголовками запроса
    """
    headers = {}
    if key:
        headers["Authorization"] = f"Bearer {key}" if is_bearer else key
    return headers

async def get_session_response(session, url: str, headers: dict, params: dict):
    errors = {
        405: "405 Method Not Allowed",
        404: "404 Not Found",
    }
    try:
        async with session.get(url, headers=headers, params=params) as response:
            if response.status in errors or response.status >= 400:
                log = errors.get(response.status, "Bad Request")
                logger.error(log)
                return None

            data = await response.json()
            return data
    except aiohttp.ClientError as e:
        logger.error(f"Error url {url} with params {params}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error url {url} with params {params}: {e}")
        return None