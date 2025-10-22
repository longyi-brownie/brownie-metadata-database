"""Stats model for metrics and analytics."""

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import BaseModel, OrgScopedMixin, TimestampMixin


class Stats(BaseModel, TimestampMixin, OrgScopedMixin):
    """Stats model for metrics and analytics."""

    __tablename__ = "stats"

    # Basic info
    metric_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    metric_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # counter, gauge, histogram, etc.

    # Values
    value: Mapped[float] = mapped_column(Float, nullable=False)
    count: Mapped[int] = mapped_column(Integer, nullable=True)

    # Time series data
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    time_window: Mapped[str] = mapped_column(
        String(50), nullable=True
    )  # 1m, 5m, 1h, 1d, etc.

    # Dimensions/labels
    labels: Mapped[dict] = mapped_column(JSON, nullable=True, default=dict)

    # Metadata
    description: Mapped[str] = mapped_column(Text, nullable=True)
    unit: Mapped[str] = mapped_column(String(50), nullable=True)

    # Foreign keys
    team_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    organization_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    organization = relationship("Organization", back_populates="stats")
    team = relationship("Team", back_populates="stats")

    def __repr__(self) -> str:
        return f"<Stats(id={self.id}, metric='{self.metric_name}', value={self.value})>"
