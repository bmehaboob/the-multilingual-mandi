"""Unit tests for LanguageDetector service"""
import pytest
import numpy as np
from app.services.vocal_vernacular.language_detector import LanguageDetector
from app.services.vocal_vernacular.models import LanguageResult, LanguageSegment


class TestLanguageDetector:
    """Test suite for LanguageDetector"""
    
    @pytest.fixture
    def detector(self):
        """Create a LanguageDetector instance"""
        return LanguageDetector()
    
    @pytest.fixture
    def sample_audio(self):
        """Create sample audio data (1 second at 16kHz)"""
        sample_rate = 16000
        duration = 1.0
        # Generate simple sine wave as test audio
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio = np.sin(2 * np.pi * 440 * t) * 0.3  # 440 Hz tone
        return audio.astype(np.float32)
    
    def test_detect_language_basic(self, detector, sample_audio):
        """Test basic language detection"""
        result = detector.detect_language(sample_audio)
        
        assert isinstance(result, LanguageResult)
        assert result.language in detector.supported_languages
        assert 0.0 <= result.confidence <= 1.0
    
    def test_detect_language_empty_audio(self, detector):
        """Test language detection with empty audio"""
        empty_audio = np.array([])
        result = detector.detect_language(empty_audio)
        
        # Should fallback to default language (Hindi)
        assert result.language == 'hin'
        assert result.confidence == 0.5
    
    def test_detect_language_latency(self, detector, sample_audio):
        """Test that language detection completes within 2 seconds (Requirement 1.2)"""
        import time
        
        start_time = time.time()
        result = detector.detect_language(sample_audio)
        elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
        
        assert elapsed_time < 2000, f"Language detection took {elapsed_time:.0f}ms, exceeds 2000ms threshold"
        assert result is not None
    
    def test_detect_code_switching_single_language(self, detector, sample_audio):
        """Test code-switching detection with single language audio"""
        segments = detector.detect_code_switching(sample_audio)
        
        assert isinstance(segments, list)
        assert len(segments) >= 1
        assert all(isinstance(seg, LanguageSegment) for seg in segments)
        
        # Check segment properties
        for seg in segments:
            assert seg.language in detector.supported_languages
            assert 0.0 <= seg.confidence <= 1.0
            assert seg.start_time >= 0.0
            assert seg.end_time > seg.start_time
    
    def test_detect_code_switching_longer_audio(self, detector):
        """Test code-switching detection with longer audio (multiple segments)"""
        # Create 10 seconds of audio
        sample_rate = 16000
        duration = 10.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio = np.sin(2 * np.pi * 440 * t) * 0.3
        audio = audio.astype(np.float32)
        
        segments = detector.detect_code_switching(audio, sample_rate, segment_duration=3.0)
        
        assert len(segments) >= 1
        
        # Verify segments cover the entire audio duration
        assert segments[0].start_time == 0.0
        assert segments[-1].end_time == pytest.approx(duration, rel=0.1)
    
    def test_detect_code_switching_empty_audio(self, detector):
        """Test code-switching detection with empty audio"""
        empty_audio = np.array([])
        segments = detector.detect_code_switching(empty_audio)
        
        # Should return fallback segment
        assert len(segments) == 1
        assert segments[0].language == 'hin'
        assert segments[0].confidence == 0.5
    
    def test_is_supported_language(self, detector):
        """Test checking if language is supported"""
        # Test supported languages
        assert detector.is_supported_language('hin') is True
        assert detector.is_supported_language('tel') is True
        assert detector.is_supported_language('tam') is True
        
        # Test unsupported language
        assert detector.is_supported_language('eng') is False
        assert detector.is_supported_language('fra') is False
    
    def test_get_supported_languages(self, detector):
        """Test getting list of supported languages"""
        languages = detector.get_supported_languages()
        
        assert isinstance(languages, list)
        assert len(languages) == 22  # 22 scheduled Indian languages
        assert 'hin' in languages
        assert 'tel' in languages
        assert 'tam' in languages
    
    def test_language_result_structure(self, detector, sample_audio):
        """Test that LanguageResult has correct structure"""
        result = detector.detect_language(sample_audio)
        
        assert hasattr(result, 'language')
        assert hasattr(result, 'confidence')
        assert hasattr(result, 'dialect')
        assert isinstance(result.language, str)
        assert isinstance(result.confidence, float)
    
    def test_language_segment_structure(self, detector, sample_audio):
        """Test that LanguageSegment has correct structure"""
        segments = detector.detect_code_switching(sample_audio)
        
        for seg in segments:
            assert hasattr(seg, 'language')
            assert hasattr(seg, 'start_time')
            assert hasattr(seg, 'end_time')
            assert hasattr(seg, 'confidence')
            assert isinstance(seg.language, str)
            assert isinstance(seg.start_time, float)
            assert isinstance(seg.end_time, float)
            assert isinstance(seg.confidence, float)
    
    def test_detect_language_with_different_sample_rates(self, detector):
        """Test language detection with different sample rates"""
        # Test with 8kHz
        audio_8k = np.random.randn(8000).astype(np.float32) * 0.1
        result_8k = detector.detect_language(audio_8k, sample_rate=8000)
        assert result_8k is not None
        
        # Test with 16kHz (default)
        audio_16k = np.random.randn(16000).astype(np.float32) * 0.1
        result_16k = detector.detect_language(audio_16k, sample_rate=16000)
        assert result_16k is not None
        
        # Test with 44.1kHz
        audio_44k = np.random.randn(44100).astype(np.float32) * 0.1
        result_44k = detector.detect_language(audio_44k, sample_rate=44100)
        assert result_44k is not None
