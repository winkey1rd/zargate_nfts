"""
SQLAlchemy ORM models for the database, optimized for PostgreSQL.
"""
from sqlalchemy import Integer, String, DateTime, ForeignKey, Boolean, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import mapped_column, Mapped, relationship
from datetime import datetime

from old.database import Base


class Wallet(Base):
    __tablename__ = 'wallets'

    address: Mapped[str] = mapped_column(String(48), primary_key=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    telegram_username: Mapped[str] = mapped_column(String)
    token: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    role: Mapped[str] = mapped_column(String)
    is_synergy: Mapped[bool] = mapped_column(Boolean, default=True)
    is_portfolio:Mapped[bool] = mapped_column(Boolean, default=True)
    is_basket_show: Mapped[bool] = mapped_column(Boolean, default=True)
    is_new_portfolio: Mapped[bool] = mapped_column(Boolean, default=True)
    is_basket_add: Mapped[bool] = mapped_column(Boolean, default=False)
    is_all_stickers_show: Mapped[bool] = mapped_column(Boolean, default=False)
    is_opening: Mapped[bool] = mapped_column(Boolean, default=False)

    timeout: Mapped[int] = mapped_column(Integer)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    last_query_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Relationships
    owned_baskets = relationship("BasketItem", foreign_keys="BasketItem.owner_address", back_populates="owner")
    recipient_baskets = relationship("BasketItem", foreign_keys="BasketItem.recipient_address", back_populates="recipient")
    trades = relationship("TradeItem", back_populates="adder")
    activities = relationship("Activity", back_populates="wallet")

    __table_args__ = (
        Index('idx_wallets_telegram', 'telegram_id', 'telegram_username'),
    )

    def __repr__(self):
        return f"<Wallet {self.address[:5]}...{self.address[-5:]}>"



class Activity(Base):
    __tablename__ = 'activities'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    token: Mapped[str] = mapped_column(String, ForeignKey('wallets.token'), nullable=False, index=True)
    methode: Mapped[str] = mapped_column(String)
    query : Mapped[dict] = mapped_column(JSONB)
    status: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    wallet = relationship("Wallet", back_populates="activities")

    __table_args__ = (
        Index('idx_activities_token_created', 'token', 'created_at'),
    )
