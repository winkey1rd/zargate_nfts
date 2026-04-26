import logging
from typing import Dict


from nft_shared.getgems.config import GETGEMS_API_KEY
from nft_shared.utility import get_headers

logger = logging.getLogger(__name__)

def get_getgems_headers() -> Dict[str, str]:
    """
    Получает заголовки для запросов к API с авторизацией.

    Returns:
        Словарь с заголовками запроса
    """
    return get_headers(GETGEMS_API_KEY)
