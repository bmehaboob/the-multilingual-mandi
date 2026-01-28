"""
Metrics models for tracking system performance and quality.

Requirements: 18.1, 18.2, 18.3, 18.4, 18.5
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, String, Float, Integer, DateTime, Boolean, JSON, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.core.database import Base


class PipelineStage(str, Enum):
    """Voice pipeline stages for latency tracking"""
    LANGUAGE_DETECTION = "language_detection"
    SPEECH_TO_TEXT = "speech_to_text"
    TRANSLATION = "translation"
    TEXT_TO_SPEECH = "text_to_speech"
    TOTAL = "total"


class MetricType(str, Enum):
    """Types of metrics tracked"""
    LATENCY = "latency"
    ACCURACY = "accuracy"
    TRANSACTION = "transaction"
    SYSTEM = "system"


class VoicePipelineMetric(Base):
    """
    Tracks latency for all voice pipeline stages.
    
    Requirements: 18.1
    """
    __tablename__ = "voice_pipeline_metrics"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    message_id = Column(PGUUID(as_uuid=True), nullable=True)  # Reference to conversation message
    user_id = Column(PGUUID(as_uuid=True), nullable=True)
    
    # Pipeline stage latencies (in milliseconds)
    language_detection_latency_ms = Column(Float, nullable=True)
    stt_latency_ms = Column(Float, nullable=True)
    translation_latency_ms = Column(Float, nullable=True)
    tts_latency_ms = Column(Float, nullable=True)
    total_latency_ms = Column(Float, nullable=False)
    
    # Source and target languages
    source_language = Column(String(10), nullable=True)
    target_language = Column(String(10), nullable=True)
    
    # Additional context
    audio_duration_ms = Column(Float, nullable=True)
    text_length = Column(Integer, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Metadata for additional tracking
    event_metadata = Column("metadata", JSON, nullable=True)


class STTAccuracyMetric(Base):
    """
    Tracks STT accuracy via user correction rates.
    
    Requirements: 18.2
    """
    __tablename__ = "stt_accuracy_metrics"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    message_id = Column(PGUUID(as_uuid=True), nullable=True)
    user_id = Column(PGUUID(as_uuid=True), nullable=False)
    
    # Original transcription
    original_transcription = Column(String, nullable=False)
    
    # User correction (if provided)
    corrected_transcription = Column(String, nullable=True)
    was_corrected = Column(Boolean, default=False, nullable=False)
    
    # Language and confidence
    language = Column(String(10), nullable=False)
    confidence_score = Column(Float, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Metadata
    event_metadata = Column("metadata", JSON, nullable=True)


class TransactionMetric(Base):
    """
    Tracks transaction completion vs. abandonment rates.
    
    Requirements: 18.3
    """
    __tablename__ = "transaction_metrics"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    conversation_id = Column(PGUUID(as_uuid=True), nullable=False)
    transaction_id = Column(PGUUID(as_uuid=True), nullable=True)  # Null if abandoned
    
    # Participants
    buyer_id = Column(PGUUID(as_uuid=True), nullable=False)
    seller_id = Column(PGUUID(as_uuid=True), nullable=False)
    
    # Transaction status
    completed = Column(Boolean, nullable=False)
    abandoned = Column(Boolean, nullable=False)
    
    # Timing
    conversation_started_at = Column(DateTime, nullable=False)
    conversation_ended_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # Transaction details (if completed)
    commodity = Column(String, nullable=True)
    agreed_price = Column(Float, nullable=True)
    market_average = Column(Float, nullable=True)
    
    # Abandonment reason (if abandoned)
    abandonment_reason = Column(String, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Metadata
    event_metadata = Column("metadata", JSON, nullable=True)


class SystemLatencyAlert(Base):
    """
    Tracks system latency alerts for administrator notification.
    
    Requirements: 18.4
    """
    __tablename__ = "system_latency_alerts"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Alert details
    alert_type = Column(String, nullable=False)  # e.g., "voice_pipeline", "api_endpoint"
    latency_ms = Column(Float, nullable=False)
    threshold_ms = Column(Float, default=10000, nullable=False)
    
    # Context
    endpoint = Column(String, nullable=True)
    user_id = Column(PGUUID(as_uuid=True), nullable=True)
    
    # Alert status
    acknowledged = Column(Boolean, default=False, nullable=False)
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(String, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Metadata
    event_metadata = Column("metadata", JSON, nullable=True)


class DailyPerformanceReport(Base):
    """
    Stores daily performance reports.
    
    Requirements: 18.5
    """
    __tablename__ = "daily_performance_reports"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Report date
    report_date = Column(DateTime, nullable=False)
    
    # Voice pipeline metrics
    avg_total_latency_ms = Column(Float, nullable=True)
    avg_stt_latency_ms = Column(Float, nullable=True)
    avg_translation_latency_ms = Column(Float, nullable=True)
    avg_tts_latency_ms = Column(Float, nullable=True)
    max_latency_ms = Column(Float, nullable=True)
    min_latency_ms = Column(Float, nullable=True)
    total_voice_messages = Column(Integer, default=0)
    
    # STT accuracy metrics
    total_transcriptions = Column(Integer, default=0)
    total_corrections = Column(Integer, default=0)
    correction_rate = Column(Float, nullable=True)  # Percentage
    avg_confidence_score = Column(Float, nullable=True)
    
    # Transaction metrics
    total_conversations = Column(Integer, default=0)
    completed_transactions = Column(Integer, default=0)
    abandoned_transactions = Column(Integer, default=0)
    completion_rate = Column(Float, nullable=True)  # Percentage
    abandonment_rate = Column(Float, nullable=True)  # Percentage
    
    # System health
    total_alerts = Column(Integer, default=0)
    service_availability = Column(Float, nullable=True)  # Percentage
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Full report data (JSON)
    report_data = Column(JSON, nullable=True)
