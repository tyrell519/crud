import pytest
from sqlalchemy import text

from core.exceptions import ConflictError, NotFoundError
from domains.users.models import User
from domains.users.repository import UserRepository
from domains.users.schemas import UserCreate, UserUpdate
from domains.users.service import UserService


@pytest.fixture()
def service(db_session) -> UserService:
    return UserService(UserRepository(db_session))


def test_create_user_assigns_increments_id(service: UserService):
    first = service.create_user(UserCreate(name="Riley", email="riley@example.com"))
    second = service.create_user(UserCreate(name="Sam", email="sam@example.com"))
    assert first.id == 1
    assert second.id == 2
    assert first.deleted_at is None
    assert first.created_at is not None


def test_get_missing_user_raises_not_found(service: UserService):
    with pytest.raises(NotFoundError):
        service.get_user(999)


def test_update_user_is_partial(service: UserService):
    user = service.create_user(UserCreate(name="Riley", email="riley@example.com"))
    updated = service.update_user(user.id, UserUpdate(name="Riley S."))
    assert updated.name == "Riley S."
    assert updated.email == "riley@example.com"


def test_duplicate_email_raises_conflict(service: UserService):
    service.create_user(UserCreate(name="Riley", email="riley@example.com"))
    with pytest.raises(ConflictError):
        service.create_user(UserCreate(name="Clone", email="riley@example.com"))


def test_soft_delete_hides_user_from_service(service: UserService):
    user = service.create_user(UserCreate(name="Riley", email="riley@example.com"))
    service.delete_user(user.id)
    with pytest.raises(NotFoundError):
        service.get_user(user.id)
    with pytest.raises(NotFoundError):
        service.delete_user(user.id)
    assert service.list_users() == []


def test_repository_soft_delete_keeps_row(db_session):
    repo = UserRepository(db_session)
    user = repo.create(name="Riley", email="riley@example.com")
    repo.soft_delete(user)
    row = db_session.execute(
        text("SELECT deleted_at FROM users WHERE id = :id"), {"id": user.id}
    ).fetchone()
    assert row is not None
    assert row[0] is not None
    assert repo.list_active() == []
    assert isinstance(repo.get_by_id(user.id), User)
    assert repo.get_active_by_id(user.id) is None
