"""
Backup API endpoints for FastAPI
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from .config import BackupConfig
from .manager import BackupManager
from .scheduler import BackupScheduler


# Pydantic models for API
class BackupCreateRequest(BaseModel):
    backup_name: Optional[str] = None


class BackupRestoreRequest(BaseModel):
    backup_name: str
    target_database: Optional[str] = None


class BackupResponse(BaseModel):
    success: bool
    message: str
    backup_name: Optional[str] = None
    error: Optional[str] = None


class BackupListResponse(BaseModel):
    success: bool
    backups: List[Dict[str, Any]]
    total: int


class BackupStatusResponse(BaseModel):
    success: bool
    status: Dict[str, Any]


# Global backup scheduler instance
backup_scheduler: Optional[BackupScheduler] = None


def create_backup_router(config: BackupConfig) -> APIRouter:
    """Create backup API router"""
    global backup_scheduler
    
    router = APIRouter(prefix="/backup", tags=["backup"])
    backup_manager = BackupManager(config)
    
    # Initialize scheduler if not already done
    if backup_scheduler is None:
        backup_scheduler = BackupScheduler(backup_manager)
        backup_scheduler.start()
    
    @router.get("/status", response_model=BackupStatusResponse)
    async def get_backup_status():
        """Get backup system status"""
        try:
            status = backup_scheduler.get_scheduler_status()
            return BackupStatusResponse(success=True, status=status)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/create", response_model=BackupResponse)
    async def create_backup(request: BackupCreateRequest, background_tasks: BackgroundTasks):
        """Create a new backup"""
        try:
            result = backup_manager.create_backup(request.backup_name)
            
            if result["success"]:
                return BackupResponse(
                    success=True,
                    message=f"Backup created successfully: {result['backup_name']}",
                    backup_name=result["backup_name"]
                )
            else:
                return BackupResponse(
                    success=False,
                    message="Backup creation failed",
                    error=result.get("error", "Unknown error")
                )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/restore", response_model=BackupResponse)
    async def restore_backup(request: BackupRestoreRequest):
        """Restore a backup"""
        try:
            result = backup_manager.restore_backup(
                request.backup_name, 
                request.target_database
            )
            
            if result["success"]:
                return BackupResponse(
                    success=True,
                    message=f"Backup restored successfully: {request.backup_name}"
                )
            else:
                return BackupResponse(
                    success=False,
                    message="Backup restore failed",
                    error=result.get("error", "Unknown error")
                )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/list", response_model=BackupListResponse)
    async def list_backups():
        """List available backups"""
        try:
            backups = backup_manager.list_backups()
            return BackupListResponse(
                success=True,
                backups=backups,
                total=len(backups)
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.delete("/{backup_name}", response_model=BackupResponse)
    async def delete_backup(backup_name: str):
        """Delete a backup"""
        try:
            result = backup_manager.delete_backup(backup_name)
            
            if result["success"]:
                return BackupResponse(
                    success=True,
                    message=result["message"]
                )
            else:
                return BackupResponse(
                    success=False,
                    message="Backup deletion failed",
                    error=result.get("error", "Unknown error")
                )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/cleanup", response_model=BackupResponse)
    async def cleanup_old_backups():
        """Clean up old backups"""
        try:
            result = backup_manager.cleanup_old_backups()
            
            if result["success"]:
                return BackupResponse(
                    success=True,
                    message=result["message"]
                )
            else:
                return BackupResponse(
                    success=False,
                    message="Backup cleanup failed",
                    error=result.get("error", "Unknown error")
                )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/run-now", response_model=BackupResponse)
    async def run_backup_now():
        """Run backup immediately"""
        try:
            result = backup_scheduler.run_backup_now()
            
            if result["success"]:
                return BackupResponse(
                    success=True,
                    message=f"Backup completed: {result['backup_name']}",
                    backup_name=result["backup_name"]
                )
            else:
                return BackupResponse(
                    success=False,
                    message="Immediate backup failed",
                    error=result.get("error", "Unknown error")
                )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/next-backup")
    async def get_next_backup_time():
        """Get next scheduled backup time"""
        try:
            next_backup = backup_scheduler.get_next_backup_time()
            return {
                "success": True,
                "next_backup": next_backup.isoformat() if next_backup else None
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    return router
