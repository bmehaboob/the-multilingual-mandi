"""Audio cleanup API endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.services.audio_storage.audio_cleanup_scheduler import get_scheduler
from app.services.audio_storage import AudioStorageService
from app.core.config import settings

router = APIRouter(prefix="/audio-cleanup", tags=["audio-cleanup"])


@router.post("/run", response_model=Dict)
async def run_cleanup_now(
    current_user: User = Depends(get_current_user)
):
    """
    Manually trigger audio cleanup job
    
    Requires authentication. Runs the cleanup job immediately.
    """
    scheduler = get_scheduler()
    
    if not scheduler:
        raise HTTPException(
            status_code=500,
            detail="Audio cleanup scheduler not initialized"
        )
    
    try:
        stats = await scheduler.run_now()
        return {
            "success": True,
            "message": "Cleanup job completed",
            "stats": stats
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error running cleanup job: {str(e)}"
        )


@router.get("/status", response_model=Dict)
async def get_cleanup_status(
    current_user: User = Depends(get_current_user)
):
    """
    Get audio cleanup scheduler status
    
    Requires authentication. Returns scheduler configuration and status.
    """
    scheduler = get_scheduler()
    
    if not scheduler:
        raise HTTPException(
            status_code=500,
            detail="Audio cleanup scheduler not initialized"
        )
    
    # Get storage statistics
    storage_service = AudioStorageService(storage_path=settings.AUDIO_STORAGE_PATH)
    storage_stats = storage_service.get_storage_stats()
    
    return {
        "scheduler_running": scheduler.is_running,
        "retention_hours": scheduler.cleanup_job.retention_hours,
        "cleanup_interval_hours": scheduler.cleanup_interval_hours,
        "storage": storage_stats
    }


@router.get("/storage-stats", response_model=Dict)
async def get_storage_stats(
    current_user: User = Depends(get_current_user)
):
    """
    Get audio storage statistics
    
    Requires authentication. Returns information about audio files in storage.
    """
    storage_service = AudioStorageService(storage_path=settings.AUDIO_STORAGE_PATH)
    stats = storage_service.get_storage_stats()
    
    return {
        "success": True,
        "stats": stats
    }
