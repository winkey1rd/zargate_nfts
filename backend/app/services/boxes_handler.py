from typing import Dict, Any

from .base_handler import CollectionHandler
from backend.app.models import GiftBoxORM, StickerBoxORM


class BoxesCollectionHandler(CollectionHandler):
    """Handler for box collections (GiftBoxes and StickerBoxes)."""

    async def _process_specific(self, nft_info: Dict[str, Any], nft_address: str, item: Dict[str, Any]) -> None:
        """Process boxes-specific logic: create GiftBoxORM or StickerBoxORM."""
        if self.collection_name == "ZarGates GiftBoxes":
            gift_box = GiftBoxORM(nft_address=nft_address)
            self.specific_objects.append(gift_box)
        elif self.collection_name == "ZarGates StickerBoxes":
            sticker_box = StickerBoxORM(
                nft_address=nft_address,
                type=nft_info.get("name").split()[0]
            )
            self.specific_objects.append(sticker_box)