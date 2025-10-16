"""Prometheus metrics collector for database operations."""

import time
from typing import Any, Dict, Optional
from contextlib import contextmanager

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Summary,
    CollectorRegistry,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
from prometheus_client.core import REGISTRY

from .config import MetricsConfig


class MetricsCollector:
    """Prometheus metrics collector for the metadata database."""
    
    def __init__(self, config: MetricsConfig):
        self.config = config
        self.registry = CollectorRegistry()
        
        # Database metrics
        self._init_database_metrics()
        
        # Business metrics
        self._init_business_metrics()
        
        # Performance metrics
        self._init_performance_metrics()
    
    def _init_database_metrics(self) -> None:
        """Initialize database-related metrics."""
        if not self.config.track_database_queries:
            return
        
        self.db_queries_total = Counter(
            'db_queries_total',
            'Total number of database queries',
            ['operation', 'table', 'org_id'],
            registry=self.registry
        )
        
        self.db_query_duration = Histogram(
            'db_query_duration_seconds',
            'Database query duration in seconds',
            ['operation', 'table', 'org_id'],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
            registry=self.registry
        )
        
        self.db_connections_active = Gauge(
            'db_connections_active',
            'Number of active database connections',
            ['org_id'],
            registry=self.registry
        )
        
        self.db_transactions_total = Counter(
            'db_transactions_total',
            'Total number of database transactions',
            ['operation', 'org_id'],
            registry=self.registry
        )
        
        self.db_errors_total = Counter(
            'db_errors_total',
            'Total number of database errors',
            ['error_type', 'operation', 'org_id'],
            registry=self.registry
        )
    
    def _init_business_metrics(self) -> None:
        """Initialize business-related metrics."""
        if self.config.track_incidents:
            self.incidents_total = Counter(
                'incidents_total',
                'Total number of incidents',
                ['status', 'priority', 'org_id', 'team_id'],
                registry=self.registry
            )
            
            self.incidents_active = Gauge(
                'incidents_active',
                'Number of active incidents',
                ['org_id', 'team_id'],
                registry=self.registry
            )
            
            self.incident_resolution_time = Histogram(
                'incident_resolution_time_minutes',
                'Incident resolution time in minutes',
                ['priority', 'org_id', 'team_id'],
                buckets=[1, 5, 15, 30, 60, 120, 240, 480, 960, 1440, 2880, 5760],
                registry=self.registry
            )
        
        if self.config.track_users:
            self.users_total = Gauge(
                'users_total',
                'Total number of users',
                ['org_id', 'team_id', 'role'],
                registry=self.registry
            )
            
            self.users_active = Gauge(
                'users_active',
                'Number of active users',
                ['org_id', 'team_id'],
                registry=self.registry
            )
        
        if self.config.track_teams:
            self.teams_total = Gauge(
                'teams_total',
                'Total number of teams',
                ['org_id'],
                registry=self.registry
            )
        
        if self.config.track_organizations:
            self.organizations_total = Gauge(
                'organizations_total',
                'Total number of organizations',
                registry=self.registry
            )
    
    def _init_performance_metrics(self) -> None:
        """Initialize performance-related metrics."""
        if self.config.track_response_times:
            self.request_duration = Histogram(
                'request_duration_seconds',
                'Request duration in seconds',
                ['method', 'endpoint', 'status_code', 'org_id'],
                buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
                registry=self.registry
            )
        
        if self.config.track_throughput:
            self.requests_total = Counter(
                'requests_total',
                'Total number of requests',
                ['method', 'endpoint', 'status_code', 'org_id'],
                registry=self.registry
            )
        
        if self.config.track_error_rates:
            self.errors_total = Counter(
                'errors_total',
                'Total number of errors',
                ['error_type', 'endpoint', 'org_id'],
                registry=self.registry
            )
    
    def record_database_query(
        self,
        operation: str,
        table: str,
        org_id: str | None = None,
        duration: float | None = None,
    ) -> None:
        """Record a database query metric."""
        if not self.config.track_database_queries:
            return
        
        labels = {
            'operation': operation,
            'table': table,
            'org_id': org_id or 'unknown'
        }
        
        self.db_queries_total.labels(**labels).inc()
        
        if duration is not None:
            self.db_query_duration.labels(**labels).observe(duration)
    
    def record_database_error(
        self,
        error_type: str,
        operation: str,
        org_id: str | None = None,
    ) -> None:
        """Record a database error metric."""
        if not self.config.track_database_queries:
            return
        
        labels = {
            'error_type': error_type,
            'operation': operation,
            'org_id': org_id or 'unknown'
        }
        
        self.db_errors_total.labels(**labels).inc()
    
    def record_incident_created(
        self,
        status: str,
        priority: str,
        org_id: str | None = None,
        team_id: str | None = None,
    ) -> None:
        """Record an incident creation metric."""
        if not self.config.track_incidents:
            return
        
        labels = {
            'status': status,
            'priority': priority,
            'org_id': org_id or 'unknown',
            'team_id': team_id or 'unknown'
        }
        
        self.incidents_total.labels(**labels).inc()
    
    def record_incident_resolved(
        self,
        priority: str,
        resolution_time_minutes: float,
        org_id: str | None = None,
        team_id: str | None = None,
    ) -> None:
        """Record an incident resolution metric."""
        if not self.config.track_incidents:
            return
        
        labels = {
            'priority': priority,
            'org_id': org_id or 'unknown',
            'team_id': team_id or 'unknown'
        }
        
        self.incident_resolution_time.labels(**labels).observe(resolution_time_minutes)
    
    def update_user_count(
        self,
        count: int,
        org_id: str | None = None,
        team_id: str | None = None,
        role: str | None = None,
    ) -> None:
        """Update user count metric."""
        if not self.config.track_users:
            return
        
        labels = {
            'org_id': org_id or 'unknown',
            'team_id': team_id or 'unknown',
            'role': role or 'unknown'
        }
        
        self.users_total.labels(**labels).set(count)
    
    def update_team_count(
        self,
        count: int,
        org_id: str | None = None,
    ) -> None:
        """Update team count metric."""
        if not self.config.track_teams:
            return
        
        labels = {
            'org_id': org_id or 'unknown'
        }
        
        self.teams_total.labels(**labels).set(count)
    
    def update_organization_count(self, count: int) -> None:
        """Update organization count metric."""
        if not self.config.track_organizations:
            return
        
        self.organizations_total.set(count)
    
    @contextmanager
    def time_database_operation(
        self,
        operation: str,
        table: str,
        org_id: str | None = None,
    ):
        """Context manager to time database operations."""
        start_time = time.time()
        try:
            yield
        except Exception as e:
            self.record_database_error(
                error_type=type(e).__name__,
                operation=operation,
                org_id=org_id
            )
            raise
        finally:
            duration = time.time() - start_time
            self.record_database_query(
                operation=operation,
                table=table,
                org_id=org_id,
                duration=duration
            )
    
    def get_metrics(self) -> str:
        """Get metrics in Prometheus format."""
        return generate_latest(self.registry)
    
    def get_content_type(self) -> str:
        """Get the content type for metrics."""
        return CONTENT_TYPE_LATEST


# Global metrics collector instance
_metrics_collector: MetricsCollector | None = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        from .config import MetricsConfig
        config = MetricsConfig()
        _metrics_collector = MetricsCollector(config)
    return _metrics_collector
