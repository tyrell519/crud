# FastAPI + SQLAlchemy CRUD

A small REST API built with **FastAPI**, **SQLAlchemy 2.0**, and **SQLite**. It exposes **3 endpoints** (`/users`, `/products`, `/orders`), each backed by its own table, with full create/read/update/delete support.

## Features

- 3 endpoints, 3 tables: `users`, `products`, `orders`
- Full CRUD per endpoint (POST, GET list, GET by id, PUT, DELETE)
- Layered modular monolith (DDD style): each domain has its own model, schemas, repository, service, and router
- Dependency injection via FastAPI `Depends` (`get_db → repository → service`); services and repositories are plain classes, unit-testable without FastAPI
- SQLAlchemy 2.0 ORM: typed `Mapped`/`mapped_column` models
- Shared declarative mixins (`core/base.py`): auto-incrementing integer `id`, `created_at`, soft delete
- Soft delete: `DELETE` flags the row (`deleted_at`) instead of removing it; soft-deleted rows are hidden from all reads (404)
- Pydantic request validation (types, min/max, email format)
- Cross-domain rules in services: an order must reference a live user and product (else 404); DB foreign keys as a backstop
- Interactive API docs (Swagger UI at `/docs`)

## Project structure

```
.
├── main.py            # App assembly: routers, exception handlers, lifespan
├── database.py        # SQLAlchemy engine, session factory, declarative base
├── core/              # Shared kernel
│   ├── base.py        # IDMixin, TimestampsMixin, SoftDeleteMixin + abstract BaseModel
│   ├── exceptions.py  # Domain errors: NotFoundError, ConflictError
│   └── repositories.py# BaseRepository — generic session-scoped data access
├── domains/           # One self-contained package per domain
│   ├── users/         # models, schemas, repository, service, router, dependencies
│   ├── products/      # same layout
│   └── orders/        # same layout; OrderService validates users + products
├── tests/             # Unit tests for services/repositories (no FastAPI)
├── requirements.txt   # Runtime dependencies
├── requirements-dev.txt
└── crud.db            # SQLite database (created at runtime, git-ignored)
```

### Architecture

Layered, one direction of dependency per request:

```
HTTP request → router (domains/*/router.py)
                 → service (domains/*/service.py)   ← business rules
                 → repository (domains/*/repository.py) ← data access
                 → SQLAlchemy session → SQLite
```

- **Routers** are thin adapters: parse the request, call the service, return the result
- **Services** own business rules, including cross-domain invariants (`OrderService` reads through `UserRepository`/`ProductRepository` to verify targets exist and are not soft-deleted)
- **Repositories** own all SQLAlchemy access and translate ORM `IntegrityError`s into domain exceptions (`ConflictError`), so services never import SQLAlchemy error types
- **Injection**: each domain's `dependencies.py` builds the `Depends` chain (`get_db → repository → service`). Because repositories and services are plain classes with constructor injection, tests construct them directly with an in-memory session — no FastAPI, no HTTP
- **Error mapping**: domain exceptions are raised in services/repositories and mapped to HTTP status codes once, in `main.py` (`NotFoundError` → 404, `ConflictError` → 400)

All models inherit from `BaseModel` in `core/base.py`, which composes three declarative mixins:

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
pip install -r requirements-dev.txt   # only needed to run the tests
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
| 400  | Constraint violated (e.g. duplicate email)                     |
| 404  | Resource not found — including orders referencing a missing or soft-deleted user/product |
| 422  | Validation error (bad type, out-of-range value, bad email)     |

## Try the error cases

```bash
# Duplicate email -> 400
curl -X POST http://127.0.0.1:8000/users \
  -H 'Content-Type: application/json' \
  -d '{"name": "Clone", "email": "riley@example.com"}'

# Order with a nonexistent user -> 404 (cross-domain check in OrderService)
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

## Tests

```bash
pytest
```

The suite in `tests/` exercises services and repositories directly against an in-memory SQLite session — no FastAPI app, no HTTP. It covers id increment, partial updates, unique-conflict → `ConflictError`, soft-delete visibility, and the cross-domain order validations.

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
