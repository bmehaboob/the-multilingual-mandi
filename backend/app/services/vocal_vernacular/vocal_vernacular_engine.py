"""Vocal Vernacular Engine - Main orchestrator for voice-to-voice translation"""
import logging
import time
import asyncio
from typing import Optional
import numpy as np

from .language_detector import LanguageDetector
from .stt_service import STTService
from .translation_service import TranslationService
from .tts_service import TTSService
from .models import (
    VoiceResponse,
    ConversationContext,
    PipelineStage,
    TranscriptionResult,
    TranslationResult,
    TTSResult
)

logger = logging.getLogger(__name__)


class VocalVernacularEngine:
    """
    Main orchestrator for voice-to-voice translation pipeline.
    
    Pipeline: Audio → Detect Language → STT → Translate → TTS
    
    Requirements:
    - 5.1: Complete voice-to-voice translation within 8 seconds
    - 5.3: Queue messages and process in order during poor connectivity
    """
    
    def __init__(
        self,
        language_detector: Optional[LanguageDetector] = None,
        stt_service: Optional[STTService] = None,
        translation_service: Optional[TranslationService] = None,
        tts_service: Optional[TTSService] = None
    ):
        """
        Initialize the Vocal Vernacular Engine.
        
        Args:
            language_detector: Language detection service (creates new if None)
            stt_service: Speech-to-text service (creates new if None)
            translation_service: Translation service (creates new if None)
            tts_service: Text-to-speech service (creates new if None)
        """
        self.language_detector = language_detector or LanguageDetector()
        self.stt_service = stt_service or STTService()
        self.translation_service = translation_service or TranslationService()
        self.tts_service = tts_service or TTSService()
        
        # Track pipeline stages for latency monitoring
        self.stages = []
        
        logger.info("VocalVernacularEngine initialized")
    
    async def process_voice_message(
        self,
        audio: np.ndarray,
        target_language: str,
        conversation_context: Optional[ConversationContext] = None,
        sample_rate: int = 16000,
        auto_detect_language: bool = True,
        source_language: Optional[str] = None
    ) -> VoiceResponse:
        """
        Complete voice-to-voice translation pipeline.
        
        Pipeline stages:
        1. Detect language (< 2s) - if auto_detect_language is True
        2. Transcribe speech to text (< 3s)
        3. Translate text (< 2s)
        4. Synthesize speech (< 2s)
        
        Target: Complete within 8 seconds (Requirement 5.1)
        
        Args:
            audio: Audio buffer as numpy array (PCM format)
            target_language: Target language code (ISO 639-3)
            conversation_context: Optional conversation context for better translation
            sample_rate: Sample rate of audio (default 16000 Hz)
            auto_detect_language: Whether to auto-detect source language
            source_language: Source language if known (skips detection)
        
        Returns:
            VoiceResponse with translated audio and metadata
        
        Raises:
            ValueError: If audio is invalid or languages are unsupported
            RuntimeError: If pipeline fails after retries
        """
        pipeline_start = time.time()
        self.stages = []
        stage_latencies = {}
        confidence_scores = {}
        
        try:
            # Validate inputs
            if audio is None or len(audio) == 0:
                raise ValueError("Audio buffer is empty")
            
            if not self.language_detector.is_supported_language(target_language):
                raise ValueError(f"Target language '{target_language}' is not supported")
            
            logger.info(f"Starting voice-to-voice translation pipeline (target: {target_language})")
            
            # Stage 1: Language Detection (< 2s)
            if auto_detect_language and source_language is None:
                detected_lang = await self._detect_language_stage(audio, sample_rate)
                source_language = detected_lang
                stage_latencies['language_detection'] = self.stages[-1].duration_ms
            elif source_language is None:
                source_language = 'hin'  # Default to Hindi
                logger.info(f"Using default source language: {source_language}")
            else:
                logger.info(f"Using provided source language: {source_language}")
            
            # Stage 2: Speech-to-Text (< 3s)
            transcription = await self._transcribe_stage(audio, source_language, sample_rate)
            stage_latencies['transcription'] = self.stages[-1].duration_ms
            confidence_scores['transcription'] = transcription.confidence
            
            # Stage 3: Translation (< 2s)
            translation = await self._translate_stage(
                transcription.text,
                source_language,
                target_language,
                conversation_context
            )
            stage_latencies['translation'] = self.stages[-1].duration_ms
            confidence_scores['translation'] = translation.confidence
            
            # Stage 4: Text-to-Speech (< 2s)
            tts_result = await self._synthesize_stage(translation.text, target_language)
            stage_latencies['synthesis'] = self.stages[-1].duration_ms
            
            # Calculate total latency
            total_latency = (time.time() - pipeline_start) * 1000
            
            # Log performance
            logger.info(f"Pipeline complete in {total_latency:.0f}ms")
            logger.info(f"Stage latencies: {stage_latencies}")
            
            # Check latency requirement (< 8 seconds)
            if total_latency > 8000:
                logger.warning(f"Pipeline exceeded 8s threshold: {total_latency:.0f}ms")
            
            return VoiceResponse(
                audio=tts_result.audio,
                transcription=transcription.text,
                translation=translation.text,
                source_language=source_language,
                target_language=target_language,
                latency_ms=total_latency,
                stage_latencies=stage_latencies,
                confidence_scores=confidence_scores
            )
            
        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}")
            # Record failed stage
            if self.stages and self.stages[-1].end_time is None:
                self.stages[-1].end_time = time.time()
                self.stages[-1].success = False
                self.stages[-1].error = str(e)
            raise RuntimeError(f"Voice translation pipeline failed: {str(e)}") from e
    
    async def _detect_language_stage(
        self,
        audio: np.ndarray,
        sample_rate: int
    ) -> str:
        """
        Execute language detection stage with retry logic.
        
        Args:
            audio: Audio buffer
            sample_rate: Sample rate
        
        Returns:
            Detected language code
        """
        stage = PipelineStage(name="language_detection", start_time=time.time())
        self.stages.append(stage)
        
        try:
            # Retry logic: up to 3 attempts
            for attempt in range(3):
                try:
                    lang_result = self.language_detector.detect_language(audio, sample_rate)
                    stage.end_time = time.time()
                    logger.info(f"Language detected: {lang_result.language} (confidence: {lang_result.confidence:.2f})")
                    return lang_result.language
                except Exception as e:
                    if attempt == 2:  # Last attempt
                        raise
                    logger.warning(f"Language detection attempt {attempt + 1} failed: {str(e)}")
                    await asyncio.sleep(0.5 * (attempt + 1))  # Exponential backoff
            
        except Exception as e:
            stage.end_time = time.time()
            stage.success = False
            stage.error = str(e)
            logger.error(f"Language detection failed after retries: {str(e)}")
            raise
    
    async def _transcribe_stage(
        self,
        audio: np.ndarray,
        language: str,
        sample_rate: int
    ) -> TranscriptionResult:
        """
        Execute speech-to-text stage with retry logic.
        
        Args:
            audio: Audio buffer
            language: Source language
            sample_rate: Sample rate
        
        Returns:
            TranscriptionResult
        """
        stage = PipelineStage(name="transcription", start_time=time.time())
        self.stages.append(stage)
        
        try:
            # Retry logic: up to 3 attempts
            for attempt in range(3):
                try:
                    transcription = self.stt_service.transcribe(audio, language, sample_rate)
                    stage.end_time = time.time()
                    logger.info(f"Transcription: '{transcription.text}' (confidence: {transcription.confidence:.2f})")
                    return transcription
                except Exception as e:
                    if attempt == 2:  # Last attempt
                        raise
                    logger.warning(f"Transcription attempt {attempt + 1} failed: {str(e)}")
                    await asyncio.sleep(0.5 * (attempt + 1))  # Exponential backoff
            
        except Exception as e:
            stage.end_time = time.time()
            stage.success = False
            stage.error = str(e)
            logger.error(f"Transcription failed after retries: {str(e)}")
            raise
    
    async def _translate_stage(
        self,
        text: str,
        source_language: str,
        target_language: str,
        conversation_context: Optional[ConversationContext] = None
    ) -> TranslationResult:
        """
        Execute translation stage with retry logic.
        
        Args:
            text: Text to translate
            source_language: Source language
            target_language: Target language
            conversation_context: Optional conversation context
        
        Returns:
            TranslationResult
        """
        stage = PipelineStage(name="translation", start_time=time.time())
        self.stages.append(stage)
        
        try:
            # Skip translation if source and target are the same
            if source_language == target_language:
                logger.info("Source and target languages are the same, skipping translation")
                stage.end_time = time.time()
                return TranslationResult(
                    text=text,
                    confidence=1.0,
                    source_language=source_language,
                    target_language=target_language,
                    processing_time_ms=stage.duration_ms
                )
            
            # Retry logic: up to 3 attempts
            for attempt in range(3):
                try:
                    # Use context-aware translation if context is provided
                    if conversation_context and conversation_context.messages:
                        translation = self.translation_service.translate_with_context(
                            text,
                            source_language,
                            target_language,
                            conversation_context.messages
                        )
                    else:
                        translation = self.translation_service.translate(
                            text,
                            source_language,
                            target_language
                        )
                    
                    stage.end_time = time.time()
                    logger.info(f"Translation: '{translation.text}' (confidence: {translation.confidence:.2f})")
                    return translation
                except Exception as e:
                    if attempt == 2:  # Last attempt
                        raise
                    logger.warning(f"Translation attempt {attempt + 1} failed: {str(e)}")
                    await asyncio.sleep(0.5 * (attempt + 1))  # Exponential backoff
            
        except Exception as e:
            stage.end_time = time.time()
            stage.success = False
            stage.error = str(e)
            logger.error(f"Translation failed after retries: {str(e)}")
            raise
    
    async def _synthesize_stage(
        self,
        text: str,
        language: str
    ) -> TTSResult:
        """
        Execute text-to-speech stage with retry logic.
        
        Args:
            text: Text to synthesize
            language: Target language
        
        Returns:
            TTSResult
        """
        stage = PipelineStage(name="synthesis", start_time=time.time())
        self.stages.append(stage)
        
        try:
            # Retry logic: up to 3 attempts
            for attempt in range(3):
                try:
                    tts_result = self.tts_service.synthesize(text, language)
                    stage.end_time = time.time()
                    logger.info(f"Speech synthesized: {tts_result.duration_seconds:.2f}s audio")
                    return tts_result
                except Exception as e:
                    if attempt == 2:  # Last attempt
                        raise
                    logger.warning(f"TTS attempt {attempt + 1} failed: {str(e)}")
                    await asyncio.sleep(0.5 * (attempt + 1))  # Exponential backoff
            
        except Exception as e:
            stage.end_time = time.time()
            stage.success = False
            stage.error = str(e)
            logger.error(f"TTS failed after retries: {str(e)}")
            raise
    
    def get_pipeline_stats(self) -> dict:
        """
        Get statistics about the last pipeline execution.
        
        Returns:
            Dictionary with stage information and performance metrics
        """
        return {
            'stages': [
                {
                    'name': stage.name,
                    'duration_ms': stage.duration_ms,
                    'success': stage.success,
                    'error': stage.error
                }
                for stage in self.stages
            ],
            'total_stages': len(self.stages),
            'successful_stages': sum(1 for s in self.stages if s.success),
            'failed_stages': sum(1 for s in self.stages if not s.success)
        }
