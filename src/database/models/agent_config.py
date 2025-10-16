"""Agent configuration model."""

from sqlalchemy import Column, String, Text, Boolean, JSON, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from ..base import BaseModel, TimestampMixin, OrgScopedMixin, AuditMixin, VersionMixin


class AgentType(str, enum.Enum):
    """Agent types."""
    INCIDENT_RESPONSE = "incident_response"
    MONITORING = "monitoring"
    ANALYSIS = "analysis"
    NOTIFICATION = "notification"
    CUSTOM = "custom"


class AgentConfig(BaseModel, TimestampMixin, OrgScopedMixin, AuditMixin, VersionMixin):
    """Agent configuration model for Brownie agents."""
    
    __tablename__ = "agent_configs"
    
    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Agent type and status
    agent_type: Mapped[AgentType] = mapped_column(Enum(AgentType), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Hierarchical configuration storage
    config_yaml: Mapped[str] = mapped_column(Text, nullable=True, comment="YAML configuration content")
    config_json: Mapped[dict] = mapped_column(JSON, nullable=True, comment="Parsed JSON configuration")
    config_version: Mapped[str] = mapped_column(String(50), nullable=True, comment="Configuration version")
    
    # Legacy config field (for backward compatibility)
    config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    
    # Execution settings
    execution_timeout_seconds: Mapped[int] = mapped_column(default=300, nullable=False)
    max_retries: Mapped[int] = mapped_column(default=3, nullable=False)
    retry_delay_seconds: Mapped[int] = mapped_column(default=60, nullable=False)
    
    # Triggers and conditions
    triggers: Mapped[dict] = mapped_column(JSON, nullable=True, default=dict)
    conditions: Mapped[dict] = mapped_column(JSON, nullable=True, default=dict)
    
    # Metadata
    tags: Mapped[list[str]] = mapped_column(JSON, nullable=True, default=list)
    config_metadata: Mapped[dict] = mapped_column(JSON, nullable=True, default=dict)
    
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
    
    # Relationships
    organization = relationship("Organization", back_populates="agent_configs")
    team = relationship("Team", back_populates="agent_configs")
    
    def __repr__(self) -> str:
        return f"<AgentConfig(id={self.id}, name='{self.name}', type='{self.agent_type}')>"