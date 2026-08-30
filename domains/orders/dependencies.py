from fastapi import Depends
from sqlalchemy.orm import Session

from database import get_db
from domains.orders.repository import OrderRepository
from domains.orders.service import OrderService
from domains.products.dependencies import get_product_repository
from domains.products.repository import ProductRepository
from domains.users.dependencies import get_user_repository
from domains.users.repository import UserRepository


def get_order_repository(db: Session = Depends(get_db)) -> OrderRepository:
    return OrderRepository(db)


def get_order_service(
    orders: OrderRepository = Depends(get_order_repository),
    users: UserRepository = Depends(get_user_repository),
    products: ProductRepository = Depends(get_product_repository),
) -> OrderService:
    return OrderService(orders=orders, users=users, products=products)
