from sqlalchemy.orm import Session

from core.repositories import BaseRepository
from domains.users.models import User


class UserRepository(BaseRepository[User]):
    """Data access for the users domain."""

    def __init__(self, db: Session):
        super().__init__(db, User)
