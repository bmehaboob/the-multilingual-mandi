"""Property-based tests for audio data deletion policy

**Property 47: Audio Data Deletion After Processing**
For any voice message processed by the system, the raw audio should be 
deleted within 24 hours after processing is complete.

**Validates: Requirements 15.2**
"""
import pytest
import uuid
import tempfile
import shutil
from datetime import datetime, timedelta
from hypothesis import given, strategies as st, settings, assume
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.conversation import Message, Conversation, ConversationStatus
from app.models.user import User
from app.core.database import Base
from app.services.audio_storage.audio_storage_service import AudioStorageService
from app.services.audio_storage.audio_cleanup_job import AudioCleanupJob


@pytest.fixture(scope="function")
def temp_storage_dir():
    """Create a temporary storage directory for testing"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="function")
def test_db():
    """Create a test database"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture(scope="function")
def storage_service(temp_storage_dir):
    """Create an audio storage service instance"""
    return AudioStorageService(storage_path=temp_storage_dir)


@pytest.fixture(scope="function")
def test_user(test_db):
    """Create a test user"""
    user = User(
        id=uuid.uuid4(),
        phone_number="+919876543210",
        name="Test User",
        primary_language="hi"
    )
    test_db.add(user)
    test_db.commit()
    return user


@pytest.fixture(scope="function")
def test_conversation(test_db, test_user):
    """Create a test conversation"""
    conversation = Conversation(
        id=uuid.uuid4(),
        participants=[test_user.id],
        status=ConversationStatus.ACTIVE
    )
    test_db.add(conversation)
    test_db.commit()
    return conversation


class TestAudioDeletionProperty:
    """Property-based tests for audio deletion policy"""
    
    @settings(max_examples=50, deadline=None)
    @given(
        hours_old=st.floats(min_value=24.1, max_value=168.0),  # 24h to 1 week
        audio_size=st.integers(min_value=100, max_value=10000)
    )
    def test_property_audio_deleted_after_24_hours(
        self,
        hours_old,
        audio_size,
        storage_service,
        test_db,
        test_user,
        test_conversation
    ):
        """
        **Property 47: Audio Data Deletion After Processing**
        
        For any voice message older than 24 hours, the cleanup job should:
        1. Delete the audio file from storage
        2. Clear the audio_url from the database
        
        **Validates: Requirements 15.2**
        """
        # Create message with audio older than 24 hours
        message_id = uuid.uuid4()
        audio_data = b"x" * audio_size
        
        # Save audio file
        file_path = storage_service.save_audio(audio_data, message_id, "wav")
        
        # Create message with old timestamp
        old_timestamp = datetime.utcnow() - timedelta(hours=hours_old)
        message = Message(
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
        
        # Run cleanup job
        cleanup_job = AudioCleanupJob(storage_service, retention_hours=24)
        stats = cleanup_job.cleanup_old_audio(test_db)
        
        # Property assertions
        # 1. Audio file should be deleted
        assert stats["files_deleted"] >= 1, \
            f"Audio file older than 24h should be deleted (age: {hours_old}h)"
        
        # 2. Database should be updated
        assert stats["database_updated"] >= 1, \
            "Database should be updated to clear audio_url"
        
        # 3. Message audio_url should be None
        test_db.refresh(message)
        assert message.audio_url is None, \
            "Message audio_url should be cleared after cleanup"
    
    @settings(max_examples=50, deadline=None)
    @given(
        hours_old=st.floats(min_value=0.0, max_value=23.9),  # Less than 24h
        audio_size=st.integers(min_value=100, max_value=10000)
    )
    def test_property_audio_retained_within_24_hours(
        self,
        hours_old,
        audio_size,
        storage_service,
        test_db,
        test_user,
        test_conversation
    ):
        """
        **Property 47 (Inverse): Audio Data Retention Within 24 Hours**
        
        For any voice message younger than 24 hours, the cleanup job should:
        1. NOT delete the audio file
        2. NOT clear the audio_url from the database
        
        **Validates: Requirements 15.2**
        """
        # Create message with audio younger than 24 hours
        message_id = uuid.uuid4()
        audio_data = b"x" * audio_size
        
        # Save audio file
        file_path = storage_service.save_audio(audio_data, message_id, "wav")
        
        # Create message with recent timestamp
        recent_timestamp = datetime.utcnow() - timedelta(hours=hours_old)
        message = Message(
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
        
        # Run cleanup job
        cleanup_job = AudioCleanupJob(storage_service, retention_hours=24)
        stats = cleanup_job.cleanup_old_audio(test_db)
        
        # Property assertions
        # 1. No files should be deleted
        assert stats["files_deleted"] == 0, \
            f"Audio file younger than 24h should NOT be deleted (age: {hours_old}h)"
        
        # 2. Message audio_url should still be present
        test_db.refresh(message)
        assert message.audio_url == file_path, \
            "Message audio_url should be retained for recent messages"
    
    @settings(max_examples=30, deadline=None)
    @given(
        num_messages=st.integers(min_value=1, max_value=10),
        retention_hours=st.integers(min_value=12, max_value=48)
    )
    def test_property_cleanup_respects_retention_policy(
        self,
        num_messages,
        retention_hours,
        storage_service,
        test_db,
        test_user,
        test_conversation
    ):
        """
        **Property 47: Configurable Retention Policy**
        
        For any retention period, the cleanup job should only delete
        audio files older than the specified retention period.
        
        **Validates: Requirements 15.2**
        """
        messages = []
        
        # Create messages with varying ages
        for i in range(num_messages):
            message_id = uuid.uuid4()
            audio_data = b"test audio"
            file_path = storage_service.save_audio(audio_data, message_id, "wav")
            
            # Create messages with ages ranging from 0 to 2x retention period
            age_hours = (i / num_messages) * (retention_hours * 2)
            timestamp = datetime.utcnow() - timedelta(hours=age_hours)
            
            message = Message(
                id=message_id,
                conversation_id=test_conversation.id,
                sender_id=test_user.id,
                original_text=f"Message {i}",
                original_language="hi",
                audio_url=file_path,
                timestamp=timestamp
            )
            test_db.add(message)
            messages.append((message, age_hours))
        
        test_db.commit()
        
        # Run cleanup with custom retention period
        cleanup_job = AudioCleanupJob(storage_service, retention_hours=retention_hours)
        stats = cleanup_job.cleanup_old_audio(test_db)
        
        # Count how many messages should be deleted
        expected_deletions = sum(1 for _, age in messages if age > retention_hours)
        
        # Property assertion
        assert stats["files_deleted"] == expected_deletions, \
            f"Should delete exactly {expected_deletions} files older than {retention_hours}h"
        
        # Verify each message
        for message, age_hours in messages:
            test_db.refresh(message)
            if age_hours > retention_hours:
                assert message.audio_url is None, \
                    f"Message {age_hours:.1f}h old should have audio_url cleared"
            else:
                assert message.audio_url is not None, \
                    f"Message {age_hours:.1f}h old should retain audio_url"
    
    @settings(max_examples=30, deadline=None)
    @given(
        num_old_messages=st.integers(min_value=1, max_value=5),
        num_recent_messages=st.integers(min_value=1, max_value=5)
    )
    def test_property_selective_deletion(
        self,
        num_old_messages,
        num_recent_messages,
        storage_service,
        test_db,
        test_user,
        test_conversation
    ):
        """
        **Property 47: Selective Deletion**
        
        The cleanup job should only delete old audio files and leave
        recent audio files intact, regardless of the mix.
        
        **Validates: Requirements 15.2**
        """
        # Create old messages
        old_messages = []
        for i in range(num_old_messages):
            message_id = uuid.uuid4()
            audio_data = b"old audio"
            file_path = storage_service.save_audio(audio_data, message_id, "wav")
            
            old_timestamp = datetime.utcnow() - timedelta(hours=25 + i)
            message = Message(
                id=message_id,
                conversation_id=test_conversation.id,
                sender_id=test_user.id,
                original_text=f"Old message {i}",
                original_language="hi",
                audio_url=file_path,
                timestamp=old_timestamp
            )
            test_db.add(message)
            old_messages.append(message)
        
        # Create recent messages
        recent_messages = []
        for i in range(num_recent_messages):
            message_id = uuid.uuid4()
            audio_data = b"recent audio"
            file_path = storage_service.save_audio(audio_data, message_id, "wav")
            
            recent_timestamp = datetime.utcnow() - timedelta(hours=i)
            message = Message(
                id=message_id,
                conversation_id=test_conversation.id,
                sender_id=test_user.id,
                original_text=f"Recent message {i}",
                original_language="hi",
                audio_url=file_path,
                timestamp=recent_timestamp
            )
            test_db.add(message)
            recent_messages.append(message)
        
        test_db.commit()
        
        # Run cleanup
        cleanup_job = AudioCleanupJob(storage_service, retention_hours=24)
        stats = cleanup_job.cleanup_old_audio(test_db)
        
        # Property assertions
        # 1. Correct number of files deleted
        assert stats["files_deleted"] == num_old_messages, \
            f"Should delete exactly {num_old_messages} old files"
        
        # 2. All old messages should have audio_url cleared
        for message in old_messages:
            test_db.refresh(message)
            assert message.audio_url is None, \
                "Old message should have audio_url cleared"
        
        # 3. All recent messages should retain audio_url
        for message in recent_messages:
            test_db.refresh(message)
            assert message.audio_url is not None, \
                "Recent message should retain audio_url"
