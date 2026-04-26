from typing import Optional, Dict, Any

from nft_shared.getgems.config import GETGEMS_API_BASE_URL
from nft_shared.getgems.session import get_getgems_headers
from nft_shared.utility import get_session_response


async def get_getgems_nft_info(session, nft_address: str) -> Optional[Dict[str, Any]]:
    """
    Асинхронно получает информацию о NFT через API Getgems.

    Args:
        nft_address: Адрес NFT

    Returns:
        Словарь с данными NFT или None в случае ошибки
    """
    url = f"{GETGEMS_API_BASE_URL}/v1/config/{nft_address}"
    headers = get_getgems_headers()
    params = {}
    data = await get_session_response(session, url, headers, params)
    return data


async def get_getgems_nft_history(session, nft_address: str, min_time: Optional[int] = None,
                                  max_time: Optional[int] = None,
                                  types: Optional[str] = None
                                  ) -> Optional[Dict[str, Any]]:
    """
    {
  "success": true,
  "response": {
    "cursor": null,
    "items": [
      {
        "address": "EQBx3nFVyj1TGkX1agdXATgS4TEMkBd5-Zj_4wmDED9Zh3Ij",
        "name": "Orc Capped #13",
        "time": "2025-12-30T16:11:24.000Z",
        "timestamp": 1767111084000,
        "collectionAddress": "EQBGNoXXfQR07HdDhtkmIu1ojTTwcjB0EhHYOMSH3P7sZGJR",
        "lt": "65238460000009",
        "hash": "ad3eaad27b2b9df3a06b6b793ab847a803a5bf4d0487ed6804e89ee7147ff78d",
        "typeData": {
          "type": "mint"
        },
        "isOffchain": false
      }
    ]
  }
}
    """
    url = f"{GETGEMS_API_BASE_URL}/v1/config/history/{nft_address}"
    headers = get_getgems_headers()
    params = {}
    if min_time is not None:
        params["minTime"] = min_time
    if max_time is not None:
        params["maxTime"] = max_time
    if types is not None:
        params["types"] = types

    data = await get_session_response(session, url, headers, params)
    return data
