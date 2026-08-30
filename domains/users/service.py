from core.exceptions import NotFoundError
from domains.users.models import User
from domains.users.repository import UserRepository
from domains.users.schemas import UserCreate, UserUpdate


class UserService:
    """Business rules for the users domain.

    Plain class with constructor injection: unit-testable with a bare
    repository instance, no FastAPI involved.
    """

    def __init__(self, users: UserRepository):
        self.users = users

    def create_user(self, data: UserCreate) -> User:
        return self.users.create(**data.model_dump())

    def get_user(self, user_id: int) -> User:
        user = self.users.get_active_by_id(user_id)
        if user is None:
            raise NotFoundError("user not found")
        return user

    def list_users(self) -> list[User]:
        return self.users.list_active()

    def update_user(self, user_id: int, data: UserUpdate) -> User:
        user = self.get_user(user_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(user, field, value)
        return self.users.save(user)

    def delete_user(self, user_id: int) -> None:
        user = self.get_user(user_id)
        self.users.soft_delete(user)
