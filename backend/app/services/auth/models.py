"""Data models for voice biometric authentication"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime
import numpy as np


@dataclass
class VoiceprintID:
    """Identifier for a stored voiceprint"""
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime


@dataclass
class VoiceSample:
    """Voice sample for enrollment or verification"""
    audio: bytes  # Raw audio data
    sample_rate: int
    duration_seconds: float
    format: str = "wav"  # Audio format


@dataclass
class EnrollmentResult:
    """Result from voice biometric enrollment"""
    voiceprint_id: VoiceprintID
    success: bool
    num_samples_used: int
    quality_score: float  # 0.0 to 1.0
    message: Optional[str] = None


@dataclass
class VerificationResult:
    """Result from voice biometric verification"""
    match: bool
    confidence: float  # Similarity score (0.0 to 1.0)
    threshold: float  # Threshold used for decision
    user_id: str
    timestamp: datetime
    message: Optional[str] = None


@dataclass
class SpeakerEmbedding:
    """Speaker embedding vector"""
    embedding: np.ndarray
    user_id: str
    created_at: datetime
    quality_score: float
