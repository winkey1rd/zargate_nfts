from  tonsdk.utils import Address


def convert_address_to_uq(address: str, is_bounceable: bool = False, is_url_safe: bool = True) -> str:
    """
    Convert TON address to UQ format (no bounce).
    Placeholder: implement actual conversion.
    """
    # For now, assume addresses are already in EQ format, convert to UQ if needed.
    # Use tonutils or API for real conversion.
    addr = Address(address)
    addr = addr.to_string(True, is_bounceable=is_bounceable, is_url_safe=is_url_safe)
    return addr

def get_key_by_values(value: str, info: dict) -> str | None:
    for key, values in info:
        if value in values:
            return key
    return None

