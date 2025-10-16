"""Metrics setup and configuration."""

from .collector import MetricsCollector
from .config import MetricsConfig


def configure_metrics(config: MetricsConfig | None = None) -> MetricsCollector:
    """Configure metrics collection."""
    if config is None:
        config = MetricsConfig()
    
    collector = MetricsCollector(config)
    return collector
