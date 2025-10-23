"""Brownie Metadata Database - A comprehensive database management library."""

# Re-export from the main package
from brownie_metadata_db.backup import (
    BackupManager,
    BackupProvider,
    LocalProvider,
    S3Provider,
)
from brownie_metadata_db.certificates import (
    CertificateConfig,
    CertificateValidator,
    cert_config,
)
from brownie_metadata_db.database import get_database_manager, get_session
from brownie_metadata_db.database.models import (
    AgentConfig,
    AgentType,
    Config,
    ConfigStatus,
    ConfigType,
    Incident,
    IncidentPriority,
    IncidentStatus,
    Organization,
    Stats,
    Team,
    User,
    UserRole,
)
from brownie_metadata_db.logging import (
    AuditLogger,
    LoggingConfig,
    PerformanceLogger,
    configure_logging,
)

__version__ = "0.1.0"

__all__ = [
    # Database
    "get_database_manager",
    "get_session",
    # Models
    "Organization",
    "Team",
    "User",
    "UserRole",
    "Incident",
    "IncidentStatus",
    "IncidentPriority",
    "AgentConfig",
    "AgentType",
    "Stats",
    "Config",
    "ConfigType",
    "ConfigStatus",
    # Backup
    "BackupManager",
    "BackupProvider",
    "S3Provider",
    "LocalProvider",
    # Certificates
    "CertificateValidator",
    "CertificateConfig",
    "cert_config",
    # Logging
    "LoggingConfig",
    "configure_logging",
    "AuditLogger",
    "PerformanceLogger",
]
