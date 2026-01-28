"""
Example usage of the Metrics Tracking Service.

This demonstrates how to integrate metrics tracking into the Multilingual Mandi platform.

Requirements: 18.1, 18.2, 18.3, 18.4, 18.5
"""
import asyncio
from datetime import datetime, timedelta
from uuid import uuid4

# Note: In production, use actual database session
# from app.core.database import get_db
# from app.services.metrics import MetricsTracker


def example_voice_pipeline_tracking():
    """
    Example 1: Tracking Voice Pipeline Latency
    
    This should be called after processing each voice message in the
    Vocal Vernacular Engine.
    
    Requirement: 18.1
    """
    print("\n" + "="*60)
    print("Example 1: Voice Pipeline Latency Tracking")
    print("="*60)
    
    # Simulated data from voice processing
    message_id = uuid4()
    user_id = uuid4()
    
    # In production:
    # db = next(get_db())
    # tracker = MetricsTracker(db)
    
    print("\nScenario: User speaks in Hindi, translated to Telugu")
    print(f"Message ID: {message_id}")
    print(f"User ID: {user_id}")
    
    # Simulated latencies from each pipeline stage
    latencies = {
        "language_detection": 450.0,  # ms
        "stt": 2300.0,
        "translation": 1650.0,
        "tts": 1800.0,
        "total": 6200.0
    }
    
    print(f"\nPipeline Latencies:")
    print(f"  Language Detection: {latencies['language_detection']}ms")
    print(f"  Speech-to-Text: {latencies['stt']}ms")
    print(f"  Translation: {latencies['translation']}ms")
    print(f"  Text-to-Speech: {latencies['tts']}ms")
    print(f"  Total: {latencies['total']}ms")
    
    # Track the metrics
    # metric = tracker.track_voice_pipeline_latency(
    #     total_latency_ms=latencies['total'],
    #     message_id=message_id,
    #     user_id=user_id,
    #     language_detection_latency_ms=latencies['language_detection'],
    #     stt_latency_ms=latencies['stt'],
    #     translation_latency_ms=latencies['translation'],
    #     tts_latency_ms=latencies['tts'],
    #     source_language="hi",
    #     target_language="te",
    #     audio_duration_ms=3500.0,
    #     text_length=42,
    #     metadata={
    #         "network_type": "3G",
    #         "device_type": "mobile",
    #         "region": "Maharashtra"
    #     }
    # )
    
    print("\n✓ Metrics tracked successfully")
    print("  - Latency data stored for analysis")
    print("  - No alert created (below 10s threshold)")


def example_high_latency_alert():
    """
    Example 2: High Latency Alert Creation
    
    When latency exceeds 10 seconds, an alert is automatically created.
    
    Requirement: 18.4
    """
    print("\n" + "="*60)
    print("Example 2: High Latency Alert")
    print("="*60)
    
    user_id = uuid4()
    
    print("\nScenario: Slow network causes high latency")
    print(f"User ID: {user_id}")
    
    # Simulated high latencies
    latencies = {
        "stt": 4500.0,
        "translation": 3800.0,
        "tts": 4200.0,
        "total": 12500.0  # Exceeds 10 second threshold!
    }
    
    print(f"\nPipeline Latencies:")
    print(f"  Speech-to-Text: {latencies['stt']}ms")
    print(f"  Translation: {latencies['translation']}ms")
    print(f"  Text-to-Speech: {latencies['tts']}ms")
    print(f"  Total: {latencies['total']}ms ⚠️  EXCEEDS THRESHOLD")
    
    # Track the metrics (alert created automatically)
    # metric = tracker.track_voice_pipeline_latency(
    #     total_latency_ms=latencies['total'],
    #     user_id=user_id,
    #     stt_latency_ms=latencies['stt'],
    #     translation_latency_ms=latencies['translation'],
    #     tts_latency_ms=latencies['tts']
    # )
    
    print("\n✓ Metrics tracked successfully")
    print("  - Latency data stored")
    print("  - ⚠️  ALERT CREATED: Latency exceeds 10 second threshold")
    print("  - Alert sent to administrators for investigation")
    
    # Administrators can retrieve and acknowledge alerts
    # alerts = tracker.get_unacknowledged_alerts()
    # for alert in alerts:
    #     print(f"\nAlert Details:")
    #     print(f"  Type: {alert.alert_type}")
    #     print(f"  Latency: {alert.latency_ms}ms")
    #     print(f"  Threshold: {alert.threshold_ms}ms")
    #     print(f"  Created: {alert.created_at}")
    
    # Acknowledge the alert after investigation
    # tracker.acknowledge_alert(alert.id, "admin@example.com")


def example_stt_accuracy_tracking():
    """
    Example 3: STT Accuracy Tracking with User Corrections
    
    Track transcription accuracy by recording user corrections.
    
    Requirement: 18.2
    """
    print("\n" + "="*60)
    print("Example 3: STT Accuracy Tracking")
    print("="*60)
    
    user_id = uuid4()
    
    print("\nScenario 1: Accurate transcription (no correction)")
    print(f"User ID: {user_id}")
    
    original_text = "मुझे टमाटर की कीमत बताइए"
    print(f"Transcription: '{original_text}'")
    print(f"Confidence: 0.95")
    
    # Track accurate transcription
    # tracker.track_stt_accuracy(
    #     user_id=user_id,
    #     original_transcription=original_text,
    #     language="hi",
    #     confidence_score=0.95
    # )
    
    print("✓ Tracked: No correction needed")
    
    print("\nScenario 2: User corrects transcription")
    
    original_text = "मुझे टमाटर की कीमत बताइए"
    corrected_text = "मुझे टमाटर की कीमत बताइये"
    print(f"Original: '{original_text}'")
    print(f"Corrected: '{corrected_text}'")
    print(f"Confidence: 0.72")
    
    # Track correction
    # tracker.track_stt_accuracy(
    #     user_id=user_id,
    #     original_transcription=original_text,
    #     language="hi",
    #     corrected_transcription=corrected_text,
    #     confidence_score=0.72
    # )
    
    print("✓ Tracked: Correction recorded for model improvement")
    
    # Calculate correction rate
    # correction_rate = tracker.get_stt_correction_rate(language="hi")
    # print(f"\nHindi STT Correction Rate: {correction_rate:.1f}%")
    print("\nHindi STT Correction Rate: 15.3%")
    print("  - Used to measure and improve STT accuracy")
    print("  - Lower rate indicates better accuracy")


def example_transaction_tracking():
    """
    Example 4: Transaction Completion and Abandonment Tracking
    
    Track whether conversations result in completed transactions or are abandoned.
    
    Requirement: 18.3
    """
    print("\n" + "="*60)
    print("Example 4: Transaction Tracking")
    print("="*60)
    
    conversation_id = uuid4()
    buyer_id = uuid4()
    seller_id = uuid4()
    
    print("\nScenario 1: Completed Transaction")
    print(f"Conversation ID: {conversation_id}")
    print(f"Buyer: {buyer_id}")
    print(f"Seller: {seller_id}")
    
    started_at = datetime.utcnow() - timedelta(minutes=8)
    ended_at = datetime.utcnow()
    
    print(f"\nConversation Duration: 8 minutes")
    print(f"Commodity: Tomato")
    print(f"Agreed Price: ₹25.00/kg")
    print(f"Market Average: ₹24.00/kg")
    
    # Track completed transaction
    # tracker.track_transaction_completion(
    #     conversation_id=conversation_id,
    #     buyer_id=buyer_id,
    #     seller_id=seller_id,
    #     conversation_started_at=started_at,
    #     completed=True,
    #     transaction_id=uuid4(),
    #     conversation_ended_at=ended_at,
    #     commodity="tomato",
    #     agreed_price=25.0,
    #     market_average=24.0
    # )
    
    print("\n✓ Tracked: Transaction completed successfully")
    
    print("\n" + "-"*60)
    print("\nScenario 2: Abandoned Transaction")
    
    conversation_id2 = uuid4()
    started_at2 = datetime.utcnow() - timedelta(minutes=3)
    ended_at2 = datetime.utcnow()
    
    print(f"Conversation ID: {conversation_id2}")
    print(f"Duration: 3 minutes")
    print(f"Reason: Price disagreement")
    
    # Track abandoned transaction
    # tracker.track_transaction_completion(
    #     conversation_id=conversation_id2,
    #     buyer_id=buyer_id,
    #     seller_id=seller_id,
    #     conversation_started_at=started_at2,
    #     completed=False,
    #     conversation_ended_at=ended_at2,
    #     abandonment_reason="price_disagreement"
    # )
    
    print("\n✓ Tracked: Transaction abandoned")
    
    # Calculate rates
    # rates = tracker.get_transaction_completion_rate()
    # print(f"\nTransaction Metrics:")
    # print(f"  Completion Rate: {rates['completion_rate']:.1f}%")
    # print(f"  Abandonment Rate: {rates['abandonment_rate']:.1f}%")
    
    print(f"\nTransaction Metrics:")
    print(f"  Completion Rate: 72.5%")
    print(f"  Abandonment Rate: 27.5%")
    print("  - Used to measure platform effectiveness")
    print("  - High abandonment may indicate UX issues")


def example_daily_report_generation():
    """
    Example 5: Daily Performance Report Generation
    
    Generate comprehensive daily reports aggregating all metrics.
    
    Requirement: 18.5
    """
    print("\n" + "="*60)
    print("Example 5: Daily Performance Report")
    print("="*60)
    
    report_date = datetime.utcnow() - timedelta(days=1)
    
    print(f"\nGenerating report for: {report_date.date()}")
    
    # Generate daily report
    # report = tracker.generate_daily_report(report_date)
    
    # Simulated report data
    print("\n" + "="*60)
    print("DAILY PERFORMANCE REPORT")
    print(f"Date: {report_date.date()}")
    print("="*60)
    
    print("\n📊 Voice Pipeline Metrics:")
    print(f"  Total Messages: 1,247")
    print(f"  Average Total Latency: 6,350ms")
    print(f"  Average STT Latency: 2,450ms")
    print(f"  Average Translation Latency: 1,820ms")
    print(f"  Average TTS Latency: 2,080ms")
    print(f"  Max Latency: 11,200ms")
    print(f"  Min Latency: 4,100ms")
    
    print("\n📝 STT Accuracy Metrics:")
    print(f"  Total Transcriptions: 1,247")
    print(f"  Total Corrections: 187")
    print(f"  Correction Rate: 15.0%")
    print(f"  Average Confidence: 0.87")
    
    print("\n💰 Transaction Metrics:")
    print(f"  Total Conversations: 423")
    print(f"  Completed Transactions: 307")
    print(f"  Abandoned Transactions: 116")
    print(f"  Completion Rate: 72.6%")
    print(f"  Abandonment Rate: 27.4%")
    
    print("\n⚠️  System Health:")
    print(f"  Total Alerts: 3")
    print(f"  Service Availability: 99.8%")
    
    print("\n✓ Report generated and stored")
    print("  - Available for administrator review")
    print("  - Can be exported or visualized in dashboards")
    
    # Get recent reports
    # recent_reports = tracker.get_recent_reports(days=7)
    # print(f"\nRecent Reports: {len(recent_reports)} reports available")


def example_alert_management():
    """
    Example 6: Alert Management Workflow
    
    Demonstrate how administrators manage latency alerts.
    
    Requirement: 18.4
    """
    print("\n" + "="*60)
    print("Example 6: Alert Management")
    print("="*60)
    
    print("\nStep 1: Retrieve unacknowledged alerts")
    
    # Get unacknowledged alerts
    # alerts = tracker.get_unacknowledged_alerts()
    
    # Simulated alerts
    print(f"\nFound 2 unacknowledged alerts:")
    
    alert1_id = uuid4()
    alert2_id = uuid4()
    
    print(f"\nAlert 1:")
    print(f"  ID: {alert1_id}")
    print(f"  Type: voice_pipeline")
    print(f"  Latency: 12,500ms")
    print(f"  Threshold: 10,000ms")
    print(f"  Created: 2024-01-15 10:23:45")
    print(f"  User: {uuid4()}")
    
    print(f"\nAlert 2:")
    print(f"  ID: {alert2_id}")
    print(f"  Type: voice_pipeline")
    print(f"  Latency: 11,200ms")
    print(f"  Threshold: 10,000ms")
    print(f"  Created: 2024-01-15 14:56:12")
    print(f"  User: {uuid4()}")
    
    print("\nStep 2: Investigate issues")
    print("  - Check network conditions")
    print("  - Review server logs")
    print("  - Identify root cause")
    
    print("\nStep 3: Acknowledge alerts after resolution")
    
    # Acknowledge alerts
    # tracker.acknowledge_alert(alert1_id, "admin@example.com")
    # tracker.acknowledge_alert(alert2_id, "admin@example.com")
    
    print(f"\n✓ Alert {alert1_id} acknowledged by admin@example.com")
    print(f"✓ Alert {alert2_id} acknowledged by admin@example.com")
    
    print("\nStep 4: Verify no unacknowledged alerts remain")
    # remaining_alerts = tracker.get_unacknowledged_alerts()
    # print(f"Unacknowledged alerts: {len(remaining_alerts)}")
    print(f"Unacknowledged alerts: 0")


def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("METRICS TRACKING SERVICE - USAGE EXAMPLES")
    print("="*60)
    print("\nThese examples demonstrate how to integrate metrics tracking")
    print("into the Multilingual Mandi platform.")
    print("\nNote: Code is commented out to avoid database dependencies.")
    print("Uncomment and use with actual database session in production.")
    
    example_voice_pipeline_tracking()
    example_high_latency_alert()
    example_stt_accuracy_tracking()
    example_transaction_tracking()
    example_daily_report_generation()
    example_alert_management()
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print("\nThe Metrics Tracking Service provides:")
    print("  ✓ Voice pipeline latency tracking (Req 18.1)")
    print("  ✓ STT accuracy monitoring (Req 18.2)")
    print("  ✓ Transaction completion tracking (Req 18.3)")
    print("  ✓ Automatic latency alerts (Req 18.4)")
    print("  ✓ Daily performance reports (Req 18.5)")
    print("\nIntegrate these tracking calls into your services to enable")
    print("comprehensive monitoring and quality assurance.")
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
