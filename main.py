import sqlite3
import json
from contextlib import asynccontextmanager
from pathlib import Path

DB_PATH = Path(__file__).parent / "app.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL CHECK(price >= 0),
            stock INTEGER NOT NULL DEFAULT 0 CHECK(stock >= 0),
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL CHECK(quantity > 0),
            total_price REAL NOT NULL,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'confirmed', 'shipped', 'cancelled')),
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)
    conn.commit()
    conn.close()


@asynccontextmanager
async def lifespan(app):
    init_db()
    yield


from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

app = FastAPI(title="CRUD API", version="1.0.0", lifespan=lifespan)


# ===================== PYDANTIC MODELS =====================

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., min_length=5, max_length=100)
    is_active: Optional[int] = 1

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[int] = None

class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    stock: int = Field(..., ge=0)

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None

class OrderCreate(BaseModel):
    user_id: int
    product_id: int
    quantity: int = Field(..., gt=0)
    total_price: float = Field(..., gt=0)
    status: Optional[str] = "pending"

class OrderUpdate(BaseModel):
    status: Optional[str] = None
    quantity: Optional[int] = None
    total_price: Optional[float] = None


# ===================== HELPERS =====================

def row_to_dict(row):
    if row is None:
        return None
    return dict(row)


# ===================== USERS ENDPOINT =====================

@app.get("/users")
def list_users(
    is_active: Optional[int] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    db = get_db()
    try:
        query = "SELECT * FROM users WHERE 1=1"
        params = {}
        if is_active is not None:
            query += " AND is_active = :is_active"
            params["is_active"] = is_active
        query += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
        params["limit"] = limit
        params["offset"] = offset
        rows = db.execute(query, params).fetchall()
        return {"data": [row_to_dict(r) for r in rows], "count": len(rows)}
    finally:
        db.close()


@app.get("/users/{user_id}")
def get_user(user_id: int):
    db = get_db()
    try:
        row = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        return row_to_dict(row)
    finally:
        db.close()


@app.post("/users", status_code=201)
def create_user(user: UserCreate):
    db = get_db()
    try:
        cursor = db.execute(
            "INSERT INTO users (username, email, is_active) VALUES (?, ?, ?)",
            (user.username, user.email, user.is_active)
        )
        db.commit()
        row = db.execute("SELECT * FROM users WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return row_to_dict(row)
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username or email already exists")
    finally:
        db.close()


@app.put("/users/{user_id}")
def update_user(user_id: int, user: UserUpdate):
    db = get_db()
    try:
        existing = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="User not found")
        updates = user.model_dump(exclude_unset=True)
        if not updates:
            return row_to_dict(existing)
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [user_id]
        db.execute(f"UPDATE users SET {set_clause} WHERE id = ?", values)
        db.commit()
        row = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return row_to_dict(row)
    finally:
        db.close()


@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    db = get_db()
    try:
        existing = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="User not found")
        db.execute("DELETE FROM users WHERE id = ?", (user_id,))
        db.commit()
        return {"message": "User deleted successfully"}
    finally:
        db.close()


# ===================== PRODUCTS ENDPOINT =====================

@app.get("/products")
def list_products(
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    in_stock: Optional[int] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    db = get_db()
    try:
        query = "SELECT * FROM products WHERE 1=1"
        params = {}
        if min_price is not None:
            query += " AND price >= :min_price"
            params["min_price"] = min_price
        if max_price is not None:
            query += " AND price <= :max_price"
            params["max_price"] = max_price
        if in_stock is not None:
            query += " AND stock > 0" if in_stock else " AND stock = 0"
        query += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
        params["limit"] = limit
        params["offset"] = offset
        rows = db.execute(query, params).fetchall()
        return {"data": [row_to_dict(r) for r in rows], "count": len(rows)}
    finally:
        db.close()


@app.get("/products/{product_id}")
def get_product(product_id: int):
    db = get_db()
    try:
        row = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Product not found")
        return row_to_dict(row)
    finally:
        db.close()


@app.post("/products", status_code=201)
def create_product(product: ProductCreate):
    db = get_db()
    try:
        cursor = db.execute(
            "INSERT INTO products (name, description, price, stock) VALUES (?, ?, ?, ?)",
            (product.name, product.description, product.price, product.stock)
        )
        db.commit()
        row = db.execute("SELECT * FROM products WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return row_to_dict(row)
    finally:
        db.close()


@app.put("/products/{product_id}")
def update_product(product_id: int, product: ProductUpdate):
    db = get_db()
    try:
        existing = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Product not found")
        updates = product.model_dump(exclude_unset=True)
        if not updates:
            return row_to_dict(existing)
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [product_id]
        db.execute(f"UPDATE products SET {set_clause} WHERE id = ?", values)
        db.commit()
        row = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        return row_to_dict(row)
    finally:
        db.close()


@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    db = get_db()
    try:
        existing = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Product not found")
        db.execute("PRAGMA foreign_keys = OFF;")
        db.execute("DELETE FROM products WHERE id = ?", (product_id,))
        db.execute("PRAGMA foreign_keys = ON;")
        db.commit()
        return {"message": "Product deleted successfully"}
    finally:
        db.close()


# ===================== ORDERS ENDPOINT =====================

@app.get("/orders")
def list_orders(
    status: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    db = get_db()
    try:
        query = """
            SELECT o.*, u.username, p.name as product_name
            FROM orders o
            JOIN users u ON o.user_id = u.id
            JOIN products p ON o.product_id = p.id
            WHERE 1=1
        """
        params = {}
        if status:
            query += " AND o.status = :status"
            params["status"] = status
        if user_id:
            query += " AND o.user_id = :user_id"
            params["user_id"] = user_id
        query += " ORDER BY o.created_at DESC LIMIT :limit OFFSET :offset"
        params["limit"] = limit
        params["offset"] = offset
        rows = db.execute(query, params).fetchall()
        return {"data": [row_to_dict(r) for r in rows], "count": len(rows)}
    finally:
        db.close()


@app.get("/orders/{order_id}")
def get_order(order_id: int):
    db = get_db()
    try:
        row = db.execute(
            """SELECT o.*, u.username, p.name as product_name
               FROM orders o
               JOIN users u ON o.user_id = u.id
               JOIN products p ON o.product_id = p.id
               WHERE o.id = ?""",
            (order_id,)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Order not found")
        return row_to_dict(row)
    finally:
        db.close()


@app.post("/orders", status_code=201)
def create_order(order: OrderCreate):
    db = get_db()
    try:
        user = db.execute("SELECT id FROM users WHERE id = ?", (order.user_id,)).fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        product = db.execute("SELECT id, stock FROM products WHERE id = ?", (order.product_id,)).fetchone()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        if product["stock"] < order.quantity:
            raise HTTPException(status_code=400, detail="Insufficient stock")
        cursor = db.execute(
            "INSERT INTO orders (user_id, product_id, quantity, total_price, status) VALUES (?, ?, ?, ?, ?)",
            (order.user_id, order.product_id, order.quantity, order.total_price, order.status)
        )
        new_stock = product["stock"] - order.quantity
        db.execute("UPDATE products SET stock = ? WHERE id = ?", (new_stock, order.product_id))
        db.commit()
        row = db.execute("SELECT * FROM orders WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return row_to_dict(row)
    finally:
        db.close()


@app.put("/orders/{order_id}")
def update_order(order_id: int, order: OrderUpdate):
    db = get_db()
    try:
        existing = db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Order not found")
        updates = order.model_dump(exclude_unset=True)
        if not updates:
            return row_to_dict(existing)
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [order_id]
        db.execute(f"UPDATE orders SET {set_clause} WHERE id = ?", values)
        db.commit()
        row = db.execute(
            "SELECT o.*, u.username, p.name as product_name FROM orders o JOIN users u ON o.user_id = u.id JOIN products p ON o.product_id = p.id WHERE o.id = ?",
            (order_id,)
        ).fetchone()
        return row_to_dict(row)
    finally:
        db.close()


@app.delete("/orders/{order_id}")
def delete_order(order_id: int):
    db = get_db()
    try:
        existing = db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Order not found")
        product = db.execute(
            "SELECT stock FROM products WHERE id = ?", (existing["product_id"],)
        ).fetchone()
        if product:
            new_stock = product["stock"] + existing["quantity"]
            db.execute("UPDATE products SET stock = ? WHERE id = ?", (new_stock, existing["product_id"]))
        db.execute("PRAGMA foreign_keys = OFF;")
        db.execute("DELETE FROM orders WHERE id = ?", (order_id,))
        db.execute("PRAGMA foreign_keys = ON;")
        db.commit()
        return {"message": "Order deleted successfully"}
    finally:
        db.close()
