"""
Backup configuration management
"""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum


class BackupProvider(Enum):
    """Supported backup providers"""
    S3 = "s3"
    GCS = "gcs"
    AZURE = "azure"
    LOCAL = "local"


@dataclass
class BackupConfig:
    """Backup configuration"""
    
    # Provider settings
    provider: BackupProvider = BackupProvider.LOCAL
    destination: str = "/backups"
    
    # Cloud provider credentials
    access_key: Optional[str] = None
    secret_key: Optional[str] = None
    token: Optional[str] = None
    region: Optional[str] = None
    
    # Backup settings
    schedule: str = "0 2 * * *"  # Daily at 2 AM
    retention_days: int = 30
    compression: bool = True
    encryption: bool = True
    
    # Database settings
    db_host: str = "postgres"
    db_port: int = 5432
    db_name: str = "brownie_metadata"
    db_user: str = "brownie"
    db_password: str = "brownie"
    
    # Advanced settings
    parallel_jobs: int = 2
    backup_timeout: int = 3600  # 1 hour
    verify_backup: bool = True
    
    @classmethod
    def from_env(cls) -> "BackupConfig":
        """Create config from environment variables"""
        return cls(
            provider=BackupProvider(os.getenv("BACKUP_PROVIDER", "local")),
            destination=os.getenv("BACKUP_DESTINATION", "/backups"),
            access_key=os.getenv("BACKUP_ACCESS_KEY"),
            secret_key=os.getenv("BACKUP_SECRET_KEY"),
            token=os.getenv("BACKUP_TOKEN"),
            region=os.getenv("BACKUP_REGION"),
            schedule=os.getenv("BACKUP_SCHEDULE", "0 2 * * *"),
            retention_days=int(os.getenv("BACKUP_RETENTION_DAYS", "30")),
            compression=os.getenv("BACKUP_COMPRESSION", "true").lower() == "true",
            encryption=os.getenv("BACKUP_ENCRYPTION", "true").lower() == "true",
            db_host=os.getenv("DB_HOST", "postgres"),
            db_port=int(os.getenv("DB_PORT", "5432")),
            db_name=os.getenv("DB_NAME", "brownie_metadata"),
            db_user=os.getenv("DB_USER", "brownie"),
            db_password=os.getenv("DB_PASSWORD", "brownie"),
            parallel_jobs=int(os.getenv("BACKUP_PARALLEL_JOBS", "2")),
            backup_timeout=int(os.getenv("BACKUP_TIMEOUT", "3600")),
            verify_backup=os.getenv("BACKUP_VERIFY", "true").lower() == "true"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "provider": self.provider.value,
            "destination": self.destination,
            "access_key": self.access_key,
            "secret_key": self.secret_key,
            "token": self.token,
            "region": self.region,
            "schedule": self.schedule,
            "retention_days": self.retention_days,
            "compression": self.compression,
            "encryption": self.encryption,
            "db_host": self.db_host,
            "db_port": self.db_port,
            "db_name": self.db_name,
            "db_user": self.db_user,
            "db_password": self.db_password,
            "parallel_jobs": self.parallel_jobs,
            "backup_timeout": self.backup_timeout,
            "verify_backup": self.verify_backup
        }
    
    def validate(self) -> None:
        """Validate configuration"""
        if self.provider != BackupProvider.LOCAL:
            if not self.destination:
                raise ValueError("Backup destination is required for cloud providers")
            
            if self.provider == BackupProvider.S3:
                if not self.access_key or not self.secret_key:
                    raise ValueError("S3 requires access_key and secret_key")
            
            elif self.provider == BackupProvider.GCS:
                if not self.token:
                    raise ValueError("GCS requires token (service account key)")
            
            elif self.provider == BackupProvider.AZURE:
                if not self.access_key or not self.secret_key:
                    raise ValueError("Azure requires access_key and secret_key")
        
        if self.retention_days < 1:
            raise ValueError("Retention days must be at least 1")
        
        if self.parallel_jobs < 1:
            raise ValueError("Parallel jobs must be at least 1")
        
        if self.backup_timeout < 60:
            raise ValueError("Backup timeout must be at least 60 seconds")
