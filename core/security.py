import base64
import os
import secrets

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

# Defaults keep the app runnable out of the box; override via environment.
DEFAULT_USERNAME = os.getenv("CRUD_USERNAME", "admin")
DEFAULT_PASSWORD = os.getenv("CRUD_PASSWORD", "admin")

_BASIC_REALM = 'Basic realm="crud"'


def _unauthorized() -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content={"detail": "Incorrect username or password"},
        headers={"WWW-Authenticate": _BASIC_REALM},
    )


class BasicAuthMiddleware(BaseHTTPMiddleware):
    """Enforce HTTP Basic authentication on every request.

    Runs at the edge of the app, so it covers all API endpoints *and* the
    auto-generated /docs, /redoc, and /openapi.json routes. Credentials come
    from the environment (``CRUD_USERNAME`` / ``CRUD_PASSWORD``).
    """

    async def dispatch(self, request: Request, call_next):
        auth_header = request.headers.get("authorization", "")
        scheme, _, value = auth_header.partition(" ")
        if scheme.lower() != "basic" or not value:
            return _unauthorized()
        try:
            decoded = base64.b64decode(value).decode("utf-8")
        except Exception:
            return _unauthorized()
        username, _, password = decoded.partition(":")
        correct_username = secrets.compare_digest(
            username.encode("utf-8"), DEFAULT_USERNAME.encode("utf-8")
        )
        correct_password = secrets.compare_digest(
            password.encode("utf-8"), DEFAULT_PASSWORD.encode("utf-8")
        )
        if not correct_username:
            # Dummy comparison so a bad username doesn't leak timing.
            secrets.compare_digest(
                password.encode("utf-8"), DEFAULT_PASSWORD.encode("utf-8")
            )
        if not (correct_username and correct_password):
            return _unauthorized()
        return await call_next(request)
