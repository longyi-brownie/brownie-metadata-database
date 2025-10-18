"""
Command-line interface for backup operations
"""

import sys
import argparse
import json
from datetime import datetime

from .config import BackupConfig
from .manager import BackupManager
from .scheduler import BackupScheduler


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Brownie Metadata Database Backup Tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Backup command
    backup_parser = subparsers.add_parser("backup", help="Create a backup")
    backup_parser.add_argument("--name", help="Backup name (optional)")
    
    # Restore command
    restore_parser = subparsers.add_parser("restore", help="Restore a backup")
    restore_parser.add_argument("name", help="Backup name to restore")
    restore_parser.add_argument("--target-db", help="Target database name")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List available backups")
    
    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a backup")
    delete_parser.add_argument("name", help="Backup name to delete")
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up old backups")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show backup status")
    
    # Schedule command
    schedule_parser = subparsers.add_parser("schedule", help="Manage backup scheduling")
    schedule_parser.add_argument("--start", action="store_true", help="Start scheduler")
    schedule_parser.add_argument("--stop", action="store_true", help="Stop scheduler")
    schedule_parser.add_argument("--status", action="store_true", help="Show scheduler status")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        # Load configuration
        config = BackupConfig.from_env()
        config.validate()
        
        # Create backup manager
        backup_manager = BackupManager(config)
        
        if args.command == "backup":
            result = backup_manager.create_backup(args.name)
            print_backup_result(result)
            
        elif args.command == "restore":
            result = backup_manager.restore_backup(args.name, args.target_db)
            print_backup_result(result)
            
        elif args.command == "list":
            backups = backup_manager.list_backups()
            print_backup_list(backups)
            
        elif args.command == "delete":
            result = backup_manager.delete_backup(args.name)
            print_backup_result(result)
            
        elif args.command == "cleanup":
            result = backup_manager.cleanup_old_backups()
            print_backup_result(result)
            
        elif args.command == "status":
            status = backup_manager.get_backup_status()
            print_backup_status(status)
            
        elif args.command == "schedule":
            handle_schedule_command(args, config)
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def print_backup_result(result):
    """Print backup operation result"""
    if result["success"]:
        print(f"✅ {result.get('message', 'Operation completed successfully')}")
        if "backup_name" in result:
            print(f"   Backup: {result['backup_name']}")
        if "deleted_count" in result:
            print(f"   Deleted: {result['deleted_count']} backups")
    else:
        print(f"❌ {result.get('message', 'Operation failed')}")
        if "error" in result:
            print(f"   Error: {result['error']}")


def print_backup_list(backups):
    """Print list of backups"""
    if not backups:
        print("No backups found")
        return
    
    print(f"Found {len(backups)} backups:")
    print()
    print(f"{'Name':<30} {'Size':<10} {'Created':<20} {'Provider'}")
    print("-" * 70)
    
    for backup in backups:
        size = format_size(backup["size"])
        created = backup["created"].strftime("%Y-%m-%d %H:%M:%S")
        print(f"{backup['name']:<30} {size:<10} {created:<20} {backup.get('provider', 'N/A')}")


def print_backup_status(status):
    """Print backup system status"""
    print("Backup System Status")
    print("=" * 50)
    print(f"Provider: {status.get('provider', 'N/A')}")
    print(f"Destination: {status.get('destination', 'N/A')}")
    print(f"Total Backups: {status.get('total_backups', 0)}")
    print(f"Retention Days: {status.get('retention_days', 'N/A')}")
    print(f"Compression: {'Yes' if status.get('compression') else 'No'}")
    print(f"Encryption: {'Yes' if status.get('encryption') else 'No'}")
    
    if status.get('last_backup'):
        last_backup = status['last_backup']
        if isinstance(last_backup, str):
            print(f"Last Backup: {last_backup}")
        else:
            print(f"Last Backup: {last_backup.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print("Last Backup: None")
    
    if status.get('backups'):
        print("\nRecent Backups:")
        for backup in status['backups'][:5]:
            size = format_size(backup["size"])
            created = backup["created"].strftime("%Y-%m-%d %H:%M:%S")
            print(f"  {backup['name']} ({size}) - {created}")


def handle_schedule_command(args, config):
    """Handle schedule-related commands"""
    scheduler = BackupScheduler(BackupManager(config))
    
    if args.start:
        scheduler.start()
        print("✅ Backup scheduler started")
        
    elif args.stop:
        scheduler.stop()
        print("✅ Backup scheduler stopped")
        
    elif args.status:
        status = scheduler.get_scheduler_status()
        print("Backup Scheduler Status")
        print("=" * 30)
        print(f"Running: {'Yes' if status['running'] else 'No'}")
        print(f"Schedule: {status['schedule']}")
        
        next_backup = status.get('next_backup')
        if next_backup:
            print(f"Next Backup: {next_backup.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print("Next Backup: Not scheduled")


def format_size(size_bytes):
    """Format size in human-readable format"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"


if __name__ == "__main__":
    main()
