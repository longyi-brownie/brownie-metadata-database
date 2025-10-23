#!/usr/bin/env python3
"""Backup scheduler for automated backup execution."""

import os
import signal
import sys
import time
from datetime import datetime
from typing import Optional

import structlog

try:
    from croniter import croniter

    CRONITER_AVAILABLE = True
except ImportError:
    CRONITER_AVAILABLE = False

from brownie_metadata_db.backup.config import BackupConfig
from brownie_metadata_db.backup.manager import BackupManager

logger = structlog.get_logger(__name__)


class BackupScheduler:
    """Scheduler for automated backup execution."""

    def __init__(self, config: BackupConfig):
        self.config = config
        self.manager = BackupManager(config)
        self.logger = logger.bind(scheduler="BackupScheduler")
        self.running = False

        # Initialize cron iterator
        if CRONITER_AVAILABLE:
            self.cron_iter = croniter(config.schedule, datetime.now())
            self.logger.info(
                "Using croniter for schedule parsing", schedule=config.schedule
            )
        else:
            self.schedule_parts = self._parse_cron_schedule(config.schedule)
            self.logger.warning(
                "croniter not available, using simple schedule parsing",
                schedule=config.schedule,
            )

    def _parse_cron_schedule(self, schedule: str) -> dict:
        """Parse cron schedule into parts."""
        parts = schedule.split()
        if len(parts) != 5:
            raise ValueError(f"Invalid cron schedule format: {schedule}")

        return {
            "minute": parts[0],
            "hour": parts[1],
            "day": parts[2],
            "month": parts[3],
            "weekday": parts[4],
        }

    def _should_run_backup(self, now: datetime) -> bool:
        """Check if backup should run at the current time."""
        if CRONITER_AVAILABLE:
            # Use croniter for accurate cron parsing
            return self.cron_iter.get_next(datetime) <= now
        else:
            # Simple implementation - check if current time matches schedule
            if (
                self.schedule_parts["minute"] != "*"
                and str(now.minute) != self.schedule_parts["minute"]
            ):
                return False

            if (
                self.schedule_parts["hour"] != "*"
                and str(now.hour) != self.schedule_parts["hour"]
            ):
                return False

            # For simplicity, assume daily backups (day=*, month=*, weekday=*)
            return True

    def run_backup(self) -> bool:
        """Run a single backup."""
        try:
            backup_name = f"backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            self.logger.info("Starting scheduled backup", backup_name=backup_name)

            result = self.manager.create_backup(
                backup_name, verify=self.config.verify_backup
            )

            self.logger.info(
                "Scheduled backup completed successfully",
                backup_name=backup_name,
                size=result.get("size"),
                duration=result.get("duration"),
            )
            return True

        except Exception as e:
            self.logger.error("Scheduled backup failed", error=str(e))
            return False

    def run_cleanup(self) -> bool:
        """Run cleanup of old backups."""
        try:
            self.logger.info("Starting scheduled cleanup")
            deleted_count = self.manager.cleanup_old_backups()
            self.logger.info("Scheduled cleanup completed", deleted_count=deleted_count)
            return True

        except Exception as e:
            self.logger.error("Scheduled cleanup failed", error=str(e))
            return False

    def start(self) -> None:
        """Start the scheduler."""
        self.running = True
        self.logger.info("Starting backup scheduler", schedule=self.config.schedule)

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        last_backup_hour = -1
        last_cleanup_day = -1

        while self.running:
            try:
                now = datetime.now()

                # Check if we should run backup
                if self._should_run_backup(now):
                    # Only run backup once per hour to avoid duplicates
                    if now.hour != last_backup_hour:
                        self.run_backup()
                        last_backup_hour = now.hour

                # Run cleanup once per day
                if now.day != last_cleanup_day:
                    self.run_cleanup()
                    last_cleanup_day = now.day

                # Sleep for 1 minute before checking again
                time.sleep(60)

            except KeyboardInterrupt:
                self.logger.info("Received interrupt signal, shutting down")
                break
            except Exception as e:
                self.logger.error("Scheduler error", error=str(e))
                time.sleep(60)  # Wait before retrying

        self.logger.info("Backup scheduler stopped")

    def stop(self) -> None:
        """Stop the scheduler."""
        self.running = False

    def _signal_handler(self, signum: int, frame) -> None:
        """Handle shutdown signals."""
        self.logger.info("Received signal", signal=signum)
        self.stop()


def main() -> int:
    """Main entry point for the scheduler."""
    # Configure centralized logging
    from ..logging.config import LoggingConfig, configure_logging

    logging_config = LoggingConfig()
    configure_logging(logging_config)

    try:
        backup_config = BackupConfig()
        scheduler = BackupScheduler(backup_config)
        scheduler.start()
        return 0
    except Exception as e:
        logger.error("Scheduler failed to start", error=str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())
