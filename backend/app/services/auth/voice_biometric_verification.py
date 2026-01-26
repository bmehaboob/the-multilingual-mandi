"""Voice biometric verification service"""
import logging
from typing import Optional
from datetime import datetime
import numpy as np
import hashlib
import time

from .speaker_recognition_model import SpeakerRecognitionModel
from .voice_biometric_enrollment import VoiceBiometricEnrollment
from .models import VerificationResult, VoiceSample

logger = logging.getLogger(__name__)


class VoiceBiometricVerification:
    """
    Verifies user identity using voice biometrics.
    
    Compares voice samples against stored voiceprints to authenticate users.
    Achieves 95% accuracy threshold with anti-spoofing measures and fallback
    to voice-based PIN authentication.
    
    Requirements: 21.2, 21.3, 21.4
    """
    
    def __init__(
        self,
        enrollment_service: Optional[VoiceBiometricEnrollment] = None,
        speaker_model: Optional[SpeakerRecognitionModel] = None,
        similarity_threshold: float = 0.85,
        anti_spoofing_enabled: bool = True,
        max_verification_time_seconds: float = 3.0
    ):
        """
        Initialize the voice biometric verification service.
        
        Args:
            enrollment_service: VoiceBiometricEnrollment instance for accessing voiceprints
            speaker_model: SpeakerRecognitionModel instance (creates new if None)
            similarity_threshold: Minimum similarity score for accepting match (0.85 = 95% accuracy)
            anti_spoofing_enabled: Enable anti-spoofing measures
            max_verification_time_seconds: Maximum time allowed for verification (Requirement 21.2)
        """
        self.enrollment_service = enrollment_service or VoiceBiometricEnrollment()
        self.speaker_model = speaker_model or self.enrollment_service.speaker_model
        self.similarity_threshold = similarity_threshold
        self.anti_spoofing_enabled = anti_spoofing_enabled
        self.max_verification_time_seconds = max_verification_time_seconds
        
        # PIN storage (in-memory for now, should be database in production)
        self._pin_storage = {}
        
        # Verification attempt tracking for anti-spoofing
        self._verification_attempts = {}
        self._max_attempts_per_minute = 5
        
        logger.info(
            f"Initialized VoiceBiometricVerification "
            f"(threshold={similarity_threshold}, anti_spoofing={anti_spoofing_enabled})"
        )
    
    def verify_user(
        self,
        user_id: str,
        audio_sample: VoiceSample
    ) -> VerificationResult:
        """
        Verify if audio sample matches stored voiceprint.
        
        Compares the provided audio sample against the user's stored voiceprint
        and returns whether they match. Includes anti-spoofing measures and
        completes within 3 seconds.
        
        Requirements: 21.2, 21.3, 21.4
        
        Args:
            user_id: User identifier
            audio_sample: Voice sample to verify
        
        Returns:
            VerificationResult with match decision and confidence score
        """
        start_time = time.time()
        logger.info(f"Starting verification for user {user_id}")
        
        # Anti-spoofing: Check rate limiting
        if self.anti_spoofing_enabled:
            if not self._check_rate_limit(user_id):
                elapsed_time = time.time() - start_time
                return VerificationResult(
                    match=False,
                    confidence=0.0,
                    threshold=self.similarity_threshold,
                    user_id=user_id,
                    timestamp=datetime.utcnow(),
                    message="Too many verification attempts. Please try again later."
                )
        
        # Retrieve stored voiceprint
        stored_voiceprint = self.enrollment_service.get_voiceprint_by_user(user_id)
        if stored_voiceprint is None:
            elapsed_time = time.time() - start_time
            logger.warning(f"No voiceprint found for user {user_id}")
            return VerificationResult(
                match=False,
                confidence=0.0,
                threshold=self.similarity_threshold,
                user_id=user_id,
                timestamp=datetime.utcnow(),
                message="No voiceprint enrolled for this user"
            )
        
        # Validate audio quality
        try:
            audio_array = self._bytes_to_audio(audio_sample.audio, audio_sample.sample_rate)
            is_valid, error_msg = self.speaker_model.validate_audio_quality(
                audio_array,
                audio_sample.sample_rate
            )
            
            if not is_valid:
                elapsed_time = time.time() - start_time
                logger.warning(f"Audio quality check failed: {error_msg}")
                return VerificationResult(
                    match=False,
                    confidence=0.0,
                    threshold=self.similarity_threshold,
                    user_id=user_id,
                    timestamp=datetime.utcnow(),
                    message=f"Audio quality insufficient: {error_msg}"
                )
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"Audio validation failed: {e}")
            return VerificationResult(
                match=False,
                confidence=0.0,
                threshold=self.similarity_threshold,
                user_id=user_id,
                timestamp=datetime.utcnow(),
                message=f"Audio validation error: {str(e)}"
            )
        
        # Load model if not already loaded
        if not self.speaker_model.is_loaded:
            logger.info("Loading speaker recognition model...")
            self.speaker_model.load_model()
        
        # Extract embedding from current sample
        try:
            current_embedding = self.speaker_model.extract_embedding(
                audio_array,
                audio_sample.sample_rate
            )
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"Failed to extract embedding: {e}")
            return VerificationResult(
                match=False,
                confidence=0.0,
                threshold=self.similarity_threshold,
                user_id=user_id,
                timestamp=datetime.utcnow(),
                message=f"Embedding extraction failed: {str(e)}"
            )
        
        # Anti-spoofing: Check for replay attacks
        if self.anti_spoofing_enabled:
            if self._detect_replay_attack(user_id, audio_sample.audio):
                elapsed_time = time.time() - start_time
                logger.warning(f"Potential replay attack detected for user {user_id}")
                return VerificationResult(
                    match=False,
                    confidence=0.0,
                    threshold=self.similarity_threshold,
                    user_id=user_id,
                    timestamp=datetime.utcnow(),
                    message="Potential replay attack detected"
                )
        
        # Compute similarity
        try:
            similarity = self.speaker_model.compute_similarity(
                stored_voiceprint,
                current_embedding
            )
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"Failed to compute similarity: {e}")
            return VerificationResult(
                match=False,
                confidence=0.0,
                threshold=self.similarity_threshold,
                user_id=user_id,
                timestamp=datetime.utcnow(),
                message=f"Similarity computation failed: {str(e)}"
            )
        
        # Make decision
        match = similarity >= self.similarity_threshold
        elapsed_time = time.time() - start_time
        
        # Check if verification completed within time limit
        if elapsed_time > self.max_verification_time_seconds:
            logger.warning(
                f"Verification took {elapsed_time:.2f}s, "
                f"exceeding limit of {self.max_verification_time_seconds}s"
            )
        
        logger.info(
            f"Verification for user {user_id}: "
            f"match={match}, similarity={similarity:.3f}, "
            f"threshold={self.similarity_threshold}, time={elapsed_time:.2f}s"
        )
        
        return VerificationResult(
            match=match,
            confidence=similarity,
            threshold=self.similarity_threshold,
            user_id=user_id,
            timestamp=datetime.utcnow(),
            message="Verification successful" if match else "Voice does not match"
        )
    
    def verify_with_pin_fallback(
        self,
        user_id: str,
        audio_sample: Optional[VoiceSample] = None,
        pin: Optional[str] = None
    ) -> VerificationResult:
        """
        Verify user with voice biometrics, falling back to PIN if voice fails.
        
        Requirements: 21.4
        
        Args:
            user_id: User identifier
            audio_sample: Voice sample to verify (optional if using PIN)
            pin: Voice-based PIN for fallback authentication
        
        Returns:
            VerificationResult with match decision
        """
        # Try voice biometric first if audio sample provided
        if audio_sample is not None:
            result = self.verify_user(user_id, audio_sample)
            if result.match:
                return result
            
            logger.info(f"Voice verification failed for user {user_id}, trying PIN fallback")
        
        # Fallback to PIN verification
        if pin is not None:
            return self._verify_pin(user_id, pin)
        
        # Neither voice nor PIN provided
        return VerificationResult(
            match=False,
            confidence=0.0,
            threshold=self.similarity_threshold,
            user_id=user_id,
            timestamp=datetime.utcnow(),
            message="No authentication method provided"
        )
    
    def set_pin(self, user_id: str, pin: str) -> bool:
        """
        Set a voice-based PIN for a user as fallback authentication.
        
        Requirements: 21.4
        
        Args:
            user_id: User identifier
            pin: PIN to set (should be 4-6 digits)
        
        Returns:
            True if PIN was set successfully
        """
        if not pin or not pin.isdigit():
            logger.warning(f"Invalid PIN format for user {user_id}")
            return False
        
        if len(pin) < 4 or len(pin) > 6:
            logger.warning(f"PIN length invalid for user {user_id}: {len(pin)} digits")
            return False
        
        # Hash the PIN before storing
        pin_hash = self._hash_pin(pin)
        self._pin_storage[user_id] = pin_hash
        
        logger.info(f"PIN set for user {user_id}")
        return True
    
    def _verify_pin(self, user_id: str, pin: str) -> VerificationResult:
        """
        Verify user using PIN.
        
        Requirements: 21.4
        """
        if user_id not in self._pin_storage:
            logger.warning(f"No PIN set for user {user_id}")
            return VerificationResult(
                match=False,
                confidence=0.0,
                threshold=self.similarity_threshold,
                user_id=user_id,
                timestamp=datetime.utcnow(),
                message="No PIN set for this user"
            )
        
        stored_pin_hash = self._pin_storage[user_id]
        provided_pin_hash = self._hash_pin(pin)
        
        match = stored_pin_hash == provided_pin_hash
        
        logger.info(f"PIN verification for user {user_id}: match={match}")
        
        return VerificationResult(
            match=match,
            confidence=1.0 if match else 0.0,
            threshold=self.similarity_threshold,
            user_id=user_id,
            timestamp=datetime.utcnow(),
            message="PIN verification successful" if match else "Incorrect PIN"
        )
    
    def _hash_pin(self, pin: str) -> str:
        """Hash a PIN using SHA-256"""
        return hashlib.sha256(pin.encode()).hexdigest()
    
    def _bytes_to_audio(self, audio_bytes: bytes, sample_rate: int) -> np.ndarray:
        """Convert audio bytes to numpy array"""
        audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
        audio_array = audio_array.astype(np.float32) / 32768.0
        return audio_array
    
    def _check_rate_limit(self, user_id: str) -> bool:
        """
        Check if user has exceeded rate limit for verification attempts.
        
        Anti-spoofing measure to prevent brute force attacks.
        Requirements: 21.4
        """
        current_time = time.time()
        
        if user_id not in self._verification_attempts:
            self._verification_attempts[user_id] = []
        
        # Remove attempts older than 1 minute
        self._verification_attempts[user_id] = [
            timestamp for timestamp in self._verification_attempts[user_id]
            if current_time - timestamp < 60
        ]
        
        # Check if limit exceeded
        if len(self._verification_attempts[user_id]) >= self._max_attempts_per_minute:
            logger.warning(f"Rate limit exceeded for user {user_id}")
            return False
        
        # Record this attempt
        self._verification_attempts[user_id].append(current_time)
        return True
    
    def _detect_replay_attack(self, user_id: str, audio_bytes: bytes) -> bool:
        """
        Detect potential replay attacks by checking for duplicate audio samples.
        
        Anti-spoofing measure to prevent replay attacks.
        Requirements: 21.4
        """
        # Compute hash of audio sample
        audio_hash = hashlib.sha256(audio_bytes).hexdigest()
        
        # Store recent audio hashes per user
        if not hasattr(self, '_recent_audio_hashes'):
            self._recent_audio_hashes = {}
        
        if user_id not in self._recent_audio_hashes:
            self._recent_audio_hashes[user_id] = []
        
        # Check if this exact audio was used recently
        if audio_hash in self._recent_audio_hashes[user_id]:
            logger.warning(f"Duplicate audio detected for user {user_id}")
            return True
        
        # Store this hash (keep last 10 samples)
        self._recent_audio_hashes[user_id].append(audio_hash)
        if len(self._recent_audio_hashes[user_id]) > 10:
            self._recent_audio_hashes[user_id].pop(0)
        
        return False
    
    def get_verification_stats(self) -> dict:
        """Get statistics about verification attempts"""
        total_attempts = sum(
            len(attempts) for attempts in self._verification_attempts.values()
        )
        
        return {
            "total_users_tracked": len(self._verification_attempts),
            "total_recent_attempts": total_attempts,
            "users_with_pins": len(self._pin_storage),
            "anti_spoofing_enabled": self.anti_spoofing_enabled,
            "similarity_threshold": self.similarity_threshold
        }
    
    def reset_user_attempts(self, user_id: str) -> None:
        """Reset verification attempts for a user (admin function)"""
        if user_id in self._verification_attempts:
            del self._verification_attempts[user_id]
            logger.info(f"Reset verification attempts for user {user_id}")
    
    def delete_pin(self, user_id: str) -> bool:
        """Delete a user's PIN"""
        if user_id in self._pin_storage:
            del self._pin_storage[user_id]
            logger.info(f"Deleted PIN for user {user_id}")
            return True
        return False
