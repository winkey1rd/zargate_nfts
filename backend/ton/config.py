import os
from dotenv import load_dotenv
load_dotenv()

TON_CENTER_API = "https://toncenter.com/api/v2"
TON_CENTER_TESTNET_API = "https://testnet.toncenter.com/api/v2"
TON_API_BASE_URL = "https://tonapi.io/"
TON_API_KEY = os.getenv("TON_API_KEY")
TON_CENTER_API_KEY = os.getenv("TON_CENTER_API_KEY")

