"""Logging configuration settings."""

import os


class LoggingConfig:
    """Logging configuration settings."""
    
    def __init__(self):
        # Log level
        self.level = os.getenv("LOG_LEVEL", "INFO")
        
        # Output format
        self.format = os.getenv("LOG_FORMAT", "json")
        
        # Include timestamps
        self.include_timestamps = os.getenv("LOG_INCLUDE_TIMESTAMPS", "true").lower() == "true"
        
        # Include caller info
        self.include_caller = os.getenv("LOG_INCLUDE_CALLER", "true").lower() == "true"
        
        # Include process info
        self.include_process = os.getenv("LOG_INCLUDE_PROCESS", "true").lower() == "true"
        
        # Structured logging
        self.structured = os.getenv("LOG_STRUCTURED", "true").lower() == "true"
        
        # Log to file
        self.log_file = os.getenv("LOG_FILE")
        
        # Log rotation
        self.max_file_size = int(os.getenv("LOG_MAX_FILE_SIZE", str(10 * 1024 * 1024)))
        self.backup_count = int(os.getenv("LOG_BACKUP_COUNT", "5"))
        
        # Performance logging
        self.log_performance = os.getenv("LOG_PERFORMANCE", "true").lower() == "true"
        self.slow_query_threshold = float(os.getenv("LOG_SLOW_QUERY_THRESHOLD", "1.0"))
        
        # Security logging
        self.log_security = os.getenv("LOG_SECURITY", "true").lower() == "true"
        self.log_auth_attempts = os.getenv("LOG_AUTH_ATTEMPTS", "true").lower() == "true"
        
        # Audit logging
        self.log_audit = os.getenv("LOG_AUDIT", "true").lower() == "true"
        self.audit_events = os.getenv("LOG_AUDIT_EVENTS", "create,update,delete,login,logout").split(",")
