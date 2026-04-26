from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import TEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from nft_shared.db.base import Base


class TradeItem(Base):
    """Стикер, который владелец готов обменять. Создаётся только самим владельцем."""

    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sticker_address: Mapped[str] = mapped_column(
        String(48), ForeignKey("nfts.address"), nullable=False, index=True, unique=True
    )
    added_address: Mapped[str] = mapped_column(
        String(48), ForeignKey("wallets.address"), nullable=False, index=True
    )
    comment: Mapped[str] = mapped_column(TEXT, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    sticker = relationship("NftBaseORM", back_populates="trade_items")
    adder = relationship("Wallet", back_populates="trades")

    __table_args__ = (Index("idx_trades_added", "added_address"),)

    def __repr__(self) -> str:
        return f"<TradeItem {self.sticker_address}>"


class BasketItem(Base):
    """Предложение обмена. Создаётся только пользователем с флагом is_basket_add."""

    __tablename__ = "baskets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sticker_address: Mapped[str] = mapped_column(
        String(48), ForeignKey("nfts.address"), nullable=False, index=True, unique=True
    )
    owner_address: Mapped[str] = mapped_column(
        String(48), ForeignKey("wallets.address"), nullable=False, index=True
    )
    recipient_address: Mapped[str] = mapped_column(
        String(48), ForeignKey("wallets.address"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    sticker = relationship("NftBaseORM", back_populates="basket_items")
    owner = relationship(
        "Wallet", foreign_keys=[owner_address], back_populates="owned_baskets"
    )
    recipient = relationship(
        "Wallet", foreign_keys=[recipient_address], back_populates="recipient_baskets"
    )

    __table_args__ = (
        Index("idx_baskets_owner_recipient", "owner_address", "recipient_address"),
    )

    def __repr__(self) -> str:
        return f"<BasketItem {self.sticker_address} {self.owner_address}→{self.recipient_address}>"