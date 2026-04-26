from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from nft_shared.crud.sticker_repository import StickerRepository
from backend.app.models import AttributeORM
from backend.app.schemas.sticker import StickerResponse, StickerSchema, StickerValuesSchema
from backend.utility import get_session

stickers_router = APIRouter(prefix="/stickers", tags=["stickers"])


def _attr_to_pair(attr: AttributeORM | None) -> dict:
    if not attr:
        return {}
    return {attr.trait_type: attr.value}


@stickers_router.get("/{address}", response_model=StickerResponse)
async def get_sticker(
    address: str,
    session: AsyncSession = Depends(get_session),
) -> StickerResponse:
    repo = StickerRepository(session)
    nft = await repo.get_full_info(address)

    if not nft:
        raise HTTPException(status_code=404, detail="NFT not found")

    sticker_orm = nft.stickers[0] if nft.stickers else None

    attributes: dict[str, str] = {}
    sticker_schema = None
    values_schema = None

    if sticker_orm:
        attributes = {
            **_attr_to_pair(sticker_orm.attr1),
            **_attr_to_pair(sticker_orm.attr2),
            **_attr_to_pair(sticker_orm.attr3),
            **_attr_to_pair(sticker_orm.attr4),
        }
        sticker_schema = StickerSchema.model_validate(sticker_orm)
        values_schema = StickerValuesSchema.model_validate(sticker_orm)

    return StickerResponse(
        address=nft.address,
        name=nft.name,
        owner=nft.owner_wallet_address,
        sticker=sticker_schema,
        attributes=attributes,
        values=values_schema,
    )