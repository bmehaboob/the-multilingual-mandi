"""Unit tests for VoiceBiometricEnrollment service"""
import pytest
import numpy as np
from datetime import datetime
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.services.auth.voice_biometric_enrollment import VoiceBiometricEnrollment
from app.services.auth.speaker_recognition_model import SpeakerRecognitionModel
from app.services.auth.models import VoiceSample, EnrollmentResult


@pytest.fixture
def mock_speaker_model():
    """Create a mock speaker recognition model"""
    model = Mock(spec=SpeakerRecognitionModel)
    model.is_loaded = True
    model.embedding_dimension = 192
    
    # Mock embedding extraction to return normalized random embeddings
    def mock_extract_embedding(audio, sample_rate):
        embedding = np.random.randn(192).astype(np.float64)
        # Normalize
        embedding = embedding / np.linalg.norm(embedding)
        return embedding
    
    model.extract_embedding.side_effect = mock_extract_embedding
    
    # Mock audio validation to always pass
    model.validate_audio_quality.return_value = (True, None)
    
    # Mock average_embeddings
    def mock_average_embeddings(embeddings):
        avg = np.mean(embeddings, axis=0)
        return avg / np.linalg.norm(avg)
    
    model.average_embeddings.side_effect = mock_average_embeddings
    
    return model


@pytest.fixture
def enrollment_service(mock_speaker_model):
    """Create enrollment service with mock model"""
    return VoiceBiometricEnrollment(
        speaker_model=mock_speaker_model,
        min_samples=3,
        max_samples=5,
        quality_threshold=0.5
    )


@pytest.fixture
def sample_voice_samples():
    """Create sample voice samples for testing"""
    # Create dummy audio data (1 second of random audio at 16kHz)
    sample_rate = 16000
    duration = 1.0
    num_samples = int(sample_rate * duration)
    
    voice_samples = []
    for i in range(3):
        # Generate random audio
        audio = np.random.randn(num_samples).astype(np.float32)
        # Normalize to [-1, 1]
        audio = audio / np.max(np.abs(audio))
        # Convert to 16-bit PCM bytes
        audio_int16 = (audio * 32767).astype(np.int16)
        audio_bytes = audio_int16.tobytes()
        
        voice_samples.append(VoiceSample(
            audio=audio_bytes,
            sample_rate=sample_rate,
            duration_seconds=duration,
            format="wav"
        ))
    
    return voice_samples


class TestVoiceBiometricEnrollment:
    """Test suite for VoiceBiometricEnrollment"""
    
    def test_initialization(self, mock_speaker_model):
        """Test service initialization"""
        service = VoiceBiometricEnrollment(
            speaker_model=mock_speaker_model,
            min_samples=3,
            max_samples=5
        )
        
        assert service.speaker_model == mock_speaker_model
        assert service.min_samples == 3
        assert service.max_samples == 5
        assert service.cipher is not None
    
    def test_enroll_user_success(self, enrollment_service, sample_voice_samples):
        """Test successful user enrollment with valid samples"""
        user_id = "test_user_123"
        
        result = enrollment_service.enroll_user(user_id, sample_voice_samples)
        
        assert result.success is True
        assert result.voiceprint_id is not None
        assert result.voiceprint_id.user_id == user_id
        assert result.num_samples_used == 3
        assert 0.0 <= result.quality_score <= 1.0
        assert result.message == "Enrollment successful"
    
    def test_enroll_user_insufficient_samples(self, enrollment_service):
        """Test enrollment fails with insufficient samples"""
        user_id = "test_user_123"
        
        # Provide only 2 samples (minimum is 3)
        voice_samples = [
            VoiceSample(
                audio=b"dummy_audio_1",
                sample_rate=16000,
                duration_seconds=1.0
            ),
            VoiceSample(
                audio=b"dummy_audio_2",
                sample_rate=16000,
                duration_seconds=1.0
            )
        ]
        
        result = enrollment_service.enroll_user(user_id, voice_samples)
        
        assert result.success is False
        assert result.voiceprint_id is None
        assert result.num_samples_used == 0
        assert "Insufficient samples" in result.message
    
    def test_enroll_user_too_many_samples(self, enrollment_service, sample_voice_samples):
        """Test enrollment uses only max_samples when too many provided"""
        user_id = "test_user_123"
        
        # Provide 7 samples (max is 5)
        extra_samples = sample_voice_samples + sample_voice_samples[:4]
        
        result = enrollment_service.enroll_user(user_id, extra_samples)
        
        assert result.success is True
        # Should use only first 5 samples
        assert result.num_samples_used <= 5
    
    def test_enroll_user_low_quality_samples(self, enrollment_service, mock_speaker_model):
        """Test enrollment fails when all samples are low quality"""
        user_id = "test_user_123"
        
        # Mock quality check to fail
        mock_speaker_model.validate_audio_quality.return_value = (
            False,
            "Audio too quiet"
        )
        
        # Create dummy samples
        voice_samples = [
            VoiceSample(
                audio=b"dummy_audio",
                sample_rate=16000,
                duration_seconds=1.0
            )
            for _ in range(3)
        ]
        
        result = enrollment_service.enroll_user(user_id, voice_samples)
        
        assert result.success is False
        assert "Insufficient valid samples" in result.message
    
    def test_store_and_retrieve_voiceprint(self, enrollment_service, sample_voice_samples):
        """Test voiceprint storage and retrieval with encryption"""
        user_id = "test_user_123"
        
        # Enroll user
        result = enrollment_service.enroll_user(user_id, sample_voice_samples)
        assert result.success is True
        
        voiceprint_id = result.voiceprint_id.id
        
        # Retrieve voiceprint
        retrieved_voiceprint = enrollment_service.get_voiceprint(voiceprint_id)
        
        assert retrieved_voiceprint is not None
        assert isinstance(retrieved_voiceprint, np.ndarray)
        assert retrieved_voiceprint.shape == (192,)  # ECAPA-TDNN embedding size
    
    def test_get_voiceprint_by_user(self, enrollment_service, sample_voice_samples):
        """Test retrieving voiceprint by user ID"""
        user_id = "test_user_123"
        
        # Enroll user
        result = enrollment_service.enroll_user(user_id, sample_voice_samples)
        assert result.success is True
        
        # Retrieve by user ID
        voiceprint = enrollment_service.get_voiceprint_by_user(user_id)
        
        assert voiceprint is not None
        assert isinstance(voiceprint, np.ndarray)
    
    def test_get_voiceprint_not_found(self, enrollment_service):
        """Test retrieving non-existent voiceprint returns None"""
        voiceprint = enrollment_service.get_voiceprint("non_existent_id")
        assert voiceprint is None
        
        voiceprint = enrollment_service.get_voiceprint_by_user("non_existent_user")
        assert voiceprint is None
    
    def test_update_voiceprint(self, enrollment_service, sample_voice_samples):
        """Test updating an existing voiceprint"""
        user_id = "test_user_123"
        
        # Initial enrollment
        result1 = enrollment_service.enroll_user(user_id, sample_voice_samples)
        assert result1.success is True
        old_voiceprint_id = result1.voiceprint_id.id
        
        # Update voiceprint
        result2 = enrollment_service.update_voiceprint(user_id, sample_voice_samples)
        assert result2.success is True
        new_voiceprint_id = result2.voiceprint_id.id
        
        # IDs should be different
        assert old_voiceprint_id != new_voiceprint_id
        
        # Old voiceprint should be deleted
        old_voiceprint = enrollment_service.get_voiceprint(old_voiceprint_id)
        assert old_voiceprint is None
        
        # New voiceprint should exist
        new_voiceprint = enrollment_service.get_voiceprint(new_voiceprint_id)
        assert new_voiceprint is not None
    
    def test_delete_voiceprint(self, enrollment_service, sample_voice_samples):
        """Test deleting a voiceprint"""
        user_id = "test_user_123"
        
        # Enroll user
        result = enrollment_service.enroll_user(user_id, sample_voice_samples)
        assert result.success is True
        
        # Delete voiceprint
        deleted = enrollment_service.delete_voiceprint(user_id)
        assert deleted is True
        
        # Voiceprint should no longer exist
        voiceprint = enrollment_service.get_voiceprint_by_user(user_id)
        assert voiceprint is None
        
        # Deleting again should return False
        deleted_again = enrollment_service.delete_voiceprint(user_id)
        assert deleted_again is False
    
    def test_calculate_quality_score(self, enrollment_service):
        """Test quality score calculation"""
        # Create a normalized embedding with good variance
        embedding = np.random.randn(192).astype(np.float64)
        embedding = embedding / np.linalg.norm(embedding)
        
        quality = enrollment_service._calculate_quality_score(embedding)
        
        assert 0.0 <= quality <= 1.0
        # Should have reasonable quality for random normalized embedding
        assert quality > 0.3
    
    def test_calculate_quality_score_uniform(self, enrollment_service):
        """Test quality score for uniform embedding (low variance)"""
        # Create uniform embedding (low variance)
        embedding = np.ones(192, dtype=np.float64)
        embedding = embedding / np.linalg.norm(embedding)
        
        quality = enrollment_service._calculate_quality_score(embedding)
        
        # Should have lower quality due to low variance
        assert 0.0 <= quality <= 1.0
    
    def test_bytes_to_audio_conversion(self, enrollment_service):
        """Test audio bytes to numpy array conversion"""
        # Create sample audio
        sample_rate = 16000
        duration = 1.0
        num_samples = int(sample_rate * duration)
        
        audio = np.random.randn(num_samples).astype(np.float32)
        audio = audio / np.max(np.abs(audio))
        audio_int16 = (audio * 32767).astype(np.int16)
        audio_bytes = audio_int16.tobytes()
        
        # Convert back
        converted = enrollment_service._bytes_to_audio(audio_bytes, sample_rate)
        
        assert isinstance(converted, np.ndarray)
        assert converted.dtype == np.float32
        assert len(converted) == num_samples
        assert np.max(np.abs(converted)) <= 1.0
    
    def test_get_enrollment_stats_empty(self, enrollment_service):
        """Test enrollment stats with no voiceprints"""
        stats = enrollment_service.get_enrollment_stats()
        
        assert stats["total_voiceprints"] == 0
        assert stats["average_quality"] == 0.0
        assert stats["unique_users"] == 0
    
    def test_get_enrollment_stats(self, enrollment_service, sample_voice_samples):
        """Test enrollment stats with enrolled users"""
        # Enroll multiple users
        enrollment_service.enroll_user("user1", sample_voice_samples)
        enrollment_service.enroll_user("user2", sample_voice_samples)
        
        stats = enrollment_service.get_enrollment_stats()
        
        assert stats["total_voiceprints"] == 2
        assert 0.0 <= stats["average_quality"] <= 1.0
        assert stats["unique_users"] == 2
    
    def test_encryption_decryption(self, enrollment_service, sample_voice_samples):
        """Test that voiceprints are properly encrypted and decrypted"""
        user_id = "test_user_123"
        
        # Enroll user
        result = enrollment_service.enroll_user(user_id, sample_voice_samples)
        assert result.success is True
        
        voiceprint_id = result.voiceprint_id.id
        
        # Check that stored data is encrypted
        stored_data = enrollment_service._voiceprint_storage[voiceprint_id]
        encrypted_voiceprint = stored_data["encrypted_voiceprint"]
        
        # Encrypted data should be bytes
        assert isinstance(encrypted_voiceprint, bytes)
        
        # Retrieve and decrypt
        decrypted_voiceprint = enrollment_service.get_voiceprint(voiceprint_id)
        
        # Should be valid numpy array
        assert isinstance(decrypted_voiceprint, np.ndarray)
        assert decrypted_voiceprint.shape == (192,)
        
        # Should be normalized
        magnitude = np.linalg.norm(decrypted_voiceprint)
        assert 0.9 <= magnitude <= 1.1  # Allow small floating point errors
    
    def test_multiple_users_enrollment(self, enrollment_service, sample_voice_samples):
        """Test enrolling multiple users"""
        users = ["user1", "user2", "user3"]
        
        for user_id in users:
            result = enrollment_service.enroll_user(user_id, sample_voice_samples)
            assert result.success is True
        
        # Each user should have their own voiceprint
        for user_id in users:
            voiceprint = enrollment_service.get_voiceprint_by_user(user_id)
            assert voiceprint is not None
        
        # Stats should reflect all users
        stats = enrollment_service.get_enrollment_stats()
        assert stats["total_voiceprints"] == 3
        assert stats["unique_users"] == 3
    
    def test_model_loading_on_enrollment(self, sample_voice_samples):
        """Test that model is loaded if not already loaded"""
        # Create a fresh mock for this test
        mock_model = Mock(spec=SpeakerRecognitionModel)
        mock_model.is_loaded = False
        mock_model.embedding_dimension = 192
        
        # Mock load_model to set is_loaded = True
        def mock_load_model():
            mock_model.is_loaded = True
        mock_model.load_model.side_effect = mock_load_model
        
        # Mock embedding extraction
        def mock_extract_embedding(audio, sample_rate):
            embedding = np.random.randn(192).astype(np.float64)
            embedding = embedding / np.linalg.norm(embedding)
            return embedding
        mock_model.extract_embedding.side_effect = mock_extract_embedding
        
        # Mock audio validation
        mock_model.validate_audio_quality.return_value = (True, None)
        
        # Mock average_embeddings
        def mock_average_embeddings(embeddings):
            avg = np.mean(embeddings, axis=0)
            return avg / np.linalg.norm(avg)
        mock_model.average_embeddings.side_effect = mock_average_embeddings
        
        service = VoiceBiometricEnrollment(
            speaker_model=mock_model,
            min_samples=3,
            quality_threshold=0.3  # Lower threshold to ensure samples pass
        )
        
        result = service.enroll_user("test_user", sample_voice_samples)
        
        # Model load should have been called
        mock_model.load_model.assert_called_once()
        assert result.success is True


class TestVoiceBiometricEnrollmentEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_empty_voice_samples(self, enrollment_service):
        """Test enrollment with empty sample list"""
        result = enrollment_service.enroll_user("user", [])
        
        assert result.success is False
        assert "Insufficient samples" in result.message
    
    def test_corrupted_audio_data(self, enrollment_service, mock_speaker_model):
        """Test handling of corrupted audio data"""
        # Mock extract_embedding to raise exception
        mock_speaker_model.extract_embedding.side_effect = Exception("Corrupted audio")
        
        voice_samples = [
            VoiceSample(
                audio=b"corrupted",
                sample_rate=16000,
                duration_seconds=1.0
            )
            for _ in range(3)
        ]
        
        result = enrollment_service.enroll_user("user", voice_samples)
        
        assert result.success is False
        assert "Insufficient valid samples" in result.message
    
    def test_mixed_quality_samples(self, enrollment_service, mock_speaker_model, sample_voice_samples):
        """Test enrollment with mix of good and bad quality samples"""
        # Mock validation to fail for some samples
        validation_results = [
            (True, None),   # Good
            (False, "Too quiet"),  # Bad
            (True, None),   # Good
            (True, None),   # Good
        ]
        mock_speaker_model.validate_audio_quality.side_effect = validation_results
        
        # Provide 4 samples
        voice_samples = sample_voice_samples + [sample_voice_samples[0]]
        
        result = enrollment_service.enroll_user("user", voice_samples)
        
        # Should succeed with 3 good samples
        assert result.success is True
        assert result.num_samples_used == 3
    
    def test_voiceprint_retrieval_decryption_error(self, enrollment_service, sample_voice_samples):
        """Test handling of decryption errors"""
        user_id = "test_user"
        
        # Enroll user
        result = enrollment_service.enroll_user(user_id, sample_voice_samples)
        assert result.success is True
        
        voiceprint_id = result.voiceprint_id.id
        
        # Corrupt the encrypted data
        enrollment_service._voiceprint_storage[voiceprint_id]["encrypted_voiceprint"] = b"corrupted"
        
        # Retrieval should return None
        voiceprint = enrollment_service.get_voiceprint(voiceprint_id)
        assert voiceprint is None
