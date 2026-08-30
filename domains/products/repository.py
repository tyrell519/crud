from sqlalchemy.orm import Session

from core.repositories import BaseRepository
from domains.products.models import Product


class ProductRepository(BaseRepository[Product]):
    """Data access for the products domain."""

    def __init__(self, db: Session):
        super().__init__(db, Product)
