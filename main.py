import sqlite3
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import APIRouter, FastAPI, HTTPException

import database
from models import (
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
    database.init_db()
    yield


app = FastAPI(title="FastAPI + SQLite CRUD", version="1.0.0", lifespan=lifespan)


def _fetch(table: str, row_id: int) -> Optional[dict]:
    with database.get_db() as conn:
        row = conn.execute(f"SELECT * FROM {table} WHERE id = ?", (row_id,)).fetchone()
        return dict(row) if row else None


def _insert(table: str, data: dict) -> dict:
    try:
        with database.get_db() as conn:
            cols = ", ".join(data)
            placeholders = ", ".join(f":{c}" for c in data)
            cur = conn.execute(
                f"INSERT INTO {table} ({cols}) VALUES ({placeholders})", data
            )
            conn.commit()
            row = conn.execute(
                f"SELECT * FROM {table} WHERE id = ?", (cur.lastrowid,)
            ).fetchone()
            return dict(row)
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


def make_router(
    table: str,
    prefix: str,
    create_model: type,
    update_model: type,
    out_model: type,
) -> APIRouter:
    router = APIRouter(prefix=prefix, tags=[prefix[1:]])

    @router.post("", status_code=201, response_model=out_model)
    def create(payload: create_model) -> dict:
        return _insert(table, payload.model_dump())

    @router.get("", response_model=List[out_model])
    def list_all() -> List[dict]:
        with database.get_db() as conn:
            rows = conn.execute(f"SELECT * FROM {table} ORDER BY id").fetchall()
        return [dict(r) for r in rows]

    @router.get("/{row_id}", response_model=out_model)
    def get_one(row_id: int) -> dict:
        item = _fetch(table, row_id)
        if item is None:
            raise HTTPException(status_code=404, detail=f"{table[:-1]} not found")
        return item

    @router.put("/{row_id}", response_model=out_model)
    def update(row_id: int, payload: update_model) -> dict:
        current = _fetch(table, row_id)
        if current is None:
            raise HTTPException(status_code=404, detail=f"{table[:-1]} not found")
        changes = payload.model_dump(exclude_unset=True)
        if not changes:
            return current
        try:
            with database.get_db() as conn:
                assignments = ", ".join(f"{c} = ?" for c in changes)
                conn.execute(
                    f"UPDATE {table} SET {assignments} WHERE id = ?",
                    (*changes.values(), row_id),
                )
                conn.commit()
        except sqlite3.IntegrityError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        return _fetch(table, row_id)

    @router.delete("/{row_id}", status_code=204)
    def delete(row_id: int) -> None:
        with database.get_db() as conn:
            cur = conn.execute(f"DELETE FROM {table} WHERE id = ?", (row_id,))
            conn.commit()
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail=f"{table[:-1]} not found")

    return router


app.include_router(make_router("users", "/users", UserCreate, UserUpdate, UserOut))
app.include_router(
    make_router("products", "/products", ProductCreate, ProductUpdate, ProductOut)
)
app.include_router(make_router("orders", "/orders", OrderCreate, OrderUpdate, OrderOut))
