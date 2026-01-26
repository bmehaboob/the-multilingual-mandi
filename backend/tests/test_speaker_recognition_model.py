"""Unit tests for SpeakerRecognitionModel"""
import pytest
import numpy as np
from app.services.auth.speaker_recognition_model import SpeakerRecognitionModel


@pytest.fixture
def speaker_model():
    """Create a speaker recognition model instance"""
    model = SpeakerRecognitionModel()
    return model


@pytest.fixture
def sample_audio():
    """Generate sample audio for testing (1 second of random audio)"""
    sample_rate = 16000
    duration = 1.0
    # Generate random audio that simulates speech (not pure noise)
    audio = np.random.randn(int(sample_rate * duration)).astype(np.float32) * 0.1
    return audio, sample_rate


class TestSpeakerRecognitionModel:
    """Test suite for SpeakerRecognitionModel"""
    
    def test_model_initialization(self, speaker_model):
        """Test that model initializes correctly"""
        assert speaker_model is not None
        assert speaker_model.model_name == "speechbrain/spkrec-ecapa-voxceleb"
        assert speaker_model.device in ["cpu", "cuda", "mps"]
        assert not speaker_model.is_loaded
    
    def test_device_detection(self, speaker_model):
        """Test that device is detected correctly"""
        device = speaker_model._get_device()
        assert device in ["cpu", "cuda", "mps"]
    
    def test_model_loading(self, speaker_model):
        """Test that model loads successfully"""
        speaker_model.load_model()
        assert speaker_model.is_loaded
        assert speaker_model.classifier is not None
    
    def test_model_loading_idempotent(self, speaker_model):
        """Test that loading model multiple times is safe"""
        speaker_model.load_model()
        assert speaker_model.is_loaded
        
        # Load again - should not fail
        speaker_model.load_model()
        assert speaker_model.is_loaded
    
    def test_embedding_extraction(self, speaker_model, sample_audio):
        """Test that embeddings can be extracted from audio"""
        audio, sample_rate = sample_audio
        
        speaker_model.load_model()
        embedding = speaker_model.extract_embedding(audio, sample_rate)
        
        # ECAPA-TDNN produces 192-dimensional embeddings
        assert embedding.shape == (192,)
        assert embedding.dtype == np.float32 or embedding.dtype == np.float64
        assert not np.isnan(embedding).any()
        assert not np.isinf(embedding).any()
    
    def test_embedding_extraction_without_loading(self, speaker_model, sample_audio):
        """Test that extraction fails if model not loaded"""
        audio, sample_rate = sample_audio
        
        with pytest.raises(RuntimeError, match="Model not loaded"):
            speaker_model.extract_embedding(audio, sample_rate)
    
    def test_embedding_dimension_property(self, speaker_model):
        """Test that embedding dimension is correct"""
        assert speaker_model.embedding_dimension == 192
    
    def test_similarity_computation(self, speaker_model):
        """Test cosine similarity computation between embeddings"""
        # Create two similar embeddings
        emb1 = np.random.randn(192).astype(np.float32)
        emb2 = emb1 + np.random.randn(192).astype(np.float32) * 0.1
        
        similarity = speaker_model.compute_similarity(emb1, emb2)
        
        # Similarity should be between 0 and 1
        assert 0.0 <= similarity <= 1.0
        # Similar embeddings should have high similarity
        assert similarity > 0.5
    
    def test_similarity_identical_embeddings(self, speaker_model):
        """Test that identical embeddings have similarity close to 1.0"""
        emb = np.random.randn(192).astype(np.float32)
        
        similarity = speaker_model.compute_similarity(emb, emb)
        
        # Identical embeddings should have similarity very close to 1.0
        assert similarity > 0.99
    
    def test_similarity_different_embeddings(self, speaker_model):
        """Test that different embeddings have lower similarity"""
        emb1 = np.random.randn(192).astype(np.float32)
        emb2 = np.random.randn(192).astype(np.float32)
        
        similarity = speaker_model.compute_similarity(emb1, emb2)
        
        # Random embeddings should have lower similarity
        assert 0.0 <= similarity <= 1.0
    
    def test_average_embeddings(self, speaker_model):
        """Test averaging multiple embeddings"""
        embeddings = [
            np.random.randn(192).astype(np.float32),
            np.random.randn(192).astype(np.float32),
            np.random.randn(192).astype(np.float32)
        ]
        
        averaged = speaker_model.average_embeddings(embeddings)
        
        assert averaged.shape == (192,)
        assert not np.isnan(averaged).any()
        assert not np.isinf(averaged).any()
        # Averaged embedding should be normalized
        norm = np.linalg.norm(averaged)
        assert abs(norm - 1.0) < 0.01
    
    def test_average_embeddings_empty_list(self, speaker_model):
        """Test that averaging empty list raises error"""
        with pytest.raises(ValueError, match="Cannot average empty list"):
            speaker_model.average_embeddings([])
    
    def test_audio_quality_validation_valid(self, speaker_model, sample_audio):
        """Test audio quality validation with valid audio"""
        audio, sample_rate = sample_audio
        
        is_valid, error_msg = speaker_model.validate_audio_quality(audio, sample_rate)
        
        assert is_valid
        assert error_msg is None
    
    def test_audio_quality_validation_too_short(self, speaker_model):
        """Test audio quality validation with too short audio"""
        audio = np.random.randn(8000).astype(np.float32) * 0.1  # 0.5 seconds
        sample_rate = 16000
        
        is_valid, error_msg = speaker_model.validate_audio_quality(audio, sample_rate)
        
        assert not is_valid
        assert "too short" in error_msg.lower()
    
    def test_audio_quality_validation_too_long(self, speaker_model):
        """Test audio quality validation with too long audio"""
        audio = np.random.randn(16000 * 35).astype(np.float32) * 0.1  # 35 seconds
        sample_rate = 16000
        
        is_valid, error_msg = speaker_model.validate_audio_quality(audio, sample_rate)
        
        assert not is_valid
        assert "too long" in error_msg.lower()
    
    def test_audio_quality_validation_silent(self, speaker_model):
        """Test audio quality validation with silent audio"""
        audio = np.zeros(16000).astype(np.float32)  # 1 second of silence
        sample_rate = 16000
        
        is_valid, error_msg = speaker_model.validate_audio_quality(audio, sample_rate)
        
        assert not is_valid
        assert "silent" in error_msg.lower() or "quiet" in error_msg.lower()
    
    def test_audio_quality_validation_clipping(self, speaker_model):
        """Test audio quality validation with clipped audio"""
        audio = np.ones(16000).astype(np.float32)  # 1 second of clipped audio
        sample_rate = 16000
        
        is_valid, error_msg = speaker_model.validate_audio_quality(audio, sample_rate)
        
        assert not is_valid
        assert "clipping" in error_msg.lower()
    
    def test_model_unload(self, speaker_model):
        """Test that model can be unloaded from memory"""
        speaker_model.load_model()
        assert speaker_model.is_loaded
        
        speaker_model.unload_model()
        assert not speaker_model.is_loaded
        assert speaker_model.classifier is None
    
    def test_cache_dir_creation(self, speaker_model):
        """Test that model cache directory is created"""
        cache_dir = speaker_model._get_model_cache_dir()
        assert cache_dir is not None
        assert isinstance(cache_dir, str)


class TestSpeakerRecognitionModelIntegration:
    """Integration tests for SpeakerRecognitionModel"""
    
    def test_full_pipeline(self, speaker_model, sample_audio):
        """Test complete pipeline: load model, extract embedding, compute similarity"""
        audio1, sample_rate = sample_audio
        # Create slightly different audio
        audio2 = audio1 + np.random.randn(len(audio1)).astype(np.float32) * 0.05
        
        # Load model
        speaker_model.load_model()
        
        # Extract embeddings
        emb1 = speaker_model.extract_embedding(audio1, sample_rate)
        emb2 = speaker_model.extract_embedding(audio2, sample_rate)
        
        # Compute similarity
        similarity = speaker_model.compute_similarity(emb1, emb2)
        
        # Similar audio should have high similarity
        assert similarity > 0.5
        
        # Unload model
        speaker_model.unload_model()
        assert not speaker_model.is_loaded
    
    def test_multiple_embeddings_averaging(self, speaker_model, sample_audio):
        """Test extracting and averaging multiple embeddings"""
        audio, sample_rate = sample_audio
        
        speaker_model.load_model()
        
        # Extract multiple embeddings from slightly different audio
        embeddings = []
        for i in range(3):
            audio_variant = audio + np.random.randn(len(audio)).astype(np.float32) * 0.05
            emb = speaker_model.extract_embedding(audio_variant, sample_rate)
            embeddings.append(emb)
        
        # Average embeddings
        averaged = speaker_model.average_embeddings(embeddings)
        
        # Averaged embedding should be similar to individual embeddings
        for emb in embeddings:
            similarity = speaker_model.compute_similarity(averaged, emb)
            assert similarity > 0.7  # Should be reasonably similar
