import logging
from typing import Dict


from nft_shared.ton.config import TON_API_KEY
from nft_shared.utility import get_headers

logger = logging.getLogger(__name__)

def get_ton_headers() -> Dict[str, str]:
    return get_headers(TON_API_KEY)
