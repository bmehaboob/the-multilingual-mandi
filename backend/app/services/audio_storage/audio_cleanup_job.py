"""Audio cleanup job for deleting old audio files

This job implements the audio data deletion policy:
- Delete raw audio within 24 hours after processing
- Run as an automated background job
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_

logger = logging.getLogger(__name__)


class AudioCleanupJob:
    """Automated job for cleaning up old audio files"""
    
    def __init__(
        self,
        storage_service,
        retention_hours: int = 24
    ):
        """
        Initialize audio cleanup job
        
        Args:
            storage_service: Audio storage service instance
            retention_hours: Hours to retain audio files (default: 24)
        """
        self.storage_service = storage_service
        self.retention_hours = retention_hours
        logger.info(f"Audio cleanup job initialized with {retention_hours}h retention")
    
    def cleanup_old_audio(self, db: Session) -> Dict[str, int]:
        """
        Clean up audio files older than retention period
        
        This method:
        1. Finds messages with audio_url older than retention period
        2. Deletes the audio files from storage
        3. Updates the database to remove audio_url references
        
        Args:
            db: Database session
        
        Returns:
            Dictionary with cleanup statistics
        """
        from app.models.conversation import Message
        
        cutoff_time = datetime.utcnow() - timedelta(hours=self.retention_hours)
        
        logger.info(f"Starting audio cleanup for files older than {cutoff_time}")
        
        stats = {
            "messages_checked": 0,
            "files_deleted": 0,
            "files_not_found": 0,
            "database_updated": 0,
            "errors": 0
        }
        
        try:
            # Find messages with audio_url older than cutoff time
            messages_with_audio = db.query(Message).filter(
                and_(
                    Message.audio_url.isnot(None),
                    Message.timestamp < cutoff_time
                )
            ).all()
            
            stats["messages_checked"] = len(messages_with_audio)
            
            logger.info(f"Found {len(messages_with_audio)} messages with audio older than {self.retention_hours}h")
            
            for message in messages_with_audio:
                try:
                    # Delete audio file
                    if self.storage_service.delete_audio(message.audio_url):
                        stats["files_deleted"] += 1
                    else:
                        stats["files_not_found"] += 1
                    
                    # Update database to remove audio_url
                    message.audio_url = None
                    stats["database_updated"] += 1
                
                except Exception as e:
                    logger.error(f"Error cleaning up audio for message {message.id}: {e}")
                    stats["errors"] += 1
            
            # Commit database changes
            db.commit()
            
            logger.info(f"Audio cleanup completed: {stats}")
            
        except Exception as e:
            logger.error(f"Error during audio cleanup: {e}")
            db.rollback()
            stats["errors"] += 1
        
        return stats
    
    def cleanup_orphaned_files(self, db: Session) -> Dict[str, int]:
        """
        Clean up orphaned audio files (files without database references)
        
        This method finds audio files in storage that don't have corresponding
        database entries and deletes them.
        
        Args:
            db: Database session
        
        Returns:
            Dictionary with cleanup statistics
        """
        from app.models.conversation import Message
        
        logger.info("Starting orphaned audio file cleanup")
        
        stats = {
            "files_checked": 0,
            "orphaned_files_deleted": 0,
            "errors": 0
        }
        
        try:
            # Get all audio files from storage
            audio_files = self.storage_service.list_audio_files()
            stats["files_checked"] = len(audio_files)
            
            # Get all audio URLs from database
            db_audio_urls = set(
                msg.audio_url for msg in db.query(Message.audio_url).filter(
                    Message.audio_url.isnot(None)
                ).all()
            )
            
            # Find orphaned files
            for file_path in audio_files:
                file_path_str = str(file_path)
                
                # Check if file is referenced in database
                if file_path_str not in db_audio_urls:
                    # Check if file is old enough (older than retention period)
                    file_age_hours = self.storage_service.get_file_age(file_path)
                    
                    if file_age_hours > self.retention_hours:
                        try:
                            if self.storage_service.delete_audio(file_path_str):
                                stats["orphaned_files_deleted"] += 1
                                logger.info(f"Deleted orphaned file: {file_path_str}")
                        except Exception as e:
                            logger.error(f"Error deleting orphaned file {file_path_str}: {e}")
                            stats["errors"] += 1
            
            logger.info(f"Orphaned file cleanup completed: {stats}")
        
        except Exception as e:
            logger.error(f"Error during orphaned file cleanup: {e}")
            stats["errors"] += 1
        
        return stats
    
    def run_full_cleanup(self, db: Session) -> Dict[str, any]:
        """
        Run full cleanup process
        
        This includes:
        1. Cleanup of old audio files with database references
        2. Cleanup of orphaned files without database references
        
        Args:
            db: Database session
        
        Returns:
            Dictionary with combined cleanup statistics
        """
        logger.info("Starting full audio cleanup")
        
        # Run both cleanup operations
        old_audio_stats = self.cleanup_old_audio(db)
        orphaned_stats = self.cleanup_orphaned_files(db)
        
        # Combine statistics
        combined_stats = {
            "timestamp": datetime.utcnow().isoformat(),
            "retention_hours": self.retention_hours,
            "old_audio_cleanup": old_audio_stats,
            "orphaned_file_cleanup": orphaned_stats,
            "total_files_deleted": (
                old_audio_stats["files_deleted"] + 
                orphaned_stats["orphaned_files_deleted"]
            ),
            "total_errors": (
                old_audio_stats["errors"] + 
                orphaned_stats["errors"]
            )
        }
        
        logger.info(f"Full cleanup completed: {combined_stats}")
        
        return combined_stats
