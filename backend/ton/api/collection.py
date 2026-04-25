from typing import Optional, Dict, Any

from backend.ton.config import TON_API_KEY
from backend.ton.session import get_ton_headers
from backend.utility import get_session_response


async def get_ton_collection_nft(
        session,
        collection_address: str,
        cursor: Optional[str] = "",
        limit: int = 100
) -> Optional[Dict[str, Any]]:
    """
      item for sticker collection Unstoppable Tribe from ZarGates EQBGNoXXfQR07HdDhtkmIu1ojTTwcjB0EhHYOMSH3P7sZGJR
      {
      "address": "0:bd2d9d5bc2a87450c927d6ba1c1a72680bdedada6079af15275162064be4939c",
      "index": 0,
      "owner": {
        "address": "0:7c1ff59472efeaddc55dccbf86e7d6dd8b9585c7ba2580d6203179838a20db55",
        "is_scam": false,
        "is_wallet": true
      },
      "collection": {
        "address": "0:463685d77d0474ec774386d92622ed688d34f07230741211d838c487dcfeec64",
        "name": "Unstoppable Tribe from ZarGates",
        "description": "Welcome to the Unstoppable Tribe!\n\nWe invite you to join ZarGates and become a full-fledged member of our unique community of gamers and investors!\n\nEvery member gains access to exclusive drops, thrilling events, and generous rewards. Together, we are truly unstoppable!\n\nHow Does It Work?\nThe model is simple: as our community grows, we attract more partners and increase the number of drops. As a result, the value of your Orcs increases, opening up new opportunities for further collaboration and enabling even more drops to take place.\n\nSimple, isn’t it?\n\nThe amazing product, dedicated community, tier 1 partners, and a stellar reputation set us apart.\n\nKicking off this year with incredible momentum, an x11 increase in our drop has already been achieved, and we've reached the Top sticker collection in Telegram!\n\nWe welcome you!\n\nThe ZarGates Team"
      },
      "verified": true,
      "metadata": {
        "lottie": "https://metadata.zargates.com/stickers/1600000.lottie.json",
        "buttons": [
          {
            "label": "Get Gear!",
            "uri": "https://t.me/ZARGatesBot/twa?startapp=utm_source=button-get-gear==utm_medium=unstoppable-tribe-from-zg==utm_campaign=sticker-orc"
          }
        ],
        "attributes": [
          {
            "trait_type": "Skin Tone",
            "value": "Swamp"
          },
          {
            "trait_type": "Bracelet",
            "value": "Gold Braid"
          },
          {
            "trait_type": "Earrings",
            "value": "Fly Agaric"
          },
          {
            "trait_type": "Hamster",
            "value": "RUB"
          }
        ],
        "description": "THE GOLDEN ORC HUNTING SEASON IS OPEN!\nZarGates offers a massive bounty to all treasure hunters out there for capturing them.\n🎯 Hunt rules:\nColor matters. Golden Orcs are the most valuable.\nCOLLECT 7 of them to build a full squad and increase your reward.\nGear up your squad to boost your odds — and 💎 claim your share of the loot from the $300,000 prize pool!\n✅ For details and links to our official channels, see the collection description.\n🚀 Let's go — adventure awaits!",
        "name": "Orc To The Moon #0",
        "image": "https://metadata.zargates.com/stickers/1600000.png"
      },
      "previews": [
        {
          "resolution": "5x5",
          "url": "https://cache.tonapi.io/imgproxy/hU5C9tLwQd8Y-Mz3CIbkxodx3qJ-raJg7L-nXB4SYpw/rs:fill:5:5:1/g:no/aHR0cHM6Ly9tZXRhZGF0YS56YXJnYXRlcy5jb20vc3RpY2tlcnMvMTYwMDAwMC5wbmc.webp"
        },
        {
          "resolution": "100x100",
          "url": "https://cache.tonapi.io/imgproxy/trMpPQYWWWuGVSpkBmTW6u1GgG4ZDLWMhlT7T26JNGI/rs:fill:100:100:1/g:no/aHR0cHM6Ly9tZXRhZGF0YS56YXJnYXRlcy5jb20vc3RpY2tlcnMvMTYwMDAwMC5wbmc.webp"
        },
        {
          "resolution": "500x500",
          "url": "https://cache.tonapi.io/imgproxy/cT_MC88tioevtOwVCav69Is6LdQRqUms2WdmCWvkg-4/rs:fill:500:500:1/g:no/aHR0cHM6Ly9tZXRhZGF0YS56YXJnYXRlcy5jb20vc3RpY2tlcnMvMTYwMDAwMC5wbmc.webp"
        },
        {
          "resolution": "1500x1500",
          "url": "https://cache.tonapi.io/imgproxy/gw0w72PbdPkWQVRgJ3Y_VxWrlOL2B6AhWStdQG-JzGo/rs:fill:1500:1500:1/g:no/aHR0cHM6Ly9tZXRhZGF0YS56YXJnYXRlcy5jb20vc3RpY2tlcnMvMTYwMDAwMC5wbmc.webp"
        }
      ],
      "approved_by": [
        "tonkeeper"
      ],
      "trust": "whitelist",
      "code_hash": "AuOiNw6jayTqv/gQzYTvY9wYBEPQtRrbnTvkwOqPcxk=",
      "data_hash": "6vUkZRB0MuEdaytPs52ncyiMMUniYTexOjq9bidmrW0="
    }
    """
    url = f"{TON_API_KEY}/v2/nfts/collections/{collection_address}/items"
    headers = get_ton_headers()
    params = {"after": cursor, "limit": limit} if cursor else {"limit": limit}
    data = await get_session_response(session, url, headers, params)
    return data

def get_ton_cursor(data: dict, cursor):
    cursor = 0 if not cursor else int(cursor)
    return cursor + len(data.get("nft_items"))

def get_ton_items(data: dict):
    return data.get("nft_items")
