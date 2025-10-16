"""Metrics configuration settings."""

from pydantic import Field
from pydantic_settings import BaseSettings


class MetricsConfig(BaseSettings):
    """Metrics configuration settings."""
    
    # Enable metrics collection
    enabled: bool = Field(default=True, description="Enable metrics collection")
    
    # Metrics endpoint
    endpoint: str = Field(default="/metrics", description="Metrics endpoint path")
    port: int = Field(default=8001, description="Metrics server port")
    
    # Database metrics
    track_database_queries: bool = Field(default=True, description="Track database query metrics")
    track_database_connections: bool = Field(default=True, description="Track database connection metrics")
    track_database_transactions: bool = Field(default=True, description="Track database transaction metrics")
    
    # Business metrics
    track_incidents: bool = Field(default=True, description="Track incident metrics")
    track_users: bool = Field(default=True, description="Track user metrics")
    track_teams: bool = Field(default=True, description="Track team metrics")
    track_organizations: bool = Field(default=True, description="Track organization metrics")
    
    # Performance metrics
    track_response_times: bool = Field(default=True, description="Track response time metrics")
    track_throughput: bool = Field(default=True, description="Track throughput metrics")
    track_error_rates: bool = Field(default=True, description="Track error rate metrics")
    
    # Custom metrics
    track_custom_metrics: bool = Field(default=True, description="Track custom business metrics")
    
    # Metrics retention
    retention_days: int = Field(default=30, description="Metrics retention period in days")
    
    # Labels
    default_labels: dict[str, str] = Field(
        default_factory=dict,
        description="Default labels for all metrics"
    )
    
    class Config:
        env_prefix = "METRICS_"
        env_file = ".env"
