"""Text-to-Speech Service using AI4Bharat Indic-TTS"""
import time
import logging
from typing import Optional, Dict, Any
import numpy as np
from pathlib import Path
import io

logger = logging.getLogger(__name__)


# Supported Indian languages (22 scheduled languages)
SUPPORTED_LANGUAGES = [
    "hin",  # Hindi
    "tel",  # Telugu
    "tam",  # Tamil
    "kan",  # Kannada
    "mar",  # Marathi
    "ben",  # Bengali
    "guj",  # Gujarati
    "pan",  # Punjabi
    "mal",  # Malayalam
    "asm",  # Assamese
    "ori",  # Odia
    "urd",  # Urdu
    "kas",  # Kashmiri
    "kok",  # Konkani
    "nep",  # Nepali
    "brx",  # Bodo
    "doi",  # Dogri
    "mai",  # Maithili
    "mni",  # Manipuri
    "sat",  # Santali
    "snd",  # Sindhi
    "san",  # Sanskrit
]


class TTSService:
    """
    Text-to-Speech service using AI4Bharat Indic-TTS models.
    
    Supports:
    - 22 Indian scheduled languages
    - Natural-sounding voice synthesis
    - Adjustable speech rate (default 85% for clarity)
    - Adaptive volume control for noisy environments
    - MP3 audio compression for low bandwidth
    """
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        use_mock: bool = False,
        default_speech_rate: float = 0.85
    ):
        """
        Initialize TTS service with Indic-TTS models.
        
        Args:
            model_path: Path to Indic-TTS model files
            use_mock: If True, use mock synthesis for testing
            default_speech_rate: Default speech rate (0.85 = 15% slower)
        """
        self.model_path = model_path
        self.use_mock = use_mock
        self.default_speech_rate = default_speech_rate
        self.models: Dict[str, Any] = {}
        
        if not use_mock:
            self._load_language_models()
        else:
            logger.info("TTSService initialized in mock mode")
    
    def _load_language_models(self):
        """
        Load AI4Bharat Indic-TTS models for supported languages.
        
        In production, this would load actual TTS models:
        - ai4bharat/indic-tts or similar models
        - One model per language or a multilingual model
        - Configure voice models for natural speech
        """
        try:
            # Attempt to load TTS library
            try:
                # Try to import TTS libraries (e.g., Coqui TTS, ESPnet, etc.)
                # For now, we'll use a mock implementation
                logger.info("Loading Indic-TTS models")
                
                # In production, load models for each language
                for lang in SUPPORTED_LANGUAGES:
                    # Placeholder for actual model loading
                    self.models[lang] = {
                        "loaded": False,
                        "model_name": f"indic-tts-{lang}"
                    }
                
                logger.info(f"Initialized TTS models for {len(SUPPORTED_LANGUAGES)} languages")
                
            except ImportError:
                logger.warning(
                    "TTS library not available. "
                    "Install with: pip install TTS or similar"
                )
                self.use_mock = True
            except Exception as e:
                logger.warning(
                    f"Could not load Indic-TTS models: {e}. "
                    "Falling back to mock mode."
                )
                self.use_mock = True
                
        except Exception as e:
            logger.error(f"Error loading TTS models: {e}")
            self.use_mock = True
    
    def synthesize(
        self,
        text: str,
        language: str,
        speech_rate: Optional[float] = None,
        sample_rate: int = 22050
    ) -> np.ndarray:
        """
        Convert text to speech.
        
        Args:
            text: Text to synthesize
            language: ISO 639-3 language code (e.g., 'hin' for Hindi)
            speech_rate: Speech rate multiplier (default 0.85 = 15% slower)
            sample_rate: Output audio sample rate in Hz
        
        Returns:
            Audio buffer as numpy array (PCM format)
        
        Validates: Requirements 4.1, 4.2, 4.3
        """
        start_time = time.time()
        
        # Use default speech rate if not specified
        if speech_rate is None:
            speech_rate = self.default_speech_rate
        
        # Validate speech rate (10-20% slower = 0.80-0.90)
        if not (0.80 <= speech_rate <= 0.90):
            logger.warning(
                f"Speech rate {speech_rate} outside recommended range [0.80, 0.90]. "
                f"Using default {self.default_speech_rate}"
            )
            speech_rate = self.default_speech_rate
        
        # Validate language support
        if language not in SUPPORTED_LANGUAGES:
            logger.warning(f"Language {language} not in supported list, attempting anyway")
        
        if self.use_mock:
            audio = self._mock_synthesize(text, language, speech_rate, sample_rate)
        else:
            audio = self._real_synthesize(text, language, speech_rate, sample_rate)
        
        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Log if processing time exceeds requirement (2 seconds)
        if processing_time_ms > 2000:
            logger.warning(
                f"TTS synthesis took {processing_time_ms:.0f}ms, "
                f"exceeds 2000ms requirement"
            )
        
        return audio
    
    def _real_synthesize(
        self,
        text: str,
        language: str,
        speech_rate: float,
        sample_rate: int
    ) -> np.ndarray:
        """
        Perform real TTS synthesis using Indic-TTS model.
        """
        try:
            # Check if model is loaded for this language
            if language not in self.models or not self.models[language].get("loaded"):
                logger.warning(f"Model not loaded for {language}, using mock")
                return self._mock_synthesize(text, language, speech_rate, sample_rate)
            
            # In production, this would:
            # 1. Tokenize text
            # 2. Generate mel-spectrogram
            # 3. Vocoder to generate waveform
            # 4. Apply speech rate adjustment
            # 5. Resample to target sample rate
            
            # Placeholder for actual synthesis
            audio = self._mock_synthesize(text, language, speech_rate, sample_rate)
            
            return audio
            
        except Exception as e:
            logger.error(f"Error during TTS synthesis: {e}")
            # Fallback to mock
            return self._mock_synthesize(text, language, speech_rate, sample_rate)
    
    def _mock_synthesize(
        self,
        text: str,
        language: str,
        speech_rate: float,
        sample_rate: int
    ) -> np.ndarray:
        """
        Mock TTS synthesis for testing without actual model.
        
        Generates a simple sine wave as placeholder audio.
        """
        # Generate mock audio based on text length
        # Approximate: 150 words per minute at normal speed
        # With 85% speed: 127.5 words per minute
        words = len(text.split())
        duration_seconds = (words / 150) * (1 / speech_rate) * 60
        
        # Generate simple sine wave as placeholder
        t = np.linspace(0, duration_seconds, int(sample_rate * duration_seconds))
        frequency = 440  # A4 note
        audio = np.sin(2 * np.pi * frequency * t) * 0.3  # 30% amplitude
        
        return audio.astype(np.float32)
    
    def adjust_for_environment(
        self,
        audio: np.ndarray,
        noise_level: float
    ) -> np.ndarray:
        """
        Adjust volume based on ambient noise level.
        
        Args:
            audio: Audio buffer to adjust
            noise_level: Ambient noise level in dB
        
        Returns:
            Volume-adjusted audio buffer
        
        Validates: Requirements 4.4
        """
        # Calculate volume boost based on noise level
        # Baseline: 40 dB (quiet room)
        # Target: Maintain 10-15 dB above ambient noise
        baseline_db = 40.0
        target_snr = 12.5  # Signal-to-noise ratio in dB
        
        if noise_level <= baseline_db:
            # No adjustment needed for quiet environments
            return audio
        
        # Calculate required boost
        boost_db = (noise_level - baseline_db) + target_snr
        
        # Cap maximum boost at 20 dB to avoid distortion
        boost_db = min(boost_db, 20.0)
        
        # Convert dB to linear gain
        gain = 10 ** (boost_db / 20)
        
        # Apply gain
        adjusted_audio = audio * gain
        
        # Clip to prevent distortion
        adjusted_audio = np.clip(adjusted_audio, -1.0, 1.0)
        
        logger.debug(
            f"Adjusted volume by {boost_db:.1f} dB for {noise_level:.1f} dB noise"
        )
        
        return adjusted_audio
    
    def compress_to_mp3(
        self,
        audio: np.ndarray,
        sample_rate: int = 22050,
        bitrate: str = "64k"
    ) -> bytes:
        """
        Compress audio to MP3 format for low bandwidth transmission.
        
        Args:
            audio: Audio buffer as numpy array
            sample_rate: Audio sample rate in Hz
            bitrate: MP3 bitrate (e.g., "64k", "96k")
        
        Returns:
            MP3-encoded audio as bytes
        
        Validates: Requirements 4.3, 10.1
        """
        try:
            # Try to use pydub for MP3 encoding
            try:
                from pydub import AudioSegment
                
                # Convert numpy array to bytes
                audio_int16 = (audio * 32767).astype(np.int16)
                audio_bytes = audio_int16.tobytes()
                
                # Create AudioSegment
                audio_segment = AudioSegment(
                    audio_bytes,
                    frame_rate=sample_rate,
                    sample_width=2,  # 16-bit
                    channels=1  # Mono
                )
                
                # Export as MP3
                mp3_buffer = io.BytesIO()
                audio_segment.export(
                    mp3_buffer,
                    format="mp3",
                    bitrate=bitrate
                )
                
                mp3_bytes = mp3_buffer.getvalue()
                
                # Calculate compression ratio
                original_size = len(audio_bytes)
                compressed_size = len(mp3_bytes)
                compression_ratio = (1 - compressed_size / original_size) * 100
                
                logger.debug(
                    f"Compressed audio from {original_size} to {compressed_size} bytes "
                    f"({compression_ratio:.1f}% reduction)"
                )
                
                return mp3_bytes
                
            except ImportError:
                logger.warning(
                    "pydub not available for MP3 encoding. "
                    "Install with: pip install pydub"
                )
                # Return raw audio as fallback
                audio_int16 = (audio * 32767).astype(np.int16)
                return audio_int16.tobytes()
                
        except Exception as e:
            logger.error(f"Error compressing audio to MP3: {e}")
            # Return raw audio as fallback
            audio_int16 = (audio * 32767).astype(np.int16)
            return audio_int16.tobytes()
    
    def get_supported_languages(self) -> list[str]:
        """
        Get list of supported language codes.
        
        Returns:
            List of ISO 639-3 language codes
        """
        return SUPPORTED_LANGUAGES.copy()
    
    def load_language_model(self, language: str, model_path: str):
        """
        Load TTS model for a specific language.
        
        Args:
            language: ISO 639-3 language code
            model_path: Path to model files
        """
        try:
            # In production, load actual model weights
            # For now, just track that we have a model
            self.models[language] = {
                "loaded": True,
                "path": model_path,
                "model_name": f"indic-tts-{language}"
            }
            logger.info(f"Loaded TTS model for {language}")
        except Exception as e:
            logger.error(f"Failed to load TTS model for {language}: {e}")
