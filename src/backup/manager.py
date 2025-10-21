"""Backup manager for orchestrating backup operations."""

import os
import subprocess
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog

from .config import BackupConfig
from .providers import BackupProvider, LocalProvider, S3Provider

logger = structlog.get_logger(__name__)


class BackupManager:
    """Manages backup operations for the database."""

    def __init__(self, config: BackupConfig):
        self.config = config
        self.logger = logger.bind(manager="BackupManager")
        self.provider = self._create_provider()

    def _create_provider(self) -> BackupProvider:
        """Create backup provider based on configuration."""
        if self.config.provider == "local":
            return LocalProvider(self.config)
        elif self.config.provider == "s3":
            return S3Provider(self.config)
        else:
            raise ValueError(f"Unsupported backup provider: {self.config.provider}")

    def create_backup(self, backup_name: str, verify: bool = True) -> Dict[str, Any]:
        """Create a database backup."""
        start_time = time.time()

        self.logger.info("Starting backup creation", backup_name=backup_name)

        try:
            # Create temporary file for backup
            with tempfile.NamedTemporaryFile(suffix=".sql", delete=False) as temp_file:
                temp_path = temp_file.name

            # Create pg_dump command and environment
            cmd = self._build_pg_dump_command(temp_path)
            env = self._get_environment()

            # Execute pg_dump
            self.logger.info("Executing pg_dump", command=" ".join(cmd))
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.backup_timeout,
                env=env,
            )

            if result.returncode != 0:
                raise RuntimeError(f"pg_dump failed: {result.stderr}")

            # Get backup size
            backup_size = Path(temp_path).stat().st_size
            self.logger.info("pg_dump completed", size=backup_size)

            # Verify backup if requested
            if verify:
                self._verify_backup(temp_path)

            # Prepare metadata
            metadata = {
                "backup_name": backup_name,
                "created": datetime.now().isoformat(),
                "size": backup_size,
                "status": "completed",
                "database": self.config.db_name,
                "compression": self.config.compression,
                "encryption": self.config.encryption,
                "provider": self.config.provider,
            }

            # Upload to storage
            upload_result = self.provider.upload_backup(
                backup_name, temp_path, metadata
            )

            # Clean up temporary file
            Path(temp_path).unlink()

            duration = time.time() - start_time
            upload_result["duration"] = duration

            self.logger.info(
                "Backup created successfully",
                backup_name=backup_name,
                size=backup_size,
                duration=duration,
            )

            return upload_result

        except Exception as e:
            self.logger.error("Backup creation failed", error=str(e))
            # Clean up temporary file if it exists
            if "temp_path" in locals() and Path(temp_path).exists():
                Path(temp_path).unlink()
            raise

    def restore_backup(self, backup_name: str) -> Dict[str, Any]:
        """Restore database from backup."""
        start_time = time.time()

        self.logger.info("Starting backup restore", backup_name=backup_name)

        try:
            # Create temporary file for download
            with tempfile.NamedTemporaryFile(suffix=".sql", delete=False) as temp_file:
                temp_path = temp_file.name

            # Download backup from storage
            if not self.provider.download_backup(backup_name, temp_path):
                raise RuntimeError(f"Failed to download backup: {backup_name}")

            # Create psql command for restore
            cmd = self._build_psql_command(temp_path)
            env = self._get_environment()

            # Execute restore
            self.logger.info("Executing database restore", command=" ".join(cmd))
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.backup_timeout,
                env=env,
            )

            if result.returncode != 0:
                raise RuntimeError(f"Database restore failed: {result.stderr}")

            # Clean up temporary file
            Path(temp_path).unlink()

            duration = time.time() - start_time

            self.logger.info(
                "Backup restored successfully",
                backup_name=backup_name,
                duration=duration,
            )

            return {
                "backup_name": backup_name,
                "duration": duration,
                "status": "completed",
            }

        except Exception as e:
            self.logger.error("Backup restore failed", error=str(e))
            # Clean up temporary file if it exists
            if "temp_path" in locals() and Path(temp_path).exists():
                Path(temp_path).unlink()
            raise

    def list_backups(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """List available backups."""
        return self.provider.list_backups(limit=limit)

    def delete_backup(self, backup_name: str) -> bool:
        """Delete a backup."""
        return self.provider.delete_backup(backup_name)

    def get_backup_info(self, backup_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific backup."""
        return self.provider.get_backup_info(backup_name)

    def cleanup_old_backups(self) -> int:
        """Clean up old backups based on retention policy."""
        self.logger.info(
            "Starting backup cleanup", retention_days=self.config.retention_days
        )

        try:
            all_backups = self.provider.list_backups()
            cutoff_date = datetime.now() - timedelta(days=self.config.retention_days)

            old_backups = []
            for backup in all_backups:
                try:
                    backup_date = datetime.fromisoformat(
                        backup["created"].replace("Z", "+00:00")
                    )
                    if backup_date < cutoff_date:
                        old_backups.append(backup)
                except (ValueError, KeyError):
                    # Skip backups with invalid dates
                    continue

            deleted_count = 0
            for backup in old_backups:
                if self.provider.delete_backup(backup["name"]):
                    deleted_count += 1
                    self.logger.info("Deleted old backup", backup_name=backup["name"])

            self.logger.info("Backup cleanup completed", deleted_count=deleted_count)
            return deleted_count

        except Exception as e:
            self.logger.error("Backup cleanup failed", error=str(e))
            raise

    def get_old_backups(self) -> List[Dict[str, Any]]:
        """Get list of old backups that would be cleaned up."""
        try:
            all_backups = self.provider.list_backups()
            cutoff_date = datetime.now() - timedelta(days=self.config.retention_days)

            old_backups = []
            for backup in all_backups:
                try:
                    backup_date = datetime.fromisoformat(
                        backup["created"].replace("Z", "+00:00")
                    )
                    if backup_date < cutoff_date:
                        old_backups.append(backup)
                except (ValueError, KeyError):
                    # Skip backups with invalid dates
                    continue

            return old_backups

        except Exception as e:
            self.logger.error("Failed to get old backups", error=str(e))
            return []

    def get_status(self) -> Dict[str, Any]:
        """Get backup system status."""
        try:
            backups = self.provider.list_backups()
            total_size = sum(backup.get("size", 0) for backup in backups)

            last_backup = None
            if backups:
                last_backup = max(backups, key=lambda x: x.get("created", ""))
                last_backup = last_backup.get("created")

            return {
                "provider": self.config.provider,
                "destination": self.config.destination,
                "schedule": self.config.schedule,
                "retention_days": self.config.retention_days,
                "last_backup": last_backup,
                "total_backups": len(backups),
                "total_size": total_size,
                "compression": self.config.compression,
                "encryption": self.config.encryption,
            }

        except Exception as e:
            self.logger.error("Failed to get backup status", error=str(e))
            return {
                "provider": self.config.provider,
                "destination": self.config.destination,
                "schedule": self.config.schedule,
                "retention_days": self.config.retention_days,
                "last_backup": None,
                "total_backups": 0,
                "total_size": 0,
                "compression": self.config.compression,
                "encryption": self.config.encryption,
            }

    def _build_pg_dump_command(self, output_path: str) -> List[str]:
        """Build pg_dump command with SSL and certificate options."""
        cmd = [
            "pg_dump",
            "--host",
            self.config.db_host,
            "--port",
            str(self.config.db_port),
            "--username",
            self.config.db_user,
            "--dbname",
            self.config.db_name,
            "--file",
            output_path,
            "--verbose",
            "--no-password",
        ]

        # Set password via environment
        env = os.environ.copy()
        env["PGPASSWORD"] = self.config.db_password

        # Add SSL options via environment variables
        if self.config.db_ssl_mode in ["require", "verify-ca", "verify-full", "prefer"]:
            env["PGSSLMODE"] = self.config.db_ssl_mode

            # Add certificate paths if available
            cert_dir = Path(self.config.cert_dir)
            client_cert = cert_dir / "client.crt"
            client_key = cert_dir / "client.key"
            ca_cert = cert_dir / "ca.crt"

            if client_cert.exists() and client_key.exists():
                env["PGSSLCERT"] = str(client_cert)
                env["PGSSLKEY"] = str(client_key)

            if ca_cert.exists():
                env["PGSSLROOTCERT"] = str(ca_cert)
        elif self.config.db_ssl_mode == "disable":
            # For disable mode, explicitly set SSL mode to disable
            env["PGSSLMODE"] = "disable"

        return cmd

    def _build_psql_command(self, input_path: str) -> List[str]:
        """Build psql command for restore with SSL and certificate options."""
        cmd = [
            "psql",
            "--host",
            self.config.db_host,
            "--port",
            str(self.config.db_port),
            "--username",
            self.config.db_user,
            "--dbname",
            self.config.db_name,
            "--file",
            input_path,
            "--verbose",
            "--no-password",
        ]

        # Set password via environment
        env = os.environ.copy()
        env["PGPASSWORD"] = self.config.db_password

        # Add SSL options via environment variables
        if self.config.db_ssl_mode in ["require", "verify-ca", "verify-full", "prefer"]:
            env["PGSSLMODE"] = self.config.db_ssl_mode

            # Add certificate paths if available
            cert_dir = Path(self.config.cert_dir)
            client_cert = cert_dir / "client.crt"
            client_key = cert_dir / "client.key"
            ca_cert = cert_dir / "ca.crt"

            if client_cert.exists() and client_key.exists():
                env["PGSSLCERT"] = str(client_cert)
                env["PGSSLKEY"] = str(client_key)

            if ca_cert.exists():
                env["PGSSLROOTCERT"] = str(ca_cert)
        elif self.config.db_ssl_mode == "disable":
            # For disable mode, explicitly set SSL mode to disable
            env["PGSSLMODE"] = "disable"

        return cmd

    def _get_environment(self) -> Dict[str, str]:
        """Get environment variables for PostgreSQL commands."""
        env = os.environ.copy()
        env["PGPASSWORD"] = self.config.db_password

        # Add SSL options via environment variables
        if self.config.db_ssl_mode in ["require", "verify-ca", "verify-full", "prefer"]:
            env["PGSSLMODE"] = self.config.db_ssl_mode

            # Add certificate paths if available
            cert_dir = Path(self.config.cert_dir)
            client_cert = cert_dir / "client.crt"
            client_key = cert_dir / "client.key"
            ca_cert = cert_dir / "ca.crt"

            if client_cert.exists() and client_key.exists():
                env["PGSSLCERT"] = str(client_cert)
                env["PGSSLKEY"] = str(client_key)

            if ca_cert.exists():
                env["PGSSLROOTCERT"] = str(ca_cert)
        elif self.config.db_ssl_mode == "disable":
            # For disable mode, explicitly set SSL mode to disable
            env["PGSSLMODE"] = "disable"

        return env

    def _verify_backup(self, backup_path: str) -> None:
        """Verify backup file integrity."""
        self.logger.info("Verifying backup integrity", path=backup_path)

        try:
            # Check if file exists and has content
            if not Path(backup_path).exists():
                raise RuntimeError("Backup file does not exist")

            if Path(backup_path).stat().st_size == 0:
                raise RuntimeError("Backup file is empty")

            # Try to read first few lines to check format
            with open(backup_path, "r") as f:
                first_line = f.readline().strip()
                if not first_line.startswith("-- PostgreSQL database dump"):
                    raise RuntimeError(
                        "Backup file does not appear to be a valid PostgreSQL dump"
                    )

            self.logger.info("Backup verification successful")

        except Exception as e:
            self.logger.error("Backup verification failed", error=str(e))
            raise RuntimeError(f"Backup verification failed: {e}")
