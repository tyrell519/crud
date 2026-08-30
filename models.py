from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from base import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)

    orders: Mapped[list["Order"]] = relationship(back_populates="user")


class Product(BaseModel):
    __tablename__ = "products"

    title: Mapped[str] = mapped_column(String(200))
    price: Mapped[float] = mapped_column()
    stock: Mapped[int] = mapped_column(default=0)

    orders: Mapped[list["Order"]] = relationship(back_populates="product")


class Order(BaseModel):
    __tablename__ = "orders"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[int]

    user: Mapped[User] = relationship(back_populates="orders")
    product: Mapped[Product] = relationship(back_populates="orders")
