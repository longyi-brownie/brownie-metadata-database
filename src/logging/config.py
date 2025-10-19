"""Logging configuration management."""

import os
import logging
import structlog
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field


class LoggingConfig(BaseSettings):
    """Centralized logging configuration."""
    
    level: str = Field(default="INFO", description="Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
    format: str = Field(default="json", description="Log format (json, text)")
    include_timestamps: bool = Field(default=True, description="Include timestamps in logs")
    include_logger_name: bool = Field(default=True, description="Include logger name in logs")
    include_log_level: bool = Field(default=True, description="Include log level in logs")
    slow_query_threshold: float = Field(default=1.0, description="Slow query threshold in seconds")
    audit_events: List[str] = Field(default=["create", "update", "delete"], description="Events to audit")
    log_performance: bool = Field(default=True, description="Enable performance logging")
    
    class Config:
        env_prefix = "LOG_"
    
    def get_log_level(self) -> int:
        """Get numeric log level."""
        return getattr(logging, self.level.upper(), logging.INFO)
    
    def configure_structlog(self) -> None:
        """Configure structlog with current settings."""
        processors = [
            structlog.stdlib.filter_by_level,
        ]
        
        if self.include_logger_name:
            processors.append(structlog.stdlib.add_logger_name)
        
        if self.include_log_level:
            processors.append(structlog.stdlib.add_log_level)
        
        processors.extend([
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
        ])
        
        if self.include_timestamps:
            processors.insert(-1, structlog.processors.TimeStamper(fmt="iso"))
        
        if self.format == "json":
            processors.append(structlog.processors.JSONRenderer())
        else:
            processors.append(structlog.dev.ConsoleRenderer())
        
        structlog.configure(
            processors=processors,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )


def configure_logging(config: Optional[LoggingConfig] = None) -> LoggingConfig:
    """Configure logging for the application."""
    if config is None:
        config = LoggingConfig()
    
    # Configure structlog
    config.configure_structlog()
    
    # Configure standard logging
    logging.basicConfig(
        level=config.get_log_level(),
        format="%(message)s",
        handlers=[logging.StreamHandler()]
    )
    
    return config


def get_logger(name: str = None) -> structlog.BoundLogger:
    """Get a configured logger."""
    return structlog.get_logger(name)
