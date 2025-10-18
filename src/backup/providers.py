"""
Backup providers for different cloud storage services
"""

import os
import gzip
import json
import tempfile
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
from google.cloud import storage
from azure.storage.blob import BlobServiceClient


class BackupProvider(ABC):
    """Abstract base class for backup providers"""
    
    def __init__(self, config):
        self.config = config
    
    @abstractmethod
    def upload_backup(self, local_path: str, remote_path: str) -> bool:
        """Upload backup file to remote storage"""
        pass
    
    @abstractmethod
    def download_backup(self, remote_path: str, local_path: str) -> bool:
        """Download backup file from remote storage"""
        pass
    
    @abstractmethod
    def list_backups(self) -> List[Dict[str, Any]]:
        """List available backups"""
        pass
    
    @abstractmethod
    def delete_backup(self, remote_path: str) -> bool:
        """Delete backup file"""
        pass
    
    @abstractmethod
    def cleanup_old_backups(self) -> int:
        """Clean up old backups based on retention policy"""
        pass


class LocalBackupProvider(BackupProvider):
    """Local filesystem backup provider"""
    
    def __init__(self, config):
        super().__init__(config)
        self.backup_dir = Path(config.destination)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def upload_backup(self, local_path: str, remote_path: str) -> bool:
        """Copy backup to local directory"""
        try:
            source = Path(local_path)
            dest = self.backup_dir / remote_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            import shutil
            shutil.copy2(source, dest)
            return True
        except Exception as e:
            print(f"Error uploading backup: {e}")
            return False
    
    def download_backup(self, remote_path: str, local_path: str) -> bool:
        """Copy backup from local directory"""
        try:
            source = self.backup_dir / remote_path
            dest = Path(local_path)
            dest.parent.mkdir(parents=True, exist_ok=True)
            
            import shutil
            shutil.copy2(source, dest)
            return True
        except Exception as e:
            print(f"Error downloading backup: {e}")
            return False
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List local backups"""
        backups = []
        for backup_file in self.backup_dir.rglob("*.sql*"):
            stat = backup_file.stat()
            backups.append({
                "name": backup_file.name,
                "path": str(backup_file.relative_to(self.backup_dir)),
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime),
                "modified": datetime.fromtimestamp(stat.st_mtime)
            })
        return sorted(backups, key=lambda x: x["created"], reverse=True)
    
    def delete_backup(self, remote_path: str) -> bool:
        """Delete local backup"""
        try:
            backup_file = self.backup_dir / remote_path
            backup_file.unlink()
            return True
        except Exception as e:
            print(f"Error deleting backup: {e}")
            return False
    
    def cleanup_old_backups(self) -> int:
        """Clean up old local backups"""
        cutoff_date = datetime.now().timestamp() - (self.config.retention_days * 24 * 3600)
        deleted_count = 0
        
        for backup_file in self.backup_dir.rglob("*.sql*"):
            if backup_file.stat().st_ctime < cutoff_date:
                try:
                    backup_file.unlink()
                    deleted_count += 1
                except Exception as e:
                    print(f"Error deleting old backup {backup_file}: {e}")
        
        return deleted_count


class S3BackupProvider(BackupProvider):
    """AWS S3 backup provider"""
    
    def __init__(self, config):
        super().__init__(config)
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=config.access_key,
            aws_secret_access_key=config.secret_key,
            region_name=config.region or 'us-east-1'
        )
        self.bucket_name = config.destination.split('/')[0]
        self.prefix = '/'.join(config.destination.split('/')[1:]) if '/' in config.destination else ''
    
    def upload_backup(self, local_path: str, remote_path: str) -> bool:
        """Upload backup to S3"""
        try:
            key = f"{self.prefix}/{remote_path}" if self.prefix else remote_path
            self.s3_client.upload_file(local_path, self.bucket_name, key)
            return True
        except ClientError as e:
            print(f"Error uploading backup to S3: {e}")
            return False
    
    def download_backup(self, remote_path: str, local_path: str) -> bool:
        """Download backup from S3"""
        try:
            key = f"{self.prefix}/{remote_path}" if self.prefix else remote_path
            self.s3_client.download_file(self.bucket_name, key, local_path)
            return True
        except ClientError as e:
            print(f"Error downloading backup from S3: {e}")
            return False
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List S3 backups"""
        backups = []
        try:
            prefix = f"{self.prefix}/" if self.prefix else ""
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            for obj in response.get('Contents', []):
                if obj['Key'].endswith('.sql') or obj['Key'].endswith('.sql.gz'):
                    backups.append({
                        "name": obj['Key'].split('/')[-1],
                        "path": obj['Key'],
                        "size": obj['Size'],
                        "created": obj['LastModified'],
                        "modified": obj['LastModified']
                    })
        except ClientError as e:
            print(f"Error listing S3 backups: {e}")
        
        return sorted(backups, key=lambda x: x["created"], reverse=True)
    
    def delete_backup(self, remote_path: str) -> bool:
        """Delete S3 backup"""
        try:
            key = f"{self.prefix}/{remote_path}" if self.prefix else remote_path
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError as e:
            print(f"Error deleting S3 backup: {e}")
            return False
    
    def cleanup_old_backups(self) -> int:
        """Clean up old S3 backups"""
        cutoff_date = datetime.now() - timedelta(days=self.config.retention_days)
        deleted_count = 0
        
        try:
            prefix = f"{self.prefix}/" if self.prefix else ""
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            for obj in response.get('Contents', []):
                if obj['LastModified'] < cutoff_date:
                    try:
                        self.s3_client.delete_object(Bucket=self.bucket_name, Key=obj['Key'])
                        deleted_count += 1
                    except ClientError as e:
                        print(f"Error deleting old backup {obj['Key']}: {e}")
        except ClientError as e:
            print(f"Error cleaning up S3 backups: {e}")
        
        return deleted_count


class GCSBackupProvider(BackupProvider):
    """Google Cloud Storage backup provider"""
    
    def __init__(self, config):
        super().__init__(config)
        # Write service account key to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(config.token)
            self.credentials_file = f.name
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.credentials_file
        self.client = storage.Client()
        self.bucket_name = config.destination.split('/')[0]
        self.prefix = '/'.join(config.destination.split('/')[1:]) if '/' in config.destination else ''
        self.bucket = self.client.bucket(self.bucket_name)
    
    def upload_backup(self, local_path: str, remote_path: str) -> bool:
        """Upload backup to GCS"""
        try:
            blob_name = f"{self.prefix}/{remote_path}" if self.prefix else remote_path
            blob = self.bucket.blob(blob_name)
            blob.upload_from_filename(local_path)
            return True
        except Exception as e:
            print(f"Error uploading backup to GCS: {e}")
            return False
    
    def download_backup(self, remote_path: str, local_path: str) -> bool:
        """Download backup from GCS"""
        try:
            blob_name = f"{self.prefix}/{remote_path}" if self.prefix else remote_path
            blob = self.bucket.blob(blob_name)
            blob.download_to_filename(local_path)
            return True
        except Exception as e:
            print(f"Error downloading backup from GCS: {e}")
            return False
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List GCS backups"""
        backups = []
        try:
            prefix = f"{self.prefix}/" if self.prefix else ""
            blobs = self.bucket.list_blobs(prefix=prefix)
            
            for blob in blobs:
                if blob.name.endswith('.sql') or blob.name.endswith('.sql.gz'):
                    backups.append({
                        "name": blob.name.split('/')[-1],
                        "path": blob.name,
                        "size": blob.size,
                        "created": blob.time_created,
                        "modified": blob.updated
                    })
        except Exception as e:
            print(f"Error listing GCS backups: {e}")
        
        return sorted(backups, key=lambda x: x["created"], reverse=True)
    
    def delete_backup(self, remote_path: str) -> bool:
        """Delete GCS backup"""
        try:
            blob_name = f"{self.prefix}/{remote_path}" if self.prefix else remote_path
            blob = self.bucket.blob(blob_name)
            blob.delete()
            return True
        except Exception as e:
            print(f"Error deleting GCS backup: {e}")
            return False
    
    def cleanup_old_backups(self) -> int:
        """Clean up old GCS backups"""
        cutoff_date = datetime.now() - timedelta(days=self.config.retention_days)
        deleted_count = 0
        
        try:
            prefix = f"{self.prefix}/" if self.prefix else ""
            blobs = self.bucket.list_blobs(prefix=prefix)
            
            for blob in blobs:
                if blob.time_created < cutoff_date:
                    try:
                        blob.delete()
                        deleted_count += 1
                    except Exception as e:
                        print(f"Error deleting old backup {blob.name}: {e}")
        except Exception as e:
            print(f"Error cleaning up GCS backups: {e}")
        
        return deleted_count


class AzureBackupProvider(BackupProvider):
    """Azure Blob Storage backup provider"""
    
    def __init__(self, config):
        super().__init__(config)
        self.account_name = config.access_key
        self.account_key = config.secret_key
        self.container_name = config.destination.split('/')[0]
        self.prefix = '/'.join(config.destination.split('/')[1:]) if '/' in config.destination else ''
        
        self.blob_service_client = BlobServiceClient(
            account_url=f"https://{self.account_name}.blob.core.windows.net",
            credential=self.account_key
        )
        self.container_client = self.blob_service_client.get_container_client(self.container_name)
    
    def upload_backup(self, local_path: str, remote_path: str) -> bool:
        """Upload backup to Azure Blob Storage"""
        try:
            blob_name = f"{self.prefix}/{remote_path}" if self.prefix else remote_path
            with open(local_path, "rb") as data:
                self.container_client.upload_blob(name=blob_name, data=data, overwrite=True)
            return True
        except Exception as e:
            print(f"Error uploading backup to Azure: {e}")
            return False
    
    def download_backup(self, remote_path: str, local_path: str) -> bool:
        """Download backup from Azure Blob Storage"""
        try:
            blob_name = f"{self.prefix}/{remote_path}" if self.prefix else remote_path
            blob_client = self.container_client.get_blob_client(blob_name)
            with open(local_path, "wb") as data:
                data.write(blob_client.download_blob().readall())
            return True
        except Exception as e:
            print(f"Error downloading backup from Azure: {e}")
            return False
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List Azure backups"""
        backups = []
        try:
            prefix = f"{self.prefix}/" if self.prefix else ""
            blobs = self.container_client.list_blobs(name_starts_with=prefix)
            
            for blob in blobs:
                if blob.name.endswith('.sql') or blob.name.endswith('.sql.gz'):
                    backups.append({
                        "name": blob.name.split('/')[-1],
                        "path": blob.name,
                        "size": blob.size,
                        "created": blob.creation_time,
                        "modified": blob.last_modified
                    })
        except Exception as e:
            print(f"Error listing Azure backups: {e}")
        
        return sorted(backups, key=lambda x: x["created"], reverse=True)
    
    def delete_backup(self, remote_path: str) -> bool:
        """Delete Azure backup"""
        try:
            blob_name = f"{self.prefix}/{remote_path}" if self.prefix else remote_path
            blob_client = self.container_client.get_blob_client(blob_name)
            blob_client.delete_blob()
            return True
        except Exception as e:
            print(f"Error deleting Azure backup: {e}")
            return False
    
    def cleanup_old_backups(self) -> int:
        """Clean up old Azure backups"""
        cutoff_date = datetime.now() - timedelta(days=self.config.retention_days)
        deleted_count = 0
        
        try:
            prefix = f"{self.prefix}/" if self.prefix else ""
            blobs = self.container_client.list_blobs(name_starts_with=prefix)
            
            for blob in blobs:
                if blob.creation_time < cutoff_date:
                    try:
                        blob_client = self.container_client.get_blob_client(blob.name)
                        blob_client.delete_blob()
                        deleted_count += 1
                    except Exception as e:
                        print(f"Error deleting old backup {blob.name}: {e}")
        except Exception as e:
            print(f"Error cleaning up Azure backups: {e}")
        
        return deleted_count


def get_backup_provider(config) -> BackupProvider:
    """Factory function to get backup provider"""
    if config.provider.value == "s3":
        return S3BackupProvider(config)
    elif config.provider.value == "gcs":
        return GCSBackupProvider(config)
    elif config.provider.value == "azure":
        return AzureBackupProvider(config)
    else:
        return LocalBackupProvider(config)
