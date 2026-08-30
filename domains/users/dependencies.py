from fastapi import Depends
from sqlalchemy.orm import Session

from database import get_db
from domains.users.repository import UserRepository
from domains.users.service import UserService


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_user_service(
    users: UserRepository = Depends(get_user_repository),
) -> UserService:
    return UserService(users=users)
