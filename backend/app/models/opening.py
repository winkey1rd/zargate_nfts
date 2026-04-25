from sqlalchemy import Integer, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import mapped_column, Mapped, relationship
from datetime import datetime

from backend.app.db.base import Base


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

    box = relationship(
        "NftBaseORM", foreign_keys=[box_address], back_populates="box_openings"
    )
    nft = relationship(
        "NftBaseORM", foreign_keys=[nft_address], back_populates="openings"
    )

    __table_args__ = (
        Index("idx_opening_wallet_at", "open_wallet_address", "open_at"),
    )