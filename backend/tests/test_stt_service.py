"""Unit tests for STTService"""
import pytest
import numpy as np
from app.services.vocal_vernacular.stt_service import (
    STTService,
    SUPPORTED_LANGUAGES,
    COMMODITY_VOCABULARY
)
from app.services.vocal_vernacular.models import TranscriptionResult


@pytest.fixture
def stt_service():
    """Create STTService instance in mock mode for testing"""
    return STTService(use_mock=True, confidence_threshold=0.7)


@pytest.fixture
def sample_audio():
    """Generate sample audio data (1 second at 16kHz)"""
    sample_rate = 16000
    duration = 1.0
    samples = int(sample_rate * duration)
    # Generate simple sine wave as test audio
    frequency = 440  # A4 note
    t = np.linspace(0, duration, samples)
    audio = np.sin(2 * np.pi * frequency * t).astype(np.float32)
    return audio


class TestSTTServiceInitialization:
    """Test STTService initialization"""
    
    def test_init_mock_mode(self):
        """Test initialization in mock mode"""
        service = STTService(use_mock=True)
        assert service.use_mock is True
        assert service.confidence_threshold == 0.7
        assert service.model is None
    
    def test_init_with_custom_threshold(self):
        """Test initialization with custom confidence threshold"""
        service = STTService(use_mock=True, confidence_threshold=0.8)
        assert service.confidence_threshold == 0.8
    
    def test_supported_languages_count(self):
        """Test that all 22 scheduled Indian languages are supported"""
        assert len(SUPPORTED_LANGUAGES) == 22
    
    def test_supported_languages_includes_major_languages(self):
        """Test that major Indian languages are in supported list"""
        major_languages = ["hin", "tel", "tam", "kan", "mar", "ben"]
        for lang in major_languages:
            assert lang in SUPPORTED_LANGUAGES


class TestSTTServiceTranscription:
    """Test transcription functionality"""
    
    def test_transcribe_hindi(self, stt_service, sample_audio):
        """Test transcription of Hindi audio"""
        result = stt_service.transcribe(sample_audio, "hin")
        
        assert isinstance(result, TranscriptionResult)
        assert result.text is not None
        assert len(result.text) > 0
        assert result.language == "hin"
        assert 0.0 <= result.confidence <= 1.0
    
    def test_transcribe_telugu(self, stt_service, sample_audio):
        """Test transcription of Telugu audio"""
        result = stt_service.transcribe(sample_audio, "tel")
        
        assert isinstance(result, TranscriptionResult)
        assert result.language == "tel"
        assert result.confidence > 0
    
    def test_transcribe_tamil(self, stt_service, sample_audio):
        """Test transcription of Tamil audio"""
        result = stt_service.transcribe(sample_audio, "tam")
        
        assert isinstance(result, TranscriptionResult)
        assert result.language == "tam"
    
    def test_transcribe_with_dialect(self, stt_service, sample_audio):
        """Test transcription with dialect parameter"""
        result = stt_service.transcribe(sample_audio, "hin", dialect="haryanvi")
        
        assert isinstance(result, TranscriptionResult)
        assert result.language == "hin"
    
    def test_transcribe_latency(self, stt_service, sample_audio):
        """Test that transcription completes within 3 seconds (Requirement 2.1)"""
        result = stt_service.transcribe(sample_audio, "hin")
        
        assert result.processing_time_ms is not None
        # In mock mode, should be very fast
        assert result.processing_time_ms < 3000
    
    def test_transcribe_unsupported_language_warning(self, stt_service, sample_audio):
        """Test transcription with unsupported language logs warning but continues"""
        # Should not raise exception, just log warning
        result = stt_service.transcribe(sample_audio, "xyz")
        assert isinstance(result, TranscriptionResult)


class TestSTTServiceDomainVocabulary:
    """Test domain vocabulary boosting"""
    
    def test_transcribe_with_correction(self, stt_service, sample_audio):
        """Test transcription with domain vocabulary boosting (Requirement 2.4)"""
        result = stt_service.transcribe_with_correction(
            sample_audio,
            "hin",
            domain_vocabulary=["tomato", "onion", "potato"]
        )
        
        assert isinstance(result, TranscriptionResult)
        assert result.text is not None
    
    def test_commodity_vocabulary_exists(self):
        """Test that commodity vocabulary is defined"""
        assert len(COMMODITY_VOCABULARY) > 0
        assert "tomato" in COMMODITY_VOCABULARY
        assert "onion" in COMMODITY_VOCABULARY
        assert "potato" in COMMODITY_VOCABULARY
    
    def test_commodity_vocabulary_includes_units(self):
        """Test that commodity vocabulary includes units"""
        assert "kilogram" in COMMODITY_VOCABULARY or "kg" in COMMODITY_VOCABULARY
        assert "quintal" in COMMODITY_VOCABULARY
    
    def test_commodity_vocabulary_includes_price_terms(self):
        """Test that commodity vocabulary includes price terms"""
        assert "rupees" in COMMODITY_VOCABULARY or "price" in COMMODITY_VOCABULARY
        assert "market" in COMMODITY_VOCABULARY or "mandi" in COMMODITY_VOCABULARY


class TestSTTServiceConfidence:
    """Test confidence scoring and low-confidence handling"""
    
    def test_requires_confirmation_low_confidence(self, stt_service):
        """Test that low confidence transcriptions require confirmation (Requirement 2.3)"""
        result = TranscriptionResult(
            text="test",
            confidence=0.65,  # Below 0.7 threshold
            language="hin"
        )
        
        assert stt_service.requires_confirmation(result) is True
    
    def test_requires_confirmation_high_confidence(self, stt_service):
        """Test that high confidence transcriptions don't require confirmation"""
        result = TranscriptionResult(
            text="test",
            confidence=0.85,  # Above 0.7 threshold
            language="hin"
        )
        
        assert stt_service.requires_confirmation(result) is False
    
    def test_requires_confirmation_at_threshold(self, stt_service):
        """Test behavior at exact threshold"""
        result = TranscriptionResult(
            text="test",
            confidence=0.7,  # Exactly at threshold
            language="hin"
        )
        
        # At threshold should not require confirmation
        assert stt_service.requires_confirmation(result) is False
    
    def test_confidence_range(self, stt_service, sample_audio):
        """Test that confidence scores are in valid range [0, 1]"""
        result = stt_service.transcribe(sample_audio, "hin")
        
        assert 0.0 <= result.confidence <= 1.0


class TestSTTServiceDialectSupport:
    """Test dialect-specific functionality"""
    
    def test_load_dialect_adapter(self, stt_service):
        """Test loading dialect adapter"""
        stt_service.load_dialect_adapter("hin", "haryanvi", "/path/to/adapter")
        
        assert "hin_haryanvi" in stt_service.dialect_adapters
        assert stt_service.dialect_adapters["hin_haryanvi"]["loaded"] is True
    
    def test_multiple_dialect_adapters(self, stt_service):
        """Test loading multiple dialect adapters"""
        stt_service.load_dialect_adapter("hin", "haryanvi", "/path/1")
        stt_service.load_dialect_adapter("hin", "bhojpuri", "/path/2")
        stt_service.load_dialect_adapter("tel", "telangana", "/path/3")
        
        assert len(stt_service.dialect_adapters) == 3


class TestSTTServiceUtilityMethods:
    """Test utility methods"""
    
    def test_get_supported_languages(self, stt_service):
        """Test getting list of supported languages"""
        languages = stt_service.get_supported_languages()
        
        assert isinstance(languages, list)
        assert len(languages) == 22
        assert "hin" in languages
        assert "tel" in languages
    
    def test_get_supported_languages_returns_copy(self, stt_service):
        """Test that get_supported_languages returns a copy, not reference"""
        languages1 = stt_service.get_supported_languages()
        languages2 = stt_service.get_supported_languages()
        
        # Modify one list
        languages1.append("test")
        
        # Other list should be unchanged
        assert len(languages2) == 22
        assert "test" not in languages2


class TestSTTServiceEdgeCases:
    """Test edge cases and error handling"""
    
    def test_transcribe_empty_audio(self, stt_service):
        """Test transcription with empty audio array"""
        empty_audio = np.array([], dtype=np.float32)
        result = stt_service.transcribe(empty_audio, "hin")
        
        # Should handle gracefully
        assert isinstance(result, TranscriptionResult)
    
    def test_transcribe_very_short_audio(self, stt_service):
        """Test transcription with very short audio (0.1 seconds)"""
        short_audio = np.random.randn(1600).astype(np.float32)  # 0.1s at 16kHz
        result = stt_service.transcribe(short_audio, "hin")
        
        assert isinstance(result, TranscriptionResult)
    
    def test_transcribe_long_audio(self, stt_service):
        """Test transcription with longer audio (10 seconds)"""
        long_audio = np.random.randn(160000).astype(np.float32)  # 10s at 16kHz
        result = stt_service.transcribe(long_audio, "hin")
        
        assert isinstance(result, TranscriptionResult)
