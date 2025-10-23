"""User model."""

import enum

from sqlalchemy import JSON, Boolean, Column, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import (
    AuditMixin,
    BaseModel,
    OrgScopedMixin,
    SoftDeleteMixin,
    TimestampMixin,
)


class UserRole(str, enum.Enum):
    """User roles within a team."""

    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class User(BaseModel, TimestampMixin, OrgScopedMixin, AuditMixin, SoftDeleteMixin):
    """User model for team members."""

    __tablename__ = "users"

    # Basic info
    email: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    username: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, index=True
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str] = mapped_column(String(500), nullable=True)

    # Auth
    password_hash: Mapped[str] = mapped_column(
        String(255), nullable=True
    )  # For password auth
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # OIDC/SSO
    oidc_subject: Mapped[str] = mapped_column(
        String(255), nullable=True, unique=True, index=True
    )
    oidc_provider: Mapped[str] = mapped_column(String(100), nullable=True)

    # Team membership
    team_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), default=UserRole.MEMBER, nullable=False
    )

    # Settings
    preferences: Mapped[dict] = mapped_column(JSON, nullable=True, default=dict)

    # Foreign keys
    organization_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    organization = relationship("Organization", back_populates="users")
    team = relationship("Team", back_populates="users")
    created_incidents = relationship(
        "Incident", foreign_keys="Incident.created_by", back_populates="creator"
    )
    assigned_incidents = relationship(
        "Incident", foreign_keys="Incident.assigned_to", back_populates="assignee"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', team_id={self.team_id})>"
