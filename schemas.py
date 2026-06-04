from pydantic import BaseModel
from typing import Optional
from datetime import date


class UserBase(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None


class UserCreate(UserBase):
    pass


class UserResponse(UserBase):
    id: int

    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    name: str
    price: float
    stock: int = 0


class ProductCreate(ProductBase):
    pass


class ProductResponse(ProductBase):
    id: int

    class Config:
        from_attributes = True


class OrderBase(BaseModel):
    product_id: int
    user_id: int
    quantity: int
    order_date: Optional[date] = None


class OrderCreate(OrderBase):
    pass


class OrderResponse(OrderBase):
    id: int

    class Config:
        from_attributes = True
