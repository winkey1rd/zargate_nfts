from typing import Optional, Dict, Any

from backend.getgems.config import GETGEMS_API_BASE_URL
from backend.getgems.session import get_getgems_headers
from backend.utility import get_session_response


async def get_getgems_nft_history(
        session,
        nft_address: str,
        types: Optional[str] = "mint",
        limit: int = 50
) -> Optional[Dict[str, Any]]:

    url = f"{GETGEMS_API_BASE_URL}/v1/nft/history/{nft_address}"
    headers = get_getgems_headers()
    params = {
        "types": types,
        "limit": limit
    }
    data = await get_session_response(session, url, headers, params)
    return data


async def get_getgems_collection_sale(
        session,
        collection_address: str,
        cursor: Optional[str] = "",
        limit: int = 100
) -> Optional[Dict[str, Any]]:
    url = f"{GETGEMS_API_BASE_URL}/v1/nfts/on-sale/{collection_address}"
    headers = get_getgems_headers()
    params = {"after": cursor, "limit": limit} if cursor else {"limit": limit}

    data = await get_session_response(session, url, headers, params)
    return data

async def get_getgems_collection_nft(
        session,
        collection_address: str,
        cursor: Optional[str] = "",
        limit: int = 100
) -> Optional[Dict[str, Any]]:
    """
    item for ZarGates GiftBoxes collection EQD1YVbwG5dNV9lZgz18F4cjBm5iqYXyeUqdGe21JXjsLCIo
    {
        "address": "EQD44v5ATMFFVf8PMx3W8-GIL7IFC84ncxPTCm2vT76WljpJ",
        "kind": "CollectionItem",
        "collectionAddress": "EQD1YVbwG5dNV9lZgz18F4cjBm5iqYXyeUqdGe21JXjsLCIo",
        "ownerAddress": "EQCvhNX6ON0DpMQEIuQ9FibI1DKXgHOAzVNfIJ6IIaPf0NGk",
        "actualOwnerAddress": "EQCvhNX6ON0DpMQEIuQ9FibI1DKXgHOAzVNfIJ6IIaPf0NGk",
        "image": "https://i.getgems.io/oJwVr6iEnV3N8RtkShY0PeXVn5OS5N7TMQdGXdrbX3k/rs:fill:500:500:1/g:ce/czM6Ly9nZXRnZW1zLXMzL25mdC1jb250ZW50LWNhY2hlL2ltYWdlcy9FUUQxWVZid0c1ZE5WOWxaZ3oxOEY0Y2pCbTVpcVlYeWVVcWRHZTIxSlhqc0xDSW8vNzhhZDA4ZjljMDAzNjNkNA.png",
        "imageSizes": {
          "96": "https://i.getgems.io/qD0oC0VJCBB8kckQ4ApZuI63XwSlmdhLAkngaHw72sM/rs:fill:96:96:1/g:ce/czM6Ly9nZXRnZW1zLXMzL25mdC1jb250ZW50LWNhY2hlL2ltYWdlcy9FUUQxWVZid0c1ZE5WOWxaZ3oxOEY0Y2pCbTVpcVlYeWVVcWRHZTIxSlhqc0xDSW8vNzhhZDA4ZjljMDAzNjNkNA.png",
          "352": "https://i.getgems.io/o23ondOyWQJZ5w6W8KIFBOBSN2dGpimSBABJiy17ne0/rs:fill:352:352:1/g:ce/czM6Ly9nZXRnZW1zLXMzL25mdC1jb250ZW50LWNhY2hlL2ltYWdlcy9FUUQxWVZid0c1ZE5WOWxaZ3oxOEY0Y2pCbTVpcVlYeWVVcWRHZTIxSlhqc0xDSW8vNzhhZDA4ZjljMDAzNjNkNA.png"
        },
    item for ZarGates StickerBoxes collection EQBzPVuHoSR_QlBFtyJiyDfJdKy-dp2sOBbY0s0BBSzaMps7
{
        "address": "EQAFFzDxUq_BZ8qUtOH40lOq8RS2iL-Zoc1TsVY-PES5GlEN",
        "kind": "CollectionItem",
        "collectionAddress": "EQBzPVuHoSR_QlBFtyJiyDfJdKy-dp2sOBbY0s0BBSzaMps7",
        "ownerAddress": "EQDo71vN4TerZ8_0FlQc2CXxKyZBB9i8w_WNj4BkQyn8vP3k",
        "actualOwnerAddress": "EQDo71vN4TerZ8_0FlQc2CXxKyZBB9i8w_WNj4BkQyn8vP3k",
        "image": "https://i.getgems.io/Vgv0pk74XI9FqOomfr0GrHsgxfhzXieNveUjbzEalpc/rs:fill:500:500:1/g:ce/czM6Ly9nZXRnZW1zLXMzL25mdC1jb250ZW50LWNhY2hlL2ltYWdlcy9FUUJ6UFZ1SG9TUl9RbEJGdHlKaXlEZkpkS3ktZHAyc09CYlkwczBCQlN6YU1wczcvMGE0MjFjOWU1NzQ1NmRlYg.png",
        "imageSizes": {
          "96": "https://i.getgems.io/ht-HP0TXgml1T_Q5p66l5dEA9ZhEhbTqvvoyB9EGlGg/rs:fill:96:96:1/g:ce/czM6Ly9nZXRnZW1zLXMzL25mdC1jb250ZW50LWNhY2hlL2ltYWdlcy9FUUJ6UFZ1SG9TUl9RbEJGdHlKaXlEZkpkS3ktZHAyc09CYlkwczBCQlN6YU1wczcvMGE0MjFjOWU1NzQ1NmRlYg.png",
          "352": "https://i.getgems.io/j6-N47j7wpBpf-4x-K2nP7KdX-i78jhlpIY3JAXPmPM/rs:fill:352:352:1/g:ce/czM6Ly9nZXRnZW1zLXMzL25mdC1jb250ZW50LWNhY2hlL2ltYWdlcy9FUUJ6UFZ1SG9TUl9RbEJGdHlKaXlEZkpkS3ktZHAyc09CYlkwczBCQlN6YU1wczcvMGE0MjFjOWU1NzQ1NmRlYg.png"
        },
        "name": "Epic StickerBox",
        "description": "THE GOLDEN ORC HUNTING SEASON IS OPEN!\n\nZarGates offers a massive bounty to all treasure hunters out there for capturing them.\n\nEPIC STICKERBOX is the choice of experienced hunters. It gives you an increased chance to pull Golden Orcs.\n\n💎 Don't miss your chance to claim your share of the loot from the $300,000 prize pool!\n\nOPEN STICKERBOXES, assemble a squad of 7 Golden Orcs, gear them up with artifacts in ZarGates, and battle for valuable prizes!\n\n✅ For details and links to our official channels, see the collection description.\n\n🚀 Let's go — adventure awaits!",
        "attributes": [],
        "warning": null
      }
      item for sticker collection Unstoppable Tribe from ZarGates EQBGNoXXfQR07HdDhtkmIu1ojTTwcjB0EhHYOMSH3P7sZGJR
      {
        "address": "EQC9LZ1bwqh0UMkn1rocGnJoC97a2mB5rxUnUWIGS-STnHo9",
        "kind": "CollectionItem",
        "collectionAddress": "EQBGNoXXfQR07HdDhtkmIu1ojTTwcjB0EhHYOMSH3P7sZGJR",
        "ownerAddress": "EQB8H_WUcu_q3cVdzL-G59bdi5WFx7olgNYgMXmDiiDbVYFu",
        "actualOwnerAddress": "EQB8H_WUcu_q3cVdzL-G59bdi5WFx7olgNYgMXmDiiDbVYFu",
        "image": "https://i.getgems.io/z_NP-Pts6_N_foU_tc9GcUtk0-GVVBXrYakQ37W7W6k/rs:fill:500:500:1/g:ce/czM6Ly9nZXRnZW1zLXMzL25mdC1jb250ZW50LWNhY2hlL2ltYWdlcy9FUUJHTm9YWGZRUjA3SGREaHRrbUl1MW9qVFR3Y2pCMEVoSFlPTVNIM1A3c1pHSlIvNmVmYmI2NGE4NjJjNzQ5Yw.png",
        "imageSizes": {
          "96": "https://i.getgems.io/8WSq3A5mF1TF2yqcSDCUDHFVQx3tEBszGL51ej7bS7g/rs:fill:96:96:1/g:ce/czM6Ly9nZXRnZW1zLXMzL25mdC1jb250ZW50LWNhY2hlL2ltYWdlcy9FUUJHTm9YWGZRUjA3SGREaHRrbUl1MW9qVFR3Y2pCMEVoSFlPTVNIM1A3c1pHSlIvNmVmYmI2NGE4NjJjNzQ5Yw.png",
          "352": "https://i.getgems.io/Y6tWKwTcYQP423dj7B70G-zF8jMhzMLAdlJ_3O9DkOM/rs:fill:352:352:1/g:ce/czM6Ly9nZXRnZW1zLXMzL25mdC1jb250ZW50LWNhY2hlL2ltYWdlcy9FUUJHTm9YWGZRUjA3SGREaHRrbUl1MW9qVFR3Y2pCMEVoSFlPTVNIM1A3c1pHSlIvNmVmYmI2NGE4NjJjNzQ5Yw.png"
        },
        "name": "Orc To The Moon #0",
        "description": "THE GOLDEN ORC HUNTING SEASON IS OPEN!\nZarGates offers a massive bounty to all treasure hunters out there for capturing them.\n🎯 Hunt rules:\nColor matters. Golden Orcs are the most valuable.\nCOLLECT 7 of them to build a full squad and increase your reward.\nGear up your squad to boost your odds — and 💎 claim your share of the loot from the $300,000 prize pool!\n✅ For details and links to our official channels, see the collection description.\n🚀 Let's go — adventure awaits!",
        "attributes": [
          {
            "traitType": "Skin Tone",
            "value": "Swamp"
          },
          {
            "traitType": "Bracelet",
            "value": "Gold Braid"
          },
          {
            "traitType": "Earrings",
            "value": "Fly Agaric"
          },
          {
            "traitType": "Hamster",
            "value": "RUB"
          }
        ],
        "warning": null
      }
    """
    url = f"{GETGEMS_API_BASE_URL}/v1/nfts/collection/{collection_address}"
    headers = get_getgems_headers()
    params = {"after": cursor, "limit": limit} if cursor else {"limit": limit}
    data = await get_session_response(session, url, headers, params)
    return data

def get_getgems_cursor(data: dict, cursor):
    return data.get("response", {}).get("cursor")

def get_getgems_items(data: dict):
    return data.get("response", {}).get("items")

async def get_getgems_owner_collection_nft(
        session,
        owner_address: str,
        collection_address: str,
        cursor: Optional[str] = "",
        limit: int = 100
) -> Optional[Dict[str, Any]]:

    url = f"{GETGEMS_API_BASE_URL}/v1/nfts/collection/{collection_address}/owner/{owner_address}"
    headers = get_getgems_headers()
    params = {"after": cursor, "limit": limit} if cursor else {"limit": limit}
    data = await get_session_response(session, url, headers, params)
    return data