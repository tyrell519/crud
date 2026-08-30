from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class IDMixin:
    """Auto-incrementing integer primary key."""

    id: Mapped[int] = mapped_column(primary_key=True)


class TimestampsMixin:
    """Automatic creation timestamp (server-side clock)."""

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class SoftDeleteMixin:
    """Soft delete: rows are flagged instead of removed."""

    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, default=None
    )

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None


class BaseModel(Base, IDMixin, TimestampsMixin, SoftDeleteMixin):
    """Abstract base shared by all CRUD models.

    Provides: incremental integer id, created_at, and soft-delete.
    """

    __abstract__ = True
