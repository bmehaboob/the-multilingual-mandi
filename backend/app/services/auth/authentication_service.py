"""Authentication service integrating voice biometrics with JWT tokens"""
import logging
import base64
from typing import Optional, Tuple
from datetime import timedelta
from sqlalchemy.orm import Session

from app.models.user import User
from app.services.auth.voice_biometric_verification import VoiceBiometricVerification
from app.services.auth.models import VoiceSample
from app.core.security import create_access_token
from app.core.config import settings

logger = logging.getLogger(__name__)


class AuthenticationService:
    """
    Authentication service that combines voice biometrics with JWT tokens.
    
    Provides login/logout functionality with voice biometric verification
    and session management using JWT tokens.
    
    Requirements: 21.2, 21.3
    """
    
    def __init__(
        self,
        voice_verification: Optional[VoiceBiometricVerification] = None
    ):
        """
        Initialize the authentication service.
        
        Args:
            voice_verification: VoiceBiometricVerification instance
        """
        self.voice_verification = voice_verification or VoiceBiometricVerification()
        logger.info("Initialized AuthenticationService")
    
    def authenticate_with_voice(
        self,
        db: Session,
        phone_number: str,
        audio_data: str,
        sample_rate: int = 16000
    ) -> Tuple[bool, Optional[User], Optional[str], float]:
        """
        Authenticate user using voice biometrics.
        
        Requirements: 21.2, 21.3
        
        Args:
            db: Database session
            phone_number: User's phone number
            audio_data: Base64 encoded audio data
            sample_rate: Audio sample rate in Hz
        
        Returns:
            Tuple of (success, user, error_message, confidence_score)
        """
        logger.info(f"Attempting voice authentication for phone: {phone_number}")
        
        # Find user by phone number
        user = db.query(User).filter(User.phone_number == phone_number).first()
        if not user:
            logger.warning(f"User not found for phone: {phone_number}")
            return False, None, "User not found", 0.0
        
        # Check if user has voiceprint enrolled
        if not user.voiceprint:
            logger.warning(f"No voiceprint enrolled for user: {user.id}")
            return False, None, "No voiceprint enrolled. Please complete onboarding.", 0.0
        
        # Decode audio data
        try:
            audio_bytes = base64.b64decode(audio_data)
        except Exception as e:
            logger.error(f"Failed to decode audio data: {e}")
            return False, None, "Invalid audio data format", 0.0
        
        # Create voice sample
        voice_sample = VoiceSample(
            audio=audio_bytes,
            sample_rate=sample_rate,
            duration_seconds=len(audio_bytes) / (sample_rate * 2),  # Assuming 16-bit audio
            format="wav"
        )
        
        # Verify voice
        verification_result = self.voice_verification.verify_user(
            user_id=str(user.id),
            audio_sample=voice_sample
        )
        
        if verification_result.match:
            logger.info(
                f"Voice authentication successful for user {user.id} "
                f"(confidence: {verification_result.confidence:.3f})"
            )
            return True, user, None, verification_result.confidence
        else:
            logger.warning(
                f"Voice authentication failed for user {user.id}: "
                f"{verification_result.message}"
            )
            return False, None, verification_result.message, verification_result.confidence
    
    def authenticate_with_pin(
        self,
        db: Session,
        phone_number: str,
        pin: str
    ) -> Tuple[bool, Optional[User], Optional[str]]:
        """
        Authenticate user using PIN (fallback method).
        
        Requirements: 21.4
        
        Args:
            db: Database session
            phone_number: User's phone number
            pin: User's PIN
        
        Returns:
            Tuple of (success, user, error_message)
        """
        logger.info(f"Attempting PIN authentication for phone: {phone_number}")
        
        # Find user by phone number
        user = db.query(User).filter(User.phone_number == phone_number).first()
        if not user:
            logger.warning(f"User not found for phone: {phone_number}")
            return False, None, "User not found"
        
        # Verify PIN
        verification_result = self.voice_verification._verify_pin(
            user_id=str(user.id),
            pin=pin
        )
        
        if verification_result.match:
            logger.info(f"PIN authentication successful for user {user.id}")
            return True, user, None
        else:
            logger.warning(f"PIN authentication failed for user {user.id}")
            return False, None, verification_result.message
    
    def authenticate_hybrid(
        self,
        db: Session,
        phone_number: str,
        audio_data: Optional[str] = None,
        sample_rate: int = 16000,
        pin: Optional[str] = None
    ) -> Tuple[bool, Optional[User], Optional[str], float, str]:
        """
        Authenticate user with voice biometrics, falling back to PIN if needed.
        
        Requirements: 21.2, 21.3, 21.4
        
        Args:
            db: Database session
            phone_number: User's phone number
            audio_data: Base64 encoded audio data (optional)
            sample_rate: Audio sample rate in Hz
            pin: User's PIN (optional)
        
        Returns:
            Tuple of (success, user, error_message, confidence, method_used)
        """
        logger.info(f"Attempting hybrid authentication for phone: {phone_number}")
        
        # Try voice authentication first if audio provided
        if audio_data:
            success, user, error, confidence = self.authenticate_with_voice(
                db, phone_number, audio_data, sample_rate
            )
            if success:
                return True, user, None, confidence, "voice"
            
            logger.info(f"Voice authentication failed, trying PIN fallback")
        
        # Fall back to PIN if provided
        if pin:
            success, user, error = self.authenticate_with_pin(db, phone_number, pin)
            if success:
                return True, user, None, 1.0, "pin"
            return False, None, error, 0.0, "pin"
        
        # Neither method succeeded or was provided
        error_msg = "Authentication failed. Please provide valid voice sample or PIN."
        return False, None, error_msg, 0.0, "none"
    
    def create_session_token(
        self,
        user: User,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT session token for authenticated user.
        
        Requirements: 21.2, 21.3
        
        Args:
            user: Authenticated user
            expires_delta: Optional custom expiration time
        
        Returns:
            JWT access token
        """
        token_data = {
            "sub": str(user.id),  # Subject (user ID)
            "phone": user.phone_number,
            "name": user.name,
            "lang": user.primary_language
        }
        
        access_token = create_access_token(
            data=token_data,
            expires_delta=expires_delta
        )
        
        logger.info(f"Created session token for user {user.id}")
        return access_token
    
    def set_user_pin(
        self,
        user_id: str,
        pin: str
    ) -> Tuple[bool, str]:
        """
        Set a PIN for a user as fallback authentication.
        
        Requirements: 21.4
        
        Args:
            user_id: User identifier
            pin: PIN to set (4-6 digits)
        
        Returns:
            Tuple of (success, message)
        """
        success = self.voice_verification.set_pin(user_id, pin)
        
        if success:
            logger.info(f"PIN set successfully for user {user_id}")
            return True, "PIN set successfully"
        else:
            logger.warning(f"Failed to set PIN for user {user_id}")
            return False, "Failed to set PIN. Please ensure PIN is 4-6 digits."
    
    def revoke_session(self, token: str) -> bool:
        """
        Revoke a session token (logout).
        
        Note: In a production system, you would typically:
        1. Add token to a blacklist in Redis with TTL
        2. Or use short-lived tokens with refresh tokens
        
        For now, we'll just log the logout. The token will expire naturally.
        
        Requirements: 21.2, 21.3
        
        Args:
            token: JWT token to revoke
        
        Returns:
            True if successful
        """
        # In production, add to Redis blacklist:
        # redis_client.setex(f"blacklist:{token}", settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, "1")
        
        logger.info("Session revoked (token will expire naturally)")
        return True
    
    def get_token_expiration_seconds(self) -> int:
        """Get the token expiration time in seconds"""
        return settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
