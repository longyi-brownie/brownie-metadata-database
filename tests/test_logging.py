"""Test logging configuration."""

import logging
from unittest.mock import patch

import pytest

from src.logging.audit import AuditLogger
from src.logging.config import LoggingConfig, configure_logging, get_logger
from src.logging.performance import PerformanceLogger


class TestLoggingConfig:
    """Test LoggingConfig class."""

    def test_default_values(self):
        """Test default configuration values."""
        config = LoggingConfig()

        assert config.level == "INFO"
        assert config.format == "json"
        assert config.include_timestamps is True
        assert config.include_logger_name is True
        assert config.include_log_level is True
        assert config.audit_events == ["create", "update", "delete"]
        assert config.log_performance is True
        assert config.slow_query_threshold == 1.0

    def test_get_log_level(self):
        """Test log level conversion."""
        config = LoggingConfig(level="DEBUG")
        assert config.get_log_level() == logging.DEBUG

        config = LoggingConfig(level="ERROR")
        assert config.get_log_level() == logging.ERROR

    def test_configure_logging(self):
        """Test logging configuration."""
        config = configure_logging()
        assert isinstance(config, LoggingConfig)

    def test_get_logger(self):
        """Test getting a logger."""
        logger = get_logger("test")
        assert logger is not None


class TestAuditLogger:
    """Test AuditLogger class."""

    def test_audit_logger_creation(self):
        """Test creating an audit logger."""
        logger = AuditLogger()

        assert logger.logger is not None

    @patch("src.logging.audit.get_logger")
    def test_log_event(self, mock_get_logger):
        """Test logging an audit event."""
        logger = AuditLogger()

        mock_logger = mock_get_logger.return_value

        logger.log_event(
            event_type="create",
            resource_type="incident",
            resource_id="inc123",
            user_id="user123",
            org_id="org456",
        )

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert call_args[1]["event_type"] == "create"
        assert call_args[1]["resource_type"] == "incident"
        assert call_args[1]["resource_id"] == "inc123"
        assert call_args[1]["user_id"] == "user123"
        assert call_args[1]["org_id"] == "org456"

    def test_log_create(self):
        """Test logging a create event."""
        logger = AuditLogger()

        with patch.object(logger, "log_event") as mock_log_event:
            logger.log_create("incident", "inc123", user_id="user123")
            mock_log_event.assert_called_once_with(
                "create", "incident", "inc123", user_id="user123"
            )

    def test_log_update(self):
        """Test logging an update event."""
        logger = AuditLogger()

        with patch.object(logger, "log_event") as mock_log_event:
            changes = {"status": "resolved"}
            logger.log_update("incident", "inc123", changes, user_id="user123")
            mock_log_event.assert_called_once_with(
                "update", "incident", "inc123", changes=changes, user_id="user123"
            )

    def test_log_delete(self):
        """Test logging a delete event."""
        logger = AuditLogger()

        with patch.object(logger, "log_event") as mock_log_event:
            logger.log_delete("incident", "inc123", user_id="user123")
            mock_log_event.assert_called_once_with(
                "delete", "incident", "inc123", user_id="user123"
            )


class TestPerformanceLogger:
    """Test PerformanceLogger class."""

    def test_performance_logger_creation(self):
        """Test creating a performance logger."""
        logger = PerformanceLogger()

        assert logger.logger is not None

    @patch("src.logging.performance.get_logger")
    def test_log_operation_context_manager(self, mock_get_logger):
        """Test logging a performance operation using context manager."""
        logger = PerformanceLogger()

        mock_logger = mock_get_logger.return_value

        with logger.log_operation("test_operation"):
            pass

        # Should have called info or warning
        assert mock_logger.info.called or mock_logger.warning.called

    @patch("src.logging.performance.get_logger")
    def test_log_query(self, mock_get_logger):
        """Test logging a database query."""
        logger = PerformanceLogger()

        mock_logger = mock_get_logger.return_value

        logger.log_query("SELECT * FROM users", 0.5, rows_affected=10)

        mock_logger.debug.assert_called_once()
        call_args = mock_logger.debug.call_args
        assert call_args[1]["query"] == "SELECT * FROM users"
        assert call_args[1]["duration_seconds"] == 0.5
        assert call_args[1]["rows_affected"] == 10

    @patch("src.logging.performance.get_logger")
    def test_log_slow_query(self, mock_get_logger):
        """Test logging a slow query."""
        logger = PerformanceLogger()

        mock_logger = mock_get_logger.return_value

        logger.log_query(
            "SELECT * FROM users", 2.0, rows_affected=10
        )  # > 1.0 threshold

        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args
        assert call_args[1]["duration_seconds"] == 2.0

    @patch("src.logging.performance.get_logger")
    def test_log_api_request(self, mock_get_logger):
        """Test logging an API request."""
        logger = PerformanceLogger()

        mock_logger = mock_get_logger.return_value

        logger.log_api_request("GET", "/api/users", 200, 0.1, user_id="user123")

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert call_args[1]["method"] == "GET"
        assert call_args[1]["path"] == "/api/users"
        assert call_args[1]["status_code"] == 200
        assert call_args[1]["user_id"] == "user123"
