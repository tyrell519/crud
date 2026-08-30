# FastAPI + SQLite CRUD

A small REST API built with **FastAPI** and **SQLite**. It exposes **3 endpoints** (`/users`, `/products`, `/orders`), each backed by its own table, with full create/read/update/delete support.

## Features

- 3 endpoints, 3 tables: `users`, `products`, `orders`
- Full CRUD per endpoint (POST, GET list, GET by id, PUT, DELETE)
- Pydantic request validation (types, min/max, email format)
- Foreign key enforcement (`orders` references `users` and `products`)
- Automatic `created_at` timestamps
- Interactive API docs (Swagger UI at `/docs`)

## Project structure

```
.
├── main.py          # FastAPI app, routes, CRUD router factory
├── database.py      # SQLite connection + schema (creates tables on startup)
├── models.py        # Pydantic request/response schemas
├── requirements.txt # Python dependencies
└── crud.db          # SQLite database (created at runtime, git-ignored)
```

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
curl -X DELETE http://127.0.0.1:8000/users/1  # delete
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
