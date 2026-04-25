import requests

from backend.utility import convert_address_to_uq


def parse_ton_nft_item(item: dict):
    nft_address = convert_address_to_uq(item["address"])
    owner_address = convert_address_to_uq(item.get("owner", {}).get("address", "")) \
        if item.get("owner", {}).get("is_wallet", "") \
        else convert_address_to_uq(item.get("sale", {}).get("owner", {}).get("address", ""))
    collection_address = convert_address_to_uq(item.get("collection", {}).get("address", ""))

    metadata = item.get("metadata", {})
    lottie = metadata.get("lottie", "")
    attributes = metadata.get("attributes", {})
    name = metadata.get("name", "")
    image = metadata.get("image", "")

    response = requests.get(image)
    image_data = response.content if response.status_code == 200 else None
    sale_data = item.get("sale", {})
    price = sale_data.get("price", {})
    price_value = price.get("value")

    return {
        "address": nft_address,
        "owner_wallet_address": owner_address,
        "collection_address": collection_address,
        "name": name,
        "attributes": attributes,

        "image": image_data,
        "lottie": lottie,

        "price": price_value,
        "sale_type": None,
        "finish_at": None
    }
