"""
SQLAlchemy ORM models for the database, optimized for PostgreSQL.
"""
from typing import List

from sqlalchemy import Integer, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB, BYTEA, TEXT, ARRAY
from sqlalchemy.orm import mapped_column, Mapped, relationship
from datetime import datetime

from old.database import Base


class NftCollectionORM(Base):
    """Sticker model - stores individual NFT stickers with their attributes."""
    __tablename__ = 'nft_collections'
    address: Mapped[str] = mapped_column(String(48), primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)

    # Relationships
    nfts = relationship("NftBaseORM", back_populates="collection")


class NftBaseORM(Base):
    """Base NFT model with common fields."""
    __tablename__ = 'nfts'

    address: Mapped[str] = mapped_column(String(48), primary_key=True)
    collection_address: Mapped[str] = mapped_column(String(48), ForeignKey('nft_collections.address'), nullable=False, index=True)
    owner_wallet_address: Mapped[str] = mapped_column(String(48), nullable=False, index=True)

    # Basic info
    name: Mapped[str] = mapped_column(String, nullable=False)

    sale_type: Mapped[str] = mapped_column(String, default="")
    price: Mapped[float] = mapped_column(Float, nullable=True)
    finish_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    # Metadata
    mint_wallet_address: Mapped[str] = mapped_column(String(48), nullable=False, index=True)
    mint_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    image: Mapped[bytes] = mapped_column(BYTEA)
    lottie: Mapped[dict] = mapped_column(JSONB)

    # Relationships
    collection = relationship("NftCollectionORM", back_populates="nfts")
    basket_items = relationship("BasketItem", back_populates="sticker")
    trade_items = relationship("TradeItem", back_populates="sticker")
    gift_boxes = relationship("GiftBoxORM", back_populates="nft")
    sticker_boxes = relationship("StickerBoxORM", back_populates="nft")
    stickers = relationship("StickerORM", back_populates="nft")
    openings = relationship("OpeningORM", foreign_keys="OpeningORM.nft_address", back_populates="nft")

    __table_args__ = (
        Index('idx_nfts_collection_owner', 'collection_address', 'owner_wallet_address'),
    )

class GiftBoxORM(NftBaseORM):
    """GiftBox model."""
    __tablename__ = 'gift_boxes'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nft_address: Mapped[str] = mapped_column(String(48), ForeignKey('nfts.address'), nullable=False, index=True)

    # Relationships
    nft = relationship("NftBaseORM", back_populates="gift_boxes")


class StickerBoxORM(Base):
    """StickerBox model."""
    __tablename__ = 'sticker_boxes'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nft_address: Mapped[str] = mapped_column(String(48), ForeignKey('nfts.address'), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String, nullable=False)

    # Relationships
    nft = relationship("NftBaseORM", back_populates="sticker_boxes")


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

