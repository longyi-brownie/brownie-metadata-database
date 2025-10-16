"""Team model."""

from sqlalchemy import Column, String, Text, Boolean, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import BaseModel, TimestampMixin, OrgScopedMixin, AuditMixin


class Team(BaseModel, TimestampMixin, OrgScopedMixin, AuditMixin):
    """Team model for organization teams."""
    
    __tablename__ = "teams"
    
    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Hierarchical configuration storage
    config_yaml: Mapped[str] = mapped_column(Text, nullable=True, comment="YAML configuration content")
    config_json: Mapped[dict] = mapped_column(JSON, nullable=True, comment="Parsed JSON configuration")
    config_version: Mapped[str] = mapped_column(String(50), nullable=True, comment="Configuration version")
    
    # Legacy settings (for backward compatibility)
    settings: Mapped[dict] = mapped_column(JSON, nullable=True, default=dict)
    
    # Permissions/RBAC
    permissions: Mapped[dict] = mapped_column(JSON, nullable=True, default=dict)
    
    # Foreign keys
    organization_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Relationships
    organization = relationship("Organization", back_populates="teams")
    users = relationship("User", back_populates="team", cascade="all, delete-orphan")
    incidents = relationship("Incident", back_populates="team", cascade="all, delete-orphan")
    agent_configs = relationship("AgentConfig", back_populates="team", cascade="all, delete-orphan")
    stats = relationship("Stats", back_populates="team", cascade="all, delete-orphan")
    configs = relationship("Config", back_populates="team", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Team(id={self.id}, name='{self.name}', org_id={self.org_id})>"