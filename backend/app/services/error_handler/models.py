"""Error handling models and enums"""
from enum import Enum
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime


class ErrorCategory(str, Enum):
    """Categories of errors that can occur in the system"""
    NETWORK = "network"
    AUDIO = "audio"
    TRANSLATION = "translation"
    SERVICE = "service"
    DATA = "data"
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    UNKNOWN = "unknown"


class ErrorSeverity(str, Enum):
    """Severity levels for errors"""
    LOW = "low"  # Minor issues, system can continue normally
    MEDIUM = "medium"  # Noticeable issues, some functionality affected
    HIGH = "high"  # Significant issues, major functionality affected
    CRITICAL = "critical"  # System cannot function properly


@dataclass
class CorrectiveAction:
    """Represents a corrective action the user can take"""
    action_id: str
    description: str  # In English (will be translated)
    priority: int  # 1 = highest priority
    is_automatic: bool = False  # Whether the system will attempt this automatically
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "action_id": self.action_id,
            "description": self.description,
            "priority": self.priority,
            "is_automatic": self.is_automatic,
        }


@dataclass
class ErrorContext:
    """Context information about where and when an error occurred"""
    user_id: Optional[str] = None
    user_language: str = "en"  # Default to English
    conversation_id: Optional[str] = None
    operation: Optional[str] = None  # What operation was being performed
    timestamp: datetime = None
    additional_data: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        return {
            "user_id": self.user_id,
            "user_language": self.user_language,
            "conversation_id": self.conversation_id,
            "operation": self.operation,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "additional_data": self.additional_data,
        }


@dataclass
class ErrorResponse:
    """Response containing error information and recovery suggestions"""
    category: ErrorCategory
    severity: ErrorSeverity
    message: str  # User-facing error message (in user's language)
    technical_message: str  # Technical error message for logging
    corrective_actions: List[CorrectiveAction]
    should_retry: bool = False
    retry_after_seconds: Optional[int] = None
    can_continue: bool = True  # Whether user can continue using the system
    error_code: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "category": self.category.value,
            "severity": self.severity.value,
            "message": self.message,
            "corrective_actions": [action.to_dict() for action in self.corrective_actions],
            "should_retry": self.should_retry,
            "retry_after_seconds": self.retry_after_seconds,
            "can_continue": self.can_continue,
            "error_code": self.error_code,
        }
