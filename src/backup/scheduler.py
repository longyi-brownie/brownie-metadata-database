"""
Backup scheduler using cron-like scheduling
"""

import schedule
import time
import threading
from datetime import datetime
from typing import Optional, Callable

from .manager import BackupManager
from .config import BackupConfig


class BackupScheduler:
    """Schedules and manages automated backups"""
    
    def __init__(self, backup_manager: BackupManager):
        self.backup_manager = backup_manager
        self.scheduler_thread: Optional[threading.Thread] = None
        self.running = False
        self.schedule_config = backup_manager.config.schedule
    
    def start(self) -> None:
        """Start the backup scheduler"""
        if self.running:
            print("Backup scheduler is already running")
            return
        
        print(f"Starting backup scheduler with schedule: {self.schedule_config}")
        
        # Clear any existing jobs
        schedule.clear()
        
        # Schedule the backup job
        self._schedule_backup_job()
        
        # Start scheduler thread
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        print("Backup scheduler started")
    
    def stop(self) -> None:
        """Stop the backup scheduler"""
        if not self.running:
            print("Backup scheduler is not running")
            return
        
        print("Stopping backup scheduler...")
        self.running = False
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        schedule.clear()
        print("Backup scheduler stopped")
    
    def run_backup_now(self) -> dict:
        """Run backup immediately"""
        print("Running immediate backup...")
        return self.backup_manager.create_backup()
    
    def cleanup_old_backups(self) -> dict:
        """Clean up old backups"""
        print("Cleaning up old backups...")
        return self.backup_manager.cleanup_old_backups()
    
    def get_next_backup_time(self) -> Optional[datetime]:
        """Get the next scheduled backup time"""
        jobs = schedule.get_jobs()
        if jobs:
            return jobs[0].next_run
        return None
    
    def get_scheduler_status(self) -> dict:
        """Get scheduler status information"""
        return {
            "running": self.running,
            "schedule": self.schedule_config,
            "next_backup": self.get_next_backup_time(),
            "backup_status": self.backup_manager.get_backup_status()
        }
    
    def _schedule_backup_job(self) -> None:
        """Schedule the backup job based on cron expression"""
        # Parse cron expression (basic implementation)
        # Format: "minute hour day month weekday"
        # Example: "0 2 * * *" = daily at 2 AM
        
        parts = self.schedule_config.split()
        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression: {self.schedule_config}")
        
        minute, hour, day, month, weekday = parts
        
        # Schedule based on the expression
        if minute != "*" and hour != "*":
            # Specific time
            schedule.every().day.at(f"{hour.zfill(2)}:{minute.zfill(2)}").do(self._backup_job)
        elif hour != "*":
            # Specific hour
            schedule.every().day.at(f"{hour.zfill(2)}:00").do(self._backup_job)
        elif weekday != "*":
            # Specific day of week
            weekday_map = {
                "0": schedule.every().sunday,
                "1": schedule.every().monday,
                "2": schedule.every().tuesday,
                "3": schedule.every().wednesday,
                "4": schedule.every().thursday,
                "5": schedule.every().friday,
                "6": schedule.every().saturday
            }
            if weekday in weekday_map:
                weekday_map[weekday].at("02:00").do(self._backup_job)
            else:
                # Default to daily
                schedule.every().day.at("02:00").do(self._backup_job)
        else:
            # Default to daily at 2 AM
            schedule.every().day.at("02:00").do(self._backup_job)
    
    def _backup_job(self) -> None:
        """The actual backup job that gets scheduled"""
        try:
            print(f"Starting scheduled backup at {datetime.now()}")
            result = self.backup_manager.create_backup()
            
            if result["success"]:
                print(f"Scheduled backup completed successfully: {result['backup_name']}")
            else:
                print(f"Scheduled backup failed: {result.get('error', 'Unknown error')}")
            
            # Clean up old backups after successful backup
            if result["success"]:
                cleanup_result = self.backup_manager.cleanup_old_backups()
                if cleanup_result["success"]:
                    print(f"Cleaned up {cleanup_result['deleted_count']} old backups")
                else:
                    print(f"Failed to clean up old backups: {cleanup_result.get('error', 'Unknown error')}")
                    
        except Exception as e:
            print(f"Error in scheduled backup job: {e}")
    
    def _run_scheduler(self) -> None:
        """Run the scheduler loop"""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                print(f"Error in scheduler loop: {e}")
                time.sleep(60)


def create_backup_scheduler(config: BackupConfig) -> BackupScheduler:
    """Factory function to create a backup scheduler"""
    backup_manager = BackupManager(config)
    return BackupScheduler(backup_manager)
