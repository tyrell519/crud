from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from core.base import BaseModel


class Product(BaseModel):
    __tablename__ = "products"

    title: Mapped[str] = mapped_column(String(200))
    price: Mapped[float] = mapped_column()
    stock: Mapped[int] = mapped_column(default=0)
