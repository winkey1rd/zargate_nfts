from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, Integer, String, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from nft_shared.db.base import Base


class Wallet(Base):
    __tablename__ = "wallets"

    address: Mapped[str] = mapped_column(String(48), primary_key=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    telegram_username: Mapped[str] = mapped_column(String, nullable=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)

    role: Mapped[str] = mapped_column(String, nullable=True)

    # Доступы к разделам
    is_synergy: Mapped[bool] = mapped_column(Boolean, default=True)
    is_portfolio: Mapped[bool] = mapped_column(Boolean, default=True)
    is_basket_show: Mapped[bool] = mapped_column(Boolean, default=True)
    is_new_portfolio: Mapped[bool] = mapped_column(Boolean, default=True)
    is_basket_add: Mapped[bool] = mapped_column(Boolean, default=False)
    is_all_stickers_show: Mapped[bool] = mapped_column(Boolean, default=False)
    is_opening: Mapped[bool] = mapped_column(Boolean, default=False)

    # Rate limit
    timeout: Mapped[int] = mapped_column(Integer, default=60)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )
    last_query_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    owned_baskets = relationship(
        "BasketItem", foreign_keys="BasketItem.owner_address", back_populates="owner"
    )
    recipient_baskets = relationship(
        "BasketItem", foreign_keys="BasketItem.recipient_address", back_populates="recipient"
    )
    trades = relationship("TradeItem", back_populates="adder")
    activities = relationship("Activity", back_populates="wallet")
    session = relationship("UserSession", back_populates="wallet", uselist=False)
    monitor_rules = relationship("MonitorRule", back_populates="wallet")

    __table_args__ = (
        Index("idx_wallets_telegram", "telegram_id", "telegram_username"),
    )

    def __repr__(self) -> str:
        return f"<Wallet {self.address[:6]}…{self.address[-4:]}>"


class Activity(Base):
    """Лог запросов пользователя — используется для rate limiting."""

    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    token: Mapped[str] = mapped_column(
        String(64), ForeignKey("wallets.token"), nullable=False, index=True
    )
    method: Mapped[str] = mapped_column(String, nullable=False)
    query: Mapped[dict] = mapped_column(JSONB, nullable=True)
    status: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    wallet = relationship("Wallet", back_populates="activities")

    __table_args__ = (
        Index("idx_activities_token_created", "token", "created_at"),
    )