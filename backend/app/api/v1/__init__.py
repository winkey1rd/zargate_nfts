from fastapi import APIRouter

from .basket import basket_router
from .stickers import stickers_router
from .wallets import wallets_router

core_router = APIRouter()

core_router.include_router(basket_router)
core_router.include_router(wallets_router)
core_router.include_router(stickers_router)