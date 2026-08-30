from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class OrderCreate(BaseModel):
    user_id: int = Field(..., ge=1)
    product_id: int = Field(..., ge=1)
    quantity: int = Field(..., ge=1)


class OrderUpdate(BaseModel):
    user_id: int | None = Field(None, ge=1)
    product_id: int | None = Field(None, ge=1)
    quantity: int | None = Field(None, ge=1)


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    product_id: int
    quantity: int
    created_at: datetime
    deleted_at: datetime | None = None
