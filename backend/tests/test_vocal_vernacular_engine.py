"""Unit tests for VocalVernacularEngine orchestrator"""
import pytest
import numpy as np
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from app.services.vocal_vernacular.vocal_vernacular_engine import VocalVernacularEngine
from app.services.vocal_vernacular.models import (
    VoiceResponse,
    ConversationContext,
    Message,
    LanguageResult,
    TranscriptionResult,
    TranslationResult,
    TTSResult
)
from datetime import datetime


class TestVocalVernacularEngine:
    """Test suite for VocalVernacularEngine"""
    
    @pytest.fixture
    def sample_audio(self):
        """Create sample audio data (1 second at 16kHz)"""
        sample_rate = 16000
        duration = 1.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio = np.sin(2 * np.pi * 440 * t) * 0.3
        return audio.astype(np.float32)
    
    @pytest.fixture
    def mock_language_detector(self):
        """Create mock language detector"""
        detector = Mock()
        detector.detect_language.return_value = LanguageResult(
            language='hin',
            confidence=0.95,
            dialect=None
        )
        detector.is_supported_language.return_value = True
        return detector
    
    @pytest.fixture
    def mock_stt_service(self):
        """Create mock STT service"""
        stt = Mock()
        stt.transcribe.return_value = TranscriptionResult(
            text="नमस्ते, टमाटर का भाव क्या है?",
            confidence=0.92,
            language='hin',
            processing_time_ms=500
        )
        return stt
    
    @pytest.fixture
    def mock_translation_service(self):
        """Create mock translation service"""
        translator = Mock()
        translator.translate.return_value = TranslationResult(
            text="Hello, what is the price of tomatoes?",
            confidence=0.94,
            source_language='hin',
            target_language='tel',
            processing_time_ms=300
        )
        translator.translate_with_context.return_value = TranslationResult(
            text="Hello, what is the price of tomatoes?",
            confidence=0.96,
            source_language='hin',
            target_language='tel',
            processing_time_ms=350
        )
        return translator
    
    @pytest.fixture
    def mock_tts_service(self):
        """Create mock TTS service"""
        tts = Mock()
        tts.synthesize.return_value = TTSResult(
            audio=b'fake_audio_data',
            format='mp3',
            sample_rate=22050,
            duration_seconds=2.5,
            speech_rate=0.85,
            processing_time_ms=400
        )
        return tts
    
    @pytest.fixture
    def engine(self, mock_language_detector, mock_stt_service, mock_translation_service, mock_tts_service):
        """Create VocalVernacularEngine with mocked services"""
        return VocalVernacularEngine(
            language_detector=mock_language_detector,
            stt_service=mock_stt_service,
            translation_service=mock_translation_service,
            tts_service=mock_tts_service
        )
    
    @pytest.mark.asyncio
    async def test_process_voice_message_basic(self, engine, sample_audio):
        """Test basic voice message processing"""
        result = await engine.process_voice_message(
            audio=sample_audio,
            target_language='tel'
        )
        
        assert isinstance(result, VoiceResponse)
        assert result.audio == b'fake_audio_data'
        assert result.transcription == "नमस्ते, टमाटर का भाव क्या है?"
        assert result.translation == "Hello, what is the price of tomatoes?"
        assert result.source_language == 'hin'
        assert result.target_language == 'tel'
        assert result.latency_ms > 0
    
    @pytest.mark.asyncio
    async def test_process_voice_message_latency_requirement(self, engine, sample_audio):
        """Test that pipeline completes within 8 seconds (Requirement 5.1)"""
        import time
        
        start_time = time.time()
        result = await engine.process_voice_message(
            audio=sample_audio,
            target_language='tel'
        )
        elapsed_time = (time.time() - start_time) * 1000
        
        assert elapsed_time < 8000, f"Pipeline took {elapsed_time:.0f}ms, exceeds 8000ms threshold"
        assert result.latency_ms < 8000
    
    @pytest.mark.asyncio
    async def test_process_voice_message_with_context(self, engine, sample_audio):
        """Test voice processing with conversation context"""
        context = ConversationContext(
            conversation_id='conv_123',
            participants=['user1', 'user2'],
            messages=[
                Message(
                    id='msg1',
                    sender_id='user1',
                    text='Previous message',
                    language='hin',
                    timestamp=datetime.now()
                )
            ]
        )
        
        result = await engine.process_voice_message(
            audio=sample_audio,
            target_language='tel',
            conversation_context=context
        )
        
        assert isinstance(result, VoiceResponse)
        # Verify that translate_with_context was called
        engine.translation_service.translate_with_context.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_voice_message_skip_language_detection(self, engine, sample_audio):
        """Test processing with known source language (skip detection)"""
        result = await engine.process_voice_message(
            audio=sample_audio,
            target_language='tel',
            source_language='hin',
            auto_detect_language=False
        )
        
        assert result.source_language == 'hin'
        # Verify language detection was not called
        engine.language_detector.detect_language.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_process_voice_message_same_language(self, engine, sample_audio):
        """Test processing when source and target languages are the same"""
        result = await engine.process_voice_message(
            audio=sample_audio,
            target_language='hin',
            source_language='hin',
            auto_detect_language=False
        )
        
        assert result.source_language == 'hin'
        assert result.target_language == 'hin'
        # Translation should still be called but will skip actual translation
        assert result.translation is not None
    
    @pytest.mark.asyncio
    async def test_process_voice_message_empty_audio(self, engine):
        """Test processing with empty audio"""
        empty_audio = np.array([])
        
        with pytest.raises(RuntimeError, match="Audio buffer is empty"):
            await engine.process_voice_message(
                audio=empty_audio,
                target_language='tel'
            )
    
    @pytest.mark.asyncio
    async def test_process_voice_message_unsupported_language(self, engine, sample_audio):
        """Test processing with unsupported target language"""
        engine.language_detector.is_supported_language.return_value = False
        
        with pytest.raises(RuntimeError, match="Target language .* is not supported"):
            await engine.process_voice_message(
                audio=sample_audio,
                target_language='xyz'
            )
    
    @pytest.mark.asyncio
    async def test_process_voice_message_stage_latencies(self, engine, sample_audio):
        """Test that stage latencies are tracked"""
        result = await engine.process_voice_message(
            audio=sample_audio,
            target_language='tel'
        )
        
        assert 'language_detection' in result.stage_latencies
        assert 'transcription' in result.stage_latencies
        assert 'translation' in result.stage_latencies
        assert 'synthesis' in result.stage_latencies
        
        # All latencies should be positive
        for stage, latency in result.stage_latencies.items():
            assert latency > 0, f"Stage {stage} has invalid latency: {latency}"
    
    @pytest.mark.asyncio
    async def test_process_voice_message_confidence_scores(self, engine, sample_audio):
        """Test that confidence scores are tracked"""
        result = await engine.process_voice_message(
            audio=sample_audio,
            target_language='tel'
        )
        
        assert 'transcription' in result.confidence_scores
        assert 'translation' in result.confidence_scores
        
        # All confidence scores should be between 0 and 1
        for stage, confidence in result.confidence_scores.items():
            assert 0.0 <= confidence <= 1.0, f"Stage {stage} has invalid confidence: {confidence}"
    
    @pytest.mark.asyncio
    async def test_process_voice_message_retry_on_failure(self, engine, sample_audio):
        """Test retry logic when a stage fails"""
        # Make STT fail twice then succeed
        engine.stt_service.transcribe.side_effect = [
            Exception("Network error"),
            Exception("Network error"),
            TranscriptionResult(
                text="Retry success",
                confidence=0.90,
                language='hin',
                processing_time_ms=500
            )
        ]
        
        result = await engine.process_voice_message(
            audio=sample_audio,
            target_language='tel'
        )
        
        assert result.transcription == "Retry success"
        # Verify STT was called 3 times (2 failures + 1 success)
        assert engine.stt_service.transcribe.call_count == 3
    
    @pytest.mark.asyncio
    async def test_process_voice_message_failure_after_retries(self, engine, sample_audio):
        """Test that pipeline fails after max retries"""
        # Make STT fail all attempts
        engine.stt_service.transcribe.side_effect = Exception("Persistent error")
        
        with pytest.raises(RuntimeError, match="Voice translation pipeline failed"):
            await engine.process_voice_message(
                audio=sample_audio,
                target_language='tel'
            )
        
        # Verify STT was called 3 times (max retries)
        assert engine.stt_service.transcribe.call_count == 3
    
    @pytest.mark.asyncio
    async def test_get_pipeline_stats(self, engine, sample_audio):
        """Test getting pipeline statistics"""
        await engine.process_voice_message(
            audio=sample_audio,
            target_language='tel'
        )
        
        stats = engine.get_pipeline_stats()
        
        assert 'stages' in stats
        assert 'total_stages' in stats
        assert 'successful_stages' in stats
        assert 'failed_stages' in stats
        
        assert stats['total_stages'] == 4  # detect, transcribe, translate, synthesize
        assert stats['successful_stages'] == 4
        assert stats['failed_stages'] == 0
        
        # Check stage details
        for stage in stats['stages']:
            assert 'name' in stage
            assert 'duration_ms' in stage
            assert 'success' in stage
            assert stage['success'] is True
    
    @pytest.mark.asyncio
    async def test_get_pipeline_stats_with_failure(self, engine, sample_audio):
        """Test pipeline stats when a stage fails"""
        # Make translation fail all attempts
        engine.translation_service.translate.side_effect = Exception("Translation error")
        
        with pytest.raises(RuntimeError):
            await engine.process_voice_message(
                audio=sample_audio,
                target_language='tel'
            )
        
        stats = engine.get_pipeline_stats()
        
        # Should have 3 stages: detect, transcribe, translate (failed)
        assert stats['total_stages'] == 3
        assert stats['successful_stages'] == 2
        assert stats['failed_stages'] == 1
        
        # Check that translation stage is marked as failed
        translation_stage = next(s for s in stats['stages'] if s['name'] == 'translation')
        assert translation_stage['success'] is False
        assert translation_stage['error'] is not None
    
    @pytest.mark.asyncio
    async def test_process_voice_message_different_sample_rates(self, engine):
        """Test processing with different sample rates"""
        # Test with 8kHz
        audio_8k = np.random.randn(8000).astype(np.float32) * 0.1
        result_8k = await engine.process_voice_message(
            audio=audio_8k,
            target_language='tel',
            sample_rate=8000
        )
        assert result_8k is not None
        
        # Test with 44.1kHz
        audio_44k = np.random.randn(44100).astype(np.float32) * 0.1
        result_44k = await engine.process_voice_message(
            audio=audio_44k,
            target_language='tel',
            sample_rate=44100
        )
        assert result_44k is not None
    
    @pytest.mark.asyncio
    async def test_engine_initialization_with_defaults(self):
        """Test that engine can be initialized with default services"""
        engine = VocalVernacularEngine()
        
        assert engine.language_detector is not None
        assert engine.stt_service is not None
        assert engine.translation_service is not None
        assert engine.tts_service is not None
