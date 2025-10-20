"""Test metrics sidecar functionality."""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock

from metrics_sidecar.__main__ import MetricsCollector


class TestMetricsCollector:
    """Test MetricsCollector class."""

    def test_metrics_collector_initialization(self):
        """Test creating a metrics collector."""
        collector = MetricsCollector()

        assert collector.db_config is not None
        assert collector.redis_config is not None
        assert collector.metrics_port == 9091  # Default port

    def test_metrics_collector_with_env_vars(self):
        """Test metrics collector with environment variables."""
        env_vars = {
            "DB_HOST": "test-host",
            "DB_PORT": "5433",
            "DB_NAME": "test_db",
            "DB_USER": "test_user",
            "DB_SSL_MODE": "disable",
            "CERT_DIR": "/test/certs",
            "REDIS_HOST": "test-redis",
            "REDIS_PORT": "6380",
            "METRICS_PORT": "9092",
        }

        with patch.dict(os.environ, env_vars):
            collector = MetricsCollector()

            assert collector.db_config["host"] == "test-host"
            assert collector.db_config["port"] == 5433
            assert collector.db_config["dbname"] == "test_db"
            assert collector.db_config["user"] == "test_user"
            assert collector.db_config["sslmode"] == "disable"
            assert collector.redis_config["host"] == "test-redis"
            assert collector.redis_config["port"] == 6380
            assert collector.metrics_port == 9092

    @patch("metrics_sidecar.__main__.psycopg.connect")
    def test_collect_database_metrics_success(self, mock_connect):
        """Test successful database metrics collection."""
        # Mock database connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        # Mock query results
        mock_cursor.fetchone.side_effect = [
            (1024 * 1024,),  # Database size
            (5,),  # Organizations count
            (10,),  # Teams count
            (25,),  # Users count
            (3,),  # Incidents count
            (1,),  # Active incidents count
            (2,),  # Agent configs count
        ]

        # Mock table sizes query
        mock_cursor.fetchall.return_value = [
            ("public", "organizations", 1024),
            ("public", "teams", 2048),
        ]

        collector = MetricsCollector()
        collector.collect_database_metrics()

        # Verify database connection was attempted
        mock_connect.assert_called_once()

        # Verify queries were executed
        assert mock_cursor.execute.call_count >= 6  # Multiple queries executed

    @patch("metrics_sidecar.__main__.psycopg.connect")
    def test_collect_database_metrics_failure(self, mock_connect):
        """Test database metrics collection failure handling."""
        mock_connect.side_effect = Exception("Connection failed")

        collector = MetricsCollector()

        # Should not raise exception
        collector.collect_database_metrics()

    @patch("metrics_sidecar.__main__.redis.Redis")
    def test_collect_redis_metrics_success(self, mock_redis_class):
        """Test successful Redis metrics collection."""
        # Mock Redis connection
        mock_redis = MagicMock()
        mock_redis_class.return_value = mock_redis

        # Mock Redis info response
        mock_redis.info.return_value = {
            "connected_clients": 5,
            "used_memory": 1024 * 1024,
            "keyspace_hits": 100,
            "keyspace_misses": 20,
        }

        collector = MetricsCollector()
        collector.collect_redis_metrics()

        # Verify Redis connection was attempted
        mock_redis_class.assert_called_once()
        mock_redis.info.assert_called_once()

    @patch("metrics_sidecar.__main__.redis.Redis")
    def test_collect_redis_metrics_failure(self, mock_redis_class):
        """Test Redis metrics collection failure handling."""
        mock_redis_class.side_effect = Exception("Redis connection failed")

        collector = MetricsCollector()

        # Should not raise exception
        collector.collect_redis_metrics()

    @patch("metrics_sidecar.__main__.start_http_server")
    @patch("metrics_sidecar.__main__.time.sleep")
    def test_run_method(self, mock_sleep, mock_start_server):
        """Test the run method starts server and collects metrics."""
        # Mock sleep to prevent infinite loop
        mock_sleep.side_effect = KeyboardInterrupt()

        collector = MetricsCollector()

        # Should raise KeyboardInterrupt when sleep is interrupted
        with pytest.raises(KeyboardInterrupt):
            collector.run()

        # Verify HTTP server was started
        mock_start_server.assert_called_once_with(9091)
