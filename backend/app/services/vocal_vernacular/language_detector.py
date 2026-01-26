"""Language Detection Service for Vocal Vernacular Engine"""
import logging
from typing import List, Optional
import numpy as np

from .models import LanguageResult, LanguageSegment

logger = logging.getLogger(__name__)

# Supported languages (22 scheduled Indian languages)
SUPPORTED_LANGUAGES = [
    'hin',  # Hindi
    'tel',  # Telugu
    'tam',  # Tamil
    'kan',  # Kannada
    'mar',  # Marathi
    'ben',  # Bengali
    'guj',  # Gujarati
    'pan',  # Punjabi
    'mal',  # Malayalam
    'asm',  # Assamese
    'ori',  # Odia
    'urd',  # Urdu
    'kas',  # Kashmiri
    'kok',  # Konkani
    'nep',  # Nepali
    'brx',  # Bodo
    'doi',  # Dogri
    'mai',  # Maithili
    'mni',  # Manipuri
    'sat',  # Santali
    'snd',  # Sindhi
    'san',  # Sanskrit
]


class LanguageDetector:
    """
    Detects language and dialect from audio using Whisper's built-in detection.
    
    Requirements:
    - 1.2: Detect source language and dialect within 2 seconds
    - 1.6: Handle code-switching (multiple languages in single utterance)
    """
    
    def __init__(self):
        """Initialize the language detector"""
        self.supported_languages = SUPPORTED_LANGUAGES
        logger.info(f"LanguageDetector initialized with {len(self.supported_languages)} supported languages")
    
    def detect_language(self, audio: np.ndarray, sample_rate: int = 16000) -> LanguageResult:
        """
        Detects primary language from audio.
        
        Uses Whisper's built-in language detection capability.
        Target: Complete within 2 seconds (Requirement 1.2)
        
        Args:
            audio: Audio buffer as numpy array (PCM format)
            sample_rate: Sample rate of audio (default 16000 Hz)
        
        Returns:
            LanguageResult with language code (ISO 639-3) and confidence score
        
        Note:
            In production, this would use Whisper's detect_language() method.
            For now, this is a placeholder implementation that simulates detection.
        """
        import time
        start_time = time.time()
        
        try:
            # Validate input
            if audio is None or len(audio) == 0:
                raise ValueError("Audio buffer is empty")
            
            # TODO: Integrate with actual Whisper model for language detection
            # For now, simulate detection with a placeholder
            # In production: result = whisper_model.detect_language(audio)
            
            # Placeholder: Simulate language detection
            # This would be replaced with actual Whisper inference
            detected_language = self._simulate_language_detection(audio)
            confidence = 0.95  # Placeholder confidence
            
            processing_time = (time.time() - start_time) * 1000
            logger.info(f"Language detected: {detected_language} (confidence: {confidence:.2f}, time: {processing_time:.0f}ms)")
            
            # Verify latency requirement (< 2 seconds)
            if processing_time > 2000:
                logger.warning(f"Language detection exceeded 2s threshold: {processing_time:.0f}ms")
            
            return LanguageResult(
                language=detected_language,
                confidence=confidence,
                dialect=None  # Dialect detection can be added later
            )
            
        except Exception as e:
            logger.error(f"Language detection failed: {str(e)}")
            # Fallback to Hindi as default
            return LanguageResult(
                language='hin',
                confidence=0.5,
                dialect=None
            )
    
    def detect_code_switching(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000,
        segment_duration: float = 3.0
    ) -> List[LanguageSegment]:
        """
        Detects multiple languages in single utterance (code-switching).
        
        Splits audio into segments and detects language for each segment.
        Requirement 1.6: Handle code-switching detection
        
        Args:
            audio: Audio buffer as numpy array
            sample_rate: Sample rate of audio
            segment_duration: Duration of each segment in seconds (default 3s)
        
        Returns:
            List of LanguageSegment with (language, start_time, end_time) tuples
        """
        import time
        start_time = time.time()
        
        try:
            if audio is None or len(audio) == 0:
                raise ValueError("Audio buffer is empty")
            
            segments = []
            audio_duration = len(audio) / sample_rate
            
            # Split audio into segments
            segment_samples = int(segment_duration * sample_rate)
            num_segments = int(np.ceil(len(audio) / segment_samples))
            
            logger.info(f"Analyzing {num_segments} segments for code-switching")
            
            for i in range(num_segments):
                start_sample = i * segment_samples
                end_sample = min((i + 1) * segment_samples, len(audio))
                segment_audio = audio[start_sample:end_sample]
                
                # Detect language for this segment
                lang_result = self.detect_language(segment_audio, sample_rate)
                
                start_time_sec = start_sample / sample_rate
                end_time_sec = end_sample / sample_rate
                
                # Only add segment if it's different from previous or first segment
                if not segments or segments[-1].language != lang_result.language:
                    segments.append(LanguageSegment(
                        language=lang_result.language,
                        start_time=start_time_sec,
                        end_time=end_time_sec,
                        confidence=lang_result.confidence
                    ))
                else:
                    # Extend previous segment
                    segments[-1].end_time = end_time_sec
            
            processing_time = (time.time() - start_time) * 1000
            logger.info(f"Code-switching detection complete: {len(segments)} language segments found (time: {processing_time:.0f}ms)")
            
            return segments
            
        except Exception as e:
            logger.error(f"Code-switching detection failed: {str(e)}")
            # Fallback: Return single segment with default language
            return [LanguageSegment(
                language='hin',
                start_time=0.0,
                end_time=len(audio) / sample_rate if audio is not None else 0.0,
                confidence=0.5
            )]
    
    def _simulate_language_detection(self, audio: np.ndarray) -> str:
        """
        Placeholder method to simulate language detection.
        
        In production, this would be replaced with actual Whisper model inference.
        For now, returns Hindi as default with some variation based on audio characteristics.
        
        Args:
            audio: Audio buffer
        
        Returns:
            Language code (ISO 639-3)
        """
        # Simple heuristic based on audio energy for simulation
        # In production, this would use Whisper's detect_language()
        
        if len(audio) == 0:
            return 'hin'
        
        # Calculate simple audio features for simulation
        energy = np.mean(np.abs(audio))
        
        # Simulate different languages based on audio characteristics
        # This is purely for demonstration and would be replaced with real detection
        if energy > 0.1:
            return 'hin'  # Hindi
        elif energy > 0.05:
            return 'tel'  # Telugu
        else:
            return 'tam'  # Tamil
    
    def is_supported_language(self, language_code: str) -> bool:
        """
        Check if a language is supported.
        
        Args:
            language_code: ISO 639-3 language code
        
        Returns:
            True if language is supported, False otherwise
        """
        return language_code in self.supported_languages
    
    def get_supported_languages(self) -> List[str]:
        """
        Get list of all supported languages.
        
        Returns:
            List of ISO 639-3 language codes
        """
        return self.supported_languages.copy()
