from sqlalchemy.orm import Session

from core.repositories import BaseRepository
from domains.orders.models import Order


class OrderRepository(BaseRepository[Order]):
    """Data access for the orders domain."""

    def __init__(self, db: Session):
        super().__init__(db, Order)
