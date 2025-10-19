"""Test logging configuration."""

import pytest
import logging
from unittest.mock import patch

from src.logging.config import LoggingConfig, configure_logging
from src.logging.audit import AuditLogger
from src.logging.performance import PerformanceLogger


class TestLoggingConfig:
    """Test LoggingConfig class."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = LoggingConfig()
        
        assert config.level == "INFO"
        assert config.format == "json"
        assert config.include_timestamps is True
        assert config.include_caller is True
        assert config.include_process is True
        assert config.structured is True
        assert config.log_file is None
        assert config.log_performance is True
        assert config.log_security is True
        assert config.log_audit is True


class TestAuditLogger:
    """Test AuditLogger class."""
    
    def test_audit_logger_creation(self):
        """Test creating an audit logger."""
        config = LoggingConfig()
        logger = AuditLogger(config)
        
        assert logger.config == config
        assert logger.logger is not None
    
    @patch('logging.setup.get_logger')
    def test_log_event(self, mock_get_logger):
        """Test logging an audit event."""
        config = LoggingConfig()
        logger = AuditLogger(config)
        
        mock_logger = mock_get_logger.return_value
        
        logger.log_event(
            event_type="create",
            user_id="user123",
            org_id="org456",
            resource_type="incident",
            resource_id="inc789",
            success=True
        )
        
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert call_args[1]["event_type"] == "create"
        assert call_args[1]["user_id"] == "user123"
        assert call_args[1]["org_id"] == "org456"
        assert call_args[1]["success"] is True
    
    def test_log_event_filtered(self):
        """Test that filtered events are not logged."""
        config = LoggingConfig(audit_events=["create", "update"])
        logger = AuditLogger(config)
        
        with patch.object(logger.logger, 'info') as mock_info:
            logger.log_event(event_type="delete")  # Not in audit_events
            mock_info.assert_not_called()


class TestPerformanceLogger:
    """Test PerformanceLogger class."""
    
    def test_performance_logger_creation(self):
        """Test creating a performance logger."""
        config = LoggingConfig()
        logger = PerformanceLogger(config)
        
        assert logger.config == config
        assert logger.logger is not None
    
    @patch('logging.setup.get_logger')
    def test_log_operation(self, mock_get_logger):
        """Test logging a performance operation."""
        config = LoggingConfig()
        logger = PerformanceLogger(config)
        
        mock_logger = mock_get_logger.return_value
        
        logger.log_operation(
            operation="database_query",
            duration=0.5,
            org_id="org123",
            team_id="team456"
        )
        
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert call_args[1]["operation"] == "database_query"
        assert call_args[1]["duration"] == 0.5
        assert call_args[1]["org_id"] == "org123"
        assert call_args[1]["is_slow"] is False  # 0.5 < 1.0 threshold
    
    @patch('logging.setup.get_logger')
    def test_log_slow_operation(self, mock_get_logger):
        """Test logging a slow operation."""
        config = LoggingConfig(slow_query_threshold=0.1)
        logger = PerformanceLogger(config)
        
        mock_logger = mock_get_logger.return_value
        
        logger.log_operation(
            operation="database_query",
            duration=0.5,  # > 0.1 threshold
            org_id="org123"
        )
        
        call_args = mock_logger.info.call_args
        assert call_args[1]["is_slow"] is True
    
    def test_log_operation_disabled(self):
        """Test that operations are not logged when disabled."""
        config = LoggingConfig(log_performance=False)
        logger = PerformanceLogger(config)
        
        with patch.object(logger.logger, 'info') as mock_info:
            logger.log_operation("test", 0.5)
            mock_info.assert_not_called()
