"""
Example of integrating Prometheus monitoring with FastAPI application.

Requirements: 18.4, 24.7

This example shows how to:
1. Add Prometheus middleware to FastAPI
2. Expose metrics endpoint
3. Record custom metrics for voice pipeline, STT, transactions, etc.
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
import time
import random

# Import Prometheus middleware and metrics functions
from app.middleware.prometheus_metrics import (
    PrometheusMiddleware,
    metrics_endpoint,
    record_voice_pipeline_latency,
    record_price_query_latency,
    update_stt_correction_rate,
    record_stt_confidence,
    record_translation_confidence,
    update_transaction_rates,
    record_transaction_duration,
    update_active_users,
    update_active_conversations,
    update_db_connection_pool_usage,
    record_error,
)


# Create FastAPI app
app = FastAPI(title="Multilingual Mandi - Monitoring Example")

# Add Prometheus middleware to track HTTP requests
app.add_middleware(PrometheusMiddleware)


# Expose Prometheus metrics endpoint
@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.
    
    This endpoint is scraped by Prometheus to collect metrics.
    """
    return metrics_endpoint()


# Example 1: Voice Pipeline with Metrics
@app.post("/api/v1/voice/translate")
async def translate_voice(
    source_language: str = "hi",
    target_language: str = "te"
):
    """
    Example voice translation endpoint with metrics tracking.
    
    Requirements: 18.1, 18.4
    """
    try:
        # Track start time
        start_time = time.time()
        
        # Simulate language detection
        lang_detect_start = time.time()
        time.sleep(random.uniform(0.1, 0.5))  # Simulate processing
        lang_detect_latency = time.time() - lang_detect_start
        
        # Simulate STT
        stt_start = time.time()
        time.sleep(random.uniform(0.5, 2.0))  # Simulate processing
        stt_latency = time.time() - stt_start
        stt_confidence = random.uniform(0.85, 0.99)
        
        # Record STT confidence
        record_stt_confidence(source_language, stt_confidence)
        
        # Simulate translation
        translation_start = time.time()
        time.sleep(random.uniform(0.3, 1.5))  # Simulate processing
        translation_latency = time.time() - translation_start
        translation_confidence = random.uniform(0.90, 0.99)
        
        # Record translation confidence
        record_translation_confidence(
            source_language,
            target_language,
            translation_confidence
        )
        
        # Simulate TTS
        tts_start = time.time()
        time.sleep(random.uniform(0.4, 1.5))  # Simulate processing
        tts_latency = time.time() - tts_start
        
        # Calculate total latency
        total_latency = time.time() - start_time
        
        # Record voice pipeline metrics
        record_voice_pipeline_latency(
            total_latency=total_latency,
            source_language=source_language,
            target_language=target_language,
            language_detection_latency=lang_detect_latency,
            stt_latency=stt_latency,
            translation_latency=translation_latency,
            tts_latency=tts_latency,
        )
        
        return {
            "status": "success",
            "total_latency_ms": total_latency * 1000,
            "stages": {
                "language_detection_ms": lang_detect_latency * 1000,
                "stt_ms": stt_latency * 1000,
                "translation_ms": translation_latency * 1000,
                "tts_ms": tts_latency * 1000,
            },
            "confidence": {
                "stt": stt_confidence,
                "translation": translation_confidence,
            }
        }
        
    except Exception as e:
        # Record error
        record_error(error_type="translation_error", component="voice_pipeline")
        raise HTTPException(status_code=500, detail=str(e))


# Example 2: Price Query with Metrics
@app.get("/api/v1/prices/{commodity}")
async def get_price(commodity: str):
    """
    Example price query endpoint with metrics tracking.
    
    Requirements: 18.4
    """
    try:
        # Track start time
        start_time = time.time()
        
        # Simulate price query
        time.sleep(random.uniform(0.2, 1.0))
        
        # Calculate latency
        latency = time.time() - start_time
        
        # Record price query latency
        record_price_query_latency(commodity, latency)
        
        return {
            "commodity": commodity,
            "price": random.uniform(15.0, 50.0),
            "unit": "kg",
            "latency_ms": latency * 1000
        }
        
    except Exception as e:
        record_error(error_type="price_query_error", component="price_oracle")
        raise HTTPException(status_code=500, detail=str(e))


# Example 3: STT Correction Tracking
@app.post("/api/v1/stt/correction")
async def submit_stt_correction(
    language: str,
    original: str,
    corrected: str
):
    """
    Example STT correction endpoint with metrics tracking.
    
    Requirements: 18.2, 18.4
    """
    try:
        # In a real implementation, this would:
        # 1. Store the correction in the database
        # 2. Update the correction rate metric
        
        # For this example, we'll simulate updating the correction rate
        # In production, this would be calculated from the database
        correction_rate = random.uniform(0.10, 0.25)
        
        # Update STT correction rate metric
        update_stt_correction_rate(language, correction_rate)
        
        return {
            "status": "success",
            "message": "Correction recorded",
            "language": language,
            "current_correction_rate": correction_rate
        }
        
    except Exception as e:
        record_error(error_type="correction_error", component="stt_service")
        raise HTTPException(status_code=500, detail=str(e))


# Example 4: Transaction Metrics
@app.post("/api/v1/transactions/complete")
async def complete_transaction(
    conversation_id: str,
    duration_seconds: int
):
    """
    Example transaction completion endpoint with metrics tracking.
    
    Requirements: 18.3, 18.4
    """
    try:
        # Record transaction duration
        record_transaction_duration(duration_seconds)
        
        # In a real implementation, calculate rates from database
        # For this example, simulate the rates
        completion_rate = random.uniform(0.70, 0.90)
        abandonment_rate = 1.0 - completion_rate
        
        # Update transaction rates
        update_transaction_rates(completion_rate, abandonment_rate)
        
        return {
            "status": "success",
            "conversation_id": conversation_id,
            "duration_seconds": duration_seconds,
            "metrics": {
                "completion_rate": completion_rate,
                "abandonment_rate": abandonment_rate
            }
        }
        
    except Exception as e:
        record_error(error_type="transaction_error", component="transactions")
        raise HTTPException(status_code=500, detail=str(e))


# Example 5: System Metrics Update
@app.get("/api/v1/system/status")
async def system_status():
    """
    Example system status endpoint that updates system metrics.
    
    Requirements: 24.7
    """
    try:
        # In a real implementation, these would be calculated from:
        # - Active sessions
        # - Database connection pool
        # - Active conversations
        
        # For this example, simulate the values
        active_users = random.randint(50, 500)
        active_conversations = random.randint(20, 200)
        db_pool_usage = random.uniform(0.3, 0.8)
        
        # Update system metrics
        update_active_users(active_users)
        update_active_conversations(active_conversations)
        update_db_connection_pool_usage(db_pool_usage)
        
        return {
            "status": "healthy",
            "active_users": active_users,
            "active_conversations": active_conversations,
            "db_pool_usage": db_pool_usage,
            "timestamp": time.time()
        }
        
    except Exception as e:
        record_error(error_type="system_error", component="system")
        raise HTTPException(status_code=500, detail=str(e))


# Example 6: Health Check
@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy"}


# Example 7: Simulate High Latency (for testing alerts)
@app.get("/api/v1/test/high-latency")
async def test_high_latency():
    """
    Test endpoint to simulate high latency and trigger alerts.
    
    This is useful for testing that alerts fire correctly.
    """
    start_time = time.time()
    
    # Simulate very high latency (>10 seconds)
    time.sleep(12)
    
    total_latency = time.time() - start_time
    
    # Record the high latency
    record_voice_pipeline_latency(
        total_latency=total_latency,
        source_language="hi",
        target_language="te",
        stt_latency=4.0,
        translation_latency=3.0,
        tts_latency=5.0,
    )
    
    return {
        "status": "completed",
        "latency_seconds": total_latency,
        "message": "This should trigger a latency alert!"
    }


if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("Multilingual Mandi - Monitoring Integration Example")
    print("=" * 60)
    print()
    print("Starting FastAPI server with Prometheus monitoring...")
    print()
    print("Endpoints:")
    print("  - Metrics:        http://localhost:8000/metrics")
    print("  - Voice Translate: http://localhost:8000/api/v1/voice/translate")
    print("  - Price Query:    http://localhost:8000/api/v1/prices/tomato")
    print("  - System Status:  http://localhost:8000/api/v1/system/status")
    print("  - Health Check:   http://localhost:8000/health")
    print("  - High Latency:   http://localhost:8000/api/v1/test/high-latency")
    print()
    print("To test:")
    print("  1. Start this server")
    print("  2. Start monitoring stack: cd monitoring && docker-compose up -d")
    print("  3. Make requests to the endpoints above")
    print("  4. View metrics at http://localhost:9090 (Prometheus)")
    print("  5. View dashboards at http://localhost:3000 (Grafana)")
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
