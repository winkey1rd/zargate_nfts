from dataclasses import dataclass
from datetime import datetime
from typing import List

from sqlalchemy import Integer, String, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB, TEXT, ARRAY
from sqlalchemy.orm import mapped_column, Mapped, relationship

from backend.app.db.base import Base


class StickerORM(Base):
    """Sticker model - stores individual NFT stickers with their attributes."""
    __tablename__ = 'stickers'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nft_address: Mapped[str] = mapped_column(String(48), ForeignKey('nfts.address'), nullable=False, index=True)

    emotion: Mapped[str] = mapped_column(String, nullable=False)
    skin_tone: Mapped[str] = mapped_column(String, nullable=False)

    first_attribute: Mapped[int] = mapped_column(Integer, ForeignKey('attributes.id'), nullable=False, index=True)      # "Skin Tone"
    second_attribute: Mapped[int] = mapped_column(Integer, ForeignKey('attributes.id'), nullable=False, index=True)     # "Earrings"
    third_attribute: Mapped[int] = mapped_column(Integer, ForeignKey('attributes.id'), nullable=False, index=True)      # "Heart", "Cup", "Cap", "Pendant Chain", "Stick", "Hamster", "Sign"
    fourth_attribute: Mapped[int] = mapped_column(Integer, ForeignKey('attributes.id'), nullable=False, index=True)     # "Armor", "Glasses", "Ring", "Bracelet"

    sticker_synergy: Mapped[dict] = mapped_column(JSONB, nullable=False)
    num_features: Mapped[List[str]] = mapped_column(ARRAY(TEXT))
    # Values
    attr_value: Mapped[int] = mapped_column(Integer, default=0)
    synergy_bonus: Mapped[int] = mapped_column(Integer, default=0)
    name_value: Mapped[int] = mapped_column(Integer, default=0)
    total_value: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    nft = relationship("NftBaseORM", back_populates="stickers")
    attr1 = relationship("AttributeORM", foreign_keys=[first_attribute])
    attr2 = relationship("AttributeORM", foreign_keys=[second_attribute])
    attr3 = relationship("AttributeORM", foreign_keys=[third_attribute])
    attr4 = relationship("AttributeORM", foreign_keys=[fourth_attribute])

    __table_args__ = (
        Index('idx_stickers_attributes', 'first_attribute', 'second_attribute', 'third_attribute', 'fourth_attribute'),
    )

    @property
    def total_value_calculated(self) -> int:
        return self.attr_value + self.synergy_bonus + self.name_value


class AttributeORM(Base):
    """ORM‑модель таблицы attribute_values для хранения ценностей атрибутов по коллекциям."""
    __tablename__ = "attributes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trait_type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    value: Mapped[str] = mapped_column(String, nullable=False, index=True)
    attribute_group: Mapped[str] = mapped_column(String, nullable=False, index=True)
    attribute_value: Mapped[int] = mapped_column(Integer, nullable=False)

@dataclass
class Sticker:
    address: str
    collection_address: str
    owner_wallet_address: str
    name: str

    sale_type: str | None
    price: float | None
    finish_at: datetime | None

    mint_wallet_address: str
    mint_at: datetime
    updated_at: datetime
    image: bytes
    lottie: dict

    emotion: str
    skin_tone: str

    first_attribute: dict
    second_attribute: dict
    third_attribute: dict
    fourth_attribute: dict

    attr_value: int
    synergy_bonus: int
    name_value: int
    total_value: int

    sticker_synergy: dict
    synergy_bonus: dict