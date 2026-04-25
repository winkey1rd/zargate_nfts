from typing import Optional, Dict, Any
from backend.ton.config import TON_API_BASE_URL
from backend.ton.session import get_ton_headers
from backend.utility import get_session_response


async def get_event_details(session, event_id: str) -> Optional[Dict[str, Any]]:
    """
    {
  "event_id": "760b88a35ae6c361ba178f63800328810805f4a3f6d74de302b393ae4c348c83",
  "timestamp": 1767111084,
  "actions": [
    {
      "type": "NftItemTransfer",
      "status": "ok",
      "NftItemTransfer": {
        "sender": {
          "address": "0:61de63b806ee8e433825ade0120aa7c520d722ff78b2f6c9976255bb5c8d6ca7",
          "is_scam": false,
          "is_wallet": true
        },
        "recipient": {
          "address": "0:e8ef5bcde137ab67cff416541cd825f12b264107d8bcc3f58d8f80644329fcbc",
          "is_scam": false,
          "is_wallet": false
        },
        "nft": "0:fce655f4a237d5167954b3271df4db5fc4e4a384df4e1f5cc7e12c9b59f4b585",
        "comment": "Call: 0x00000000"
      },
      "simple_preview": {
        "name": "NFT Transfer",
        "description": "Перевод NFT",
        "value": "1 NFT",
        "accounts": [
          {
            "address": "0:e8ef5bcde137ab67cff416541cd825f12b264107d8bcc3f58d8f80644329fcbc",
            "is_scam": false,
            "is_wallet": false
          },
          {
            "address": "0:61de63b806ee8e433825ade0120aa7c520d722ff78b2f6c9976255bb5c8d6ca7",
            "is_scam": false,
            "is_wallet": true
          },
          {
            "address": "0:fce655f4a237d5167954b3271df4db5fc4e4a384df4e1f5cc7e12c9b59f4b585",
            "is_scam": false,
            "is_wallet": false
          }
        ]
      },
      "base_transactions": [
        "f5657502f4925537bab04d2bbb3f9db202a723a046f1466f58669b5e98dc23fd",
        "7ac82be459de4758304ef440db69038d5610cb526fb698e30af793ce2cf736f9",
        "1e9986364575e6c6d2f94440952c4510115e2948a4b64708b9d907a94eb4b350"
      ]
    },
    {
      "type": "SmartContractExec",
      "status": "ok",
      "SmartContractExec": {
        "executor": {
          "address": "0:e8ef5bcde137ab67cff416541cd825f12b264107d8bcc3f58d8f80644329fcbc",
          "is_scam": false,
          "is_wallet": false
        },
        "contract": {
          "address": "0:463685d77d0474ec774386d92622ed688d34f07230741211d838c487dcfeec64",
          "is_scam": false,
          "is_wallet": false
        },
        "ton_attached": 40000000,
        "operation": "0x00000001"
      },
      "simple_preview": {
        "name": "Smart Contract Execution",
        "description": "Выполнение смарт-контракта",
        "accounts": [
          {
            "address": "0:e8ef5bcde137ab67cff416541cd825f12b264107d8bcc3f58d8f80644329fcbc",
            "is_scam": false,
            "is_wallet": false
          },
          {
            "address": "0:463685d77d0474ec774386d92622ed688d34f07230741211d838c487dcfeec64",
            "is_scam": false,
            "is_wallet": false
          }
        ]
      },
      "base_transactions": [
        "cdd0a7b74e0742a76a34788e4f837b7f14dcd4e7e7f7261126a7cc2a40dce8fd"
      ]
    },
    {
      "type": "SmartContractExec",
      "status": "ok",
      "SmartContractExec": {
        "executor": {
          "address": "0:463685d77d0474ec774386d92622ed688d34f07230741211d838c487dcfeec64",
          "is_scam": false,
          "is_wallet": false
        },
        "contract": {
          "address": "0:71de7155ca3d531a45f56a0757013812e1310c901779f998ffe30983103f5987",
          "is_scam": false,
          "is_wallet": false
        },
        "ton_attached": 30000000,
        "operation": "0x800c3bcc"
      },
      "simple_preview": {
        "name": "Smart Contract Execution",
        "description": "Выполнение смарт-контракта",
        "accounts": [
          {
            "address": "0:463685d77d0474ec774386d92622ed688d34f07230741211d838c487dcfeec64",
            "is_scam": false,
            "is_wallet": false
          },
          {
            "address": "0:71de7155ca3d531a45f56a0757013812e1310c901779f998ffe30983103f5987",
            "is_scam": false,
            "is_wallet": false
          }
        ]
      },
      "base_transactions": [
        "ad3eaad27b2b9df3a06b6b793ab847a803a5bf4d0487ed6804e89ee7147ff78d"
      ]
    },
    {
      "type": "ContractDeploy",
      "status": "ok",
      "ContractDeploy": {
        "address": "0:71de7155ca3d531a45f56a0757013812e1310c901779f998ffe30983103f5987",
        "interfaces": [
          "nft_item"
        ]
      },
      "simple_preview": {
        "name": "Contract Deploy",
        "description": "Деплой контракта  с интерфейсами nft_item",
        "accounts": [
          {
            "address": "0:71de7155ca3d531a45f56a0757013812e1310c901779f998ffe30983103f5987",
            "is_scam": false,
            "is_wallet": false
          }
        ]
      },
      "base_transactions": [
        "ad3eaad27b2b9df3a06b6b793ab847a803a5bf4d0487ed6804e89ee7147ff78d"
      ]
    },
    {
      "type": "TonTransfer",
      "status": "ok",
      "TonTransfer": {
        "sender": {
          "address": "0:e8ef5bcde137ab67cff416541cd825f12b264107d8bcc3f58d8f80644329fcbc",
          "is_scam": false,
          "is_wallet": false
        },
        "recipient": {
          "address": "0:38ab226aa53cdd584208816f8e524837261ae5e2fac692a624ccd0b147e7e4ef",
          "is_scam": false,
          "is_wallet": true
        },
        "amount": 1350000000
      },
      "simple_preview": {
        "name": "Ton Transfer",
        "description": "Перевод 1.35 TON",
        "value": "1.35 TON",
        "accounts": [
          {
            "address": "0:e8ef5bcde137ab67cff416541cd825f12b264107d8bcc3f58d8f80644329fcbc",
            "is_scam": false,
            "is_wallet": false
          },
          {
            "address": "0:38ab226aa53cdd584208816f8e524837261ae5e2fac692a624ccd0b147e7e4ef",
            "is_scam": false,
            "is_wallet": true
          }
        ]
      },
      "base_transactions": [
        "c75f2d3638bb8500778a27fe4ef3300f339843fb3506f94f9f0a6cf79a727101"
      ]
    }
  ],
  "value_flow": [
    {
      "account": {
        "address": "0:463685d77d0474ec774386d92622ed688d34f07230741211d838c487dcfeec64",
        "is_scam": false,
        "is_wallet": false
      },
      "ton": 3862793,
      "fees": 6137207
    },
    {
      "account": {
        "address": "0:71de7155ca3d531a45f56a0757013812e1310c901779f998ffe30983103f5987",
        "is_scam": false,
        "is_wallet": false
      },
      "ton": 28608400,
      "fees": 1391600
    },
    {
      "account": {
        "address": "0:38ab226aa53cdd584208816f8e524837261ae5e2fac692a624ccd0b147e7e4ef",
        "is_scam": false,
        "is_wallet": true
      },
      "ton": 1349712398,
      "fees": 287602
    },
    {
      "account": {
        "address": "0:fce655f4a237d5167954b3271df4db5fc4e4a384df4e1f5cc7e12c9b59f4b585",
        "is_scam": false,
        "is_wallet": false
      },
      "ton": 18829614,
      "fees": 4668817
    },
    {
      "account": {
        "address": "0:61de63b806ee8e433825ade0120aa7c520d722ff78b2f6c9976255bb5c8d6ca7",
        "is_scam": false,
        "is_wallet": true
      },
      "ton": -1527123651,
      "fees": 3625220
    },
    {
      "account": {
        "address": "0:e8ef5bcde137ab67cff416541cd825f12b264107d8bcc3f58d8f80644329fcbc",
        "is_scam": false,
        "is_wallet": false
      },
      "ton": 102296386,
      "fees": 7703614
    }
  ],
  "is_scam": false,
  "lt": 65238460000001,
  "in_progress": false,
  "progress": 1,
  "last_slice_id": 55593372,
  "ext_msg_hash": "f764d9a851805a901dc3f27faa0542f0f333abf521a6faa81f5956d0c07fb1a8"
}
    """
    headers = get_ton_headers()
    params = {}
    url = f"{TON_API_BASE_URL}/v2/events/{event_id}"
    data = await get_session_response(session, url, headers, params)
    return data
