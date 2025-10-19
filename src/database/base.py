"""Base database models and mixins."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Column, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column

Base = declarative_base()


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class OrgScopedMixin:
    """Mixin for organization-scoped entities."""

    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="Organization ID for multi-tenancy",
    )


class AuditMixin:
    """Mixin for audit logging on mutations."""

    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User ID who created this record",
    )
    updated_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User ID who last updated this record",
    )


class VersionMixin:
    """Mixin for optimistic concurrency control."""

    version: Mapped[int] = mapped_column(
        default=1,
        nullable=False,
        comment="Version number for optimistic concurrency control",
    )


class IdempotencyMixin:
    """Mixin for idempotency key support."""

    idempotency_key: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        index=True,
        comment="Idempotency key for preventing duplicate operations",
    )


class SoftDeleteMixin:
    """Mixin for soft delete functionality."""

    deleted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when record was soft deleted",
    )
    deleted_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User ID who soft deleted this record",
    )


class BaseModel(Base, TimestampMixin):
    """Base model with common fields."""

    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }
