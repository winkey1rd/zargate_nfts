from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from .base_handler import CollectionHandler
from nft_shared.crud.nft_repository import NftRepository
from backend.app.models import GiftBoxORM, StickerBoxORM


class BoxesCollectionHandler(CollectionHandler):
    """Handler for box collections (GiftBoxes and StickerBoxes)."""

    def __init__(
        self,
        collection_address: str,
        db_session: AsyncSession,
        api_session,
        attribute_values: Dict[str, Any],  # unused for boxes, kept for uniform signature
        nft_repository: NftRepository,
    ):
        super().__init__(collection_address, db_session, api_session, nft_repository)

    def _build_special_repository(self):
        # Boxes have no extra repository — NftRepository covers everything needed.
        return None

    async def _process_specific(
        self, nft_info: Dict[str, Any], nft_address: str, item: Dict[str, Any]
    ) -> None:
        if self.collection_name == "ZarGates GiftBoxes":
            self.specific_objects.append(GiftBoxORM(nft_address=nft_address))

        elif self.collection_name == "ZarGates StickerBoxes":
            self.specific_objects.append(
                StickerBoxORM(
                    nft_address=nft_address,
                    type=nft_info.get("name", "").split()[0],
                )
            )