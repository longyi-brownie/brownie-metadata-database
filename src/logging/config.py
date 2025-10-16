"""Logging configuration settings."""

from pydantic import Field
from pydantic_settings import BaseSettings


class LoggingConfig(BaseSettings):
    """Logging configuration settings."""
    
    # Log level
    level: str = Field(default="INFO", description="Log level")
    
    # Output format
    format: str = Field(default="json", description="Log format: json or console")
    
    # Include timestamps
    include_timestamps: bool = Field(default=True, description="Include timestamps in logs")
    
    # Include caller info
    include_caller: bool = Field(default=True, description="Include caller information")
    
    # Include process info
    include_process: bool = Field(default=True, description="Include process information")
    
    # Structured logging
    structured: bool = Field(default=True, description="Use structured logging")
    
    # Log to file
    log_file: str | None = Field(default=None, description="Log file path")
    
    # Log rotation
    max_file_size: int = Field(default=10 * 1024 * 1024, description="Max log file size in bytes")
    backup_count: int = Field(default=5, description="Number of backup files to keep")
    
    # Performance logging
    log_performance: bool = Field(default=True, description="Log performance metrics")
    slow_query_threshold: float = Field(default=1.0, description="Slow query threshold in seconds")
    
    # Security logging
    log_security: bool = Field(default=True, description="Log security events")
    log_auth_attempts: bool = Field(default=True, description="Log authentication attempts")
    
    # Audit logging
    log_audit: bool = Field(default=True, description="Log audit events")
    audit_events: list[str] = Field(
        default=["create", "update", "delete", "login", "logout"],
        description="Events to audit"
    )
    
    class Config:
        env_prefix = "LOG_"
        env_file = ".env"
