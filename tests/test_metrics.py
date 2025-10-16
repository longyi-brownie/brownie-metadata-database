"""Test metrics collection."""

import pytest
from unittest.mock import patch, MagicMock

from metrics.config import MetricsConfig
from metrics.collector import MetricsCollector


class TestMetricsConfig:
    """Test MetricsConfig class."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = MetricsConfig()
        
        assert config.enabled is True
        assert config.endpoint == "/metrics"
        assert config.port == 8001
        assert config.track_database_queries is True
        assert config.track_incidents is True
        assert config.track_users is True
        assert config.track_teams is True
        assert config.track_organizations is True
        assert config.track_response_times is True
        assert config.track_throughput is True
        assert config.track_error_rates is True


class TestMetricsCollector:
    """Test MetricsCollector class."""
    
    def test_metrics_collector_creation(self):
        """Test creating a metrics collector."""
        config = MetricsConfig()
        collector = MetricsCollector(config)
        
        assert collector.config == config
        assert collector.registry is not None
    
    def test_record_database_query(self):
        """Test recording database query metrics."""
        config = MetricsConfig()
        collector = MetricsCollector(config)
        
        # Test recording a query
        collector.record_database_query(
            operation="SELECT",
            table="users",
            org_id="org123",
            duration=0.1
        )
        
        # Verify metrics were recorded
        metrics = collector.get_metrics()
        assert b"db_queries_total" in metrics
        assert b"db_query_duration_seconds" in metrics
    
    def test_record_database_error(self):
        """Test recording database error metrics."""
        config = MetricsConfig()
        collector = MetricsCollector(config)
        
        collector.record_database_error(
            error_type="IntegrityError",
            operation="INSERT",
            org_id="org123"
        )
        
        metrics = collector.get_metrics()
        assert b"db_errors_total" in metrics
    
    def test_record_incident_created(self):
        """Test recording incident creation metrics."""
        config = MetricsConfig()
        collector = MetricsCollector(config)
        
        collector.record_incident_created(
            status="OPEN",
            priority="HIGH",
            org_id="org123",
            team_id="team456"
        )
        
        metrics = collector.get_metrics()
        assert b"incidents_total" in metrics
    
    def test_record_incident_resolved(self):
        """Test recording incident resolution metrics."""
        config = MetricsConfig()
        collector = MetricsCollector(config)
        
        collector.record_incident_resolved(
            priority="HIGH",
            resolution_time_minutes=30.0,
            org_id="org123",
            team_id="team456"
        )
        
        metrics = collector.get_metrics()
        assert b"incident_resolution_time_minutes" in metrics
    
    def test_update_user_count(self):
        """Test updating user count metrics."""
        config = MetricsConfig()
        collector = MetricsCollector(config)
        
        collector.update_user_count(
            count=100,
            org_id="org123",
            team_id="team456",
            role="MEMBER"
        )
        
        metrics = collector.get_metrics()
        assert b"users_total" in metrics
    
    def test_update_team_count(self):
        """Test updating team count metrics."""
        config = MetricsConfig()
        collector = MetricsCollector(config)
        
        collector.update_team_count(
            count=10,
            org_id="org123"
        )
        
        metrics = collector.get_metrics()
        assert b"teams_total" in metrics
    
    def test_update_organization_count(self):
        """Test updating organization count metrics."""
        config = MetricsConfig()
        collector = MetricsCollector(config)
        
        collector.update_organization_count(count=5)
        
        metrics = collector.get_metrics()
        assert b"organizations_total" in metrics
    
    def test_time_database_operation_success(self):
        """Test timing a successful database operation."""
        config = MetricsConfig()
        collector = MetricsCollector(config)
        
        with collector.time_database_operation("SELECT", "users", "org123"):
            pass  # Simulate successful operation
        
        metrics = collector.get_metrics()
        assert b"db_queries_total" in metrics
        assert b"db_query_duration_seconds" in metrics
    
    def test_time_database_operation_error(self):
        """Test timing a database operation that raises an error."""
        config = MetricsConfig()
        collector = MetricsCollector(config)
        
        with pytest.raises(ValueError):
            with collector.time_database_operation("SELECT", "users", "org123"):
                raise ValueError("Test error")
        
        metrics = collector.get_metrics()
        assert b"db_errors_total" in metrics
    
    def test_disabled_metrics(self):
        """Test that metrics are not recorded when disabled."""
        config = MetricsConfig(
            track_database_queries=False,
            track_incidents=False,
            track_users=False,
            track_teams=False,
            track_organizations=False
        )
        collector = MetricsCollector(config)
        
        # Try to record various metrics
        collector.record_database_query("SELECT", "users", "org123")
        collector.record_incident_created("OPEN", "HIGH", "org123")
        collector.update_user_count(100, "org123")
        collector.update_team_count(10, "org123")
        collector.update_organization_count(5)
        
        # Metrics should be empty or minimal
        metrics = collector.get_metrics()
        assert b"db_queries_total" not in metrics
        assert b"incidents_total" not in metrics
        assert b"users_total" not in metrics
        assert b"teams_total" not in metrics
        assert b"organizations_total" not in metrics
