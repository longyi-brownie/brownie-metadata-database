"""Backup configuration and settings."""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class BackupConfig(BaseSettings):
    """Backup configuration settings."""
    
    # Provider settings
    provider: str = Field(default="local", description="Backup provider (s3, gcs, azure, local)")
    destination: str = Field(default="/backups", description="Backup destination path/bucket")
    
    # Schedule settings
    schedule: str = Field(default="0 2 * * *", description="Cron schedule for automated backups")
    retention_days: int = Field(default=30, description="Days to keep backups")
    
    # Backup settings
    compression: bool = Field(default=True, description="Enable compression")
    encryption: bool = Field(default=True, description="Enable encryption")
    parallel_jobs: int = Field(default=2, description="Number of parallel backup jobs")
    backup_timeout: int = Field(default=3600, description="Backup timeout in seconds")
    verify_backup: bool = Field(default=True, description="Verify backup after creation")
    
    # Cloud provider credentials
    access_key: Optional[str] = Field(default=None, description="Cloud provider access key")
    secret_key: Optional[str] = Field(default=None, description="Cloud provider secret key")
    token: Optional[str] = Field(default=None, description="Service account token (GCS)")
    region: Optional[str] = Field(default=None, description="Cloud provider region")
    
    # Database settings
    db_host: str = Field(default="postgres", description="Database host")
    db_port: int = Field(default=5432, description="Database port")
    db_name: str = Field(default="brownie_metadata", description="Database name")
    db_user: str = Field(default="brownie-fastapi-server", description="Database user")
    db_password: str = Field(default="brownie", description="Database password")
    db_ssl_mode: str = Field(default="require", description="Database SSL mode")
    cert_dir: str = Field(default="/certs", description="Certificate directory")
    
    class Config:
        env_prefix = "BACKUP_"
        env_file = ".env"
    
    @property
    def database_url(self) -> str:
        """Get the database URL for pg_dump."""
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    @property
    def is_cloud_provider(self) -> bool:
        """Check if using a cloud provider."""
        return self.provider in ["s3", "gcs", "azure"]
    
    @property
    def requires_credentials(self) -> bool:
        """Check if provider requires credentials."""
        return self.is_cloud_provider and not self.access_key
