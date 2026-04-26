from datetime import datetime
from typing import List, Optional

from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from nft_shared.db.base import Base


# ---------------------------------------------------------------------------
# UserSession — кошельки, введённые пользователем в поле синергии
# ---------------------------------------------------------------------------

class UserSession(Base):
    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    wallet_address: Mapped[str] = mapped_column(
        String(48), ForeignKey("wallets.address"), nullable=False, unique=True, index=True
    )
    # Список адресов кошельков, введённых пользователем (до 20)
    wallets: Mapped[List[str]] = mapped_column(ARRAY(String(48)), nullable=False, default=list)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    wallet = relationship("Wallet", back_populates="session")


# ---------------------------------------------------------------------------
# OpeningORM — статистика открытий боксов
# ---------------------------------------------------------------------------

class OpeningORM(Base):
    __tablename__ = "opening"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hash: Mapped[str] = mapped_column(String, nullable=False, index=True, unique=True)
    box_address: Mapped[str] = mapped_column(
        String(48), ForeignKey("nfts.address"), nullable=False, index=True
    )
    nft_address: Mapped[str] = mapped_column(
        String(48), ForeignKey("nfts.address"), nullable=False, index=True
    )
    price: Mapped[float] = mapped_column(Float, nullable=False)
    fees: Mapped[float] = mapped_column(Float, nullable=False)
    open_wallet_address: Mapped[str] = mapped_column(
        String(48), nullable=False, index=True
    )
    open_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    box = relationship("NftBaseORM", foreign_keys=[box_address], back_populates="box_openings")
    nft = relationship("NftBaseORM", foreign_keys=[nft_address], back_populates="openings")

    __table_args__ = (
        Index("idx_opening_wallet_at", "open_wallet_address", "open_at"),
    )


# ---------------------------------------------------------------------------
# MonitorRule — правила мониторинга цен и атрибутов
# ---------------------------------------------------------------------------

class MonitorRule(Base):
    __tablename__ = "monitor_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    wallet_address: Mapped[str] = mapped_column(
        String(48), ForeignKey("wallets.address"), nullable=False, index=True
    )
    # Тип: 'min_price' | 'value_ratio' | 'attrs'
    rule_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # Структура зависит от rule_type, см. документацию
    filter_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    tg_chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    wallet = relationship("Wallet", back_populates="monitor_rules")


# ---------------------------------------------------------------------------
# PriceSnapshot — история цен для мониторинга
# ---------------------------------------------------------------------------

class PriceSnapshot(Base):
    __tablename__ = "price_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nft_address: Mapped[str] = mapped_column(
        String(48), ForeignKey("nfts.address"), nullable=False, index=True
    )
    price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, index=True
    )

    nft = relationship("NftBaseORM", back_populates="price_snapshots")

    __table_args__ = (
        Index("idx_price_snap_nft_time", "nft_address", "captured_at"),
    )