"""Data models for onboarding service"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
import uuid


class OnboardingStep(Enum):
    """Steps in the onboarding process"""
    WELCOME = "welcome"
    LANGUAGE_CONFIRMATION = "language_confirmation"
    COLLECT_NAME = "collect_name"
    COLLECT_LOCATION = "collect_location"
    COLLECT_PHONE = "collect_phone"
    EXPLAIN_DATA_USAGE = "explain_data_usage"
    COLLECT_CONSENT = "collect_consent"
    CREATE_VOICEPRINT = "create_voiceprint"
    TUTORIAL = "tutorial"
    COMPLETE = "complete"


@dataclass
class OnboardingSession:
    """Represents an onboarding session for a new user"""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    preferred_language: str = "hin"  # ISO 639-3 code, default Hindi
    current_step: OnboardingStep = OnboardingStep.WELCOME
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    # Collected user data
    name: Optional[str] = None
    phone_number: Optional[str] = None
    location: Optional[Dict[str, Any]] = None
    secondary_languages: List[str] = field(default_factory=list)
    
    # Consent tracking
    consent_given: bool = False
    consent_timestamp: Optional[datetime] = None
    
    # Voice biometric data
    voice_samples: List[bytes] = field(default_factory=list)
    voiceprint_id: Optional[str] = None
    
    # Session metadata
    step_history: List[str] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3
    
    def advance_to_step(self, step: OnboardingStep) -> None:
        """Advance to the next step in the onboarding process"""
        self.step_history.append(self.current_step.value)
        self.current_step = step
        self.retry_count = 0
    
    def retry_current_step(self) -> bool:
        """Retry the current step, returns False if max retries exceeded"""
        self.retry_count += 1
        return self.retry_count <= self.max_retries
    
    def is_complete(self) -> bool:
        """Check if onboarding is complete"""
        return self.current_step == OnboardingStep.COMPLETE
    
    def get_duration_seconds(self) -> float:
        """Get the duration of the onboarding session in seconds"""
        end_time = self.completed_at or datetime.utcnow()
        return (end_time - self.started_at).total_seconds()
    
    def has_required_data(self) -> bool:
        """Check if all required data has been collected"""
        return all([
            self.name,
            self.phone_number,
            self.location,
            self.preferred_language,
            self.consent_given,
            self.voiceprint_id
        ])


@dataclass
class VoicePrompt:
    """Represents a voice prompt to be delivered to the user"""
    text: str
    language: str
    step: OnboardingStep
    requires_response: bool = True
    expected_response_type: str = "text"  # text, yes_no, voice_sample
    
    def __str__(self) -> str:
        return f"VoicePrompt({self.step.value}, lang={self.language})"


@dataclass
class OnboardingResponse:
    """Response from the onboarding service"""
    session_id: str
    current_step: OnboardingStep
    prompt: VoicePrompt
    is_complete: bool = False
    user_id: Optional[str] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            "session_id": self.session_id,
            "current_step": self.current_step.value,
            "prompt": {
                "text": self.prompt.text,
                "language": self.prompt.language,
                "requires_response": self.prompt.requires_response,
                "expected_response_type": self.prompt.expected_response_type
            },
            "is_complete": self.is_complete,
            "user_id": self.user_id,
            "error_message": self.error_message
        }
