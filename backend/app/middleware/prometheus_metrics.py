"""
Prometheus metrics middleware for FastAPI application.

Requirements: 18.4, 24.7
"""
import time
from typing import Callable
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse


# HTTP Request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0)
)

# Voice pipeline metrics
voice_pipeline_latency_seconds = Histogram(
    'voice_pipeline_latency_seconds',
    'Voice pipeline end-to-end latency in seconds',
    ['source_language', 'target_language'],
    buckets=(0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 10.0, 15.0, 20.0)
)

language_detection_latency_seconds = Histogram(
    'language_detection_latency_seconds',
    'Language detection latency in seconds',
    buckets=(0.1, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0)
)

stt_latency_seconds = Histogram(
    'stt_latency_seconds',
    'Speech-to-text latency in seconds',
    ['language'],
    buckets=(0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0)
)

translation_latency_seconds = Histogram(
    'translation_latency_seconds',
    'Translation latency in seconds',
    ['source_language', 'target_language'],
    buckets=(0.1, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0)
)

tts_latency_seconds = Histogram(
    'tts_latency_seconds',
    'Text-to-speech latency in seconds',
    ['language'],
    buckets=(0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0)
)

# Price Oracle metrics
price_query_latency_seconds = Histogram(
    'price_query_latency_seconds',
    'Price query latency in seconds',
    ['commodity'],
    buckets=(0.1, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0)
)

# STT accuracy metrics
stt_correction_rate = Gauge(
    'stt_correction_rate',
    'STT correction rate (percentage of transcriptions corrected)',
    ['language']
)

stt_confidence_score = Histogram(
    'stt_confidence_score',
    'STT confidence scores',
    ['language'],
    buckets=(0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 0.99, 1.0)
)

# Translation quality metrics
translation_confidence_score = Histogram(
    'translation_confidence_score',
    'Translation confidence scores',
    ['source_language', 'target_language'],
    buckets=(0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 0.99, 1.0)
)

# Transaction metrics
transaction_completion_rate = Gauge(
    'transaction_completion_rate',
    'Transaction completion rate (percentage)'
)

transaction_abandonment_rate = Gauge(
    'transaction_abandonment_rate',
    'Transaction abandonment rate (percentage)'
)

transaction_duration_seconds = Histogram(
    'transaction_duration_seconds',
    'Transaction duration in seconds',
    buckets=(30, 60, 120, 180, 300, 600, 900, 1800, 3600)
)

# System metrics
active_users_total = Gauge(
    'active_users_total',
    'Total number of active users'
)

active_conversations_total = Gauge(
    'active_conversations_total',
    'Total number of active conversations'
)

db_connection_pool_usage = Gauge(
    'db_connection_pool_usage',
    'Database connection pool usage (0-1)'
)

# Error metrics
error_count_total = Counter(
    'error_count_total',
    'Total number of errors',
    ['error_type', 'component']
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track HTTP request metrics.
    
    Requirements: 18.4, 24.7
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Track request metrics.
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
        
        Returns:
            Response from handler
        """
        # Skip metrics endpoint itself
        if request.url.path == "/metrics":
            return await call_next(request)
        
        # Track request start time
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Extract endpoint (remove query params)
        endpoint = request.url.path
        
        # Record metrics
        http_requests_total.labels(
            method=request.method,
            endpoint=endpoint,
            status=response.status_code
        ).inc()
        
        http_request_duration_seconds.labels(
            method=request.method,
            endpoint=endpoint
        ).observe(duration)
        
        return response


def metrics_endpoint() -> StarletteResponse:
    """
    Endpoint to expose Prometheus metrics.
    
    Requirements: 18.4, 24.7
    
    Returns:
        Response with Prometheus metrics
    """
    return StarletteResponse(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# Helper functions to record custom metrics

def record_voice_pipeline_latency(
    total_latency: float,
    source_language: str,
    target_language: str,
    language_detection_latency: float = None,
    stt_latency: float = None,
    translation_latency: float = None,
    tts_latency: float = None,
):
    """
    Record voice pipeline latency metrics.
    
    Requirements: 18.1, 18.4
    
    Args:
        total_latency: Total pipeline latency in seconds
        source_language: Source language code
        target_language: Target language code
        language_detection_latency: Language detection latency in seconds
        stt_latency: STT latency in seconds
        translation_latency: Translation latency in seconds
        tts_latency: TTS latency in seconds
    """
    voice_pipeline_latency_seconds.labels(
        source_language=source_language,
        target_language=target_language
    ).observe(total_latency)
    
    if language_detection_latency is not None:
        language_detection_latency_seconds.observe(language_detection_latency)
    
    if stt_latency is not None:
        stt_latency_seconds.labels(language=source_language).observe(stt_latency)
    
    if translation_latency is not None:
        translation_latency_seconds.labels(
            source_language=source_language,
            target_language=target_language
        ).observe(translation_latency)
    
    if tts_latency is not None:
        tts_latency_seconds.labels(language=target_language).observe(tts_latency)


def record_price_query_latency(commodity: str, latency: float):
    """
    Record price query latency.
    
    Requirements: 18.4
    
    Args:
        commodity: Commodity name
        latency: Query latency in seconds
    """
    price_query_latency_seconds.labels(commodity=commodity).observe(latency)


def update_stt_correction_rate(language: str, rate: float):
    """
    Update STT correction rate gauge.
    
    Requirements: 18.2, 18.4
    
    Args:
        language: Language code
        rate: Correction rate (0-1)
    """
    stt_correction_rate.labels(language=language).set(rate)


def record_stt_confidence(language: str, confidence: float):
    """
    Record STT confidence score.
    
    Requirements: 18.2, 18.4
    
    Args:
        language: Language code
        confidence: Confidence score (0-1)
    """
    stt_confidence_score.labels(language=language).observe(confidence)


def record_translation_confidence(
    source_language: str,
    target_language: str,
    confidence: float
):
    """
    Record translation confidence score.
    
    Requirements: 18.4
    
    Args:
        source_language: Source language code
        target_language: Target language code
        confidence: Confidence score (0-1)
    """
    translation_confidence_score.labels(
        source_language=source_language,
        target_language=target_language
    ).observe(confidence)


def update_transaction_rates(completion_rate: float, abandonment_rate: float):
    """
    Update transaction completion and abandonment rates.
    
    Requirements: 18.3, 18.4
    
    Args:
        completion_rate: Completion rate (0-1)
        abandonment_rate: Abandonment rate (0-1)
    """
    transaction_completion_rate.set(completion_rate)
    transaction_abandonment_rate.set(abandonment_rate)


def record_transaction_duration(duration: float):
    """
    Record transaction duration.
    
    Requirements: 18.3, 18.4
    
    Args:
        duration: Transaction duration in seconds
    """
    transaction_duration_seconds.observe(duration)


def update_active_users(count: int):
    """
    Update active users count.
    
    Requirements: 24.7
    
    Args:
        count: Number of active users
    """
    active_users_total.set(count)


def update_active_conversations(count: int):
    """
    Update active conversations count.
    
    Requirements: 24.7
    
    Args:
        count: Number of active conversations
    """
    active_conversations_total.set(count)


def update_db_connection_pool_usage(usage: float):
    """
    Update database connection pool usage.
    
    Requirements: 24.7
    
    Args:
        usage: Pool usage (0-1)
    """
    db_connection_pool_usage.set(usage)


def record_error(error_type: str, component: str):
    """
    Record an error occurrence.
    
    Requirements: 18.4
    
    Args:
        error_type: Type of error
        component: Component where error occurred
    """
    error_count_total.labels(
        error_type=error_type,
        component=component
    ).inc()
