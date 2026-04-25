from backend.utility import convert_address_to_uq


def parse_open_event(data: dict):
    actions = data.get("actions", [])
    event_id = data.get("event_id")
    sender, box_address, price, fees = None, None, 0, 0
    for action in actions:
        action_type = action.get("type")
        if action_type == "NftItemTransfer":
            info = action.get("NftItemTransfer")
            sender = convert_address_to_uq(info.get("sender")) if info.get("is_wallet") else None
            box_address = convert_address_to_uq(action.get("nft"))

        if action_type == "TonTransfer":
            info = action.get("TonTransfer")
            price = float(info.get("amount")) / 1_000_000_000
    value_flow = data.get("value_flow", [])
    for flow in value_flow:
        if flow.get("account", {}).get("address") == sender:
            full_price = float(flow.get("ton")) / 1_000_000_000
            fees = full_price - price
    return {
        "hash": event_id,
        "box_address": box_address,
        "price": price,
        "fees": fees,
        "open_wallet_address": sender,
    }
