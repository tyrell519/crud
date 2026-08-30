from typing import Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.exceptions import ConflictError

ModelT = TypeVar("ModelT")


class BaseRepository(Generic[ModelT]):
    """Session-scoped data access for a BaseModel-derived ORM class.

    Translates SQLAlchemy integrity errors into domain exceptions so
    services and routers never see ORM-level failures.
    """

    def __init__(self, db: Session, model: type[ModelT]):
        self.db = db
        self.model = model

    def get_by_id(self, item_id: int) -> ModelT | None:
        return self.db.get(self.model, item_id)

    def get_active_by_id(self, item_id: int) -> ModelT | None:
        item = self.get_by_id(item_id)
        return None if item is None or item.is_deleted else item

    def list_active(self) -> list[ModelT]:
        stmt = (
            select(self.model)
            .where(self.model.deleted_at.is_(None))
            .order_by(self.model.id)
        )
        return list(self.db.scalars(stmt))

    def create(self, **data: object) -> ModelT:
        try:
            item = self.model(**data)
            self.db.add(item)
            self.db.commit()
            self.db.refresh(item)
            return item
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError(str(exc.orig)) from exc

    def save(self, item: ModelT) -> ModelT:
        try:
            self.db.commit()
            self.db.refresh(item)
            return item
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError(str(exc.orig)) from exc

    def soft_delete(self, item: ModelT) -> None:
        item.deleted_at = func.now()
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError(str(exc.orig)) from exc
