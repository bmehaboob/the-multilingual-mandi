"""
OnboardingService - Voice-guided user registration flow

This service manages the complete onboarding process for new users,
guiding them through registration using voice prompts in their preferred language.

Requirements: 23.1, 23.2, 23.3, 23.4, 23.6, 23.7, 23.8
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import re

from .models import (
    OnboardingSession,
    OnboardingStep,
    VoicePrompt,
    OnboardingResponse
)
from .prompts import get_prompt, get_supported_languages
from app.services.auth.voice_biometric_enrollment import VoiceBiometricEnrollment
from app.services.auth.models import VoiceSample
from app.models.user import User
from app.models.user_preferences import UserPreferences
from app.models.voiceprint import Voiceprint

logger = logging.getLogger(__name__)


class OnboardingService:
    """
    Manages voice-based user onboarding and registration.
    
    Guides new users through a step-by-step voice-guided registration process,
    collecting essential information, obtaining consent, and creating voice
    biometric profiles.
    
    Requirements: 23.1, 23.2, 23.3, 23.4
    """
    
    def __init__(
        self,
        voice_enrollment: Optional[VoiceBiometricEnrollment] = None,
        max_session_duration_minutes: int = 10
    ):
        """
        Initialize the onboarding service.
        
        Args:
            voice_enrollment: Voice biometric enrollment service
            max_session_duration_minutes: Maximum time allowed for onboarding
        """
        self.voice_enrollment = voice_enrollment or VoiceBiometricEnrollment()
        self.max_session_duration_minutes = max_session_duration_minutes
        
        # In-memory session storage (should be Redis/database in production)
        self._sessions: Dict[str, OnboardingSession] = {}
        
        logger.info("Initialized OnboardingService")
    
    def start_onboarding(
        self,
        preferred_language: str = "hin"
    ) -> OnboardingResponse:
        """
        Initiate a new onboarding session.
        
        Creates a new onboarding session and returns the welcome prompt
        in the user's preferred language.
        
        Requirements: 23.1, 23.7
        
        Args:
            preferred_language: ISO 639-3 language code (default: Hindi)
        
        Returns:
            OnboardingResponse with welcome prompt
        """
        # Validate language
        if preferred_language not in get_supported_languages():
            logger.warning(f"Unsupported language {preferred_language}, defaulting to Hindi")
            preferred_language = "hin"
        
        # Create new session
        session = OnboardingSession(preferred_language=preferred_language)
        self._sessions[session.session_id] = session
        
        logger.info(
            f"Started onboarding session {session.session_id} "
            f"in language {preferred_language}"
        )
        
        # Generate welcome prompt
        prompt = self._generate_prompt(session, OnboardingStep.WELCOME)
        
        return OnboardingResponse(
            session_id=session.session_id,
            current_step=session.current_step,
            prompt=prompt,
            is_complete=False
        )
    
    def process_response(
        self,
        session_id: str,
        user_input: str,
        audio_sample: Optional[bytes] = None,
        sample_rate: int = 16000
    ) -> OnboardingResponse:
        """
        Process user response and advance to the next step.
        
        Validates user input, updates the session state, and returns
        the next prompt or completion message.
        
        Requirements: 23.2, 23.8
        
        Args:
            session_id: Onboarding session identifier
            user_input: Transcribed text from user's voice input
            audio_sample: Raw audio bytes (required for voiceprint creation)
            sample_rate: Audio sample rate in Hz
        
        Returns:
            OnboardingResponse with next prompt or completion status
        """
        # Retrieve session
        session = self._sessions.get(session_id)
        if not session:
            logger.error(f"Session {session_id} not found")
            return self._error_response(
                session_id,
                "Session not found or expired"
            )
        
        # Check session timeout
        if session.get_duration_seconds() > self.max_session_duration_minutes * 60:
            logger.warning(f"Session {session_id} exceeded time limit")
            return self._error_response(
                session_id,
                "Session expired. Please start again."
            )
        
        # Process based on current step
        try:
            if session.current_step == OnboardingStep.WELCOME:
                return self._handle_welcome(session)
            
            elif session.current_step == OnboardingStep.LANGUAGE_CONFIRMATION:
                return self._handle_language_confirmation(session, user_input)
            
            elif session.current_step == OnboardingStep.COLLECT_NAME:
                return self._handle_collect_name(session, user_input)
            
            elif session.current_step == OnboardingStep.COLLECT_LOCATION:
                return self._handle_collect_location(session, user_input)
            
            elif session.current_step == OnboardingStep.COLLECT_PHONE:
                return self._handle_collect_phone(session, user_input)
            
            elif session.current_step == OnboardingStep.EXPLAIN_DATA_USAGE:
                return self._handle_explain_data_usage(session)
            
            elif session.current_step == OnboardingStep.COLLECT_CONSENT:
                return self._handle_collect_consent(session, user_input)
            
            elif session.current_step == OnboardingStep.CREATE_VOICEPRINT:
                return self._handle_create_voiceprint(
                    session, audio_sample, sample_rate
                )
            
            elif session.current_step == OnboardingStep.TUTORIAL:
                return self._handle_tutorial(session, user_input)
            
            elif session.current_step == OnboardingStep.COMPLETE:
                return self._handle_complete(session)
            
            else:
                logger.error(f"Unknown step: {session.current_step}")
                return self._error_response(
                    session_id,
                    "Internal error. Please try again."
                )
        
        except Exception as e:
            logger.error(f"Error processing response: {e}", exc_info=True)
            return self._error_response(
                session_id,
                "An error occurred. Please try again."
            )
    
    def _handle_welcome(self, session: OnboardingSession) -> OnboardingResponse:
        """Handle welcome step - advance to language confirmation"""
        session.advance_to_step(OnboardingStep.LANGUAGE_CONFIRMATION)
        prompt = self._generate_prompt(session, session.current_step)
        
        return OnboardingResponse(
            session_id=session.session_id,
            current_step=session.current_step,
            prompt=prompt,
            is_complete=False
        )
    
    def _handle_language_confirmation(
        self,
        session: OnboardingSession,
        user_input: str
    ) -> OnboardingResponse:
        """
        Handle language confirmation step.
        
        Requirements: 23.8 - Validate user response and request clarification
        """
        # Parse yes/no response
        is_yes = self._parse_yes_no(user_input, session.preferred_language)
        
        if is_yes is None:
            # Unclear response - request clarification
            if not session.retry_current_step():
                return self._error_response(
                    session.session_id,
                    "Too many unclear responses. Please start again."
                )
            
            prompt = self._generate_prompt(
                session,
                session.current_step,
                clarification=True
            )
            return OnboardingResponse(
                session_id=session.session_id,
                current_step=session.current_step,
                prompt=prompt,
                is_complete=False
            )
        
        if is_yes:
            # Language confirmed, proceed to collect name
            session.advance_to_step(OnboardingStep.COLLECT_NAME)
        else:
            # User wants different language - would need language selection
            # For now, proceed with current language
            logger.info(f"User declined language {session.preferred_language}")
            session.advance_to_step(OnboardingStep.COLLECT_NAME)
        
        prompt = self._generate_prompt(session, session.current_step)
        return OnboardingResponse(
            session_id=session.session_id,
            current_step=session.current_step,
            prompt=prompt,
            is_complete=False
        )
    
    def _handle_collect_name(
        self,
        session: OnboardingSession,
        user_input: str
    ) -> OnboardingResponse:
        """
        Handle name collection step.
        
        Requirements: 23.2 - Collect name via voice input
        Requirements: 23.8 - Validate input
        """
        # Validate name (basic validation)
        name = user_input.strip()
        
        if len(name) < 2 or len(name) > 100:
            if not session.retry_current_step():
                return self._error_response(
                    session.session_id,
                    "Invalid name provided multiple times. Please start again."
                )
            
            prompt = VoicePrompt(
                text="Please provide a valid name.",
                language=session.preferred_language,
                step=session.current_step,
                requires_response=True,
                expected_response_type="text"
            )
            return OnboardingResponse(
                session_id=session.session_id,
                current_step=session.current_step,
                prompt=prompt,
                is_complete=False
            )
        
        # Store name and advance
        session.name = name
        session.advance_to_step(OnboardingStep.COLLECT_LOCATION)
        
        logger.info(f"Collected name for session {session.session_id}")
        
        prompt = self._generate_prompt(session, session.current_step)
        return OnboardingResponse(
            session_id=session.session_id,
            current_step=session.current_step,
            prompt=prompt,
            is_complete=False
        )
    
    def _handle_collect_location(
        self,
        session: OnboardingSession,
        user_input: str
    ) -> OnboardingResponse:
        """
        Handle location collection step.
        
        Requirements: 23.2 - Collect location via voice input
        """
        # Parse location (basic parsing - state and district)
        location_text = user_input.strip()
        
        if len(location_text) < 3:
            if not session.retry_current_step():
                return self._error_response(
                    session.session_id,
                    "Invalid location provided multiple times. Please start again."
                )
            
            prompt = VoicePrompt(
                text="Please provide a valid location.",
                language=session.preferred_language,
                step=session.current_step,
                requires_response=True,
                expected_response_type="text"
            )
            return OnboardingResponse(
                session_id=session.session_id,
                current_step=session.current_step,
                prompt=prompt,
                is_complete=False
            )
        
        # Store location as structured data
        session.location = {
            "raw_text": location_text,
            "state": None,  # Would parse from text in production
            "district": None
        }
        session.advance_to_step(OnboardingStep.COLLECT_PHONE)
        
        logger.info(f"Collected location for session {session.session_id}")
        
        prompt = self._generate_prompt(session, session.current_step)
        return OnboardingResponse(
            session_id=session.session_id,
            current_step=session.current_step,
            prompt=prompt,
            is_complete=False
        )
    
    def _handle_collect_phone(
        self,
        session: OnboardingSession,
        user_input: str
    ) -> OnboardingResponse:
        """
        Handle phone number collection step.
        
        Requirements: 23.2 - Collect phone via voice input
        Requirements: 23.8 - Validate input
        """
        # Extract and validate phone number
        phone = self._extract_phone_number(user_input)
        
        if not phone:
            if not session.retry_current_step():
                return self._error_response(
                    session.session_id,
                    "Invalid phone number provided multiple times. Please start again."
                )
            
            prompt = VoicePrompt(
                text="Please provide a valid 10-digit mobile number.",
                language=session.preferred_language,
                step=session.current_step,
                requires_response=True,
                expected_response_type="text"
            )
            return OnboardingResponse(
                session_id=session.session_id,
                current_step=session.current_step,
                prompt=prompt,
                is_complete=False
            )
        
        # Store phone and advance to data usage explanation
        session.phone_number = phone
        session.advance_to_step(OnboardingStep.EXPLAIN_DATA_USAGE)
        
        logger.info(f"Collected phone for session {session.session_id}")
        
        prompt = self._generate_prompt(session, session.current_step)
        return OnboardingResponse(
            session_id=session.session_id,
            current_step=session.current_step,
            prompt=prompt,
            is_complete=False
        )
    
    def _handle_explain_data_usage(
        self,
        session: OnboardingSession
    ) -> OnboardingResponse:
        """
        Handle data usage explanation step.
        
        Requirements: 23.3 - Explain data usage policies in simple language
        """
        # Advance to consent collection after explanation
        session.advance_to_step(OnboardingStep.COLLECT_CONSENT)
        
        prompt = self._generate_prompt(session, session.current_step)
        return OnboardingResponse(
            session_id=session.session_id,
            current_step=session.current_step,
            prompt=prompt,
            is_complete=False
        )
    
    def _handle_collect_consent(
        self,
        session: OnboardingSession,
        user_input: str
    ) -> OnboardingResponse:
        """
        Handle consent collection step.
        
        Requirements: 23.3 - Obtain explicit verbal consent
        Requirements: 23.6 - Confirm consent
        """
        # Parse yes/no response
        is_yes = self._parse_yes_no(user_input, session.preferred_language)
        
        if is_yes is None:
            # Unclear response
            if not session.retry_current_step():
                return self._error_response(
                    session.session_id,
                    "Consent not clearly provided. Please start again."
                )
            
            prompt = VoicePrompt(
                text="Please clearly say yes or no for consent.",
                language=session.preferred_language,
                step=session.current_step,
                requires_response=True,
                expected_response_type="yes_no"
            )
            return OnboardingResponse(
                session_id=session.session_id,
                current_step=session.current_step,
                prompt=prompt,
                is_complete=False
            )
        
        if not is_yes:
            # User declined consent - cannot proceed
            logger.info(f"User declined consent in session {session.session_id}")
            return self._error_response(
                session.session_id,
                "Consent is required to use the platform. Registration cancelled."
            )
        
        # Record consent
        session.consent_given = True
        session.consent_timestamp = datetime.utcnow()
        session.advance_to_step(OnboardingStep.CREATE_VOICEPRINT)
        
        logger.info(f"Consent obtained for session {session.session_id}")
        
        prompt = self._generate_prompt(
            session,
            session.current_step,
            name=session.name,
            location=session.location.get("raw_text", "your location")
        )
        return OnboardingResponse(
            session_id=session.session_id,
            current_step=session.current_step,
            prompt=prompt,
            is_complete=False
        )
    
    def _handle_create_voiceprint(
        self,
        session: OnboardingSession,
        audio_sample: Optional[bytes],
        sample_rate: int
    ) -> OnboardingResponse:
        """
        Handle voiceprint creation step.
        
        Requirements: 23.4 - Create voice biometric profile during onboarding
        """
        if not audio_sample:
            prompt = VoicePrompt(
                text="Please provide a voice sample.",
                language=session.preferred_language,
                step=session.current_step,
                requires_response=True,
                expected_response_type="voice_sample"
            )
            return OnboardingResponse(
                session_id=session.session_id,
                current_step=session.current_step,
                prompt=prompt,
                is_complete=False
            )
        
        # Store voice sample
        session.voice_samples.append(audio_sample)
        
        # Need 3-5 samples for enrollment
        required_samples = 3
        if len(session.voice_samples) < required_samples:
            remaining = required_samples - len(session.voice_samples)
            prompt = VoicePrompt(
                text=f"Good! Please repeat {remaining} more time(s).",
                language=session.preferred_language,
                step=session.current_step,
                requires_response=True,
                expected_response_type="voice_sample"
            )
            return OnboardingResponse(
                session_id=session.session_id,
                current_step=session.current_step,
                prompt=prompt,
                is_complete=False
            )
        
        # Enroll voiceprint
        try:
            voice_samples = [
                VoiceSample(
                    audio=sample,
                    sample_rate=sample_rate,
                    duration_seconds=len(sample) / (sample_rate * 2)  # Approximate duration
                )
                for sample in session.voice_samples
            ]
            
            enrollment_result = self.voice_enrollment.enroll_user(
                session.session_id,  # Temporary user ID
                voice_samples
            )
            
            if not enrollment_result.success:
                logger.error(
                    f"Voiceprint enrollment failed: {enrollment_result.message}"
                )
                return self._error_response(
                    session.session_id,
                    "Failed to create voice profile. Please try again."
                )
            
            session.voiceprint_id = enrollment_result.voiceprint_id.id
            session.advance_to_step(OnboardingStep.TUTORIAL)
            
            logger.info(
                f"Voiceprint created for session {session.session_id}: "
                f"{enrollment_result.voiceprint_id.id}"
            )
            
            prompt = self._generate_prompt(session, session.current_step)
            return OnboardingResponse(
                session_id=session.session_id,
                current_step=session.current_step,
                prompt=prompt,
                is_complete=False
            )
        
        except Exception as e:
            logger.error(f"Error creating voiceprint: {e}", exc_info=True)
            return self._error_response(
                session.session_id,
                "Error creating voice profile. Please try again."
            )
    
    def _handle_tutorial(
        self,
        session: OnboardingSession,
        user_input: str
    ) -> OnboardingResponse:
        """
        Handle tutorial step.
        
        Requirements: 23.5 - Provide interactive voice tutorial
        """
        # For now, skip tutorial and complete onboarding
        # In production, would provide detailed tutorial
        session.advance_to_step(OnboardingStep.COMPLETE)
        session.completed_at = datetime.utcnow()
        
        logger.info(
            f"Onboarding completed for session {session.session_id} "
            f"in {session.get_duration_seconds():.1f} seconds"
        )
        
        prompt = self._generate_prompt(session, session.current_step)
        return OnboardingResponse(
            session_id=session.session_id,
            current_step=session.current_step,
            prompt=prompt,
            is_complete=True
        )
    
    def _handle_complete(
        self,
        session: OnboardingSession
    ) -> OnboardingResponse:
        """Handle completion step"""
        prompt = self._generate_prompt(session, session.current_step)
        return OnboardingResponse(
            session_id=session.session_id,
            current_step=session.current_step,
            prompt=prompt,
            is_complete=True
        )
    
    def _generate_prompt(
        self,
        session: OnboardingSession,
        step: OnboardingStep,
        clarification: bool = False,
        **kwargs
    ) -> VoicePrompt:
        """Generate a voice prompt for the current step"""
        prompt_text = get_prompt(session.preferred_language, step, **kwargs)
        
        if clarification:
            prompt_text = "I didn't understand. " + prompt_text
        
        # Determine expected response type
        response_type = "text"
        if step in [OnboardingStep.LANGUAGE_CONFIRMATION, OnboardingStep.COLLECT_CONSENT]:
            response_type = "yes_no"
        elif step == OnboardingStep.CREATE_VOICEPRINT:
            response_type = "voice_sample"
        
        return VoicePrompt(
            text=prompt_text,
            language=session.preferred_language,
            step=step,
            requires_response=step != OnboardingStep.COMPLETE,
            expected_response_type=response_type
        )
    
    def _error_response(
        self,
        session_id: str,
        error_message: str
    ) -> OnboardingResponse:
        """Generate an error response"""
        return OnboardingResponse(
            session_id=session_id,
            current_step=OnboardingStep.COMPLETE,
            prompt=VoicePrompt(
                text=error_message,
                language="eng",
                step=OnboardingStep.COMPLETE,
                requires_response=False
            ),
            is_complete=True,
            error_message=error_message
        )
    
    def _parse_yes_no(self, user_input: str, language: str) -> Optional[bool]:
        """
        Parse yes/no response from user input.
        
        Returns:
            True for yes, False for no, None for unclear
        """
        text = user_input.lower().strip()
        
        # English
        if language == "eng":
            if any(word in text for word in ["yes", "yeah", "yep", "sure", "ok", "okay"]):
                return True
            if any(word in text for word in ["no", "nope", "nah"]):
                return False
        
        # Hindi
        elif language == "hin":
            if any(word in text for word in ["हां", "हाँ", "जी", "ठीक", "yes"]):
                return True
            if any(word in text for word in ["नहीं", "ना", "no"]):
                return False
        
        # Telugu
        elif language == "tel":
            if any(word in text for word in ["అవును", "సరే", "yes"]):
                return True
            if any(word in text for word in ["కాదు", "లేదు", "no"]):
                return False
        
        # Tamil
        elif language == "tam":
            if any(word in text for word in ["ஆம்", "சரி", "yes"]):
                return True
            if any(word in text for word in ["இல்லை", "வேண்டாம்", "no"]):
                return False
        
        return None
    
    def _extract_phone_number(self, user_input: str) -> Optional[str]:
        """
        Extract phone number from user input.
        
        Returns:
            10-digit phone number or None if invalid
        """
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', user_input)
        
        # Indian mobile numbers are 10 digits
        if len(digits) == 10 and digits[0] in ['6', '7', '8', '9']:
            return digits
        
        # Handle +91 prefix
        if len(digits) == 12 and digits.startswith('91'):
            phone = digits[2:]
            if phone[0] in ['6', '7', '8', '9']:
                return phone
        
        return None
    
    def get_session(self, session_id: str) -> Optional[OnboardingSession]:
        """Retrieve an onboarding session"""
        return self._sessions.get(session_id)
    
    def complete_registration(
        self,
        session_id: str,
        db_session: Any
    ) -> Optional[User]:
        """
        Complete registration by creating user in database.
        
        This method should be called after onboarding is complete
        to persist the user data.
        
        Requirements: 23.6 - Confirm account creation
        
        Args:
            session_id: Onboarding session identifier
            db_session: Database session for persistence
        
        Returns:
            Created User object or None if failed
        """
        session = self._sessions.get(session_id)
        if not session or not session.is_complete():
            logger.error(f"Cannot complete registration for session {session_id}")
            return None
        
        if not session.has_required_data():
            logger.error(f"Session {session_id} missing required data")
            return None
        
        try:
            # Create user
            user = User(
                name=session.name,
                phone_number=session.phone_number,
                primary_language=session.preferred_language,
                secondary_languages=session.secondary_languages,
                location=session.location
            )
            db_session.add(user)
            db_session.flush()  # Get user ID
            
            # Create user preferences
            preferences = UserPreferences(
                user_id=user.id,
                speech_rate=0.85,  # Default 15% slower
                volume_boost=False,
                offline_mode=False
            )
            db_session.add(preferences)
            
            # Create voiceprint (would need to transfer from enrollment service)
            # This is a placeholder - in production, would properly handle voiceprint data
            voiceprint = Voiceprint(
                user_id=user.id,
                embedding_data=b"placeholder",  # Would get from enrollment service
                sample_count=len(session.voice_samples)
            )
            db_session.add(voiceprint)
            
            db_session.commit()
            
            logger.info(f"User {user.id} created from session {session_id}")
            
            # Clean up session
            del self._sessions[session_id]
            
            return user
        
        except Exception as e:
            logger.error(f"Error creating user: {e}", exc_info=True)
            db_session.rollback()
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get onboarding statistics"""
        active_sessions = len(self._sessions)
        completed_sessions = sum(
            1 for s in self._sessions.values() if s.is_complete()
        )
        
        return {
            "active_sessions": active_sessions,
            "completed_sessions": completed_sessions,
            "supported_languages": get_supported_languages()
        }
