from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import BYTEA, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from nft_shared.db.base import Base


class NftCollectionORM(Base):
    __tablename__ = "nft_collections"

    address: Mapped[str] = mapped_column(String(48), primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)

    nfts = relationship("NftBaseORM", back_populates="collection")


class NftBaseORM(Base):
    __tablename__ = "nfts"

    address: Mapped[str] = mapped_column(String(48), primary_key=True)
    collection_address: Mapped[str] = mapped_column(
        String(48), ForeignKey("nft_collections.address"), nullable=False, index=True
    )
    owner_wallet_address: Mapped[str] = mapped_column(
        String(48), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String, nullable=False)

    sale_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    finish_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    mint_wallet_address: Mapped[str] = mapped_column(
        String(48), nullable=False, index=True
    )
    mint_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
    image: Mapped[Optional[bytes]] = mapped_column(BYTEA, nullable=True)
    lottie: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    collection = relationship("NftCollectionORM", back_populates="nfts")
    basket_items = relationship("BasketItem", back_populates="sticker")
    trade_items = relationship("TradeItem", back_populates="sticker")
    gift_boxes = relationship("GiftBoxORM", back_populates="nft")
    sticker_boxes = relationship("StickerBoxORM", back_populates="nft")
    stickers = relationship("StickerORM", back_populates="nft")
    openings = relationship(
        "OpeningORM", foreign_keys="OpeningORM.nft_address", back_populates="nft"
    )
    box_openings = relationship(
        "OpeningORM", foreign_keys="OpeningORM.box_address", back_populates="box"
    )
    price_snapshots = relationship("PriceSnapshot", back_populates="nft")

    __table_args__ = (
        Index("idx_nfts_collection_owner", "collection_address", "owner_wallet_address"),
    )


class GiftBoxORM(Base):
    __tablename__ = "gift_boxes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nft_address: Mapped[str] = mapped_column(
        String(48), ForeignKey("nfts.address"), nullable=False, index=True
    )
    nft = relationship("NftBaseORM", back_populates="gift_boxes")


class StickerBoxORM(Base):
    __tablename__ = "sticker_boxes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nft_address: Mapped[str] = mapped_column(
        String(48), ForeignKey("nfts.address"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String, nullable=False)
    nft = relationship("NftBaseORM", back_populates="sticker_boxes")