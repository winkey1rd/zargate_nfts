"""
SQLAlchemy ORM models for the database, optimized for PostgreSQL.
"""
from sqlalchemy import Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import TEXT
from sqlalchemy.orm import mapped_column, Mapped, relationship
from datetime import datetime

from backend.app.db.base import Base


class BasketItem(Base):
    __tablename__ = 'baskets'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sticker_address: Mapped[str] = mapped_column(String(48), ForeignKey('nfts.address'), nullable=False, index=True, unique=True)
    owner_address: Mapped[str] = mapped_column(String(48), ForeignKey('wallets.address'), nullable=False, index=True)
    recipient_address: Mapped[str] = mapped_column(String(48), ForeignKey('wallets.address'), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now())

    # Relationships
    sticker = relationship("NftBaseORM", back_populates="basket_items")
    owner = relationship("Wallet", foreign_keys=[owner_address], back_populates="owned_baskets")
    recipient = relationship("Wallet", foreign_keys=[recipient_address], back_populates="recipient_baskets")

    __table_args__ = (
        Index('idx_baskets_owner_recipient', 'owner_address', 'recipient_address'),
    )

    def __repr__(self):
        return f"<BasketItem {self.sticker_address} ({self.owner_address or '-'} -> {self.recipient_address or '-'})>"

class TradeItem(Base):
    __tablename__ = 'trades'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sticker_address: Mapped[str] = mapped_column(String(48), ForeignKey('nfts.address'), nullable=False, index=True, unique=True)
    added_address: Mapped[str] = mapped_column(String(48), ForeignKey('wallets.address'), nullable=False, index=True)
    comment: Mapped[str] = mapped_column(TEXT)

    # Relationships
    sticker = relationship("NftBaseORM", back_populates="trade_items")
    adder = relationship("Wallet", back_populates="trades")

    __table_args__ = (
        Index('idx_trades_added', 'added_address'),
    )

    def __repr__(self):
        return f"<TradeItem {self.sticker_address} ({self.comment or '-'})>"
