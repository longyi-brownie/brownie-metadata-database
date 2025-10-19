"""Performance logging functionality."""

import time
from contextlib import contextmanager
from typing import Any, Dict, Optional
from .config import get_logger


class PerformanceLogger:
    """Performance logging for tracking operation timing."""
    
    def __init__(self, logger_name: str = "performance"):
        self.logger = get_logger(logger_name)
    
    @contextmanager
    def log_operation(
        self,
        operation: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        slow_threshold: float = 1.0,
    ):
        """Log the duration of an operation."""
        start_time = time.time()
        
        try:
            yield
        finally:
            duration = time.time() - start_time
            
            log_data = {
                "operation": operation,
                "duration_seconds": duration,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "metadata": metadata or {},
            }
            
            if duration > slow_threshold:
                self.logger.warning("Slow operation", **log_data)
            else:
                self.logger.info("Operation completed", **log_data)
    
    def log_query(
        self,
        query: str,
        duration: float,
        rows_affected: Optional[int] = None,
        slow_threshold: float = 1.0,
    ) -> None:
        """Log a database query."""
        log_data = {
            "query": query,
            "duration_seconds": duration,
            "rows_affected": rows_affected,
        }
        
        if duration > slow_threshold:
            self.logger.warning("Slow query", **log_data)
        else:
            self.logger.debug("Query executed", **log_data)
    
    def log_api_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration: float,
        user_id: Optional[str] = None,
        slow_threshold: float = 1.0,
    ) -> None:
        """Log an API request."""
        log_data = {
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_seconds": duration,
            "user_id": user_id,
        }
        
        if duration > slow_threshold:
            self.logger.warning("Slow API request", **log_data)
        else:
            self.logger.info("API request", **log_data)
