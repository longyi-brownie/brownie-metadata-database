"""Audit logging functionality."""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from .config import get_logger


class AuditLogger:
    """Audit logging for tracking data changes."""
    
    def __init__(self, logger_name: str = "audit"):
        self.logger = get_logger(logger_name)
    
    def log_event(
        self,
        event_type: str,
        resource_type: str,
        resource_id: str,
        user_id: Optional[str] = None,
        org_id: Optional[str] = None,
        team_id: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log an audit event."""
        event_id = str(uuid.uuid4())
        
        self.logger.info(
            "Audit event",
            event_id=event_id,
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            org_id=org_id,
            team_id=team_id,
            changes=changes or {},
            metadata=metadata or {},
            timestamp=datetime.utcnow().isoformat(),
        )
    
    def log_create(self, resource_type: str, resource_id: str, **kwargs) -> None:
        """Log a create event."""
        self.log_event("create", resource_type, resource_id, **kwargs)
    
    def log_update(self, resource_type: str, resource_id: str, changes: Dict[str, Any], **kwargs) -> None:
        """Log an update event."""
        self.log_event("update", resource_type, resource_id, changes=changes, **kwargs)
    
    def log_delete(self, resource_type: str, resource_id: str, **kwargs) -> None:
        """Log a delete event."""
        self.log_event("delete", resource_type, resource_id, **kwargs)
    
    def log_access(self, resource_type: str, resource_id: str, action: str, **kwargs) -> None:
        """Log an access event."""
        self.log_event("access", resource_type, resource_id, metadata={"action": action}, **kwargs)
