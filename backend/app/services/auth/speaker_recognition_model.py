"""Speaker recognition model using SpeechBrain ECAPA-TDNN"""
import os
import logging
from typing import Optional
import numpy as np
import torch

# Set torchaudio backend to soundfile before importing torchaudio
# This fixes compatibility issues with newer torchaudio versions
os.environ.setdefault("TORCHAUDIO_BACKEND", "soundfile")

import torchaudio
from pathlib import Path

# Monkey patch for torchaudio 2.10+ compatibility with SpeechBrain
# The list_audio_backends() function was removed in torchaudio 2.1+
# This workaround ensures SpeechBrain works with newer torchaudio versions
if not hasattr(torchaudio, 'list_audio_backends'):
    def _list_audio_backends():
        """Compatibility shim for torchaudio 2.1+"""
        return ["soundfile"]
    torchaudio.list_audio_backends = _list_audio_backends

logger = logging.getLogger(__name__)


class SpeakerRecognitionModel:
    """
    Speaker recognition model using SpeechBrain's ECAPA-TDNN.
    
    This model extracts speaker embeddings from audio for voice biometric
    authentication. It uses the pre-trained ECAPA-TDNN model from SpeechBrain
    which is trained on VoxCeleb for speaker recognition tasks.
    
    Requirements: 21.7
    """
    
    def __init__(
        self,
        model_name: str = "speechbrain/spkrec-ecapa-voxceleb",
        device: Optional[str] = None
    ):
        """
        Initialize the speaker recognition model.
        
        Args:
            model_name: HuggingFace model identifier for SpeechBrain model
            device: Device to run model on ('cpu', 'cuda', or None for auto-detect)
        """
        self.model_name = model_name
        self.device = device or self._get_device()
        self.model = None
        self.classifier = None
        self._is_loaded = False
        
        logger.info(f"Initializing SpeakerRecognitionModel with {model_name} on {self.device}")
    
    def _get_device(self) -> str:
        """Automatically detect the best available device"""
        if torch.cuda.is_available():
            return "cuda"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"
    
    def load_model(self) -> None:
        """
        Download and load the ECAPA-TDNN model for speaker embeddings.
        
        This method downloads the pre-trained model from HuggingFace if not
        already cached, and loads it into memory for inference.
        
        Requirements: 21.7
        """
        if self._is_loaded:
            logger.info("Model already loaded")
            return
        
        try:
            logger.info(f"Loading SpeechBrain model: {self.model_name}")
            
            # Import SpeechBrain here to avoid import errors if not installed
            try:
                from speechbrain.inference.speaker import EncoderClassifier
            except ImportError:
                raise ImportError(
                    "SpeechBrain is not installed. Please install it with: "
                    "pip install speechbrain"
                )
            
            # Load the pre-trained ECAPA-TDNN model
            # This will download the model if not already cached
            self.classifier = EncoderClassifier.from_hparams(
                source=self.model_name,
                savedir=self._get_model_cache_dir(),
                run_opts={"device": self.device}
            )
            
            self._is_loaded = True
            logger.info("Model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load speaker recognition model: {e}")
            raise RuntimeError(f"Failed to load model: {e}")
    
    def _get_model_cache_dir(self) -> str:
        """Get the directory for caching downloaded models"""
        cache_dir = os.getenv("MODEL_CACHE_DIR", "./models/speaker_recognition")
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        return cache_dir
    
    def extract_embedding(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000
    ) -> np.ndarray:
        """
        Extract speaker embedding from audio.
        
        Args:
            audio: Audio data as numpy array (mono, float32)
            sample_rate: Sample rate of the audio (default: 16000 Hz)
        
        Returns:
            Speaker embedding as numpy array (192-dimensional for ECAPA-TDNN)
        
        Requirements: 21.7
        """
        if not self._is_loaded:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        try:
            # Ensure audio is the right shape and type
            if audio.ndim == 1:
                # Add batch dimension if needed
                audio = audio.reshape(1, -1)
            
            # Convert to torch tensor
            audio_tensor = torch.from_numpy(audio).float()
            
            # Resample if necessary
            if sample_rate != 16000:
                logger.debug(f"Resampling audio from {sample_rate} Hz to 16000 Hz")
                resampler = torchaudio.transforms.Resample(
                    orig_freq=sample_rate,
                    new_freq=16000
                )
                audio_tensor = resampler(audio_tensor)
            
            # Move to device
            audio_tensor = audio_tensor.to(self.device)
            
            # Extract embedding
            with torch.no_grad():
                embedding = self.classifier.encode_batch(audio_tensor)
            
            # Convert back to numpy and squeeze to 1D
            embedding_np = embedding.cpu().numpy().squeeze()
            
            logger.debug(f"Extracted embedding with shape: {embedding_np.shape}")
            return embedding_np
            
        except Exception as e:
            logger.error(f"Failed to extract embedding: {e}")
            raise RuntimeError(f"Embedding extraction failed: {e}")
    
    def compute_similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray
    ) -> float:
        """
        Compute cosine similarity between two speaker embeddings.
        
        Args:
            embedding1: First speaker embedding
            embedding2: Second speaker embedding
        
        Returns:
            Similarity score between 0.0 and 1.0 (higher = more similar)
        """
        try:
            # Normalize embeddings
            emb1_norm = embedding1 / np.linalg.norm(embedding1)
            emb2_norm = embedding2 / np.linalg.norm(embedding2)
            
            # Compute cosine similarity
            similarity = np.dot(emb1_norm, emb2_norm)
            
            # Convert from [-1, 1] to [0, 1] range
            similarity = (similarity + 1.0) / 2.0
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Failed to compute similarity: {e}")
            raise RuntimeError(f"Similarity computation failed: {e}")
    
    def average_embeddings(
        self,
        embeddings: list[np.ndarray]
    ) -> np.ndarray:
        """
        Average multiple speaker embeddings to create a robust voiceprint.
        
        Args:
            embeddings: List of speaker embeddings
        
        Returns:
            Averaged embedding
        """
        if not embeddings:
            raise ValueError("Cannot average empty list of embeddings")
        
        # Stack and average
        embeddings_array = np.stack(embeddings, axis=0)
        averaged = np.mean(embeddings_array, axis=0)
        
        # Normalize the averaged embedding
        averaged = averaged / np.linalg.norm(averaged)
        
        return averaged
    
    def validate_audio_quality(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000,
        min_duration_seconds: float = 1.0,
        max_duration_seconds: float = 30.0
    ) -> tuple[bool, Optional[str]]:
        """
        Validate audio quality for speaker recognition.
        
        Args:
            audio: Audio data as numpy array
            sample_rate: Sample rate of the audio
            min_duration_seconds: Minimum required duration
            max_duration_seconds: Maximum allowed duration
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check duration
        duration = len(audio) / sample_rate
        if duration < min_duration_seconds:
            return False, f"Audio too short: {duration:.2f}s (minimum: {min_duration_seconds}s)"
        if duration > max_duration_seconds:
            return False, f"Audio too long: {duration:.2f}s (maximum: {max_duration_seconds}s)"
        
        # Check for silence (very low amplitude)
        rms = np.sqrt(np.mean(audio ** 2))
        if rms < 0.001:
            return False, "Audio appears to be silent or too quiet"
        
        # Check for clipping
        clipping_ratio = np.sum(np.abs(audio) > 0.99) / len(audio)
        if clipping_ratio > 0.01:  # More than 1% clipping
            return False, f"Audio has excessive clipping: {clipping_ratio*100:.1f}%"
        
        return True, None
    
    def unload_model(self) -> None:
        """Unload the model from memory"""
        if self._is_loaded:
            self.classifier = None
            self.model = None
            self._is_loaded = False
            
            # Clear CUDA cache if using GPU
            if self.device == "cuda":
                torch.cuda.empty_cache()
            
            logger.info("Model unloaded from memory")
    
    @property
    def is_loaded(self) -> bool:
        """Check if model is loaded"""
        return self._is_loaded
    
    @property
    def embedding_dimension(self) -> int:
        """Get the dimension of the speaker embeddings"""
        # ECAPA-TDNN produces 192-dimensional embeddings
        return 192
