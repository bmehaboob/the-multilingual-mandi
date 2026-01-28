"""
Pydantic schemas for feedback collection.

Requirements: 20.1, 20.2, 22.1, 22.3, 22.4
"""
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.feedback import SatisfactionRating


# Transcription Feedback Schemas
class TranscriptionCorrectionCreate(BaseModel):
    """Schema for creating a transcription correction"""
    message_id: Optional[UUID] = None
    audio_hash: Optional[str] = Field(None, max_length=64)
    incorrect_transcription: str = Field(..., min_length=1)
    correct_transcription: str = Field(..., min_length=1)
    language: str = Field(..., min_length=2, max_length=10)
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    dialect: Optional[str] = Field(None, max_length=50)
    metadata: Optional[Dict[str, Any]] = None


class TranscriptionCorrectionResponse(BaseModel):
    """Schema for transcription correction response"""
    id: UUID
    user_id: UUID
    message_id: Optional[UUID]
    audio_hash: Optional[str]
    incorrect_transcription: str
    correct_transcription: str
    language: str
    confidence_score: Optional[float]
    dialect: Optional[str]
    created_at: datetime
    metadata: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True


# Negotiation Feedback Schemas
class NegotiationFeedbackCreate(BaseModel):
    """Schema for creating negotiation feedback"""
    conversation_id: Optional[UUID] = None
    suggestion_id: Optional[str] = Field(None, max_length=100)
    suggested_price: Optional[float] = Field(None, gt=0)
    suggested_message: Optional[str] = None
    rating: int = Field(..., ge=1, le=5)
    was_helpful: bool
    was_culturally_appropriate: Optional[bool] = None
    was_used: Optional[bool] = None
    feedback_text: Optional[str] = None
    commodity: Optional[str] = Field(None, max_length=100)
    market_average: Optional[float] = Field(None, gt=0)
    language: Optional[str] = Field(None, max_length=10)
    region: Optional[str] = Field(None, max_length=100)
    metadata: Optional[Dict[str, Any]] = None


class NegotiationFeedbackResponse(BaseModel):
    """Schema for negotiation feedback response"""
    id: UUID
    user_id: UUID
    conversation_id: Optional[UUID]
    suggestion_id: Optional[str]
    suggested_price: Optional[float]
    suggested_message: Optional[str]
    rating: int
    was_helpful: bool
    was_culturally_appropriate: Optional[bool]
    was_used: Optional[bool]
    feedback_text: Optional[str]
    commodity: Optional[str]
    market_average: Optional[float]
    language: Optional[str]
    region: Optional[str]
    created_at: datetime
    metadata: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True


# Satisfaction Survey Schemas
class SatisfactionSurveyCreate(BaseModel):
    """Schema for creating a satisfaction survey"""
    survey_type: str = Field(..., max_length=50)
    transaction_id: Optional[UUID] = None
    conversation_id: Optional[UUID] = None
    overall_rating: SatisfactionRating
    voice_translation_rating: Optional[int] = Field(None, ge=1, le=5)
    price_oracle_rating: Optional[int] = Field(None, ge=1, le=5)
    negotiation_assistant_rating: Optional[int] = Field(None, ge=1, le=5)
    price_oracle_helpful: Optional[bool] = None
    negotiation_suggestions_helpful: Optional[bool] = None
    negotiation_culturally_appropriate: Optional[bool] = None
    feedback_text: Optional[str] = None
    language: str = Field(..., min_length=2, max_length=10)
    metadata: Optional[Dict[str, Any]] = None


class SatisfactionSurveyResponse(BaseModel):
    """Schema for satisfaction survey response"""
    id: UUID
    user_id: UUID
    survey_type: str
    transaction_id: Optional[UUID]
    conversation_id: Optional[UUID]
    overall_rating: SatisfactionRating
    voice_translation_rating: Optional[int]
    price_oracle_rating: Optional[int]
    negotiation_assistant_rating: Optional[int]
    price_oracle_helpful: Optional[bool]
    negotiation_suggestions_helpful: Optional[bool]
    negotiation_culturally_appropriate: Optional[bool]
    feedback_text: Optional[str]
    language: str
    created_at: datetime
    metadata: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True


# Translation Feedback Schemas
class TranslationFeedbackCreate(BaseModel):
    """Schema for creating translation feedback"""
    message_id: Optional[UUID] = None
    source_text: str = Field(..., min_length=1)
    translated_text: str = Field(..., min_length=1)
    source_language: str = Field(..., min_length=2, max_length=10)
    target_language: str = Field(..., min_length=2, max_length=10)
    rating: int = Field(..., ge=1, le=5)
    was_accurate: bool
    preserved_meaning: Optional[bool] = None
    corrected_translation: Optional[str] = None
    feedback_text: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class TranslationFeedbackResponse(BaseModel):
    """Schema for translation feedback response"""
    id: UUID
    user_id: UUID
    message_id: Optional[UUID]
    source_text: str
    translated_text: str
    source_language: str
    target_language: str
    rating: int
    was_accurate: bool
    preserved_meaning: Optional[bool]
    corrected_translation: Optional[str]
    feedback_text: Optional[str]
    created_at: datetime
    metadata: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True


# Price Oracle Feedback Schemas
class PriceOracleFeedbackCreate(BaseModel):
    """Schema for creating price oracle feedback"""
    transaction_id: Optional[UUID] = None
    conversation_id: Optional[UUID] = None
    commodity: str = Field(..., min_length=1, max_length=100)
    quoted_price: Optional[float] = Field(None, gt=0)
    market_average: Optional[float] = Field(None, gt=0)
    price_verdict: Optional[str] = Field(None, max_length=20)
    was_helpful: bool
    was_accurate: Optional[bool] = None
    influenced_decision: Optional[bool] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    feedback_text: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class PriceOracleFeedbackResponse(BaseModel):
    """Schema for price oracle feedback response"""
    id: UUID
    user_id: UUID
    transaction_id: Optional[UUID]
    conversation_id: Optional[UUID]
    commodity: str
    quoted_price: Optional[float]
    market_average: Optional[float]
    price_verdict: Optional[str]
    was_helpful: bool
    was_accurate: Optional[bool]
    influenced_decision: Optional[bool]
    rating: Optional[int]
    feedback_text: Optional[str]
    created_at: datetime
    metadata: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True


# Voice-based survey request schema
class VoiceSurveyRequest(BaseModel):
    """Schema for initiating a voice-based survey"""
    survey_type: str = Field(..., max_length=50)
    language: str = Field(..., min_length=2, max_length=10)
    transaction_id: Optional[UUID] = None
    conversation_id: Optional[UUID] = None


class VoiceSurveyPrompt(BaseModel):
    """Schema for voice survey prompts"""
    prompt_text: str
    prompt_audio_url: Optional[str] = None
    expected_response_type: str  # e.g., "rating", "boolean", "text"
    options: Optional[list[str]] = None
