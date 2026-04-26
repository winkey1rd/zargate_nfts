from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from .base_handler import CollectionHandler
from nft_shared.crud.nft_repository import NftRepository
from nft_shared.crud.sticker_repository import StickerRepository
from backend.app.models import AttributeORM, StickerORM

from nft_shared.utility.calculator import (
    normalize_value,
    calculate_attribute_value,
    calculate_sticker_synergy_value,
    calculate_name_value,
    calculate_number_value,
)
from nft_shared.utility import (
    get_group_by_trait_type,
    get_attr_num_by_emo_trait,
    get_emotion_by_name,
)


class StickersCollectionHandler(CollectionHandler):
    """Handler for Unstoppable Tribe stickers collection."""

    def __init__(
        self,
        collection_address: str,
        db_session: AsyncSession,
        api_session,
        attribute_values: Dict[str, Any],
        nft_repository: NftRepository,
    ):
        super().__init__(collection_address, db_session, api_session, nft_repository)

        self.attribute_data = attribute_values.get("attribute", {})
        self.synergy_data = attribute_values.get("synergy", {})
        self.name_attributes = attribute_values.get("name", {})
        self.num_attributes = attribute_values.get("number", {})

        # in-memory attr cache: (trait_type, value) → AttributeORM
        self._attr_cache: Dict[tuple, AttributeORM] = {}

    def _build_special_repository(self) -> StickerRepository:
        return StickerRepository(self.db_session)

    async def _get_or_create_attribute(
        self, trait_type: str, value: str
    ) -> AttributeORM:
        """Return cached attribute or fetch/create it, updating the cache."""
        key = (trait_type, value)
        if key in self._attr_cache:
            return self._attr_cache[key]

        existing = await self.nft_repository.get_attribute_by_value(trait_type, value)
        if existing:
            self._attr_cache[key] = existing
            return existing

        new_attr = AttributeORM(
            trait_type=trait_type,
            value=value,
            attribute_group=get_group_by_trait_type(trait_type),
            attribute_value=calculate_attribute_value(
                trait_type, normalize_value(value), self.attribute_data
            ),
        )
        self.db_session.add(new_attr)
        await self.db_session.flush()  # populate new_attr.id
        self._attr_cache[key] = new_attr
        return new_attr

    async def _process_specific(
        self, nft_info: Dict[str, Any], nft_address: str, item: Dict[str, Any]
    ) -> None:
        """Parse attributes and create StickerORM."""
        emotion = get_emotion_by_name(nft_info.get("name"))
        skin_tone: Optional[str] = None

        attr_ids: Dict[str, int] = {}
        attr_value = 0

        for attr in nft_info.get("attributes", []):
            trait_type = attr.get("traitType")
            if trait_type == "Earring":
                trait_type = "Earrings"
            value = normalize_value(attr.get("value"))

            attr_num = get_attr_num_by_emo_trait(emotion, trait_type)
            if not attr_num:
                continue
            if attr_num == "1":
                skin_tone = value

            orm_attr = await self._get_or_create_attribute(trait_type, value)
            attr_ids[attr_num] = orm_attr.id
            attr_value += orm_attr.attribute_value

        total, synergy_bonus = calculate_sticker_synergy_value(
            nft_info.get("attributes", []), self.synergy_data
        )
        name_value = calculate_name_value(nft_info.get("name"), self.name_attributes)
        num_value, num_features = calculate_number_value(
            nft_info.get("name"), self.num_attributes
        )

        sticker = StickerORM(
            nft_address=nft_address,
            emotion=emotion,
            skin_tone=skin_tone,
            sticker_synergy=synergy_bonus,
            num_features=num_features,
            first_attribute=attr_ids.get("1"),
            second_attribute=attr_ids.get("2"),
            third_attribute=attr_ids.get("3"),
            fourth_attribute=attr_ids.get("4"),
            name_value=name_value + num_value,
            attr_value=attr_value,
            synergy_bonus=total,
            total_value=name_value + num_value + attr_value + total,
        )
        self.specific_objects.append(sticker)