# FastAPI + SQLAlchemy CRUD

A small REST API built with **FastAPI**, **SQLAlchemy 2.0**, and **SQLite**. It exposes **3 endpoints** (`/users`, `/products`, `/orders`), each backed by its own table, with full create/read/update/delete support.

## Features

- 3 endpoints, 3 tables: `users`, `products`, `orders`
- Full CRUD per endpoint (POST, GET list, GET by id, PUT, DELETE)
- SQLAlchemy 2.0 ORM: typed `Mapped`/`mapped_column` models with relationships
- Shared declarative mixins (`base.py`): auto-incrementing integer `id`, `created_at`, soft delete
- Soft delete: `DELETE` flags the row (`deleted_at`) instead of removing it; soft-deleted rows are hidden from all reads (404)
- Pydantic request validation (types, min/max, email format)
- Foreign key enforcement (`orders` references `users` and `products`)
- Interactive API docs (Swagger UI at `/docs`)

## Project structure

```
.
├── main.py          # FastAPI app, routes, CRUD router factory
├── database.py      # SQLAlchemy engine, session factory, declarative base
├── base.py          # IDMixin, TimestampsMixin, SoftDeleteMixin + abstract BaseModel
├── models.py        # SQLAlchemy 2.0 ORM models (User, Product, Order)
├── schemas.py       # Pydantic request/response schemas
├── requirements.txt # Python dependencies
└── crud.db          # SQLite database (created at runtime, git-ignored)
```

All models inherit from `BaseModel` in `base.py`, which composes three declarative mixins:

| Mixin             | Provides                                    |
|-------------------|---------------------------------------------|
| `IDMixin`         | auto-incrementing integer `id` primary key  |
| `TimestampsMixin` | server-side `created_at`                    |
| `SoftDeleteMixin` | nullable `deleted_at` + `is_deleted` helper |

## Requirements

- Python 3.10+

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn main:app --port 8000
```

> If port 8000 is already in use, pick another: `uvicorn main:app --port 8010`

Then open:

- **Swagger UI:** http://127.0.0.1:8000/docs
- **ReDoc:** http://127.0.0.1:8000/redoc

The SQLite database (`crud.db`) is created automatically on first start. To reset all data, stop the server and delete the file.

## API reference

### `POST /users` — create a user

```bash
curl -X POST http://127.0.0.1:8000/users \
  -H 'Content-Type: application/json' \
  -d '{"name": "Riley", "email": "riley@example.com"}'
```

| Field   | Type | Rules            |
|---------|------|------------------|
| `name`  | str  | required, 1-100  |
| `email` | email| required, unique |

### `POST /products` — create a product

```bash
curl -X POST http://127.0.0.1:8000/products \
  -H 'Content-Type: application/json' \
  -d '{"title": "Keyboard", "price": 79.99, "stock": 12}'
```

| Field   | Type  | Rules          |
|---------|-------|----------------|
| `title` | str   | required, 1-200|
| `price` | float | required, >= 0 |
| `stock` | int   | optional, >= 0 (default 0) |

### `POST /orders` — create an order

```bash
curl -X POST http://127.0.0.1:8000/orders \
  -H 'Content-Type: application/json' \
  -d '{"user_id": 1, "product_id": 1, "quantity": 2}'
```

| Field      | Type | Rules                        |
|------------|------|------------------------------|
| `user_id`  | int  | required, must exist in `users`    |
| `product_id` | int | required, must exist in `products` |
| `quantity` | int  | required, >= 1               |

### Shared operations (all three endpoints)

```bash
curl http://127.0.0.1:8000/users            # list all
curl http://127.0.0.1:8000/users/1          # get one
curl -X PUT http://127.0.0.1:8000/users/1 \
  -H 'Content-Type: application/json' \
  -d '{"name": "Riley S."}'                 # partial update (only fields sent change)
curl -X DELETE http://127.0.0.1:8000/users/1  # soft delete (sets deleted_at)
```

Replace `/users` with `/products` or `/orders` as needed.

## Status codes

| Code | Meaning                                                        |
|------|----------------------------------------------------------------|
| 200  | Success (list, get, update)                                    |
| 201  | Created                                                        |
| 204  | Deleted                                                        |
| 400  | Constraint violated (duplicate email, bad foreign key)         |
| 404  | Resource not found                                             |
| 422  | Validation error (bad type, out-of-range value, bad email)     |

## Try the error cases

```bash
# Duplicate email -> 400
curl -X POST http://127.0.0.1:8000/users \
  -H 'Content-Type: application/json' \
  -d '{"name": "Clone", "email": "riley@example.com"}'

# Order with a nonexistent user -> 400 (FK violation)
curl -X POST http://127.0.0.1:8000/orders \
  -H 'Content-Type: application/json' \
  -d '{"user_id": 999, "product_id": 1, "quantity": 1}'

# Negative price -> 422
curl -X POST http://127.0.0.1:8000/products \
  -H 'Content-Type: application/json' \
  -d '{"title": "Bad", "price": -5}'

# Missing resource -> 404
curl http://127.0.0.1:8000/products/999
```

## Soft delete

`DELETE` does not remove the row — it sets `deleted_at`, and the row becomes invisible through the API:

```bash
curl -X DELETE http://127.0.0.1:8000/users/1   # 204
curl http://127.0.0.1:8000/users/1             # 404 (hidden)
curl http://127.0.0.1:8000/users               # list excludes it
curl -X PUT http://127.0.0.1:8000/users/1 -H 'Content-Type: application/json' -d '{"name":"x"}'  # 404
```

The row still exists in `crud.db` with `deleted_at` populated, so nothing is ever actually lost.

## Full walkthrough

A complete happy path from scratch:

```bash
curl -X POST http://127.0.0.1:8000/users    -H 'Content-Type: application/json' -d '{"name":"Riley","email":"riley@example.com"}'
curl -X POST http://127.0.0.1:8000/products -H 'Content-Type: application/json' -d '{"title":"Keyboard","price":79.99,"stock":12}'
curl -X POST http://127.0.0.1:8000/orders   -H 'Content-Type: application/json' -d '{"user_id":1,"product_id":1,"quantity":2}'
curl http://127.0.0.1:8000/users
curl http://127.0.0.1:8000/products
curl http://127.0.0.1:8000/orders
curl -X PUT http://127.0.0.1:8000/orders/1  -H 'Content-Type: application/json' -d '{"quantity":5}'
curl -X DELETE http://127.0.0.1:8000/orders/1
```
