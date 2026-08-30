from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

import database
from core.exceptions import ConflictError, NotFoundError
from core.security import BasicAuthMiddleware
from domains.orders.router import router as orders_router
from domains.products.router import router as products_router
from domains.users.router import router as users_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    database.init_db()
    yield


app = FastAPI(title="FastAPI + SQLAlchemy CRUD", version="3.0.0", lifespan=lifespan)

# Enforce Basic auth on every route (API endpoints + /docs + /openapi.json).
app.add_middleware(BasicAuthMiddleware)


@app.exception_handler(NotFoundError)
async def handle_not_found(_: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ConflictError)
async def handle_conflict(_: Request, exc: ConflictError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


app.include_router(users_router)
app.include_router(products_router)
app.include_router(orders_router)
