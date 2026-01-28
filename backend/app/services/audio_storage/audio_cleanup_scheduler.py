"""Scheduler for automated audio cleanup job

This module provides a background scheduler that runs the audio cleanup job
at regular intervals to ensure compliance with the 24-hour deletion policy.
"""
import logging
import asyncio
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from .audio_cleanup_job import AudioCleanupJob
from .audio_storage_service import AudioStorageService

logger = logging.getLogger(__name__)


class AudioCleanupScheduler:
    """Scheduler for running audio cleanup job periodically"""
    
    def __init__(
        self,
        storage_service: AudioStorageService,
        retention_hours: int = 24,
        cleanup_interval_hours: int = 1
    ):
        """
        Initialize audio cleanup scheduler
        
        Args:
            storage_service: Audio storage service instance
            retention_hours: Hours to retain audio files (default: 24)
            cleanup_interval_hours: Hours between cleanup runs (default: 1)
        """
        self.cleanup_job = AudioCleanupJob(storage_service, retention_hours)
        self.cleanup_interval_hours = cleanup_interval_hours
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        
        logger.info(
            f"Audio cleanup scheduler initialized: "
            f"retention={retention_hours}h, interval={cleanup_interval_hours}h"
        )
    
    async def start(self):
        """Start the cleanup scheduler"""
        if self.is_running:
            logger.warning("Cleanup scheduler is already running")
            return
        
        self.is_running = True
        self._task = asyncio.create_task(self._run_scheduler())
        logger.info("Audio cleanup scheduler started")
    
    async def stop(self):
        """Stop the cleanup scheduler"""
        if not self.is_running:
            logger.warning("Cleanup scheduler is not running")
            return
        
        self.is_running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info("Audio cleanup scheduler stopped")
    
    async def _run_scheduler(self):
        """Internal method to run the scheduler loop"""
        logger.info("Cleanup scheduler loop started")
        
        while self.is_running:
            try:
                # Run cleanup job
                await self._run_cleanup()
                
                # Wait for next interval
                await asyncio.sleep(self.cleanup_interval_hours * 3600)
            
            except asyncio.CancelledError:
                logger.info("Cleanup scheduler cancelled")
                break
            
            except Exception as e:
                logger.error(f"Error in cleanup scheduler: {e}")
                # Wait a bit before retrying
                await asyncio.sleep(60)
    
    async def _run_cleanup(self):
        """Run the cleanup job"""
        logger.info("Running scheduled audio cleanup")
        
        db: Session = SessionLocal()
        try:
            stats = self.cleanup_job.run_full_cleanup(db)
            logger.info(f"Scheduled cleanup completed: {stats}")
        
        except Exception as e:
            logger.error(f"Error running cleanup job: {e}")
        
        finally:
            db.close()
    
    async def run_now(self) -> dict:
        """
        Run cleanup job immediately (manual trigger)
        
        Returns:
            Cleanup statistics
        """
        logger.info("Running manual audio cleanup")
        
        db: Session = SessionLocal()
        try:
            stats = self.cleanup_job.run_full_cleanup(db)
            logger.info(f"Manual cleanup completed: {stats}")
            return stats
        
        except Exception as e:
            logger.error(f"Error running manual cleanup: {e}")
            raise
        
        finally:
            db.close()


# Global scheduler instance
_scheduler: Optional[AudioCleanupScheduler] = None


def get_scheduler() -> Optional[AudioCleanupScheduler]:
    """Get the global scheduler instance"""
    return _scheduler


def initialize_scheduler(
    storage_service: AudioStorageService,
    retention_hours: int = 24,
    cleanup_interval_hours: int = 1
) -> AudioCleanupScheduler:
    """
    Initialize the global scheduler instance
    
    Args:
        storage_service: Audio storage service instance
        retention_hours: Hours to retain audio files (default: 24)
        cleanup_interval_hours: Hours between cleanup runs (default: 1)
    
    Returns:
        Initialized scheduler instance
    """
    global _scheduler
    
    if _scheduler is not None:
        logger.warning("Scheduler already initialized")
        return _scheduler
    
    _scheduler = AudioCleanupScheduler(
        storage_service,
        retention_hours,
        cleanup_interval_hours
    )
    
    return _scheduler
