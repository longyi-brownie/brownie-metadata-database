#!/usr/bin/env python3
"""Backup CLI for Brownie Metadata Database."""

import os
import sys
import argparse
import structlog
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from .manager import BackupManager
from .config import BackupConfig

logger = structlog.get_logger(__name__)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Brownie Metadata Database Backup")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Backup command
    backup_parser = subparsers.add_parser("backup", help="Create a backup")
    backup_parser.add_argument("--name", help="Custom backup name")
    backup_parser.add_argument("--verify", action="store_true", help="Verify backup after creation")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List available backups")
    list_parser.add_argument("--limit", type=int, default=10, help="Limit number of backups to show")
    
    # Restore command
    restore_parser = subparsers.add_parser("restore", help="Restore from backup")
    restore_parser.add_argument("backup_name", help="Name of backup to restore")
    restore_parser.add_argument("--force", action="store_true", help="Force restore without confirmation")
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up old backups")
    cleanup_parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show backup status")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Configure logging
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    try:
        config = BackupConfig()
        manager = BackupManager(config)
        
        if args.command == "backup":
            return backup_command(manager, args)
        elif args.command == "list":
            return list_command(manager, args)
        elif args.command == "restore":
            return restore_command(manager, args)
        elif args.command == "cleanup":
            return cleanup_command(manager, args)
        elif args.command == "status":
            return status_command(manager, args)
        else:
            parser.print_help()
            return 1
            
    except Exception as e:
        logger.error("Backup operation failed", error=str(e), exc_info=True)
        return 1


def backup_command(manager: BackupManager, args) -> int:
    """Create a backup."""
    backup_name = args.name or f"backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    logger.info("Starting backup", backup_name=backup_name)
    
    try:
        result = manager.create_backup(backup_name, verify=args.verify)
        logger.info("Backup completed successfully", 
                   backup_name=backup_name, 
                   size=result.get('size'),
                   duration=result.get('duration'))
        print(f"✅ Backup '{backup_name}' created successfully")
        return 0
    except Exception as e:
        logger.error("Backup failed", error=str(e))
        print(f"❌ Backup failed: {e}")
        return 1


def list_command(manager: BackupManager, args) -> int:
    """List available backups."""
    try:
        backups = manager.list_backups(limit=args.limit)
        
        if not backups:
            print("No backups found")
            return 0
        
        print(f"\n📦 Available Backups (showing {len(backups)}):")
        print("-" * 80)
        print(f"{'Name':<30} {'Size':<12} {'Created':<20} {'Status':<10}")
        print("-" * 80)
        
        for backup in backups:
            size_str = format_size(backup.get('size', 0))
            created_str = backup.get('created', 'Unknown')
            status = backup.get('status', 'Unknown')
            print(f"{backup['name']:<30} {size_str:<12} {created_str:<20} {status:<10}")
        
        return 0
    except Exception as e:
        logger.error("Failed to list backups", error=str(e))
        print(f"❌ Failed to list backups: {e}")
        return 1


def restore_command(manager: BackupManager, args) -> int:
    """Restore from backup."""
    if not args.force:
        confirm = input(f"Are you sure you want to restore from '{args.backup_name}'? This will overwrite the current database! (yes/no): ")
        if confirm.lower() != 'yes':
            print("Restore cancelled")
            return 0
    
    logger.info("Starting restore", backup_name=args.backup_name)
    
    try:
        result = manager.restore_backup(args.backup_name)
        logger.info("Restore completed successfully", 
                   backup_name=args.backup_name,
                   duration=result.get('duration'))
        print(f"✅ Restore from '{args.backup_name}' completed successfully")
        return 0
    except Exception as e:
        logger.error("Restore failed", error=str(e))
        print(f"❌ Restore failed: {e}")
        return 1


def cleanup_command(manager: BackupManager, args) -> int:
    """Clean up old backups."""
    try:
        if args.dry_run:
            old_backups = manager.get_old_backups()
            if not old_backups:
                print("No old backups to clean up")
                return 0
            
            print(f"\n🗑️  Old backups that would be deleted (dry run):")
            print("-" * 50)
            for backup in old_backups:
                print(f"  - {backup['name']} ({backup.get('created', 'Unknown')})")
            return 0
        else:
            deleted_count = manager.cleanup_old_backups()
            print(f"✅ Cleaned up {deleted_count} old backups")
            return 0
    except Exception as e:
        logger.error("Cleanup failed", error=str(e))
        print(f"❌ Cleanup failed: {e}")
        return 1


def status_command(manager: BackupManager, args) -> int:
    """Show backup status."""
    try:
        status = manager.get_status()
        
        print("\n📊 Backup Status:")
        print("-" * 40)
        print(f"Provider: {status['provider']}")
        print(f"Destination: {status['destination']}")
        print(f"Schedule: {status['schedule']}")
        print(f"Retention: {status['retention_days']} days")
        print(f"Last Backup: {status.get('last_backup', 'Never')}")
        print(f"Total Backups: {status.get('total_backups', 0)}")
        print(f"Total Size: {format_size(status.get('total_size', 0))}")
        
        return 0
    except Exception as e:
        logger.error("Failed to get status", error=str(e))
        print(f"❌ Failed to get status: {e}")
        return 1


def format_size(size_bytes: int) -> str:
    """Format size in bytes to human readable format."""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


if __name__ == "__main__":
    sys.exit(main())
