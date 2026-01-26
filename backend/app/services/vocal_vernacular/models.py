"""Data models for Vocal Vernacular Engine"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from datetime import datetime


@dataclass
class TranscriptionResult:
    """Result from speech-to-text transcription"""
    text: str
    confidence: float
    language: str
    word_timestamps: Optional[List[Dict[str, any]]] = None
    processing_time_ms: Optional[float] = None


@dataclass
class LanguageResult:
    """Result from language detection"""
    language: str  # ISO 639-3 code
    confidence: float
    dialect: Optional[str] = None


@dataclass
class LanguageSegment:
    """Segment of audio with detected language"""
    language: str
    start_time: float
    end_time: float
    confidence: float


@dataclass
class Entity:
    """Entity to preserve in translation (commodity names, prices, units)"""
    text: str
    entity_type: str  # 'commodity', 'price', 'unit'
    start_pos: int
    end_pos: int


@dataclass
class TranslationResult:
    """Result from text translation"""
    text: str
    confidence: float
    source_language: str
    target_language: str
    preserved_entities: Optional[List[Entity]] = None
    processing_time_ms: Optional[float] = None


@dataclass
class Message:
    """Message in a conversation"""
    id: str
    sender_id: str
    text: str
    language: str
    timestamp: datetime


@dataclass
class TTSResult:
    """Result from text-to-speech synthesis"""
    audio: bytes  # Audio data (MP3 or raw PCM)
    format: str  # 'mp3' or 'pcm'
    sample_rate: int
    duration_seconds: float
    speech_rate: float
    processing_time_ms: Optional[float] = None


@dataclass
class ConversationContext:
    """Context for a conversation"""
    conversation_id: str
    participants: List[str]
    messages: List[Message] = field(default_factory=list)
    commodity: Optional[str] = None
    metadata: Dict[str, any] = field(default_factory=dict)


@dataclass
class VoiceResponse:
    """Complete response from voice-to-voice translation pipeline"""
    audio: bytes  # Translated audio output
    transcription: str  # Original transcription
    translation: str  # Translated text
    source_language: str
    target_language: str
    latency_ms: float  # Total end-to-end latency
    stage_latencies: Dict[str, float] = field(default_factory=dict)  # Latency per stage
    confidence_scores: Dict[str, float] = field(default_factory=dict)  # Confidence per stage


@dataclass
class PipelineStage:
    """Represents a stage in the voice processing pipeline"""
    name: str
    start_time: float
    end_time: Optional[float] = None
    success: bool = True
    error: Optional[str] = None
    
    @property
    def duration_ms(self) -> float:
        """Calculate duration in milliseconds"""
        if self.end_time is None:
            return 0.0
        return (self.end_time - self.start_time) * 1000

