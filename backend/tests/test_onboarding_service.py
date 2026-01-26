"""Unit tests for OnboardingService"""
import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock

from app.services.onboarding import OnboardingService, OnboardingSession, OnboardingStep
from app.services.onboarding.models import VoicePrompt, OnboardingResponse
from app.services.auth.models import VoiceSample, EnrollmentResult, VoiceprintID


class TestOnboardingService:
    """Test suite for OnboardingService"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Mock voice enrollment service
        self.mock_enrollment = Mock()
        self.service = OnboardingService(voice_enrollment=self.mock_enrollment)
    
    def test_start_onboarding_creates_session(self):
        """Test that starting onboarding creates a new session"""
        response = self.service.start_onboarding(preferred_language="hin")
        
        assert response.session_id is not None
        assert response.current_step == OnboardingStep.WELCOME
        assert response.prompt.language == "hin"
        assert not response.is_complete
        assert response.error_message is None
    
    def test_start_onboarding_with_unsupported_language_defaults_to_hindi(self):
        """Test that unsupported language defaults to Hindi"""
        response = self.service.start_onboarding(preferred_language="xyz")
        
        assert response.prompt.language == "hin"
    
    def test_start_onboarding_supports_multiple_languages(self):
        """Test that onboarding supports multiple languages"""
        for lang in ["hin", "eng", "tel", "tam"]:
            response = self.service.start_onboarding(preferred_language=lang)
            assert response.prompt.language == lang
    
    def test_process_response_invalid_session(self):
        """Test processing response with invalid session ID"""
        response = self.service.process_response(
            session_id="invalid-id",
            user_input="test"
        )
        
        assert response.error_message is not None
        assert "not found" in response.error_message.lower()
    
    def test_language_confirmation_yes(self):
        """Test language confirmation with yes response"""
        response = self.service.start_onboarding(preferred_language="hin")
        session_id = response.session_id
        
        # Advance to language confirmation
        response = self.service.process_response(session_id, "")
        assert response.current_step == OnboardingStep.LANGUAGE_CONFIRMATION
        
        # Confirm language
        response = self.service.process_response(session_id, "हां")
        assert response.current_step == OnboardingStep.COLLECT_NAME
    
    def test_language_confirmation_unclear_response(self):
        """Test language confirmation with unclear response"""
        response = self.service.start_onboarding(preferred_language="hin")
        session_id = response.session_id
        
        # Advance to language confirmation
        response = self.service.process_response(session_id, "")
        
        # Provide unclear response
        response = self.service.process_response(session_id, "maybe")
        assert response.current_step == OnboardingStep.LANGUAGE_CONFIRMATION
        assert "understand" in response.prompt.text.lower() or "समझ" in response.prompt.text
    
    def test_collect_name_valid(self):
        """Test collecting valid name"""
        response = self.service.start_onboarding(preferred_language="eng")
        session_id = response.session_id
        
        # Navigate to name collection
        self.service.process_response(session_id, "")  # Welcome
        self.service.process_response(session_id, "yes")  # Language confirmation
        
        # Provide name
        response = self.service.process_response(session_id, "Rajesh Kumar")
        assert response.current_step == OnboardingStep.COLLECT_LOCATION
        
        session = self.service.get_session(session_id)
        assert session.name == "Rajesh Kumar"
    
    def test_collect_name_invalid_too_short(self):
        """Test collecting invalid name (too short)"""
        response = self.service.start_onboarding(preferred_language="eng")
        session_id = response.session_id
        
        # Navigate to name collection
        self.service.process_response(session_id, "")
        self.service.process_response(session_id, "yes")
        
        # Provide invalid name
        response = self.service.process_response(session_id, "A")
        assert response.current_step == OnboardingStep.COLLECT_NAME
        assert "valid name" in response.prompt.text.lower()
    
    def test_collect_location_valid(self):
        """Test collecting valid location"""
        response = self.service.start_onboarding(preferred_language="eng")
        session_id = response.session_id
        
        # Navigate to location collection
        self.service.process_response(session_id, "")
        self.service.process_response(session_id, "yes")
        self.service.process_response(session_id, "Rajesh Kumar")
        
        # Provide location
        response = self.service.process_response(session_id, "Maharashtra, Pune")
        assert response.current_step == OnboardingStep.COLLECT_PHONE
        
        session = self.service.get_session(session_id)
        assert session.location is not None
        assert "Maharashtra, Pune" in session.location["raw_text"]
    
    def test_collect_phone_valid(self):
        """Test collecting valid phone number"""
        response = self.service.start_onboarding(preferred_language="eng")
        session_id = response.session_id
        
        # Navigate to phone collection
        self.service.process_response(session_id, "")
        self.service.process_response(session_id, "yes")
        self.service.process_response(session_id, "Rajesh Kumar")
        self.service.process_response(session_id, "Maharashtra, Pune")
        
        # Provide phone number
        response = self.service.process_response(session_id, "9876543210")
        assert response.current_step == OnboardingStep.EXPLAIN_DATA_USAGE
        
        session = self.service.get_session(session_id)
        assert session.phone_number == "9876543210"
    
    def test_collect_phone_invalid(self):
        """Test collecting invalid phone number"""
        response = self.service.start_onboarding(preferred_language="eng")
        session_id = response.session_id
        
        # Navigate to phone collection
        self.service.process_response(session_id, "")
        self.service.process_response(session_id, "yes")
        self.service.process_response(session_id, "Rajesh Kumar")
        self.service.process_response(session_id, "Maharashtra, Pune")
        
        # Provide invalid phone
        response = self.service.process_response(session_id, "123")
        assert response.current_step == OnboardingStep.COLLECT_PHONE
        assert "valid" in response.prompt.text.lower()
    
    def test_consent_collection_yes(self):
        """Test consent collection with yes response"""
        response = self.service.start_onboarding(preferred_language="eng")
        session_id = response.session_id
        
        # Navigate to consent
        self.service.process_response(session_id, "")
        self.service.process_response(session_id, "yes")
        self.service.process_response(session_id, "Rajesh Kumar")
        self.service.process_response(session_id, "Maharashtra, Pune")
        self.service.process_response(session_id, "9876543210")
        self.service.process_response(session_id, "")  # Data usage explanation
        
        # Give consent
        response = self.service.process_response(session_id, "yes")
        assert response.current_step == OnboardingStep.CREATE_VOICEPRINT
        
        session = self.service.get_session(session_id)
        assert session.consent_given is True
        assert session.consent_timestamp is not None
    
    def test_consent_collection_no(self):
        """Test consent collection with no response"""
        response = self.service.start_onboarding(preferred_language="eng")
        session_id = response.session_id
        
        # Navigate to consent
        self.service.process_response(session_id, "")
        self.service.process_response(session_id, "yes")
        self.service.process_response(session_id, "Rajesh Kumar")
        self.service.process_response(session_id, "Maharashtra, Pune")
        self.service.process_response(session_id, "9876543210")
        self.service.process_response(session_id, "")
        
        # Decline consent
        response = self.service.process_response(session_id, "no")
        assert response.error_message is not None
        assert "consent" in response.error_message.lower()
    
    def test_voiceprint_creation_requires_multiple_samples(self):
        """Test that voiceprint creation requires 3 samples"""
        response = self.service.start_onboarding(preferred_language="eng")
        session_id = response.session_id
        
        # Navigate to voiceprint creation
        self.service.process_response(session_id, "")
        self.service.process_response(session_id, "yes")
        self.service.process_response(session_id, "Rajesh Kumar")
        self.service.process_response(session_id, "Maharashtra, Pune")
        self.service.process_response(session_id, "9876543210")
        self.service.process_response(session_id, "")
        self.service.process_response(session_id, "yes")
        
        # Provide first sample
        audio_sample = b"fake_audio_data_1"
        response = self.service.process_response(
            session_id, "", audio_sample=audio_sample
        )
        assert response.current_step == OnboardingStep.CREATE_VOICEPRINT
        assert "repeat" in response.prompt.text.lower()
        
        # Provide second sample
        response = self.service.process_response(
            session_id, "", audio_sample=b"fake_audio_data_2"
        )
        assert response.current_step == OnboardingStep.CREATE_VOICEPRINT
        
        session = self.service.get_session(session_id)
        assert len(session.voice_samples) == 2
    
    def test_voiceprint_creation_success(self):
        """Test successful voiceprint creation"""
        # Mock successful enrollment
        mock_voiceprint_id = VoiceprintID(
            id="test-voiceprint-id",
            user_id="test-user",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.mock_enrollment.enroll_user.return_value = EnrollmentResult(
            voiceprint_id=mock_voiceprint_id,
            success=True,
            num_samples_used=3,
            quality_score=0.85,
            message="Success"
        )
        
        response = self.service.start_onboarding(preferred_language="eng")
        session_id = response.session_id
        
        # Navigate to voiceprint creation
        self.service.process_response(session_id, "")
        self.service.process_response(session_id, "yes")
        self.service.process_response(session_id, "Rajesh Kumar")
        self.service.process_response(session_id, "Maharashtra, Pune")
        self.service.process_response(session_id, "9876543210")
        self.service.process_response(session_id, "")
        self.service.process_response(session_id, "yes")
        
        # Provide 3 samples
        for i in range(3):
            response = self.service.process_response(
                session_id, "", audio_sample=f"audio_{i}".encode()
            )
        
        # Should advance to tutorial
        assert response.current_step == OnboardingStep.TUTORIAL
        
        session = self.service.get_session(session_id)
        assert session.voiceprint_id == "test-voiceprint-id"
    
    def test_complete_onboarding_flow(self):
        """Test complete onboarding flow from start to finish"""
        # Mock successful enrollment
        mock_voiceprint_id = VoiceprintID(
            id="test-voiceprint-id",
            user_id="test-user",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.mock_enrollment.enroll_user.return_value = EnrollmentResult(
            voiceprint_id=mock_voiceprint_id,
            success=True,
            num_samples_used=3,
            quality_score=0.85,
            message="Success"
        )
        
        # Start onboarding
        response = self.service.start_onboarding(preferred_language="eng")
        session_id = response.session_id
        assert response.current_step == OnboardingStep.WELCOME
        
        # Complete all steps
        response = self.service.process_response(session_id, "")
        assert response.current_step == OnboardingStep.LANGUAGE_CONFIRMATION
        
        response = self.service.process_response(session_id, "yes")
        assert response.current_step == OnboardingStep.COLLECT_NAME
        
        response = self.service.process_response(session_id, "Rajesh Kumar")
        assert response.current_step == OnboardingStep.COLLECT_LOCATION
        
        response = self.service.process_response(session_id, "Maharashtra, Pune")
        assert response.current_step == OnboardingStep.COLLECT_PHONE
        
        response = self.service.process_response(session_id, "9876543210")
        assert response.current_step == OnboardingStep.EXPLAIN_DATA_USAGE
        
        response = self.service.process_response(session_id, "")
        assert response.current_step == OnboardingStep.COLLECT_CONSENT
        
        response = self.service.process_response(session_id, "yes")
        assert response.current_step == OnboardingStep.CREATE_VOICEPRINT
        
        # Provide voice samples
        for i in range(3):
            response = self.service.process_response(
                session_id, "", audio_sample=f"audio_{i}".encode()
            )
        assert response.current_step == OnboardingStep.TUTORIAL
        
        # Complete tutorial
        response = self.service.process_response(session_id, "no")
        assert response.current_step == OnboardingStep.COMPLETE
        assert response.is_complete is True
        
        # Verify session data
        session = self.service.get_session(session_id)
        assert session.name == "Rajesh Kumar"
        assert session.phone_number == "9876543210"
        assert session.consent_given is True
        assert session.voiceprint_id is not None
        assert session.is_complete()
    
    def test_session_has_required_data(self):
        """Test session validation for required data"""
        session = OnboardingSession(preferred_language="eng")
        assert not session.has_required_data()
        
        session.name = "Test User"
        session.phone_number = "9876543210"
        session.location = {"raw_text": "Test Location"}
        session.consent_given = True
        session.voiceprint_id = "test-id"
        
        assert session.has_required_data()
    
    def test_get_stats(self):
        """Test getting onboarding statistics"""
        stats = self.service.get_stats()
        
        assert "active_sessions" in stats
        assert "completed_sessions" in stats
        assert "supported_languages" in stats
        assert isinstance(stats["supported_languages"], list)


class TestOnboardingSession:
    """Test suite for OnboardingSession model"""
    
    def test_session_initialization(self):
        """Test session initialization with defaults"""
        session = OnboardingSession()
        
        assert session.session_id is not None
        assert session.preferred_language == "hin"
        assert session.current_step == OnboardingStep.WELCOME
        assert session.started_at is not None
        assert session.completed_at is None
        assert not session.consent_given
    
    def test_advance_to_step(self):
        """Test advancing to next step"""
        session = OnboardingSession()
        initial_step = session.current_step
        
        session.advance_to_step(OnboardingStep.COLLECT_NAME)
        
        assert session.current_step == OnboardingStep.COLLECT_NAME
        assert initial_step.value in session.step_history
        assert session.retry_count == 0
    
    def test_retry_current_step(self):
        """Test retrying current step"""
        session = OnboardingSession()
        
        assert session.retry_current_step() is True
        assert session.retry_count == 1
        
        assert session.retry_current_step() is True
        assert session.retry_count == 2
        
        assert session.retry_current_step() is True
        assert session.retry_count == 3
        
        # Max retries exceeded
        assert session.retry_current_step() is False
        assert session.retry_count == 4
    
    def test_get_duration_seconds(self):
        """Test getting session duration"""
        session = OnboardingSession()
        duration = session.get_duration_seconds()
        
        assert duration >= 0
        assert duration < 1  # Should be very small for new session
    
    def test_is_complete(self):
        """Test checking if session is complete"""
        session = OnboardingSession()
        assert not session.is_complete()
        
        session.current_step = OnboardingStep.COMPLETE
        assert session.is_complete()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
