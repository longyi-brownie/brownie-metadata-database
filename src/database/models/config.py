"""Configuration model for hierarchical configs."""

import enum

from sqlalchemy import JSON, Boolean, Column, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import AuditMixin, BaseModel, OrgScopedMixin, TimestampMixin, VersionMixin


class ConfigType(str, enum.Enum):
    """Configuration types."""

    ORGANIZATION = "organization"
    TEAM = "team"
    ALERT = "alert"
    AGENT = "agent"
    GLOBAL = "global"


class ConfigStatus(str, enum.Enum):
    """Configuration status."""

    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class Config(BaseModel, TimestampMixin, OrgScopedMixin, AuditMixin, VersionMixin):
    """Configuration model for hierarchical configs."""

    __tablename__ = "configs"

    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    # Configuration type and status
    config_type: Mapped[ConfigType] = mapped_column(Enum(ConfigType), nullable=False)
    status: Mapped[ConfigStatus] = mapped_column(
        Enum(ConfigStatus), default=ConfigStatus.DRAFT, nullable=False
    )

    # Pattern matching (for hierarchical configs)
    name_pattern: Mapped[str] = mapped_column(
        String(500), nullable=True, comment="Regex pattern for name matching"
    )
    severity_pattern: Mapped[str] = mapped_column(
        String(500), nullable=True, comment="Regex pattern for severity matching"
    )
    team_pattern: Mapped[str] = mapped_column(
        String(500), nullable=True, comment="Regex pattern for team matching"
    )

    # Configuration content
    config_yaml: Mapped[str] = mapped_column(
        Text, nullable=True, comment="YAML configuration content"
    )
    config_json: Mapped[dict] = mapped_column(
        JSON, nullable=True, comment="Parsed JSON configuration"
    )
    config_version: Mapped[str] = mapped_column(
        String(50), nullable=True, comment="Configuration version"
    )

    # Priority for resolution (higher number = higher priority)
    priority: Mapped[int] = mapped_column(
        default=0, nullable=False, comment="Resolution priority"
    )

    # Scope
    is_global: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="Apply globally"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Metadata
    tags: Mapped[list[str]] = mapped_column(JSON, nullable=True, default=list)
    config_metadata: Mapped[dict] = mapped_column(JSON, nullable=True, default=dict)

    # Foreign keys
    team_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Team this config applies to (if team-specific)",
    )
    organization_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    organization = relationship("Organization", back_populates="configs")
    team = relationship("Team", back_populates="configs")

    def __repr__(self) -> str:
        return f"<Config(id={self.id}, name='{self.name}', type='{self.config_type}', status='{self.status}')>"
