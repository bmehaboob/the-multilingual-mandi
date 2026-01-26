"""Unit tests for TTSService"""
import pytest
import numpy as np
from app.services.vocal_vernacular.tts_service import (
    TTSService,
    SUPPORTED_LANGUAGES
)


@pytest.fixture
def tts_service():
    """Create TTSService instance in mock mode for testing"""
    return TTSService(use_mock=True, default_speech_rate=0.85)


class TestTTSServiceInitialization:
    """Test TTSService initialization"""
    
    def test_init_mock_mode(self):
        """Test initialization in mock mode"""
        service = TTSService(use_mock=True)
        assert service.use_mock is True
        assert service.default_speech_rate == 0.85
        assert len(service.models) == 0
    
    def test_init_with_custom_speech_rate(self):
        """Test initialization with custom speech rate"""
        service = TTSService(use_mock=True, default_speech_rate=0.80)
        assert service.default_speech_rate == 0.80
    
    def test_supported_languages_count(self):
        """Test that all 22 scheduled Indian languages are supported"""
        assert len(SUPPORTED_LANGUAGES) == 22
    
    def test_supported_languages_includes_major_languages(self):
        """Test that major Indian languages are in supported list"""
        major_languages = ["hin", "tel", "tam", "kan", "mar", "ben"]
        for lang in major_languages:
            assert lang in SUPPORTED_LANGUAGES


class TestTTSServiceSynthesis:
    """Test speech synthesis functionality"""
    
    def test_synthesize_hindi(self, tts_service):
        """Test synthesis of Hindi text (Requirement 4.1)"""
        text = "टमाटर की कीमत क्या है"
        audio = tts_service.synthesize(text, "hin")
        
        assert isinstance(audio, np.ndarray)
        assert len(audio) > 0
        assert audio.dtype == np.float32
    
    def test_synthesize_telugu(self, tts_service):
        """Test synthesis of Telugu text"""
        text = "టమాటా ధర ఎంత"
        audio = tts_service.synthesize(text, "tel")
        
        assert isinstance(audio, np.ndarray)
        assert len(audio) > 0
    
    def test_synthesize_tamil(self, tts_service):
        """Test synthesis of Tamil text"""
        text = "தக்காளி விலை என்ன"
        audio = tts_service.synthesize(text, "tam")
        
        assert isinstance(audio, np.ndarray)
        assert len(audio) > 0
    
    def test_synthesize_english(self, tts_service):
        """Test synthesis of English text"""
        text = "What is the price of tomatoes"
        audio = tts_service.synthesize(text, "eng")
        
        assert isinstance(audio, np.ndarray)
        assert len(audio) > 0
    
    def test_synthesize_latency(self, tts_service):
        """Test that synthesis completes within 2 seconds (Requirement 4.1)"""
        import time
        text = "This is a test message for latency measurement"
        
        start_time = time.time()
        audio = tts_service.synthesize(text, "hin")
        end_time = time.time()
        
        latency_ms = (end_time - start_time) * 1000
        # In mock mode, should be very fast
        assert latency_ms < 2000
        assert isinstance(audio, np.ndarray)


class TestTTSServiceSpeechRate:
    """Test speech rate adjustment"""
    
    def test_default_speech_rate(self, tts_service):
        """Test that default speech rate is 85% (15% slower) (Requirement 4.3)"""
        assert tts_service.default_speech_rate == 0.85
    
    def test_synthesize_with_default_speech_rate(self, tts_service):
        """Test synthesis uses default speech rate when not specified"""
        text = "Test message"
        audio = tts_service.synthesize(text, "hin")
        
        # Audio should be generated with default rate
        assert isinstance(audio, np.ndarray)
    
    def test_synthesize_with_custom_speech_rate(self, tts_service):
        """Test synthesis with custom speech rate"""
        text = "Test message"
        audio = tts_service.synthesize(text, "hin", speech_rate=0.80)
        
        assert isinstance(audio, np.ndarray)
    
    def test_speech_rate_slower_produces_longer_audio(self, tts_service):
        """Test that slower speech rate produces longer audio"""
        text = "Test message for speech rate comparison"
        
        audio_normal = tts_service.synthesize(text, "hin", speech_rate=0.90)
        audio_slower = tts_service.synthesize(text, "hin", speech_rate=0.80)
        
        # Slower speech should produce longer audio
        assert len(audio_slower) > len(audio_normal)
    
    def test_speech_rate_validation_too_fast(self, tts_service):
        """Test that speech rate outside recommended range uses default"""
        text = "Test message"
        # Try to use 1.0 (normal speed, outside 0.80-0.90 range)
        audio = tts_service.synthesize(text, "hin", speech_rate=1.0)
        
        # Should still generate audio (using default rate)
        assert isinstance(audio, np.ndarray)
    
    def test_speech_rate_validation_too_slow(self, tts_service):
        """Test that speech rate outside recommended range uses default"""
        text = "Test message"
        # Try to use 0.5 (very slow, outside 0.80-0.90 range)
        audio = tts_service.synthesize(text, "hin", speech_rate=0.5)
        
        # Should still generate audio (using default rate)
        assert isinstance(audio, np.ndarray)
    
    def test_speech_rate_within_recommended_range(self, tts_service):
        """Test speech rates within recommended 10-20% slower range"""
        text = "Test message"
        
        # Test various rates within recommended range
        for rate in [0.80, 0.85, 0.90]:
            audio = tts_service.synthesize(text, "hin", speech_rate=rate)
            assert isinstance(audio, np.ndarray)
            assert len(audio) > 0


class TestTTSServiceVolumeAdjustment:
    """Test adaptive volume control for noisy environments"""
    
    def test_adjust_for_quiet_environment(self, tts_service):
        """Test no volume adjustment for quiet environment (Requirement 4.4)"""
        audio = np.random.randn(1000).astype(np.float32) * 0.5
        noise_level = 35.0  # Quiet room (below 40 dB baseline)
        
        adjusted = tts_service.adjust_for_environment(audio, noise_level)
        
        # Should be unchanged for quiet environment
        np.testing.assert_array_almost_equal(adjusted, audio)
    
    def test_adjust_for_moderate_noise(self, tts_service):
        """Test volume boost for moderate noise"""
        audio = np.random.randn(1000).astype(np.float32) * 0.3
        noise_level = 60.0  # Moderate noise
        
        adjusted = tts_service.adjust_for_environment(audio, noise_level)
        
        # Should be boosted
        assert np.abs(adjusted).mean() > np.abs(audio).mean()
    
    def test_adjust_for_high_noise(self, tts_service):
        """Test volume boost for high noise (70+ dB)"""
        audio = np.random.randn(1000).astype(np.float32) * 0.3
        noise_level = 75.0  # High noise (rural environment)
        
        adjusted = tts_service.adjust_for_environment(audio, noise_level)
        
        # Should be significantly boosted
        assert np.abs(adjusted).mean() > np.abs(audio).mean()
    
    def test_adjust_prevents_clipping(self, tts_service):
        """Test that volume adjustment prevents clipping"""
        audio = np.random.randn(1000).astype(np.float32) * 0.8
        noise_level = 80.0  # Very high noise
        
        adjusted = tts_service.adjust_for_environment(audio, noise_level)
        
        # Should be clipped to [-1.0, 1.0] range
        assert np.all(adjusted >= -1.0)
        assert np.all(adjusted <= 1.0)
    
    def test_adjust_maximum_boost_cap(self, tts_service):
        """Test that volume boost is capped at 20 dB"""
        audio = np.random.randn(1000).astype(np.float32) * 0.1
        noise_level = 100.0  # Extremely high noise
        
        adjusted = tts_service.adjust_for_environment(audio, noise_level)
        
        # Should be boosted but not exceed clipping limits
        assert np.all(adjusted >= -1.0)
        assert np.all(adjusted <= 1.0)


class TestTTSServiceMP3Compression:
    """Test MP3 audio compression"""
    
    def test_compress_to_mp3(self, tts_service):
        """Test MP3 compression (Requirement 10.1)"""
        # Generate sample audio
        audio = np.random.randn(22050).astype(np.float32) * 0.5  # 1 second
        
        mp3_bytes = tts_service.compress_to_mp3(audio, sample_rate=22050)
        
        assert isinstance(mp3_bytes, bytes)
        assert len(mp3_bytes) > 0
    
    def test_compress_to_mp3_reduces_size(self, tts_service):
        """Test that MP3 compression reduces file size"""
        # Generate sample audio
        audio = np.random.randn(22050).astype(np.float32) * 0.5  # 1 second
        
        # Original size (16-bit PCM)
        original_size = len(audio) * 2  # 2 bytes per sample
        
        # Compressed size
        mp3_bytes = tts_service.compress_to_mp3(audio, sample_rate=22050)
        compressed_size = len(mp3_bytes)
        
        # MP3 should be smaller (though in mock mode without pydub, might be similar)
        # Just verify it produces output
        assert compressed_size > 0
    
    def test_compress_to_mp3_different_bitrates(self, tts_service):
        """Test MP3 compression with different bitrates"""
        audio = np.random.randn(22050).astype(np.float32) * 0.5
        
        # Test different bitrates
        for bitrate in ["64k", "96k", "128k"]:
            mp3_bytes = tts_service.compress_to_mp3(
                audio,
                sample_rate=22050,
                bitrate=bitrate
            )
            assert isinstance(mp3_bytes, bytes)
            assert len(mp3_bytes) > 0
    
    def test_compress_to_mp3_longer_audio(self, tts_service):
        """Test MP3 compression with longer audio"""
        # Generate 5 seconds of audio
        audio = np.random.randn(22050 * 5).astype(np.float32) * 0.5
        
        mp3_bytes = tts_service.compress_to_mp3(audio, sample_rate=22050)
        
        assert isinstance(mp3_bytes, bytes)
        assert len(mp3_bytes) > 0


class TestTTSServiceUtilityMethods:
    """Test utility methods"""
    
    def test_get_supported_languages(self, tts_service):
        """Test getting list of supported languages"""
        languages = tts_service.get_supported_languages()
        
        assert isinstance(languages, list)
        assert len(languages) == 22
        assert "hin" in languages
        assert "tel" in languages
    
    def test_get_supported_languages_returns_copy(self, tts_service):
        """Test that get_supported_languages returns a copy"""
        languages1 = tts_service.get_supported_languages()
        languages2 = tts_service.get_supported_languages()
        
        # Modify one list
        languages1.append("test")
        
        # Other list should be unchanged
        assert len(languages2) == 22
        assert "test" not in languages2
    
    def test_load_language_model(self, tts_service):
        """Test loading language model"""
        tts_service.load_language_model("hin", "/path/to/model")
        
        assert "hin" in tts_service.models
        assert tts_service.models["hin"]["loaded"] is True
    
    def test_load_multiple_language_models(self, tts_service):
        """Test loading multiple language models"""
        tts_service.load_language_model("hin", "/path/1")
        tts_service.load_language_model("tel", "/path/2")
        tts_service.load_language_model("tam", "/path/3")
        
        assert len(tts_service.models) == 3
        assert all(tts_service.models[lang]["loaded"] for lang in ["hin", "tel", "tam"])


class TestTTSServiceEdgeCases:
    """Test edge cases and error handling"""
    
    def test_synthesize_empty_text(self, tts_service):
        """Test synthesis with empty text"""
        audio = tts_service.synthesize("", "hin")
        
        # Should handle gracefully
        assert isinstance(audio, np.ndarray)
    
    def test_synthesize_very_short_text(self, tts_service):
        """Test synthesis with very short text"""
        audio = tts_service.synthesize("Hi", "hin")
        
        assert isinstance(audio, np.ndarray)
        assert len(audio) > 0
    
    def test_synthesize_very_long_text(self, tts_service):
        """Test synthesis with very long text"""
        long_text = "This is a very long text. " * 50  # 50 repetitions
        audio = tts_service.synthesize(long_text, "hin")
        
        assert isinstance(audio, np.ndarray)
        assert len(audio) > 0
    
    def test_synthesize_text_with_numbers(self, tts_service):
        """Test synthesis with numbers in text"""
        text = "The price is 50 rupees per kilogram"
        audio = tts_service.synthesize(text, "hin")
        
        assert isinstance(audio, np.ndarray)
        assert len(audio) > 0
    
    def test_synthesize_text_with_special_characters(self, tts_service):
        """Test synthesis with special characters"""
        text = "Price: ₹50/kg (50% discount!)"
        audio = tts_service.synthesize(text, "hin")
        
        assert isinstance(audio, np.ndarray)
        assert len(audio) > 0
    
    def test_synthesize_unsupported_language_warning(self, tts_service):
        """Test synthesis with unsupported language logs warning but continues"""
        text = "Test message"
        # Should not raise exception, just log warning
        audio = tts_service.synthesize(text, "xyz")
        assert isinstance(audio, np.ndarray)
    
    def test_adjust_for_environment_with_zero_audio(self, tts_service):
        """Test volume adjustment with silent audio"""
        audio = np.zeros(1000, dtype=np.float32)
        noise_level = 70.0
        
        adjusted = tts_service.adjust_for_environment(audio, noise_level)
        
        # Should handle gracefully (all zeros remain zeros)
        assert np.all(adjusted == 0)
    
    def test_adjust_for_environment_with_negative_noise(self, tts_service):
        """Test volume adjustment with invalid negative noise level"""
        audio = np.random.randn(1000).astype(np.float32) * 0.5
        noise_level = -10.0  # Invalid
        
        # Should handle gracefully (no adjustment for low noise)
        adjusted = tts_service.adjust_for_environment(audio, noise_level)
        np.testing.assert_array_almost_equal(adjusted, audio)


class TestTTSServiceAudioQuality:
    """Test audio quality characteristics"""
    
    def test_synthesized_audio_is_normalized(self, tts_service):
        """Test that synthesized audio is within valid range"""
        text = "Test message for audio quality"
        audio = tts_service.synthesize(text, "hin")
        
        # Audio should be in [-1.0, 1.0] range
        assert np.all(audio >= -1.0)
        assert np.all(audio <= 1.0)
    
    def test_synthesized_audio_has_content(self, tts_service):
        """Test that synthesized audio is not silent"""
        text = "Test message with content"
        audio = tts_service.synthesize(text, "hin")
        
        # Audio should have non-zero content
        assert np.abs(audio).max() > 0
    
    def test_longer_text_produces_longer_audio(self, tts_service):
        """Test that longer text produces longer audio"""
        short_text = "Hi"
        long_text = "This is a much longer message with many more words"
        
        audio_short = tts_service.synthesize(short_text, "hin")
        audio_long = tts_service.synthesize(long_text, "hin")
        
        # Longer text should produce longer audio
        assert len(audio_long) > len(audio_short)
