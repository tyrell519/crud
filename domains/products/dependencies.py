from fastapi import Depends
from sqlalchemy.orm import Session

from database import get_db
from domains.products.repository import ProductRepository
from domains.products.service import ProductService


def get_product_repository(db: Session = Depends(get_db)) -> ProductRepository:
    return ProductRepository(db)


def get_product_service(
    products: ProductRepository = Depends(get_product_repository),
) -> ProductService:
    return ProductService(products=products)
