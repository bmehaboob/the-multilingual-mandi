"""
Simplified unit tests for metrics tracking service focusing on core logic.

Requirements: 18.1, 18.2, 18.3, 18.4, 18.5
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import Mock, MagicMock, patch

from app.services.metrics.metrics_tracker import MetricsTracker


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = Mock()
    session.add = Mock()
    session.commit = Mock()
    session.refresh = Mock()
    session.query = Mock()
    session.rollback = Mock()
    return session


@pytest.fixture
def metrics_tracker(mock_db_session):
    """Create a MetricsTracker instance with mock database."""
    return MetricsTracker(mock_db_session)


# Voice Pipeline Latency Tests (Requirement 18.1)


def test_track_voice_pipeline_latency_basic(metrics_tracker, mock_db_session):
    """Test basic voice pipeline latency tracking."""
    # Arrange
    user_id = uuid4()
    message_id = uuid4()
    
    # Act
    metric = metrics_tracker.track_voice_pipeline_latency(
        total_latency_ms=5000.0,
        message_id=message_id,
        user_id=user_id,
        stt_latency_ms=2000.0,
        translation_latency_ms=1500.0,
        tts_latency_ms=1500.0,
        source_language="hi",
        target_language="te",
    )
    
    # Assert
    assert metric is not None
    assert metric.total_latency_ms == 5000.0
    assert metric.stt_latency_ms == 2000.0
    assert metric.translation_latency_ms == 1500.0
    assert metric.tts_latency_ms == 1500.0
    assert metric.source_language == "hi"
    assert metric.target_language == "te"
    
    # Verify database operations were called
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called()


def test_track_voice_pipeline_latency_creates_alert_when_exceeds_threshold(
    metrics_tracker, mock_db_session
):
    """Test that latency alert is created when threshold is exceeded."""
    # Arrange
    user_id = uuid4()
    high_latency = 12000.0  # 12 seconds, exceeds 10 second threshold
    
    # Act
    metric = metrics_tracker.track_voice_pipeline_latency(
        total_latency_ms=high_latency,
        user_id=user_id,
        stt_latency_ms=4000.0,
        translation_latency_ms=4000.0,
        tts_latency_ms=4000.0,
    )
    
    # Assert
    assert metric is not None
    # Should have called add twice: once for metric, once for alert
    assert mock_db_session.add.call_count == 2


def test_track_voice_pipeline_latency_no_alert_when_below_threshold(
    metrics_tracker, mock_db_session
):
    """Test that no alert is created when latency is below threshold."""
    # Arrange
    low_latency = 5000.0  # 5 seconds, below 10 second threshold
    
    # Act
    metric = metrics_tracker.track_voice_pipeline_latency(
        total_latency_ms=low_latency,
        stt_latency_ms=2000.0,
        translation_latency_ms=1500.0,
        tts_latency_ms=1500.0,
    )
    
    # Assert
    assert metric is not None
    # Should have called add only once for the metric, not for alert
    assert mock_db_session.add.call_count == 1


def test_track_voice_pipeline_latency_with_metadata(metrics_tracker, mock_db_session):
    """Test tracking latency with additional metadata."""
    # Arrange
    metadata = {
        "network_type": "3G",
        "device_type": "mobile",
        "region": "Maharashtra",
    }
    
    # Act
    metric = metrics_tracker.track_voice_pipeline_latency(
        total_latency_ms=6000.0,
        stt_latency_ms=2000.0,
        translation_latency_ms=2000.0,
        tts_latency_ms=2000.0,
        metadata=metadata,
    )
    
    # Assert
    assert metric is not None
    assert metric.event_metadata == metadata


# STT Accuracy Tests (Requirement 18.2)


def test_track_stt_accuracy_without_correction(metrics_tracker, mock_db_session):
    """Test tracking STT accuracy when no correction is provided."""
    # Arrange
    user_id = uuid4()
    original = "यह एक परीक्षण है"
    
    # Act
    metric = metrics_tracker.track_stt_accuracy(
        user_id=user_id,
        original_transcription=original,
        language="hi",
        confidence_score=0.95,
    )
    
    # Assert
    assert metric is not None
    assert metric.original_transcription == original
    assert metric.corrected_transcription is None
    assert metric.was_corrected == False
    assert metric.language == "hi"
    assert metric.confidence_score == 0.95
    
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called()


def test_track_stt_accuracy_with_correction(metrics_tracker, mock_db_session):
    """Test tracking STT accuracy when user provides correction."""
    # Arrange
    user_id = uuid4()
    original = "यह एक परीक्षण है"
    corrected = "यह एक परीक्षा है"
    
    # Act
    metric = metrics_tracker.track_stt_accuracy(
        user_id=user_id,
        original_transcription=original,
        language="hi",
        corrected_transcription=corrected,
        confidence_score=0.75,
    )
    
    # Assert
    assert metric is not None
    assert metric.original_transcription == original
    assert metric.corrected_transcription == corrected
    assert metric.was_corrected == True
    assert metric.language == "hi"


def test_track_stt_accuracy_same_text_not_correction(metrics_tracker, mock_db_session):
    """Test that identical text is not counted as correction."""
    # Arrange
    user_id = uuid4()
    text = "यह एक परीक्षण है"
    
    # Act
    metric = metrics_tracker.track_stt_accuracy(
        user_id=user_id,
        original_transcription=text,
        language="hi",
        corrected_transcription=text,  # Same as original
    )
    
    # Assert
    assert metric.was_corrected == False


def test_get_stt_correction_rate_no_data(metrics_tracker, mock_db_session):
    """Test correction rate calculation with no data."""
    # Arrange
    mock_query = Mock()
    mock_query.count.return_value = 0
    mock_db_session.query.return_value = mock_query
    
    # Act
    rate = metrics_tracker.get_stt_correction_rate()
    
    # Assert
    assert rate == 0.0


# Transaction Tracking Tests (Requirement 18.3)


def test_track_transaction_completion(metrics_tracker, mock_db_session):
    """Test tracking completed transaction."""
    # Arrange
    conversation_id = uuid4()
    transaction_id = uuid4()
    buyer_id = uuid4()
    seller_id = uuid4()
    started_at = datetime.utcnow() - timedelta(minutes=10)
    ended_at = datetime.utcnow()
    
    # Act
    metric = metrics_tracker.track_transaction_completion(
        conversation_id=conversation_id,
        buyer_id=buyer_id,
        seller_id=seller_id,
        conversation_started_at=started_at,
        completed=True,
        transaction_id=transaction_id,
        conversation_ended_at=ended_at,
        commodity="tomato",
        agreed_price=25.0,
        market_average=24.0,
    )
    
    # Assert
    assert metric is not None
    assert metric.completed == True
    assert metric.abandoned == False
    assert metric.transaction_id == transaction_id
    assert metric.commodity == "tomato"
    assert metric.agreed_price == 25.0
    assert metric.duration_seconds == 600  # 10 minutes
    
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called()


def test_track_transaction_abandonment(metrics_tracker, mock_db_session):
    """Test tracking abandoned transaction."""
    # Arrange
    conversation_id = uuid4()
    buyer_id = uuid4()
    seller_id = uuid4()
    started_at = datetime.utcnow() - timedelta(minutes=5)
    ended_at = datetime.utcnow()
    
    # Act
    metric = metrics_tracker.track_transaction_completion(
        conversation_id=conversation_id,
        buyer_id=buyer_id,
        seller_id=seller_id,
        conversation_started_at=started_at,
        completed=False,
        conversation_ended_at=ended_at,
        abandonment_reason="price_too_high",
    )
    
    # Assert
    assert metric is not None
    assert metric.completed == False
    assert metric.abandoned == True
    assert metric.transaction_id is None
    assert metric.abandonment_reason == "price_too_high"
    assert metric.duration_seconds == 300  # 5 minutes


def test_transaction_duration_calculation(metrics_tracker, mock_db_session):
    """Test that transaction duration is calculated correctly."""
    # Arrange
    started_at = datetime(2024, 1, 1, 10, 0, 0)
    ended_at = datetime(2024, 1, 1, 10, 15, 30)  # 15 minutes 30 seconds later
    
    # Act
    metric = metrics_tracker.track_transaction_completion(
        conversation_id=uuid4(),
        buyer_id=uuid4(),
        seller_id=uuid4(),
        conversation_started_at=started_at,
        completed=True,
        conversation_ended_at=ended_at,
        transaction_id=uuid4(),
    )
    
    # Assert
    assert metric.duration_seconds == 930  # 15 * 60 + 30 = 930 seconds


def test_get_transaction_completion_rate_no_data(metrics_tracker, mock_db_session):
    """Test transaction rate calculation with no data."""
    # Arrange
    mock_query = Mock()
    mock_query.count.return_value = 0
    mock_db_session.query.return_value = mock_query
    
    # Act
    rates = metrics_tracker.get_transaction_completion_rate()
    
    # Assert
    assert rates["completion_rate"] == 0.0
    assert rates["abandonment_rate"] == 0.0


# System Latency Alert Tests (Requirement 18.4)


def test_acknowledge_alert_success(metrics_tracker, mock_db_session):
    """Test acknowledging an alert successfully."""
    # Arrange
    alert_id = uuid4()
    mock_alert = Mock()
    mock_alert.id = alert_id
    mock_alert.acknowledged = False
    
    mock_query = Mock()
    mock_query.filter.return_value.first.return_value = mock_alert
    mock_db_session.query.return_value = mock_query
    
    # Act
    success = metrics_tracker.acknowledge_alert(alert_id, "admin@example.com")
    
    # Assert
    assert success == True
    assert mock_alert.acknowledged == True
    assert mock_alert.acknowledged_by == "admin@example.com"
    assert mock_alert.acknowledged_at is not None
    mock_db_session.commit.assert_called()


def test_acknowledge_nonexistent_alert(metrics_tracker, mock_db_session):
    """Test acknowledging a non-existent alert."""
    # Arrange
    alert_id = uuid4()
    
    mock_query = Mock()
    mock_query.filter.return_value.first.return_value = None
    mock_db_session.query.return_value = mock_query
    
    # Act
    success = metrics_tracker.acknowledge_alert(alert_id, "admin@example.com")
    
    # Assert
    assert success == False


# Daily Performance Report Tests (Requirement 18.5)


def test_generate_daily_report_structure(metrics_tracker, mock_db_session):
    """Test that daily report has correct structure."""
    # Arrange
    report_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Mock the query methods to return empty results
    mock_query = Mock()
    mock_query.filter.return_value = mock_query
    mock_query.count.return_value = 0
    mock_query.first.return_value = None
    mock_db_session.query.return_value = mock_query
    
    # Act
    report = metrics_tracker.generate_daily_report(report_date)
    
    # Assert
    assert report is not None
    assert report.report_date == report_date
    assert report.total_voice_messages == 0
    assert report.total_transcriptions == 0
    assert report.total_conversations == 0
    assert hasattr(report, 'avg_total_latency_ms')
    assert hasattr(report, 'correction_rate')
    assert hasattr(report, 'completion_rate')
    assert hasattr(report, 'service_availability')
    
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called()


# Integration Tests


def test_metrics_tracker_initialization(mock_db_session):
    """Test MetricsTracker initialization."""
    # Act
    tracker = MetricsTracker(mock_db_session)
    
    # Assert
    assert tracker.db == mock_db_session
    assert tracker.latency_threshold_ms == 10000


def test_latency_threshold_configurable():
    """Test that latency threshold can be configured."""
    # Arrange
    mock_db = Mock()
    tracker = MetricsTracker(mock_db)
    
    # Act
    tracker.latency_threshold_ms = 15000
    
    # Assert
    assert tracker.latency_threshold_ms == 15000


# Error Handling Tests


def test_track_voice_pipeline_latency_handles_db_error(metrics_tracker, mock_db_session):
    """Test that database errors are handled gracefully."""
    # Arrange
    mock_db_session.commit.side_effect = Exception("Database error")
    
    # Act & Assert
    with pytest.raises(Exception):
        metrics_tracker.track_voice_pipeline_latency(
            total_latency_ms=5000.0,
            stt_latency_ms=2000.0,
            translation_latency_ms=1500.0,
            tts_latency_ms=1500.0,
        )
    
    # Verify rollback was called
    mock_db_session.rollback.assert_called()


def test_track_stt_accuracy_handles_db_error(metrics_tracker, mock_db_session):
    """Test that STT accuracy tracking handles database errors."""
    # Arrange
    mock_db_session.commit.side_effect = Exception("Database error")
    
    # Act & Assert
    with pytest.raises(Exception):
        metrics_tracker.track_stt_accuracy(
            user_id=uuid4(),
            original_transcription="test",
            language="hi",
        )
    
    mock_db_session.rollback.assert_called()


def test_track_transaction_handles_db_error(metrics_tracker, mock_db_session):
    """Test that transaction tracking handles database errors."""
    # Arrange
    mock_db_session.commit.side_effect = Exception("Database error")
    
    # Act & Assert
    with pytest.raises(Exception):
        metrics_tracker.track_transaction_completion(
            conversation_id=uuid4(),
            buyer_id=uuid4(),
            seller_id=uuid4(),
            conversation_started_at=datetime.utcnow(),
            completed=True,
        )
    
    mock_db_session.rollback.assert_called()
