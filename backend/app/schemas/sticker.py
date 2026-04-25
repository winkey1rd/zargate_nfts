from typing import Optional
from pydantic import BaseModel, Field


class AttributeSchema(BaseModel):
    trait_type: str
    value: str
    attribute_group: str
    attribute_value: int

    model_config = {"from_attributes": True}


class StickerValuesSchema(BaseModel):
    attr_value: int = Field(description="Sum of individual attribute values")
    synergy_bonus: int = Field(description="Total synergy bonus")
    name_value: int = Field(description="Value derived from NFT name and number features")
    total_value: int = Field(description="attr_value + synergy_bonus + name_value")

    model_config = {"from_attributes": True}


class StickerSchema(BaseModel):
    emotion: str
    num_features: Optional[list[str]] = None
    sticker_synergy: Optional[dict] = None
    skin_tone: Optional[str] = None

    model_config = {"from_attributes": True}


class StickerResponse(BaseModel):
    address: str = Field(description="NFT contract address")
    name: str
    owner: str = Field(description="Owner wallet address")

    sticker: Optional[StickerSchema] = None
    attributes: dict[str, str] = Field(
        default_factory=dict,
        description="Flat map of trait_type → value",
    )
    values: Optional[StickerValuesSchema] = None

    model_config = {"from_attributes": True}
