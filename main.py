from contextlib import asynccontextmanager
from typing import List

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import models
from database import get_db, init_db
from schemas import (
    OrderCreate,
    OrderOut,
    OrderUpdate,
    ProductCreate,
    ProductOut,
    ProductUpdate,
    UserCreate,
    UserOut,
    UserUpdate,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="FastAPI + SQLAlchemy CRUD", version="2.0.0", lifespan=lifespan
)


def make_router(
    prefix: str,
    model: type,
    create_model: type,
    update_model: type,
    out_model: type,
) -> APIRouter:
    router = APIRouter(prefix=prefix, tags=[prefix[1:]])
    label = model.__name__.lower()

    @router.post("", status_code=201, response_model=out_model)
    def create(payload: create_model, db: Session = Depends(get_db)):
        try:
            item = model(**payload.model_dump())
            db.add(item)
            db.commit()
            db.refresh(item)
            return item
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(status_code=400, detail=str(exc.orig))

    @router.get("", response_model=List[out_model])
    def list_all(db: Session = Depends(get_db)):
        stmt = select(model).where(model.deleted_at.is_(None)).order_by(model.id)
        return db.scalars(stmt).all()

    @router.get("/{row_id}", response_model=out_model)
    def get_one(row_id: int, db: Session = Depends(get_db)):
        item = db.get(model, row_id)
        if item is None or item.is_deleted:
            raise HTTPException(status_code=404, detail=f"{label} not found")
        return item

    @router.put("/{row_id}", response_model=out_model)
    def update(row_id: int, payload: update_model, db: Session = Depends(get_db)):
        item = db.get(model, row_id)
        if item is None or item.is_deleted:
            raise HTTPException(status_code=404, detail=f"{label} not found")
        try:
            for field, value in payload.model_dump(exclude_unset=True).items():
                setattr(item, field, value)
            db.commit()
            db.refresh(item)
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(status_code=400, detail=str(exc.orig))
        return item

    @router.delete("/{row_id}", status_code=204)
    def delete(row_id: int, db: Session = Depends(get_db)):
        item = db.get(model, row_id)
        if item is None or item.is_deleted:
            raise HTTPException(status_code=404, detail=f"{label} not found")
        try:
            item.deleted_at = func.now()
            db.commit()
            db.refresh(item)
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(status_code=400, detail=str(exc.orig))

    return router


app.include_router(make_router("/users", models.User, UserCreate, UserUpdate, UserOut))
app.include_router(
    make_router("/products", models.Product, ProductCreate, ProductUpdate, ProductOut)
)
app.include_router(make_router("/orders", models.Order, OrderCreate, OrderUpdate, OrderOut))
