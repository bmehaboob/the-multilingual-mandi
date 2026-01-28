"""Tests for audio cleanup job"""
import pytest
import uuid
import tempfile
import shutil
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.sql import func

# Create a minimal Base for testing
TestBase = declarative_base()


class TestUser(TestBase):
    """Minimal User model for testing"""
    __tablename__ = "users"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone_number = Column(String(20), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    primary_language = Column(String(10), nullable=False)


class TestConversation(TestBase):
    """Minimal Conversation model for testing"""
    __tablename__ = "conversations"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(String(20), default="active", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class TestMessage(TestBase):
    """Minimal Message model for testing"""
    __tablename__ = "messages"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(PGUUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    sender_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    original_text = Column(Text, nullable=False)
    original_language = Column(String(10), nullable=False)
    audio_url = Column(String(512), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)


from app.services.audio_storage.audio_storage_service import AudioStorageService
from app.services.audio_storage.audio_cleanup_job import AudioCleanupJob


@pytest.fixture
def temp_storage_dir():
    """Create a temporary storage directory for testing"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def test_db():
    """Create a test database"""
    engine = create_engine("sqlite:///:memory:")
    TestBase.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture
def storage_service(temp_storage_dir):
    """Create an audio storage service instance"""
    return AudioStorageService(storage_path=temp_storage_dir)


@pytest.fixture
def cleanup_job(storage_service):
    """Create an audio cleanup job instance"""
    return AudioCleanupJob(storage_service, retention_hours=24)


@pytest.fixture
def test_user(test_db):
    """Create a test user"""
    user = TestUser(
        id=uuid.uuid4(),
        phone_number="+919876543210",
        name="Test User",
        primary_language="hi"
    )
    test_db.add(user)
    test_db.commit()
    return user


@pytest.fixture
def test_conversation(test_db, test_user):
    """Create a test conversation"""
    conversation = TestConversation(
        id=uuid.uuid4(),
        status="active"
    )
    test_db.add(conversation)
    test_db.commit()
    return conversation


class TestAudioCleanupJob:
    """Test suite for AudioCleanupJob"""
    
    def test_initialization(self, storage_service):
        """Test that cleanup job initializes correctly"""
        job = AudioCleanupJob(storage_service, retention_hours=24)
        
        assert job.storage_service == storage_service
        assert job.retention_hours == 24
    
    def test_cleanup_old_audio_no_messages(self, cleanup_job, test_db):
        """Test cleanup when there are no messages"""
        stats = cleanup_job.cleanup_old_audio(test_db)
        
        assert stats["messages_checked"] == 0
        assert stats["files_deleted"] == 0
        assert stats["database_updated"] == 0
    
    def test_cleanup_old_audio_with_old_message(
        self,
        cleanup_job,
        storage_service,
        test_db,
        test_user,
        test_conversation
    ):
        """Test cleanup of old audio files"""
        # Create an old message with audio
        message_id = uuid.uuid4()
        audio_data = b"old audio data"
        
        # Save audio file
        file_path = storage_service.save_audio(audio_data, message_id, "wav")
        
        # Create message with timestamp 25 hours ago (older than retention)
        old_timestamp = datetime.utcnow() - timedelta(hours=25)
        message = TestMessage(
            id=message_id,
            conversation_id=test_conversation.id,
            sender_id=test_user.id,
            original_text="Test message",
            original_language="hi",
            audio_url=file_path,
            timestamp=old_timestamp
        )
        test_db.add(message)
        test_db.commit()
        
        # Run cleanup
        stats = cleanup_job.cleanup_old_audio(test_db)
        
        # Verify cleanup
        assert stats["messages_checked"] == 1
        assert stats["files_deleted"] == 1
        assert stats["database_updated"] == 1
        
        # Verify message audio_url is cleared
        test_db.refresh(message)
        assert message.audio_url is None
    
    def test_cleanup_old_audio_with_recent_message(
        self,
        cleanup_job,
        storage_service,
        test_db,
        test_user,
        test_conversation
    ):
        """Test that recent audio files are not deleted"""
        # Create a recent message with audio
        message_id = uuid.uuid4()
        audio_data = b"recent audio data"
        
        # Save audio file
        file_path = storage_service.save_audio(audio_data, message_id, "wav")
        
        # Create message with recent timestamp (1 hour ago)
        recent_timestamp = datetime.utcnow() - timedelta(hours=1)
        message = TestMessage(
            id=message_id,
            conversation_id=test_conversation.id,
            sender_id=test_user.id,
            original_text="Recent message",
            original_language="hi",
            audio_url=file_path,
            timestamp=recent_timestamp
        )
        test_db.add(message)
        test_db.commit()
        
        # Run cleanup
        stats = cleanup_job.cleanup_old_audio(test_db)
        
        # Verify no cleanup occurred
        assert stats["messages_checked"] == 0
        assert stats["files_deleted"] == 0
        
        # Verify message audio_url is still present
        test_db.refresh(message)
        assert message.audio_url == file_path
    
    def test_cleanup_old_audio_mixed_messages(
        self,
        cleanup_job,
        storage_service,
        test_db,
        test_user,
        test_conversation
    ):
        """Test cleanup with mix of old and recent messages"""
        # Create old message
        old_message_id = uuid.uuid4()
        old_audio_data = b"old audio"
        old_file_path = storage_service.save_audio(old_audio_data, old_message_id, "wav")
        old_timestamp = datetime.utcnow() - timedelta(hours=25)
        
        old_message = TestMessage(
            id=old_message_id,
            conversation_id=test_conversation.id,
            sender_id=test_user.id,
            original_text="Old message",
            original_language="hi",
            audio_url=old_file_path,
            timestamp=old_timestamp
        )
        test_db.add(old_message)
        
        # Create recent message
        recent_message_id = uuid.uuid4()
        recent_audio_data = b"recent audio"
        recent_file_path = storage_service.save_audio(recent_audio_data, recent_message_id, "wav")
        recent_timestamp = datetime.utcnow() - timedelta(hours=1)
        
        recent_message = TestMessage(
            id=recent_message_id,
            conversation_id=test_conversation.id,
            sender_id=test_user.id,
            original_text="Recent message",
            original_language="hi",
            audio_url=recent_file_path,
            timestamp=recent_timestamp
        )
        test_db.add(recent_message)
        test_db.commit()
        
        # Run cleanup
        stats = cleanup_job.cleanup_old_audio(test_db)
        
        # Verify only old message was cleaned up
        assert stats["messages_checked"] == 1
        assert stats["files_deleted"] == 1
        assert stats["database_updated"] == 1
        
        # Verify old message audio_url is cleared
        test_db.refresh(old_message)
        assert old_message.audio_url is None
        
        # Verify recent message audio_url is still present
        test_db.refresh(recent_message)
        assert recent_message.audio_url == recent_file_path
    
    def test_cleanup_old_audio_file_not_found(
        self,
        cleanup_job,
        test_db,
        test_user,
        test_conversation
    ):
        """Test cleanup when audio file doesn't exist"""
        # Create message with non-existent audio file
        message_id = uuid.uuid4()
        fake_file_path = "/fake/path/audio.wav"
        old_timestamp = datetime.utcnow() - timedelta(hours=25)
        
        message = TestMessage(
            id=message_id,
            conversation_id=test_conversation.id,
            sender_id=test_user.id,
            original_text="Message with missing audio",
            original_language="hi",
            audio_url=fake_file_path,
            timestamp=old_timestamp
        )
        test_db.add(message)
        test_db.commit()
        
        # Run cleanup
        stats = cleanup_job.cleanup_old_audio(test_db)
        
        # Verify cleanup attempted
        assert stats["messages_checked"] == 1
        assert stats["files_not_found"] == 1
        assert stats["database_updated"] == 1
        
        # Verify message audio_url is still cleared
        test_db.refresh(message)
        assert message.audio_url is None
    
    def test_cleanup_orphaned_files(
        self,
        cleanup_job,
        storage_service,
        test_db
    ):
        """Test cleanup of orphaned audio files"""
        # Create audio file without database reference
        message_id = uuid.uuid4()
        audio_data = b"orphaned audio"
        file_path = storage_service.save_audio(audio_data, message_id, "wav")
        
        # Make file appear old by modifying its timestamp
        import os
        import time
        old_time = time.time() - (25 * 3600)  # 25 hours ago
        os.utime(file_path, (old_time, old_time))
        
        # Run orphaned file cleanup
        stats = cleanup_job.cleanup_orphaned_files(test_db)
        
        # Verify orphaned file was deleted
        assert stats["files_checked"] == 1
        assert stats["orphaned_files_deleted"] == 1
    
    def test_cleanup_orphaned_files_recent(
        self,
        cleanup_job,
        storage_service,
        test_db
    ):
        """Test that recent orphaned files are not deleted"""
        # Create recent audio file without database reference
        message_id = uuid.uuid4()
        audio_data = b"recent orphaned audio"
        file_path = storage_service.save_audio(audio_data, message_id, "wav")
        
        # Run orphaned file cleanup
        stats = cleanup_job.cleanup_orphaned_files(test_db)
        
        # Verify recent orphaned file was not deleted
        assert stats["files_checked"] == 1
        assert stats["orphaned_files_deleted"] == 0
    
    def test_run_full_cleanup(
        self,
        cleanup_job,
        storage_service,
        test_db,
        test_user,
        test_conversation
    ):
        """Test full cleanup process"""
        # Create old message with audio
        message_id = uuid.uuid4()
        audio_data = b"old audio"
        file_path = storage_service.save_audio(audio_data, message_id, "wav")
        old_timestamp = datetime.utcnow() - timedelta(hours=25)
        
        message = TestMessage(
            id=message_id,
            conversation_id=test_conversation.id,
            sender_id=test_user.id,
            original_text="Old message",
            original_language="hi",
            audio_url=file_path,
            timestamp=old_timestamp
        )
        test_db.add(message)
        test_db.commit()
        
        # Run full cleanup
        stats = cleanup_job.run_full_cleanup(test_db)
        
        # Verify combined statistics
        assert "old_audio_cleanup" in stats
        assert "orphaned_file_cleanup" in stats
        assert stats["total_files_deleted"] >= 1
        assert "timestamp" in stats
        assert stats["retention_hours"] == 24
    
    def test_custom_retention_hours(self, storage_service):
        """Test cleanup job with custom retention hours"""
        job = AudioCleanupJob(storage_service, retention_hours=48)
        
        assert job.retention_hours == 48
