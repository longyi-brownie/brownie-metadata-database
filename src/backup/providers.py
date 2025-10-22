"""Backup providers for different storage backends."""

import gzip
import json
import os
import time
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)


class BackupProvider(ABC):
    """Abstract base class for backup providers."""

    def __init__(self, config):
        self.config = config
        self.logger = logger.bind(provider=self.__class__.__name__)

    @abstractmethod
    def upload_backup(
        self, backup_name: str, backup_path: str, metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Upload backup to storage."""
        pass

    @abstractmethod
    def download_backup(self, backup_name: str, destination_path: str) -> bool:
        """Download backup from storage."""
        pass

    @abstractmethod
    def list_backups(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """List available backups."""
        pass

    @abstractmethod
    def delete_backup(self, backup_name: str) -> bool:
        """Delete backup from storage."""
        pass

    @abstractmethod
    def get_backup_info(self, backup_name: str) -> Optional[Dict[str, Any]]:
        """Get backup information."""
        pass

    def compress_backup(self, source_path: str, dest_path: str) -> bool:
        """Compress backup file."""
        try:
            with open(source_path, "rb") as f_in:
                with gzip.open(dest_path, "wb") as f_out:
                    f_out.write(f_in.read())
            return True
        except Exception as e:
            self.logger.error("Failed to compress backup", error=str(e))
            return False

    def decompress_backup(self, source_path: str, dest_path: str) -> bool:
        """Decompress backup file."""
        try:
            with gzip.open(source_path, "rb") as f_in:
                with open(dest_path, "wb") as f_out:
                    f_out.write(f_in.read())
            return True
        except Exception as e:
            self.logger.error("Failed to decompress backup", error=str(e))
            return False


class LocalProvider(BackupProvider):
    """Local filesystem backup provider."""

    def __init__(self, config):
        super().__init__(config)
        self.backup_dir = Path(config.destination)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def upload_backup(
        self, backup_name: str, backup_path: str, metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Upload backup to local filesystem."""
        try:
            source_path = Path(backup_path)
            dest_path = self.backup_dir / f"{backup_name}.sql"

            if self.config.compression:
                compressed_path = self.backup_dir / f"{backup_name}.sql.gz"
                if self.compress_backup(backup_path, str(compressed_path)):
                    dest_path = compressed_path
                else:
                    # Fallback to uncompressed
                    dest_path = self.backup_dir / f"{backup_name}.sql"

            # Copy file
            import shutil

            shutil.copy2(backup_path, str(dest_path))

            # Save metadata
            metadata_path = self.backup_dir / f"{backup_name}.json"
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)

            file_size = dest_path.stat().st_size

            self.logger.info(
                "Backup uploaded successfully",
                backup_name=backup_name,
                size=file_size,
                path=str(dest_path),
            )

            return {
                "backup_name": backup_name,
                "path": str(dest_path),
                "size": file_size,
                "created": datetime.now().isoformat(),
                "status": "completed",
            }

        except Exception as e:
            self.logger.error("Failed to upload backup", error=str(e))
            raise

    def download_backup(self, backup_name: str, destination_path: str) -> bool:
        """Download backup from local filesystem."""
        try:
            # Try compressed first, then uncompressed
            compressed_path = self.backup_dir / f"{backup_name}.sql.gz"
            uncompressed_path = self.backup_dir / f"{backup_name}.sql"

            if compressed_path.exists():
                if self.config.compression:
                    return self.decompress_backup(
                        str(compressed_path), destination_path
                    )
                else:
                    # Decompress to destination
                    return self.decompress_backup(
                        str(compressed_path), destination_path
                    )
            elif uncompressed_path.exists():
                import shutil

                shutil.copy2(str(uncompressed_path), destination_path)
                return True
            else:
                self.logger.error("Backup not found", backup_name=backup_name)
                return False

        except Exception as e:
            self.logger.error("Failed to download backup", error=str(e))
            return False

    def list_backups(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """List available backups."""
        try:
            backups = []

            for file_path in self.backup_dir.glob("*.sql*"):
                if file_path.suffix == ".json":
                    continue

                backup_name = file_path.stem
                if backup_name.endswith(".sql"):
                    backup_name = backup_name[:-4]  # Remove .sql suffix

                # Load metadata
                metadata_path = self.backup_dir / f"{backup_name}.json"
                metadata = {}
                if metadata_path.exists():
                    with open(metadata_path, "r") as f:
                        metadata = json.load(f)

                backup_info = {
                    "name": backup_name,
                    "size": file_path.stat().st_size,
                    "created": metadata.get(
                        "created",
                        datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                    ),
                    "status": metadata.get("status", "unknown"),
                    "path": str(file_path),
                }
                backups.append(backup_info)

            # Sort by creation time (newest first)
            backups.sort(key=lambda x: x["created"], reverse=True)

            if limit:
                backups = backups[:limit]

            return backups

        except Exception as e:
            self.logger.error("Failed to list backups", error=str(e))
            return []

    def delete_backup(self, backup_name: str) -> bool:
        """Delete backup from local filesystem."""
        try:
            # Try compressed first, then uncompressed
            compressed_path = self.backup_dir / f"{backup_name}.sql.gz"
            uncompressed_path = self.backup_dir / f"{backup_name}.sql"
            metadata_path = self.backup_dir / f"{backup_name}.json"

            deleted = False
            if compressed_path.exists():
                compressed_path.unlink()
                deleted = True
            if uncompressed_path.exists():
                uncompressed_path.unlink()
                deleted = True
            if metadata_path.exists():
                metadata_path.unlink()

            if deleted:
                self.logger.info("Backup deleted successfully", backup_name=backup_name)
                return True
            else:
                self.logger.warning(
                    "Backup not found for deletion", backup_name=backup_name
                )
                return False

        except Exception as e:
            self.logger.error("Failed to delete backup", error=str(e))
            return False

    def get_backup_info(self, backup_name: str) -> Optional[Dict[str, Any]]:
        """Get backup information."""
        try:
            metadata_path = self.backup_dir / f"{backup_name}.json"
            if not metadata_path.exists():
                return None

            with open(metadata_path, "r") as f:
                return json.load(f)

        except Exception as e:
            self.logger.error("Failed to get backup info", error=str(e))
            return None


class S3Provider(BackupProvider):
    """AWS S3 backup provider."""

    def __init__(self, config):
        super().__init__(config)
        try:
            import boto3
            from botocore.exceptions import ClientError

            self.boto3 = boto3
            self.ClientError = ClientError

            # Initialize S3 client
            self.s3_client = boto3.client(
                "s3",
                aws_access_key_id=config.access_key,
                aws_secret_access_key=config.secret_key,
                region_name=config.region,
            )

            # Parse bucket and prefix from destination
            if "/" in config.destination:
                self.bucket_name, self.prefix = config.destination.split("/", 1)
            else:
                self.bucket_name = config.destination
                self.prefix = ""

        except ImportError:
            raise RuntimeError(
                "boto3 package required for S3 provider. Install with: pip install boto3"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize S3 provider: {e}")

    def upload_backup(
        self, backup_name: str, backup_path: str, metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Upload backup to S3."""
        try:
            source_path = Path(backup_path)

            # Determine file extension
            file_extension = ".sql.gz" if self.config.compression else ".sql"
            s3_key = (
                f"{self.prefix}/{backup_name}{file_extension}"
                if self.prefix
                else f"{backup_name}{file_extension}"
            )

            # Compress if needed
            if self.config.compression and not backup_path.endswith(".gz"):
                compressed_path = f"{backup_path}.gz"
                if not self.compress_backup(backup_path, compressed_path):
                    raise RuntimeError("Failed to compress backup")
                upload_path = compressed_path
            else:
                upload_path = backup_path

            # Upload to S3
            self.s3_client.upload_file(upload_path, self.bucket_name, s3_key)

            # Upload metadata
            metadata_key = (
                f"{self.prefix}/{backup_name}.json"
                if self.prefix
                else f"{backup_name}.json"
            )
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=metadata_key,
                Body=json.dumps(metadata, indent=2),
                ContentType="application/json",
            )

            # Get file size
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            file_size = response["ContentLength"]

            self.logger.info(
                "Backup uploaded to S3 successfully",
                backup_name=backup_name,
                size=file_size,
                bucket=self.bucket_name,
                key=s3_key,
            )

            return {
                "backup_name": backup_name,
                "path": f"s3://{self.bucket_name}/{s3_key}",
                "size": file_size,
                "created": datetime.now().isoformat(),
                "status": "completed",
            }

        except Exception as e:
            self.logger.error("Failed to upload backup to S3", error=str(e))
            raise

    def download_backup(self, backup_name: str, destination_path: str) -> bool:
        """Download backup from S3."""
        try:
            # Try compressed first, then uncompressed
            compressed_key = (
                f"{self.prefix}/{backup_name}.sql.gz"
                if self.prefix
                else f"{backup_name}.sql.gz"
            )
            uncompressed_key = (
                f"{self.prefix}/{backup_name}.sql"
                if self.prefix
                else f"{backup_name}.sql"
            )

            # Determine which key exists
            s3_key = None
            try:
                self.s3_client.head_object(Bucket=self.bucket_name, Key=compressed_key)
                s3_key = compressed_key
            except self.ClientError:
                try:
                    self.s3_client.head_object(
                        Bucket=self.bucket_name, Key=uncompressed_key
                    )
                    s3_key = uncompressed_key
                except self.ClientError:
                    self.logger.error("Backup not found in S3", backup_name=backup_name)
                    return False

            # Download file
            self.s3_client.download_file(self.bucket_name, s3_key, destination_path)

            # Decompress if needed
            if s3_key.endswith(".gz") and self.config.compression:
                decompressed_path = destination_path.replace(".gz", "")
                if self.decompress_backup(destination_path, decompressed_path):
                    # Replace compressed with decompressed
                    import shutil

                    shutil.move(decompressed_path, destination_path)

            self.logger.info(
                "Backup downloaded from S3 successfully",
                backup_name=backup_name,
                key=s3_key,
            )
            return True

        except Exception as e:
            self.logger.error("Failed to download backup from S3", error=str(e))
            return False

    def list_backups(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """List available backups from S3."""
        try:
            backups = []

            # List objects with prefix
            paginator = self.s3_client.get_paginator("list_objects_v2")
            page_iterator = paginator.paginate(
                Bucket=self.bucket_name, Prefix=self.prefix + "/" if self.prefix else ""
            )

            for page in page_iterator:
                if "Contents" not in page:
                    continue

                for obj in page["Contents"]:
                    key = obj["Key"]

                    # Skip metadata files
                    if key.endswith(".json"):
                        continue

                    # Extract backup name
                    backup_name = Path(key).stem
                    if backup_name.endswith(".sql"):
                        backup_name = backup_name[:-4]

                    # Get metadata
                    metadata_key = (
                        f"{self.prefix}/{backup_name}.json"
                        if self.prefix
                        else f"{backup_name}.json"
                    )
                    metadata = {}
                    try:
                        response = self.s3_client.get_object(
                            Bucket=self.bucket_name, Key=metadata_key
                        )
                        metadata = json.loads(response["Body"].read().decode("utf-8"))
                    except self.ClientError:
                        # No metadata, use object info
                        pass

                    backup_info = {
                        "name": backup_name,
                        "size": obj["Size"],
                        "created": metadata.get(
                            "created", obj["LastModified"].isoformat()
                        ),
                        "status": metadata.get("status", "unknown"),
                        "path": f"s3://{self.bucket_name}/{key}",
                    }
                    backups.append(backup_info)

            # Sort by creation time (newest first)
            backups.sort(key=lambda x: x["created"], reverse=True)

            if limit:
                backups = backups[:limit]

            return backups

        except Exception as e:
            self.logger.error("Failed to list backups from S3", error=str(e))
            return []

    def delete_backup(self, backup_name: str) -> bool:
        """Delete backup from S3."""
        try:
            # Try compressed first, then uncompressed
            compressed_key = (
                f"{self.prefix}/{backup_name}.sql.gz"
                if self.prefix
                else f"{backup_name}.sql.gz"
            )
            uncompressed_key = (
                f"{self.prefix}/{backup_name}.sql"
                if self.prefix
                else f"{backup_name}.sql"
            )
            metadata_key = (
                f"{self.prefix}/{backup_name}.json"
                if self.prefix
                else f"{backup_name}.json"
            )

            deleted = False

            # Delete backup file
            for key in [compressed_key, uncompressed_key]:
                try:
                    self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
                    deleted = True
                    break
                except self.ClientError:
                    continue

            # Delete metadata
            try:
                self.s3_client.delete_object(Bucket=self.bucket_name, Key=metadata_key)
            except self.ClientError:
                pass

            if deleted:
                self.logger.info(
                    "Backup deleted from S3 successfully", backup_name=backup_name
                )
                return True
            else:
                self.logger.warning(
                    "Backup not found for deletion in S3", backup_name=backup_name
                )
                return False

        except Exception as e:
            self.logger.error("Failed to delete backup from S3", error=str(e))
            return False

    def get_backup_info(self, backup_name: str) -> Optional[Dict[str, Any]]:
        """Get backup information from S3."""
        try:
            metadata_key = (
                f"{self.prefix}/{backup_name}.json"
                if self.prefix
                else f"{backup_name}.json"
            )
            response = self.s3_client.get_object(
                Bucket=self.bucket_name, Key=metadata_key
            )
            return json.loads(response["Body"].read().decode("utf-8"))
        except self.ClientError:
            return None
        except Exception as e:
            self.logger.error("Failed to get backup info from S3", error=str(e))
            return None
