"""
SQLAlchemy Base class and common model utilities
"""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import MetaData, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Naming conventions for constraints (required for Alembic autogenerate)
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models"""
    
    metadata = MetaData(naming_convention=convention)
    
    # Type annotation map for common types
    type_annotation_map = {
        datetime: DateTime(timezone=True),
    }


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps"""
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )


class SoftDeleteMixin:
    """Mixin for soft delete functionality"""
    
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=None,
        nullable=True
    )
    
    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
    
    def soft_delete(self) -> None:
        self.deleted_at = datetime.now(timezone.utc)
    
    def restore(self) -> None:
        self.deleted_at = None
