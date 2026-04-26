from nft_shared.ton.parser.nft import parse_ton_nft_item


def parse_ton_collection_nft_item(item: dict):
    return parse_ton_nft_item(item)
