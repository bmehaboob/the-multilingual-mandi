"""Audio storage service for managing audio files

This service handles:
- Storing audio files temporarily
- Tracking audio file metadata
- Providing file paths for cleanup
"""
import os
import uuid
from pathlib import Path
from typing import Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AudioStorageService:
    """Service for managing audio file storage"""
    
    def __init__(self, storage_path: str = "audio_storage"):
        """
        Initialize audio storage service
        
        Args:
            storage_path: Base directory for audio storage
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Audio storage initialized at: {self.storage_path.absolute()}")
    
    def save_audio(
        self,
        audio_data: bytes,
        message_id: uuid.UUID,
        file_extension: str = "wav"
    ) -> str:
        """
        Save audio data to storage
        
        Args:
            audio_data: Raw audio bytes
            message_id: Message ID for tracking
            file_extension: File extension (default: wav)
        
        Returns:
            File path relative to storage root
        """
        # Create filename based on message ID
        filename = f"{message_id}.{file_extension}"
        file_path = self.storage_path / filename
        
        try:
            # Write audio data to file
            with open(file_path, "wb") as f:
                f.write(audio_data)
            
            logger.info(f"Saved audio file: {filename}")
            return str(file_path)
        
        except Exception as e:
            logger.error(f"Error saving audio file {filename}: {e}")
            raise
    
    def delete_audio(self, file_path: str) -> bool:
        """
        Delete audio file from storage
        
        Args:
            file_path: Path to audio file
        
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                logger.info(f"Deleted audio file: {file_path}")
                return True
            else:
                logger.warning(f"Audio file not found: {file_path}")
                return False
        
        except Exception as e:
            logger.error(f"Error deleting audio file {file_path}: {e}")
            return False
    
    def get_audio(self, file_path: str) -> Optional[bytes]:
        """
        Retrieve audio data from storage
        
        Args:
            file_path: Path to audio file
        
        Returns:
            Audio data as bytes, or None if not found
        """
        try:
            path = Path(file_path)
            if path.exists():
                with open(path, "rb") as f:
                    return f.read()
            else:
                logger.warning(f"Audio file not found: {file_path}")
                return None
        
        except Exception as e:
            logger.error(f"Error reading audio file {file_path}: {e}")
            return None
    
    def list_audio_files(self) -> List[Path]:
        """
        List all audio files in storage
        
        Returns:
            List of audio file paths
        """
        try:
            # Get all files in storage directory
            audio_files = [
                f for f in self.storage_path.iterdir()
                if f.is_file() and f.suffix in ['.wav', '.mp3', '.ogg', '.opus']
            ]
            return audio_files
        
        except Exception as e:
            logger.error(f"Error listing audio files: {e}")
            return []
    
    def get_file_age(self, file_path: Path) -> float:
        """
        Get age of file in hours
        
        Args:
            file_path: Path to file
        
        Returns:
            Age in hours
        """
        try:
            # Get file modification time
            mtime = file_path.stat().st_mtime
            age_seconds = datetime.now().timestamp() - mtime
            age_hours = age_seconds / 3600
            return age_hours
        
        except Exception as e:
            logger.error(f"Error getting file age for {file_path}: {e}")
            return 0.0
    
    def get_storage_stats(self) -> dict:
        """
        Get storage statistics
        
        Returns:
            Dictionary with storage stats
        """
        try:
            audio_files = self.list_audio_files()
            total_size = sum(f.stat().st_size for f in audio_files)
            
            return {
                "total_files": len(audio_files),
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "storage_path": str(self.storage_path.absolute())
            }
        
        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            return {
                "total_files": 0,
                "total_size_bytes": 0,
                "total_size_mb": 0.0,
                "storage_path": str(self.storage_path.absolute())
            }
