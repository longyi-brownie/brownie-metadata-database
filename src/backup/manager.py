"""
Backup manager for orchestrating database backups
"""

import os
import gzip
import json
import subprocess
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List

from .config import BackupConfig
from .providers import get_backup_provider


class BackupManager:
    """Manages database backups with cloud storage support"""
    
    def __init__(self, config: BackupConfig):
        self.config = config
        self.provider = get_backup_provider(config)
        self.backup_dir = Path("/tmp/backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def create_backup(self, backup_name: Optional[str] = None) -> Dict[str, Any]:
        """Create a new database backup"""
        if not backup_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"brownie_metadata_{timestamp}"
        
        # Create backup file path
        backup_file = self.backup_dir / f"{backup_name}.sql"
        compressed_file = self.backup_dir / f"{backup_name}.sql.gz"
        
        try:
            # Create database dump
            print(f"Creating database backup: {backup_name}")
            success = self._create_database_dump(backup_file)
            
            if not success:
                return {
                    "success": False,
                    "error": "Failed to create database dump",
                    "backup_name": backup_name
                }
            
            # Compress if enabled
            if self.config.compression:
                print("Compressing backup...")
                self._compress_file(backup_file, compressed_file)
                final_file = compressed_file
            else:
                final_file = backup_file
            
            # Upload to storage
            print(f"Uploading backup to {self.config.provider.value}...")
            remote_path = f"{backup_name}.sql.gz" if self.config.compression else f"{backup_name}.sql"
            upload_success = self.provider.upload_backup(str(final_file), remote_path)
            
            if not upload_success:
                return {
                    "success": False,
                    "error": "Failed to upload backup",
                    "backup_name": backup_name
                }
            
            # Verify backup if enabled
            if self.config.verify_backup:
                print("Verifying backup...")
                verify_success = self._verify_backup(final_file)
                if not verify_success:
                    print("Warning: Backup verification failed")
            
            # Clean up local files
            self._cleanup_local_files(backup_file, compressed_file)
            
            # Get backup info
            backup_info = self._get_backup_info(final_file, remote_path)
            
            print(f"Backup completed successfully: {backup_name}")
            return {
                "success": True,
                "backup_name": backup_name,
                "remote_path": remote_path,
                "size": backup_info["size"],
                "created": backup_info["created"],
                "provider": self.config.provider.value
            }
            
        except Exception as e:
            print(f"Error creating backup: {e}")
            self._cleanup_local_files(backup_file, compressed_file)
            return {
                "success": False,
                "error": str(e),
                "backup_name": backup_name
            }
    
    def restore_backup(self, backup_name: str, target_database: Optional[str] = None) -> Dict[str, Any]:
        """Restore a database backup"""
        if not target_database:
            target_database = self.config.db_name
        
        # Determine file extension
        remote_path = f"{backup_name}.sql.gz" if self.config.compression else f"{backup_name}.sql"
        local_file = self.backup_dir / f"restore_{backup_name}.sql"
        compressed_file = self.backup_dir / f"restore_{backup_name}.sql.gz"
        
        try:
            print(f"Restoring backup: {backup_name}")
            
            # Download backup
            print("Downloading backup...")
            download_success = self.provider.download_backup(remote_path, str(compressed_file if self.config.compression else local_file))
            
            if not download_success:
                return {
                    "success": False,
                    "error": "Failed to download backup"
                }
            
            # Decompress if needed
            if self.config.compression:
                print("Decompressing backup...")
                self._decompress_file(compressed_file, local_file)
            
            # Restore database
            print(f"Restoring to database: {target_database}")
            restore_success = self._restore_database_dump(local_file, target_database)
            
            if not restore_success:
                return {
                    "success": False,
                    "error": "Failed to restore database"
                }
            
            # Clean up local files
            self._cleanup_local_files(local_file, compressed_file)
            
            print(f"Backup restored successfully: {backup_name}")
            return {
                "success": True,
                "backup_name": backup_name,
                "target_database": target_database
            }
            
        except Exception as e:
            print(f"Error restoring backup: {e}")
            self._cleanup_local_files(local_file, compressed_file)
            return {
                "success": False,
                "error": str(e)
            }
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List available backups"""
        return self.provider.list_backups()
    
    def delete_backup(self, backup_name: str) -> Dict[str, Any]:
        """Delete a backup"""
        remote_path = f"{backup_name}.sql.gz" if self.config.compression else f"{backup_name}.sql"
        
        try:
            success = self.provider.delete_backup(remote_path)
            if success:
                return {
                    "success": True,
                    "message": f"Backup {backup_name} deleted successfully"
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to delete backup"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def cleanup_old_backups(self) -> Dict[str, Any]:
        """Clean up old backups based on retention policy"""
        try:
            deleted_count = self.provider.cleanup_old_backups()
            return {
                "success": True,
                "deleted_count": deleted_count,
                "message": f"Cleaned up {deleted_count} old backups"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _create_database_dump(self, output_file: Path) -> bool:
        """Create PostgreSQL database dump"""
        try:
            # Set PGPASSWORD environment variable
            env = os.environ.copy()
            env['PGPASSWORD'] = self.config.db_password
            
            # Build pg_dump command
            cmd = [
                'pg_dump',
                '-h', self.config.db_host,
                '-p', str(self.config.db_port),
                '-U', self.config.db_user,
                '-d', self.config.db_name,
                '-f', str(output_file),
                '--verbose',
                '--no-password'
            ]
            
            # Add compression options
            if self.config.compression:
                cmd.extend(['-Z', '9'])
            
            # Run pg_dump
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=self.config.backup_timeout
            )
            
            if result.returncode != 0:
                print(f"pg_dump failed: {result.stderr}")
                return False
            
            return True
            
        except subprocess.TimeoutExpired:
            print("pg_dump timed out")
            return False
        except Exception as e:
            print(f"Error creating database dump: {e}")
            return False
    
    def _restore_database_dump(self, input_file: Path, target_database: str) -> bool:
        """Restore PostgreSQL database dump"""
        try:
            # Set PGPASSWORD environment variable
            env = os.environ.copy()
            env['PGPASSWORD'] = self.config.db_password
            
            # Build psql command
            cmd = [
                'psql',
                '-h', self.config.db_host,
                '-p', str(self.config.db_port),
                '-U', self.config.db_user,
                '-d', target_database,
                '-f', str(input_file),
                '--quiet'
            ]
            
            # Run psql
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=self.config.backup_timeout
            )
            
            if result.returncode != 0:
                print(f"psql restore failed: {result.stderr}")
                return False
            
            return True
            
        except subprocess.TimeoutExpired:
            print("psql restore timed out")
            return False
        except Exception as e:
            print(f"Error restoring database dump: {e}")
            return False
    
    def _compress_file(self, input_file: Path, output_file: Path) -> None:
        """Compress file with gzip"""
        with open(input_file, 'rb') as f_in:
            with gzip.open(output_file, 'wb') as f_out:
                f_out.writelines(f_in)
    
    def _decompress_file(self, input_file: Path, output_file: Path) -> None:
        """Decompress gzip file"""
        with gzip.open(input_file, 'rb') as f_in:
            with open(output_file, 'wb') as f_out:
                f_out.write(f_in.read())
    
    def _verify_backup(self, backup_file: Path) -> bool:
        """Verify backup file integrity"""
        try:
            # Check if file exists and has content
            if not backup_file.exists() or backup_file.stat().st_size == 0:
                return False
            
            # For compressed files, try to decompress
            if backup_file.suffix == '.gz':
                with gzip.open(backup_file, 'rb') as f:
                    # Try to read first few bytes
                    f.read(1024)
            
            return True
            
        except Exception as e:
            print(f"Backup verification failed: {e}")
            return False
    
    def _get_backup_info(self, backup_file: Path, remote_path: str) -> Dict[str, Any]:
        """Get backup file information"""
        stat = backup_file.stat()
        return {
            "size": stat.st_size,
            "created": datetime.fromtimestamp(stat.st_ctime),
            "remote_path": remote_path
        }
    
    def _cleanup_local_files(self, *files: Path) -> None:
        """Clean up local temporary files"""
        for file_path in files:
            if file_path.exists():
                try:
                    file_path.unlink()
                except Exception as e:
                    print(f"Warning: Could not delete {file_path}: {e}")
    
    def get_backup_status(self) -> Dict[str, Any]:
        """Get backup system status"""
        try:
            backups = self.list_backups()
            return {
                "provider": self.config.provider.value,
                "destination": self.config.destination,
                "total_backups": len(backups),
                "retention_days": self.config.retention_days,
                "compression": self.config.compression,
                "encryption": self.config.encryption,
                "last_backup": backups[0]["created"] if backups else None,
                "backups": backups[:10]  # Last 10 backups
            }
        except Exception as e:
            return {
                "error": str(e),
                "provider": self.config.provider.value,
                "destination": self.config.destination
            }
