"""
Unit tests for metrics tracking service.

Requirements: 18.1, 18.2, 18.3, 18.4, 18.5
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from app.services.metrics.metrics_tracker import MetricsTracker

# Create a separate base for testing to avoid SQLAlchemy compatibility issues
TestBase = declarative_base()


# Test models (simplified for SQLite compatibility)
class TestVoicePipelineMetric(TestBase):
    """Test voice pipeline metric model"""
    __tablename__ = "voice_pipeline_metrics"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    message_id = Column(String, nullable=True)
    user_id = Column(String, nullable=True)
    language_detection_latency_ms = Column(Float, nullable=True)
    stt_latency_ms = Column(Float, nullable=True)
    translation_latency_ms = Column(Float, nullable=True)
    tts_latency_ms = Column(Float, nullable=True)
    total_latency_ms = Column(Float, nullable=False)
    source_language = Column(String(10), nullable=True)
    target_language = Column(String(10), nullable=True)
    audio_duration_ms = Column(Float, nullable=True)
    text_length = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    metadata = Column(String, nullable=True)  # JSON string for SQLite


class TestSTTAccuracyMetric(TestBase):
    """Test STT accuracy metric model"""
    __tablename__ = "stt_accuracy_metrics"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    message_id = Column(String, nullable=True)
    user_id = Column(String, nullable=False)
    original_transcription = Column(String, nullable=False)
    corrected_transcription = Column(String, nullable=True)
    was_corrected = Column(Boolean, default=False, nullable=False)
    language = Column(String(10), nullable=False)
    confidence_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    metadata = Column(String, nullable=True)


class TestTransactionMetric(TestBase):
    """Test transaction metric model"""
    __tablename__ = "transaction_metrics"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    conversation_id = Column(String, nullable=False)
    transaction_id = Column(String, nullable=True)
    buyer_id = Column(String, nullable=False)
    seller_id = Column(String, nullable=False)
    completed = Column(Boolean, nullable=False)
    abandoned = Column(Boolean, nullable=False)
    conversation_started_at = Column(DateTime, nullable=False)
    conversation_ended_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    commodity = Column(String, nullable=True)
    agreed_price = Column(Float, nullable=True)
    market_average = Column(Float, nullable=True)
    abandonment_reason = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    metadata = Column(String, nullable=True)


class TestSystemLatencyAlert(TestBase):
    """Test system latency alert model"""
    __tablename__ = "system_latency_alerts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    alert_type = Column(String, nullable=False)
    latency_ms = Column(Float, nullable=False)
    threshold_ms = Column(Float, default=10000, nullable=False)
    endpoint = Column(String, nullable=True)
    user_id = Column(String, nullable=True)
    acknowledged = Column(Boolean, default=False, nullable=False)
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    metadata = Column(String, nullable=True)


class TestDailyPerformanceReport(TestBase):
    """Test daily performance report model"""
    __tablename__ = "daily_performance_reports"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    report_date = Column(DateTime, nullable=False)
    avg_total_latency_ms = Column(Float, nullable=True)
    avg_stt_latency_ms = Column(Float, nullable=True)
    avg_translation_latency_ms = Column(Float, nullable=True)
    avg_tts_latency_ms = Column(Float, nullable=True)
    max_latency_ms = Column(Float, nullable=True)
    min_latency_ms = Column(Float, nullable=True)
    total_voice_messages = Column(Integer, default=0)
    total_transcriptions = Column(Integer, default=0)
    total_corrections = Column(Integer, default=0)
    correction_rate = Column(Float, nullable=True)
    avg_confidence_score = Column(Float, nullable=True)
    total_conversations = Column(Integer, default=0)
    completed_transactions = Column(Integer, default=0)
    abandoned_transactions = Column(Integer, default=0)
    completion_rate = Column(Float, nullable=True)
    abandonment_rate = Column(Float, nullable=True)
    total_alerts = Column(Integer, default=0)
    service_availability = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    report_data = Column(String, nullable=True)


# Test database setup
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def db_session():
    """Create a test database session."""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    TestBase.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    
    # Monkey-patch the models to use test models
    import app.models.metrics as metrics_module
    original_models = {
        'VoicePipelineMetric': metrics_module.VoicePipelineMetric,
        'STTAccuracyMetric': metrics_module.STTAccuracyMetric,
        'TransactionMetric': metrics_module.TransactionMetric,
        'SystemLatencyAlert': metrics_module.SystemLatencyAlert,
        'DailyPerformanceReport': metrics_module.DailyPerformanceReport,
    }
    
    metrics_module.VoicePipelineMetric = TestVoicePipelineMetric
    metrics_module.STTAccuracyMetric = TestSTTAccuracyMetric
    metrics_module.TransactionMetric = TestTransactionMetric
    metrics_module.SystemLatencyAlert = TestSystemLatencyAlert
    metrics_module.DailyPerformanceReport = TestDailyPerformanceReport
    
    yield session
    
    # Restore original models
    for name, model in original_models.items():
        setattr(metrics_module, name, model)
    
    session.close()
    TestBase.metadata.drop_all(bind=engine)


@pytest.fixture
def metrics_tracker(db_session):
    """Create a MetricsTracker instance."""
    return MetricsTracker(db_session)


# Voice Pipeline Latency Tests (Requirement 18.1)


def test_track_voice_pipeline_latency_basic(metrics_tracker, db_session):
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
    assert str(metric.user_id) == str(user_id)
    assert str(metric.message_id) == str(message_id)
    
    # Verify it's in database
    saved_metric = db_session.query(TestVoicePipelineMetric).filter_by(id=metric.id).first()
    assert saved_metric is not None
    assert saved_metric.total_latency_ms == 5000.0


def test_track_voice_pipeline_latency_creates_alert_when_exceeds_threshold(
    metrics_tracker, db_session
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
    
    # Check that alert was created
    alerts = db_session.query(TestSystemLatencyAlert).all()
    assert len(alerts) == 1
    assert alerts[0].latency_ms == high_latency
    assert alerts[0].alert_type == "voice_pipeline"
    assert str(alerts[0].user_id) == str(user_id)
    assert alerts[0].acknowledged == False


def test_track_voice_pipeline_latency_no_alert_when_below_threshold(
    metrics_tracker, db_session
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
    
    # Check that no alert was created
    alerts = db_session.query(TestSystemLatencyAlert).all()
    assert len(alerts) == 0


# STT Accuracy Tests (Requirement 18.2)


def test_track_stt_accuracy_without_correction(metrics_tracker, db_session):
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


def test_track_stt_accuracy_with_correction(metrics_tracker, db_session):
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


def test_get_stt_correction_rate_no_data(metrics_tracker):
    """Test correction rate calculation with no data."""
    # Act
    rate = metrics_tracker.get_stt_correction_rate()
    
    # Assert
    assert rate == 0.0


def test_get_stt_correction_rate_with_data(metrics_tracker, db_session):
    """Test correction rate calculation with mixed data."""
    # Arrange
    user_id = uuid4()
    
    # Create 10 transcriptions, 3 with corrections
    for i in range(10):
        corrected = "corrected text" if i < 3 else None
        metrics_tracker.track_stt_accuracy(
            user_id=user_id,
            original_transcription=f"original {i}",
            language="hi",
            corrected_transcription=corrected,
        )
    
    # Act
    rate = metrics_tracker.get_stt_correction_rate()
    
    # Assert
    assert rate == 30.0  # 3 out of 10 = 30%


def test_get_stt_correction_rate_filtered_by_language(metrics_tracker, db_session):
    """Test correction rate calculation filtered by language."""
    # Arrange
    user_id = uuid4()
    
    # Create transcriptions in different languages
    for i in range(5):
        metrics_tracker.track_stt_accuracy(
            user_id=user_id,
            original_transcription=f"hindi {i}",
            language="hi",
            corrected_transcription="corrected" if i < 2 else None,
        )
    
    for i in range(5):
        metrics_tracker.track_stt_accuracy(
            user_id=user_id,
            original_transcription=f"telugu {i}",
            language="te",
            corrected_transcription="corrected" if i < 4 else None,
        )
    
    # Act
    hindi_rate = metrics_tracker.get_stt_correction_rate(language="hi")
    telugu_rate = metrics_tracker.get_stt_correction_rate(language="te")
    
    # Assert
    assert hindi_rate == 40.0  # 2 out of 5 = 40%
    assert telugu_rate == 80.0  # 4 out of 5 = 80%


# Transaction Tracking Tests (Requirement 18.3)


def test_track_transaction_completion(metrics_tracker, db_session):
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


def test_track_transaction_abandonment(metrics_tracker, db_session):
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


def test_get_transaction_completion_rate_no_data(metrics_tracker):
    """Test transaction rate calculation with no data."""
    # Act
    rates = metrics_tracker.get_transaction_completion_rate()
    
    # Assert
    assert rates["completion_rate"] == 0.0
    assert rates["abandonment_rate"] == 0.0


def test_get_transaction_completion_rate_with_data(metrics_tracker, db_session):
    """Test transaction rate calculation with mixed data."""
    # Arrange
    buyer_id = uuid4()
    seller_id = uuid4()
    started_at = datetime.utcnow()
    
    # Create 10 transactions: 7 completed, 3 abandoned
    for i in range(10):
        completed = i < 7
        metrics_tracker.track_transaction_completion(
            conversation_id=uuid4(),
            buyer_id=buyer_id,
            seller_id=seller_id,
            conversation_started_at=started_at,
            completed=completed,
            transaction_id=uuid4() if completed else None,
        )
    
    # Act
    rates = metrics_tracker.get_transaction_completion_rate()
    
    # Assert
    assert rates["completion_rate"] == 70.0  # 7 out of 10 = 70%
    assert rates["abandonment_rate"] == 30.0  # 3 out of 10 = 30%


# System Latency Alert Tests (Requirement 18.4)


def test_get_unacknowledged_alerts(metrics_tracker, db_session):
    """Test retrieving unacknowledged alerts."""
    # Arrange
    # Create some alerts by tracking high latency
    for i in range(3):
        metrics_tracker.track_voice_pipeline_latency(
            total_latency_ms=11000.0 + i * 1000,  # All exceed threshold
            stt_latency_ms=4000.0,
            translation_latency_ms=4000.0,
            tts_latency_ms=3000.0,
        )
    
    # Act
    alerts = metrics_tracker.get_unacknowledged_alerts()
    
    # Assert
    assert len(alerts) == 3
    for alert in alerts:
        assert alert.acknowledged == False


def test_acknowledge_alert(metrics_tracker, db_session):
    """Test acknowledging an alert."""
    # Arrange
    # Create an alert
    metrics_tracker.track_voice_pipeline_latency(
        total_latency_ms=12000.0,
        stt_latency_ms=4000.0,
        translation_latency_ms=4000.0,
        tts_latency_ms=4000.0,
    )
    
    alerts = metrics_tracker.get_unacknowledged_alerts()
    assert len(alerts) == 1
    alert_id = alerts[0].id
    
    # Act
    success = metrics_tracker.acknowledge_alert(alert_id, "admin@example.com")
    
    # Assert
    assert success == True
    
    # Verify alert is acknowledged
    alert = db_session.query(TestSystemLatencyAlert).filter_by(id=alert_id).first()
    assert alert.acknowledged == True
    assert alert.acknowledged_by == "admin@example.com"
    assert alert.acknowledged_at is not None
    
    # Verify it's no longer in unacknowledged list
    unack_alerts = metrics_tracker.get_unacknowledged_alerts()
    assert len(unack_alerts) == 0


def test_acknowledge_nonexistent_alert(metrics_tracker):
    """Test acknowledging a non-existent alert."""
    # Act
    success = metrics_tracker.acknowledge_alert(uuid4(), "admin@example.com")
    
    # Assert
    assert success == False


# Daily Performance Report Tests (Requirement 18.5)


def test_generate_daily_report_no_data(metrics_tracker, db_session):
    """Test generating daily report with no data."""
    # Arrange
    report_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Act
    report = metrics_tracker.generate_daily_report(report_date)
    
    # Assert
    assert report is not None
    assert report.report_date == report_date
    assert report.total_voice_messages == 0
    assert report.total_transcriptions == 0
    assert report.total_conversations == 0


def test_generate_daily_report_with_data(metrics_tracker, db_session):
    """Test generating daily report with comprehensive data."""
    # Arrange
    report_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    user_id = uuid4()
    
    # Create voice pipeline metrics
    for i in range(5):
        metrics_tracker.track_voice_pipeline_latency(
            total_latency_ms=5000.0 + i * 1000,
            user_id=user_id,
            stt_latency_ms=2000.0,
            translation_latency_ms=1500.0,
            tts_latency_ms=1500.0,
        )
    
    # Create STT accuracy metrics (3 with corrections)
    for i in range(10):
        metrics_tracker.track_stt_accuracy(
            user_id=user_id,
            original_transcription=f"text {i}",
            language="hi",
            corrected_transcription="corrected" if i < 3 else None,
            confidence_score=0.85,
        )
    
    # Create transaction metrics (7 completed, 3 abandoned)
    buyer_id = uuid4()
    seller_id = uuid4()
    for i in range(10):
        metrics_tracker.track_transaction_completion(
            conversation_id=uuid4(),
            buyer_id=buyer_id,
            seller_id=seller_id,
            conversation_started_at=datetime.utcnow(),
            completed=i < 7,
            transaction_id=uuid4() if i < 7 else None,
        )
    
    # Act
    report = metrics_tracker.generate_daily_report(report_date)
    
    # Assert
    assert report is not None
    assert report.total_voice_messages == 5
    assert report.avg_total_latency_ms == 7000.0  # Average of 5000, 6000, 7000, 8000, 9000
    assert report.total_transcriptions == 10
    assert report.total_corrections == 3
    assert report.correction_rate == 30.0
    assert report.total_conversations == 10
    assert report.completed_transactions == 7
    assert report.abandoned_transactions == 3
    assert report.completion_rate == 70.0
    assert report.abandonment_rate == 30.0


def test_get_recent_reports(metrics_tracker, db_session):
    """Test retrieving recent daily reports."""
    # Arrange
    # Generate reports for last 5 days
    for i in range(5):
        report_date = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        ) - timedelta(days=i)
        metrics_tracker.generate_daily_report(report_date)
    
    # Act
    reports = metrics_tracker.get_recent_reports(days=7)
    
    # Assert
    assert len(reports) == 5
    # Should be ordered by date descending
    for i in range(len(reports) - 1):
        assert reports[i].report_date >= reports[i + 1].report_date


def test_get_recent_reports_limited(metrics_tracker, db_session):
    """Test retrieving recent reports with limit."""
    # Arrange
    # Generate reports for last 10 days
    for i in range(10):
        report_date = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        ) - timedelta(days=i)
        metrics_tracker.generate_daily_report(report_date)
    
    # Act
    reports = metrics_tracker.get_recent_reports(days=3)
    
    # Assert
    assert len(reports) == 3


# Edge Cases and Error Handling


def test_track_voice_pipeline_latency_with_metadata(metrics_tracker, db_session):
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


def test_track_stt_accuracy_same_text_not_correction(metrics_tracker, db_session):
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


def test_transaction_duration_calculation(metrics_tracker, db_session):
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
