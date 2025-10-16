"""Logging setup and configuration."""

import logging
import logging.handlers
import sys
from typing import Any, Dict

import structlog
from structlog.stdlib import LoggerFactory

from .config import LoggingConfig


def configure_logging(config: LoggingConfig | None = None) -> None:
    """Configure structured logging for the application."""
    if config is None:
        config = LoggingConfig()
    
    # Configure structlog
    processors = []
    
    # Add timestamp
    if config.include_timestamps:
        processors.append(structlog.processors.TimeStamper(fmt="ISO"))
    
    # Add caller info
    if config.include_caller:
        processors.append(structlog.processors.CallsiteParameterAdder(
            parameters=[structlog.processors.CallsiteParameter.FILENAME,
                       structlog.processors.CallsiteParameter.FUNC_NAME,
                       structlog.processors.CallsiteParameter.LINENO]
        ))
    
    # Add process info
    if config.include_process:
        processors.append(structlog.processors.add_log_level)
        processors.append(structlog.processors.StackInfoRenderer())
    
    # Add exception info
    processors.append(structlog.processors.format_exc_info)
    
    # Choose output format
    if config.format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, config.level.upper()),
    )
    
    # Set up file logging if configured
    if config.log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            config.log_file,
            maxBytes=config.max_file_size,
            backupCount=config.backup_count,
        )
        file_handler.setLevel(getattr(logging, config.level.upper()))
        logging.getLogger().addHandler(file_handler)
    
    # Configure specific loggers
    _configure_database_logging(config)
    _configure_security_logging(config)
    _configure_performance_logging(config)


def _configure_database_logging(config: LoggingConfig) -> None:
    """Configure database-specific logging."""
    db_logger = logging.getLogger("sqlalchemy.engine")
    if config.level.upper() == "DEBUG":
        db_logger.setLevel(logging.INFO)
    else:
        db_logger.setLevel(logging.WARNING)


def _configure_security_logging(config: LoggingConfig) -> None:
    """Configure security-specific logging."""
    if config.log_security:
        security_logger = logging.getLogger("security")
        security_logger.setLevel(logging.INFO)


def _configure_performance_logging(config: LoggingConfig) -> None:
    """Configure performance-specific logging."""
    if config.log_performance:
        perf_logger = logging.getLogger("performance")
        perf_logger.setLevel(logging.INFO)


def get_logger(name: str | None = None) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


class AuditLogger:
    """Audit logging for security and compliance."""
    
    def __init__(self, config: LoggingConfig):
        self.config = config
        self.logger = get_logger("audit")
    
    def log_event(
        self,
        event_type: str,
        user_id: str | None = None,
        org_id: str | None = None,
        team_id: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        details: Dict[str, Any] | None = None,
        success: bool = True,
    ) -> None:
        """Log an audit event."""
        if not self.config.log_audit or event_type not in self.config.audit_events:
            return
        
        self.logger.info(
            "audit_event",
            event_type=event_type,
            user_id=user_id,
            org_id=org_id,
            team_id=team_id,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            success=success,
        )


class PerformanceLogger:
    """Performance logging for monitoring and optimization."""
    
    def __init__(self, config: LoggingConfig):
        self.config = config
        self.logger = get_logger("performance")
    
    def log_operation(
        self,
        operation: str,
        duration: float,
        org_id: str | None = None,
        team_id: str | None = None,
        details: Dict[str, Any] | None = None,
    ) -> None:
        """Log a performance operation."""
        if not self.config.log_performance:
            return
        
        is_slow = duration > self.config.slow_query_threshold
        
        self.logger.info(
            "performance_operation",
            operation=operation,
            duration=duration,
            org_id=org_id,
            team_id=team_id,
            details=details or {},
            is_slow=is_slow,
        )
    
    def log_database_query(
        self,
        query: str,
        duration: float,
        org_id: str | None = None,
        team_id: str | None = None,
    ) -> None:
        """Log a database query performance."""
        if not self.config.log_performance:
            return
        
        is_slow = duration > self.config.slow_query_threshold
        
        self.logger.info(
            "database_query",
            query=query[:200] + "..." if len(query) > 200 else query,
            duration=duration,
            org_id=org_id,
            team_id=team_id,
            is_slow=is_slow,
        )
