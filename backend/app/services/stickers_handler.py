from sqlalchemy.ext.asyncio import AsyncSession

from .base_handler import CollectionHandler
from backend.app.models import AttributeORM, StickerORM

from utility.calculator import *
from utility.sticker import get_group_by_trait_type, get_attr_num_by_emo_trait, get_emotion_by_name


class StickersCollectionHandler(CollectionHandler):
    """Handler for Unstoppable Tribe stickers collection."""

    def __init__(self, collection_address: str, db_session: AsyncSession, api_session, attribute_values: Dict[str, Any]):
        super().__init__(collection_address, db_session, api_session)
        self.attribute_data = attribute_values.get("attribute", {})
        self.synergy_data = attribute_values.get("synergy", {})
        self.name_attributes = attribute_values.get("name", {})
        self.num_attributes = attribute_values.get("number", {})

    async def _process_specific(self, nft_info: Dict[str, Any], nft_address: str, item: Dict[str, Any]) -> None:
        """Process stickers-specific logic: parse attributes and create StickerORM."""
        emotion = get_emotion_by_name(nft_info.get("name"))
        skin_tone = None

        attr_ids = {}
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

            existing_attr = get_attributes_by_value(self.db_session, trait_type, value)
            if not existing_attr:
                new_attr = AttributeORM(
                    trait_type=trait_type,
                    value=value,
                    attribute_group=get_group_by_trait_type(trait_type),
                    attribute_value=calculate_attribute_value(trait_type, normalize_value(value), self.attribute_data)
                )
                self.db_session.add(new_attr)
                await self.db_session.flush()

                attr_ids[attr_num] = new_attr.id
                attr_value += new_attr.attribute_value
            else:
                attr_ids[attr_num] = existing_attr.id
                attr_value += existing_attr.attribute_value

        total, synergy_bonus = calculate_sticker_synergy_value(nft_info.get("attributes", []), self.synergy_data)
        name_value = calculate_name_value(nft_info.get("name"), self.name_attributes)
        num_value, num_features = calculate_number_value(nft_info.get("name"), self.num_attributes)

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
            total_value=name_value + num_value + attr_value + total
        )
        self.specific_objects.append(sticker)