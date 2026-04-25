from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.crud.sticker_crud import StickerRepository
from backend.app.models import AttributeORM

from utility.session import get_session

stickers_router = APIRouter(prefix="/stickers", tags=["stickers"])


@stickers_router.get("/{address}")
async def get_sticker(
        address: str,
        session: AsyncSession = Depends(get_session),
):
    sticker_rep = StickerRepository(session)
    nft = await sticker_rep.get_sticker_full_info(address)

    if not nft:
        raise HTTPException(status_code=404, detail="NFT not found")

    sticker = nft.stickers[0] if nft.stickers else None

    def attr_to_pair(attr: AttributeORM | None):
        if not attr:
            return {}
        return {attr.trait_type: attr.value}

    attributes = {}
    if sticker:
        attributes = {
            **attr_to_pair(sticker.attr1),
            **attr_to_pair(sticker.attr2),
            **attr_to_pair(sticker.attr3),
            **attr_to_pair(sticker.attr4),
        }

    return {
        "address": nft.address,
        "name": nft.name,
        "owner": nft.owner_wallet_address,

        "emotion": sticker.emotion if sticker else None,

        "attributes": attributes,

        "num_features": sticker.num_features if sticker else None,
        "sticker_synergy": sticker.sticker_synergy if sticker else None,

        "attr_value": sticker.attr_value if sticker else None,
        "synergy_bonus": sticker.synergy_bonus if sticker else None,
        "name_value": sticker.name_value if sticker else None,
        "total_value": sticker.total_value if sticker else None,
    }