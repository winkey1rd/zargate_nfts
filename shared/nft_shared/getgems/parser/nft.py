from datetime import datetime

import requests

from nft_shared.utility import convert_address_to_uq

def parse_getgems_nft_item(item: dict):
    nft_address = convert_address_to_uq(item.get("address"))
    owner_address = convert_address_to_uq(item.get("ownerAddress"))
    sale_data = item.get("sale", {})
    s_type = sale_data.get("type")

    finish_at = datetime.fromisoformat(sale_data.get("finishAt").replace("Z", "+00:00")) if s_type == "Auction" \
        else None

    sale_type = {
        "FixPriceSale": "fullPrice",
        "Auction": "minBid"
    }
    price_str = sale_data.get(sale_type.get(s_type), None) if sale_data else None
    price = float(price_str.strip()) / 1_000_000_000 if price_str else None
    name = item.get("name", "")
    attributes = item.get("attributes", [])
    image = item.get("image", "")
    response = requests.get(image)
    image_data = response.content if response.status_code == 200 else None
    return {
        "address": nft_address,
        "owner_wallet_address": owner_address,
        "name": name,
        "attributes": attributes,

        "image": image_data,

        "price": price,
        "sale_type": s_type,
        "finish_at": finish_at,
    }

def parse_getgems_nft_info(item: dict):
    nft_item = parse_getgems_nft_item(item)
    nft_item["collection_address"] = convert_address_to_uq(item.get("collectionAddress"))
    return nft_item
