from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    price: float = Field(..., ge=0)
    stock: int = Field(0, ge=0)


class ProductUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    price: float | None = Field(None, ge=0)
    stock: int | None = Field(None, ge=0)


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    price: float
    stock: int
    created_at: datetime
    deleted_at: datetime | None = None
