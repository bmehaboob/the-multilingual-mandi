"""
Feedback models for collecting user feedback and corrections.

Requirements: 20.1, 20.2, 22.1, 22.3, 22.4
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, String, Float, Integer, DateTime, Boolean, JSON, Enum as SQLEnum, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.core.database import Base


class FeedbackType(str, Enum):
    """Types of feedback collected"""
    TRANSCRIPTION_CORRECTION = "transcription_correction"
    TRANSLATION_QUALITY = "translation_quality"
    NEGOTIATION_SUGGESTION = "negotiation_suggestion"
    PRICE_ORACLE_HELPFULNESS = "price_oracle_helpfulness"
    SATISFACTION_SURVEY = "satisfaction_survey"


class SatisfactionRating(str, Enum):
    """Satisfaction rating levels"""
    VERY_DISSATISFIED = "very_dissatisfied"
    DISSATISFIED = "dissatisfied"
    NEUTRAL = "neutral"
    SATISFIED = "satisfied"
    VERY_SATISFIED = "very_satisfied"


class TranscriptionFeedback(Base):
    """
    Stores user corrections to transcriptions for model improvement.
    
    Requirements: 20.1
    """
    __tablename__ = "transcription_feedback"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), nullable=False)
    message_id = Column(PGUUID(as_uuid=True), nullable=True)  # Reference to conversation message
    
    # Audio reference (hash, not raw audio for privacy)
    audio_hash = Column(String(64), nullable=True)
    
    # Transcription data
    incorrect_transcription = Column(Text, nullable=False)
    correct_transcription = Column(Text, nullable=False)
    language = Column(String(10), nullable=False)
    
    # Context
    confidence_score = Column(Float, nullable=True)
    dialect = Column(String(50), nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Metadata for additional context
    event_metadata = Column("metadata", JSON, nullable=True)


class NegotiationFeedback(Base):
    """
    Stores user feedback on negotiation suggestions.
    
    Requirements: 20.2, 22.4
    """
    __tablename__ = "negotiation_feedback"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), nullable=False)
    conversation_id = Column(PGUUID(as_uuid=True), nullable=True)
    
    # Suggestion reference
    suggestion_id = Column(String(100), nullable=True)  # Internal suggestion ID
    suggested_price = Column(Float, nullable=True)
    suggested_message = Column(Text, nullable=True)
    
    # Feedback
    rating = Column(Integer, nullable=False)  # 1-5 scale
    was_helpful = Column(Boolean, nullable=False)
    was_culturally_appropriate = Column(Boolean, nullable=True)
    was_used = Column(Boolean, nullable=True)  # Did user use the suggestion?
    
    # Free-form feedback
    feedback_text = Column(Text, nullable=True)
    
    # Context
    commodity = Column(String(100), nullable=True)
    market_average = Column(Float, nullable=True)
    language = Column(String(10), nullable=True)
    region = Column(String(100), nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Metadata
    event_metadata = Column("metadata", JSON, nullable=True)


class SatisfactionSurvey(Base):
    """
    Stores voice-based satisfaction survey responses.
    
    Requirements: 22.1, 22.3
    """
    __tablename__ = "satisfaction_surveys"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), nullable=False)
    
    # Survey context
    survey_type = Column(String(50), nullable=False)  # e.g., "post_transaction", "periodic", "feature_specific"
    transaction_id = Column(PGUUID(as_uuid=True), nullable=True)
    conversation_id = Column(PGUUID(as_uuid=True), nullable=True)
    
    # Overall satisfaction
    overall_rating = Column(SQLEnum(SatisfactionRating), nullable=False)
    
    # Feature-specific ratings (1-5 scale)
    voice_translation_rating = Column(Integer, nullable=True)
    price_oracle_rating = Column(Integer, nullable=True)
    negotiation_assistant_rating = Column(Integer, nullable=True)
    
    # Boolean feedback
    price_oracle_helpful = Column(Boolean, nullable=True)
    negotiation_suggestions_helpful = Column(Boolean, nullable=True)
    negotiation_culturally_appropriate = Column(Boolean, nullable=True)
    
    # Free-form feedback (transcribed from voice)
    feedback_text = Column(Text, nullable=True)
    
    # User language
    language = Column(String(10), nullable=False)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Metadata
    event_metadata = Column("metadata", JSON, nullable=True)


class TranslationFeedback(Base):
    """
    Stores user feedback on translation quality.
    
    Requirements: 20.2
    """
    __tablename__ = "translation_feedback"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), nullable=False)
    message_id = Column(PGUUID(as_uuid=True), nullable=True)
    
    # Translation data
    source_text = Column(Text, nullable=False)
    translated_text = Column(Text, nullable=False)
    source_language = Column(String(10), nullable=False)
    target_language = Column(String(10), nullable=False)
    
    # Feedback
    rating = Column(Integer, nullable=False)  # 1-5 scale
    was_accurate = Column(Boolean, nullable=False)
    preserved_meaning = Column(Boolean, nullable=True)
    
    # Corrected translation (if provided)
    corrected_translation = Column(Text, nullable=True)
    
    # Free-form feedback
    feedback_text = Column(Text, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Metadata
    event_metadata = Column("metadata", JSON, nullable=True)


class PriceOracleFeedback(Base):
    """
    Stores user feedback on Price Oracle helpfulness.
    
    Requirements: 22.3
    """
    __tablename__ = "price_oracle_feedback"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), nullable=False)
    transaction_id = Column(PGUUID(as_uuid=True), nullable=True)
    conversation_id = Column(PGUUID(as_uuid=True), nullable=True)
    
    # Price check context
    commodity = Column(String(100), nullable=False)
    quoted_price = Column(Float, nullable=True)
    market_average = Column(Float, nullable=True)
    price_verdict = Column(String(20), nullable=True)  # fair, high, low
    
    # Feedback
    was_helpful = Column(Boolean, nullable=False)
    was_accurate = Column(Boolean, nullable=True)
    influenced_decision = Column(Boolean, nullable=True)
    rating = Column(Integer, nullable=True)  # 1-5 scale
    
    # Free-form feedback
    feedback_text = Column(Text, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Metadata
    event_metadata = Column("metadata", JSON, nullable=True)
