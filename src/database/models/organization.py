"""Organization model."""

from sqlalchemy import Column, String, Text, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import BaseModel, TimestampMixin


class Organization(BaseModel, TimestampMixin):
    """Organization model for multi-tenancy."""
    
    __tablename__ = "organizations"
    
    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Hierarchical configuration storage
    config_yaml: Mapped[str] = mapped_column(Text, nullable=True, comment="YAML configuration content")
    config_json: Mapped[dict] = mapped_column(JSON, nullable=True, comment="Parsed JSON configuration")
    config_version: Mapped[str] = mapped_column(String(50), nullable=True, comment="Configuration version")
    
    # Legacy settings (for backward compatibility)
    settings: Mapped[dict] = mapped_column(JSON, nullable=True, default=dict)
    
    # Billing/limits
    max_teams: Mapped[int] = mapped_column(default=10, nullable=False)
    max_users_per_team: Mapped[int] = mapped_column(default=50, nullable=False)
    
    # Relationships
    teams = relationship("Team", back_populates="organization", cascade="all, delete-orphan")
    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    incidents = relationship("Incident", back_populates="organization", cascade="all, delete-orphan")
    agent_configs = relationship("AgentConfig", back_populates="organization", cascade="all, delete-orphan")
    stats = relationship("Stats", back_populates="organization", cascade="all, delete-orphan")
    configs = relationship("Config", back_populates="organization", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Organization(id={self.id}, name='{self.name}', slug='{self.slug}')>"