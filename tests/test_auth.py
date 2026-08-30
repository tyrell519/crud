import base64

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import database
import domains  # noqa: F401  (register tables with Base.metadata)
from database import Base, get_db
from main import app


def _make_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _fk(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)()


@pytest.fixture()
def client(monkeypatch):
    session = _make_session()

    def _override_get_db():
        yield session

    monkeypatch.setattr(database, "init_db", lambda: None)
    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    session.close()


def _basic(username: str, password: str) -> dict:
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def test_requires_credentials(client: TestClient):
    resp = client.get("/users")
    assert resp.status_code == 401
    assert "WWW-Authenticate" in resp.headers


def test_rejects_wrong_password(client: TestClient):
    resp = client.get("/users", headers=_basic("admin", "nope"))
    assert resp.status_code == 401


def test_rejects_wrong_username(client: TestClient):
    resp = client.get("/users", headers=_basic("someone", "admin"))
    assert resp.status_code == 401


def test_allows_valid_credentials(client: TestClient):
    resp = client.get("/users", headers=_basic("admin", "admin"))
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_with_valid_credentials(client: TestClient):
    resp = client.post(
        "/users",
        headers=_basic("admin", "admin"),
        json={"name": "Riley", "email": "riley@example.com"},
    )
    assert resp.status_code == 201
    assert resp.json()["id"] == 1


def test_auth_required_on_every_endpoint(client: TestClient):
    for url in ("/users", "/products", "/orders", "/users/1", "/products/1", "/orders/1"):
        assert client.get(url).status_code == 401


def test_docs_and_openapi_require_credentials(client: TestClient):
    assert client.get("/docs").status_code == 401
    assert client.get("/openapi.json").status_code == 401
