from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from core.base import BaseModel


class Order(BaseModel):
    __tablename__ = "orders"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[int]
