"""Tests for audio storage service"""
import pytest
import uuid
import tempfile
import shutil
from pathlib import Path
from app.services.audio_storage.audio_storage_service import AudioStorageService


@pytest.fixture
def temp_storage_dir():
    """Create a temporary storage directory for testing"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup after test
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def storage_service(temp_storage_dir):
    """Create an audio storage service instance"""
    return AudioStorageService(storage_path=temp_storage_dir)


class TestAudioStorageService:
    """Test suite for AudioStorageService"""
    
    def test_initialization(self, temp_storage_dir):
        """Test that storage service initializes correctly"""
        service = AudioStorageService(storage_path=temp_storage_dir)
        
        assert service.storage_path == Path(temp_storage_dir)
        assert service.storage_path.exists()
        assert service.storage_path.is_dir()
    
    def test_save_audio(self, storage_service):
        """Test saving audio data"""
        message_id = uuid.uuid4()
        audio_data = b"fake audio data"
        
        file_path = storage_service.save_audio(audio_data, message_id, "wav")
        
        assert file_path is not None
        assert Path(file_path).exists()
        assert str(message_id) in file_path
    
    def test_save_and_retrieve_audio(self, storage_service):
        """Test saving and retrieving audio data"""
        message_id = uuid.uuid4()
        audio_data = b"test audio content"
        
        # Save audio
        file_path = storage_service.save_audio(audio_data, message_id, "wav")
        
        # Retrieve audio
        retrieved_data = storage_service.get_audio(file_path)
        
        assert retrieved_data == audio_data
    
    def test_delete_audio(self, storage_service):
        """Test deleting audio file"""
        message_id = uuid.uuid4()
        audio_data = b"audio to delete"
        
        # Save audio
        file_path = storage_service.save_audio(audio_data, message_id, "wav")
        assert Path(file_path).exists()
        
        # Delete audio
        result = storage_service.delete_audio(file_path)
        
        assert result is True
        assert not Path(file_path).exists()
    
    def test_delete_nonexistent_audio(self, storage_service):
        """Test deleting a file that doesn't exist"""
        fake_path = str(storage_service.storage_path / "nonexistent.wav")
        
        result = storage_service.delete_audio(fake_path)
        
        assert result is False
    
    def test_get_nonexistent_audio(self, storage_service):
        """Test retrieving audio that doesn't exist"""
        fake_path = str(storage_service.storage_path / "nonexistent.wav")
        
        result = storage_service.get_audio(fake_path)
        
        assert result is None
    
    def test_list_audio_files(self, storage_service):
        """Test listing audio files"""
        # Create multiple audio files
        message_ids = [uuid.uuid4() for _ in range(3)]
        audio_data = b"test audio"
        
        for msg_id in message_ids:
            storage_service.save_audio(audio_data, msg_id, "wav")
        
        # List files
        files = storage_service.list_audio_files()
        
        assert len(files) == 3
        assert all(f.suffix == ".wav" for f in files)
    
    def test_list_audio_files_multiple_formats(self, storage_service):
        """Test listing audio files with different formats"""
        message_id1 = uuid.uuid4()
        message_id2 = uuid.uuid4()
        message_id3 = uuid.uuid4()
        audio_data = b"test audio"
        
        storage_service.save_audio(audio_data, message_id1, "wav")
        storage_service.save_audio(audio_data, message_id2, "mp3")
        storage_service.save_audio(audio_data, message_id3, "ogg")
        
        files = storage_service.list_audio_files()
        
        assert len(files) == 3
        extensions = {f.suffix for f in files}
        assert extensions == {".wav", ".mp3", ".ogg"}
    
    def test_get_file_age(self, storage_service):
        """Test getting file age"""
        message_id = uuid.uuid4()
        audio_data = b"test audio"
        
        file_path = storage_service.save_audio(audio_data, message_id, "wav")
        
        age_hours = storage_service.get_file_age(Path(file_path))
        
        # File should be very new (less than 1 hour old)
        assert age_hours >= 0
        assert age_hours < 1
    
    def test_get_storage_stats(self, storage_service):
        """Test getting storage statistics"""
        # Create some audio files
        for i in range(3):
            message_id = uuid.uuid4()
            audio_data = b"x" * 1000  # 1KB of data
            storage_service.save_audio(audio_data, message_id, "wav")
        
        stats = storage_service.get_storage_stats()
        
        assert stats["total_files"] == 3
        assert stats["total_size_bytes"] >= 3000  # At least 3KB
        assert stats["total_size_mb"] >= 0  # Should be at least 0
        assert "storage_path" in stats
    
    def test_get_storage_stats_empty(self, storage_service):
        """Test getting storage statistics when empty"""
        stats = storage_service.get_storage_stats()
        
        assert stats["total_files"] == 0
        assert stats["total_size_bytes"] == 0
        assert stats["total_size_mb"] == 0.0
    
    def test_save_audio_with_different_extensions(self, storage_service):
        """Test saving audio with different file extensions"""
        message_id = uuid.uuid4()
        audio_data = b"test audio"
        
        extensions = ["wav", "mp3", "ogg", "opus"]
        
        for ext in extensions:
            file_path = storage_service.save_audio(audio_data, message_id, ext)
            assert file_path.endswith(f".{ext}")
            assert Path(file_path).exists()
