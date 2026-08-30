from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    created_at: str


class ProductCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    price: float = Field(..., ge=0)
    stock: int = Field(0, ge=0)


class ProductUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    price: Optional[float] = Field(None, ge=0)
    stock: Optional[int] = Field(None, ge=0)


class ProductOut(BaseModel):
    id: int
    title: str
    price: float
    stock: int
    created_at: str


class OrderCreate(BaseModel):
    user_id: int = Field(..., ge=1)
    product_id: int = Field(..., ge=1)
    quantity: int = Field(..., ge=1)


class OrderUpdate(BaseModel):
    user_id: Optional[int] = Field(None, ge=1)
    product_id: Optional[int] = Field(None, ge=1)
    quantity: Optional[int] = Field(None, ge=1)


class OrderOut(BaseModel):
    id: int
    user_id: int
    product_id: int
    quantity: int
    created_at: str
