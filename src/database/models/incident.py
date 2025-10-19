"""Incident model."""

import enum
from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import (
    AuditMixin,
    BaseModel,
    IdempotencyMixin,
    OrgScopedMixin,
    TimestampMixin,
    VersionMixin,
)


class IncidentStatus(str, enum.Enum):
    """Incident status values."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class IncidentPriority(str, enum.Enum):
    """Incident priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Incident(
    BaseModel,
    TimestampMixin,
    OrgScopedMixin,
    AuditMixin,
    VersionMixin,
    IdempotencyMixin,
):
    """Incident model for tracking incidents."""

    __tablename__ = "incidents"

    # Basic info
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    # Status and priority
    status: Mapped[IncidentStatus] = mapped_column(
        Enum(IncidentStatus), default=IncidentStatus.OPEN, nullable=False
    )
    priority: Mapped[IncidentPriority] = mapped_column(
        Enum(IncidentPriority), default=IncidentPriority.MEDIUM, nullable=False
    )

    # Assignment
    assigned_to: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Timestamps
    started_at: Mapped[datetime] = mapped_column(nullable=True)
    resolved_at: Mapped[datetime] = mapped_column(nullable=True)
    closed_at: Mapped[datetime] = mapped_column(nullable=True)

    # Metadata
    tags: Mapped[list[str]] = mapped_column(JSON, nullable=True, default=list)
    incident_metadata: Mapped[dict] = mapped_column(JSON, nullable=True, default=dict)

    # Metrics
    response_time_minutes: Mapped[int] = mapped_column(Integer, nullable=True)
    resolution_time_minutes: Mapped[int] = mapped_column(Integer, nullable=True)

    # Foreign keys
    team_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    organization_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Relationships
    organization = relationship("Organization", back_populates="incidents")
    team = relationship("Team", back_populates="incidents")
    creator = relationship(
        "User", foreign_keys=[created_by], back_populates="created_incidents"
    )
    assignee = relationship(
        "User", foreign_keys=[assigned_to], back_populates="assigned_incidents"
    )

    def __repr__(self) -> str:
        return f"<Incident(id={self.id}, title='{self.title}', status='{self.status}')>"
