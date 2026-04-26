from fastapi import APIRouter

from backend.app.models import BasketItem

basket_router = APIRouter(prefix="/basket", tags=["basket"])


class BasketRepository:
    """Repository for storing and retrieving basket items."""

    def __init__(self, session: Session):
        self.session = session

    def create_items(self, items: List[Dict]) -> List[Dict]:
        """Insert multiple basket rows.

        Each item should be a dict with keys
        `sticker_address`, and optionally `owner_address` and `recipient_address`.
        Returns list of created records as dicts.
        """
        created = []
        from sqlalchemy.exc import IntegrityError
        for it in items:
            bi = BasketItem(
                sticker_address=it.get('sticker_address'),
                owner_address=it.get('owner_address'),
                recipient_address=it.get('recipient_address')
            )
            self.session.add(bi)
            try:
                self.session.flush()  # get id
            except IntegrityError:
                # duplicate sticker_address, skip it
                self.session.rollback()
                continue
            created.append({
                'id': bi.id,
                'sticker_address': bi.sticker_address,
                'owner_address': bi.owner_address,
                'recipient_address': bi.recipient_address,
                'created_at': bi.created_at.isoformat() if bi.created_at else None
            })
        self.session.commit()
        return created

    def get_all(self) -> List[Dict]:
        """Return all basket items."""
        from transfer_app.db.models import BasketItem
        rows = self.session.query(BasketItem).order_by(BasketItem.id.desc()).all()
        return [
            {
                'id': r.id,
                'sticker_address': r.sticker_address,
                'owner_address': r.owner_address,
                'recipient_address': r.recipient_address,
                'created_at': r.created_at.isoformat() if r.created_at else None
            }
            for r in rows
        ]

    def filter(self, owner_address: Optional[str] = None, recipient_address: Optional[str] = None) -> List[Dict]:
        """Retrieve items optionally filtered by owner or recipient."""
        from transfer_app.db.models import BasketItem
        q = self.session.query(BasketItem)
        if owner_address is not None:
            q = q.filter(BasketItem.owner_address == owner_address)
        if recipient_address is not None:
            q = q.filter(BasketItem.recipient_address == recipient_address)
        rows = q.order_by(BasketItem.id.desc()).all()
        return [
            {
                'id': r.id,
                'sticker_address': r.sticker_address,
                'owner_address': r.owner_address,
                'recipient_address': r.recipient_address,
                'created_at': r.created_at.isoformat() if r.created_at else None
            }
            for r in rows
        ]

    # -- new convenience operations ------------------------------------------------
    def add_item(self, sticker_address: str, owner_address: Optional[str] = None,
                 recipient_address: Optional[str] = None) -> Dict:
        """Add a single sticker to the basket.

        If the sticker already exists in the database the call is a no-op and the
        existing row is returned.
        """
        from transfer_app.db.models import BasketItem
        bi = self.session.query(BasketItem).filter(BasketItem.sticker_address == sticker_address).first()
        if bi:
            return {
                'id': bi.id,
                'sticker_address': bi.sticker_address,
                'owner_address': bi.owner_address,
                'recipient_address': bi.recipient_address,
                'created_at': bi.created_at.isoformat() if bi.created_at else None
            }
        bi = BasketItem(
            sticker_address=sticker_address,
            owner_address=owner_address,
            recipient_address=recipient_address
        )
        self.session.add(bi)
        self.session.commit()
        return {
            'id': bi.id,
            'sticker_address': bi.sticker_address,
            'owner_address': bi.owner_address,
            'recipient_address': bi.recipient_address,
            'created_at': bi.created_at.isoformat() if bi.created_at else None
        }

    def update_item(self, sticker_address: str, recipient_address: Optional[str]) -> Optional[Dict]:
        """Change recipient for a sticker already in the basket."""
        from transfer_app.db.models import BasketItem
        bi = self.session.query(BasketItem).filter(BasketItem.sticker_address == sticker_address).first()
        if not bi:
            return None
        bi.recipient_address = recipient_address
        self.session.commit()
        return {
            'id': bi.id,
            'sticker_address': bi.sticker_address,
            'owner_address': bi.owner_address,
            'recipient_address': bi.recipient_address,
            'created_at': bi.created_at.isoformat() if bi.created_at else None
        }

    def delete_item(self, sticker_address: str) -> bool:
        """Remove a single sticker from the basket. Returns True if deleted."""
        from transfer_app.db.models import BasketItem
        deleted = self.session.query(BasketItem).filter(BasketItem.sticker_address == sticker_address).delete()
        if deleted:
            self.session.commit()
            return True
        return False

    def clear_all(self) -> None:
        """Delete all basket records."""
        from transfer_app.db.models import BasketItem
        self.session.query(BasketItem).delete()
        self.session.commit()
