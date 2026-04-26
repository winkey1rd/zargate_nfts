from typing import List, Optional

from sqlalchemy import ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, TEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from nft_shared.db.base import Base


class AttributeORM(Base):
    __tablename__ = "attributes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trait_type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    value: Mapped[str] = mapped_column(String, nullable=False, index=True)
    attribute_group: Mapped[str] = mapped_column(String, nullable=False, index=True)
    attribute_value: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint("trait_type", "value", name="uq_attribute_trait_value"),
    )


class StickerORM(Base):
    __tablename__ = "stickers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nft_address: Mapped[str] = mapped_column(
        String(48), ForeignKey("nfts.address"), nullable=False, index=True
    )

    emotion: Mapped[str] = mapped_column(String, nullable=False)
    skin_tone: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    first_attribute: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("attributes.id"), nullable=True, index=True
    )
    second_attribute: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("attributes.id"), nullable=True, index=True
    )
    third_attribute: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("attributes.id"), nullable=True, index=True
    )
    fourth_attribute: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("attributes.id"), nullable=True, index=True
    )

    sticker_synergy: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    num_features: Mapped[Optional[List[str]]] = mapped_column(ARRAY(TEXT), nullable=True)

    attr_value: Mapped[int] = mapped_column(Integer, default=0)
    synergy_bonus: Mapped[int] = mapped_column(Integer, default=0)
    name_value: Mapped[int] = mapped_column(Integer, default=0)
    total_value: Mapped[int] = mapped_column(Integer, default=0)

    nft = relationship("NftBaseORM", back_populates="stickers")
    attr1 = relationship("AttributeORM", foreign_keys=[first_attribute])
    attr2 = relationship("AttributeORM", foreign_keys=[second_attribute])
    attr3 = relationship("AttributeORM", foreign_keys=[third_attribute])
    attr4 = relationship("AttributeORM", foreign_keys=[fourth_attribute])

    __table_args__ = (
        Index(
            "idx_stickers_attributes",
            "first_attribute",
            "second_attribute",
            "third_attribute",
            "fourth_attribute",
        ),
    )

    def get_attribute_values_for_group(self, group_name: str) -> List[str]:
        """Возвращает значения атрибутов, принадлежащих указанной группе."""
        values = []
        for attr in (self.attr1, self.attr2, self.attr3, self.attr4):
            if attr and attr.attribute_group == group_name:
                values.append(attr.value)
        return values