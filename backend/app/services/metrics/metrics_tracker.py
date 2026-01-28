"""
Metrics tracking service for monitoring system performance and quality.

Requirements: 18.1, 18.2, 18.3, 18.4, 18.5
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.metrics import (
    VoicePipelineMetric,
    STTAccuracyMetric,
    TransactionMetric,
    SystemLatencyAlert,
    DailyPerformanceReport,
    PipelineStage,
)

logger = logging.getLogger(__name__)


class MetricsTracker:
    """
    Service for tracking and analyzing system performance metrics.
    
    Tracks:
    - Voice pipeline latency for all stages
    - STT accuracy via user correction rates
    - Transaction completion vs. abandonment rates
    - System latency alerts
    - Daily performance reports
    
    Requirements: 18.1, 18.2, 18.3, 18.4, 18.5
    """
    
    def __init__(self, db: Session):
        """
        Initialize metrics tracker.
        
        Args:
            db: Database session
        """
        self.db = db
        self.latency_threshold_ms = 10000  # 10 seconds
    
    # Voice Pipeline Latency Tracking (Requirement 18.1)
    
    def track_voice_pipeline_latency(
        self,
        total_latency_ms: float,
        message_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        language_detection_latency_ms: Optional[float] = None,
        stt_latency_ms: Optional[float] = None,
        translation_latency_ms: Optional[float] = None,
        tts_latency_ms: Optional[float] = None,
        source_language: Optional[str] = None,
        target_language: Optional[str] = None,
        audio_duration_ms: Optional[float] = None,
        text_length: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> VoicePipelineMetric:
        """
        Track latency for voice pipeline stages.
        
        Requirements: 18.1
        
        Args:
            total_latency_ms: Total end-to-end latency
            message_id: Optional message ID reference
            user_id: Optional user ID
            language_detection_latency_ms: Language detection stage latency
            stt_latency_ms: Speech-to-text stage latency
            translation_latency_ms: Translation stage latency
            tts_latency_ms: Text-to-speech stage latency
            source_language: Source language code
            target_language: Target language code
            audio_duration_ms: Duration of input audio
            text_length: Length of transcribed text
            metadata: Additional metadata
        
        Returns:
            Created VoicePipelineMetric instance
        """
        try:
            metric = VoicePipelineMetric(
                message_id=message_id,
                user_id=user_id,
                language_detection_latency_ms=language_detection_latency_ms,
                stt_latency_ms=stt_latency_ms,
                translation_latency_ms=translation_latency_ms,
                tts_latency_ms=tts_latency_ms,
                total_latency_ms=total_latency_ms,
                source_language=source_language,
                target_language=target_language,
                audio_duration_ms=audio_duration_ms,
                text_length=text_length,
                event_metadata=metadata,
            )
            
            self.db.add(metric)
            self.db.commit()
            self.db.refresh(metric)
            
            # Check if latency exceeds threshold and create alert
            if total_latency_ms > self.latency_threshold_ms:
                self._create_latency_alert(
                    alert_type="voice_pipeline",
                    latency_ms=total_latency_ms,
                    user_id=user_id,
                    event_metadata={
                        "message_id": str(message_id) if message_id else None,
                        "stages": {
                            "language_detection": language_detection_latency_ms,
                            "stt": stt_latency_ms,
                            "translation": translation_latency_ms,
                            "tts": tts_latency_ms,
                        }
                    }
                )
            
            logger.info(
                f"Tracked voice pipeline latency: {total_latency_ms}ms "
                f"(STT: {stt_latency_ms}ms, Translation: {translation_latency_ms}ms, "
                f"TTS: {tts_latency_ms}ms)"
            )
            
            return metric
            
        except Exception as e:
            logger.error(f"Error tracking voice pipeline latency: {e}")
            self.db.rollback()
            raise
    
    # STT Accuracy Tracking (Requirement 18.2)
    
    def track_stt_accuracy(
        self,
        user_id: UUID,
        original_transcription: str,
        language: str,
        message_id: Optional[UUID] = None,
        corrected_transcription: Optional[str] = None,
        confidence_score: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> STTAccuracyMetric:
        """
        Track STT accuracy via user correction rates.
        
        Requirements: 18.2
        
        Args:
            user_id: User who provided the transcription/correction
            original_transcription: Original STT output
            language: Language code
            message_id: Optional message ID reference
            corrected_transcription: User's correction (if provided)
            confidence_score: STT confidence score
            metadata: Additional metadata
        
        Returns:
            Created STTAccuracyMetric instance
        """
        try:
            was_corrected = corrected_transcription is not None and \
                           corrected_transcription != original_transcription
            
            metric = STTAccuracyMetric(
                message_id=message_id,
                user_id=user_id,
                original_transcription=original_transcription,
                corrected_transcription=corrected_transcription,
                was_corrected=was_corrected,
                language=language,
                confidence_score=confidence_score,
                event_metadata=metadata,
            )
            
            self.db.add(metric)
            self.db.commit()
            self.db.refresh(metric)
            
            if was_corrected:
                logger.info(
                    f"STT correction recorded for language {language}: "
                    f"'{original_transcription}' -> '{corrected_transcription}'"
                )
            
            return metric
            
        except Exception as e:
            logger.error(f"Error tracking STT accuracy: {e}")
            self.db.rollback()
            raise
    
    def get_stt_correction_rate(
        self,
        language: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> float:
        """
        Calculate STT correction rate (percentage of transcriptions corrected).
        
        Requirements: 18.2
        
        Args:
            language: Optional language filter
            start_date: Optional start date filter
            end_date: Optional end date filter
        
        Returns:
            Correction rate as percentage (0-100)
        """
        try:
            query = self.db.query(STTAccuracyMetric)
            
            if language:
                query = query.filter(STTAccuracyMetric.language == language)
            if start_date:
                query = query.filter(STTAccuracyMetric.created_at >= start_date)
            if end_date:
                query = query.filter(STTAccuracyMetric.created_at <= end_date)
            
            total = query.count()
            if total == 0:
                return 0.0
            
            corrected = query.filter(STTAccuracyMetric.was_corrected == True).count()
            
            return (corrected / total) * 100.0
            
        except Exception as e:
            logger.error(f"Error calculating STT correction rate: {e}")
            return 0.0
    
    # Transaction Tracking (Requirement 18.3)
    
    def track_transaction_completion(
        self,
        conversation_id: UUID,
        buyer_id: UUID,
        seller_id: UUID,
        conversation_started_at: datetime,
        completed: bool,
        transaction_id: Optional[UUID] = None,
        conversation_ended_at: Optional[datetime] = None,
        commodity: Optional[str] = None,
        agreed_price: Optional[float] = None,
        market_average: Optional[float] = None,
        abandonment_reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TransactionMetric:
        """
        Track transaction completion or abandonment.
        
        Requirements: 18.3
        
        Args:
            conversation_id: Conversation ID
            buyer_id: Buyer user ID
            seller_id: Seller user ID
            conversation_started_at: When conversation started
            completed: Whether transaction was completed
            transaction_id: Transaction ID if completed
            conversation_ended_at: When conversation ended
            commodity: Commodity name if completed
            agreed_price: Agreed price if completed
            market_average: Market average at time if completed
            abandonment_reason: Reason for abandonment if not completed
            metadata: Additional metadata
        
        Returns:
            Created TransactionMetric instance
        """
        try:
            duration_seconds = None
            if conversation_ended_at:
                duration_seconds = int(
                    (conversation_ended_at - conversation_started_at).total_seconds()
                )
            
            metric = TransactionMetric(
                conversation_id=conversation_id,
                transaction_id=transaction_id,
                buyer_id=buyer_id,
                seller_id=seller_id,
                completed=completed,
                abandoned=not completed,
                conversation_started_at=conversation_started_at,
                conversation_ended_at=conversation_ended_at,
                duration_seconds=duration_seconds,
                commodity=commodity,
                agreed_price=agreed_price,
                market_average=market_average,
                abandonment_reason=abandonment_reason,
                event_metadata=metadata,
            )
            
            self.db.add(metric)
            self.db.commit()
            self.db.refresh(metric)
            
            status = "completed" if completed else "abandoned"
            logger.info(
                f"Tracked transaction {status}: conversation_id={conversation_id}, "
                f"duration={duration_seconds}s"
            )
            
            return metric
            
        except Exception as e:
            logger.error(f"Error tracking transaction: {e}")
            self.db.rollback()
            raise
    
    def get_transaction_completion_rate(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, float]:
        """
        Calculate transaction completion and abandonment rates.
        
        Requirements: 18.3
        
        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter
        
        Returns:
            Dictionary with completion_rate and abandonment_rate (percentages)
        """
        try:
            query = self.db.query(TransactionMetric)
            
            if start_date:
                query = query.filter(TransactionMetric.created_at >= start_date)
            if end_date:
                query = query.filter(TransactionMetric.created_at <= end_date)
            
            total = query.count()
            if total == 0:
                return {"completion_rate": 0.0, "abandonment_rate": 0.0}
            
            completed = query.filter(TransactionMetric.completed == True).count()
            abandoned = query.filter(TransactionMetric.abandoned == True).count()
            
            return {
                "completion_rate": (completed / total) * 100.0,
                "abandonment_rate": (abandoned / total) * 100.0,
            }
            
        except Exception as e:
            logger.error(f"Error calculating transaction rates: {e}")
            return {"completion_rate": 0.0, "abandonment_rate": 0.0}
    
    # System Latency Alerts (Requirement 18.4)
    
    def _create_latency_alert(
        self,
        alert_type: str,
        latency_ms: float,
        endpoint: Optional[str] = None,
        user_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SystemLatencyAlert:
        """
        Create a system latency alert when threshold is exceeded.
        
        Requirements: 18.4
        
        Args:
            alert_type: Type of alert (e.g., "voice_pipeline", "api_endpoint")
            latency_ms: Measured latency
            endpoint: Optional endpoint name
            user_id: Optional user ID
            metadata: Additional metadata
        
        Returns:
            Created SystemLatencyAlert instance
        """
        try:
            alert = SystemLatencyAlert(
                alert_type=alert_type,
                latency_ms=latency_ms,
                threshold_ms=self.latency_threshold_ms,
                endpoint=endpoint,
                user_id=user_id,
                event_metadata=metadata,
            )
            
            self.db.add(alert)
            self.db.commit()
            self.db.refresh(alert)
            
            logger.warning(
                f"LATENCY ALERT: {alert_type} exceeded threshold "
                f"({latency_ms}ms > {self.latency_threshold_ms}ms)"
            )
            
            return alert
            
        except Exception as e:
            logger.error(f"Error creating latency alert: {e}")
            self.db.rollback()
            raise
    
    def get_unacknowledged_alerts(self) -> List[SystemLatencyAlert]:
        """
        Get all unacknowledged latency alerts.
        
        Requirements: 18.4
        
        Returns:
            List of unacknowledged alerts
        """
        try:
            return self.db.query(SystemLatencyAlert)\
                .filter(SystemLatencyAlert.acknowledged == False)\
                .order_by(SystemLatencyAlert.created_at.desc())\
                .all()
        except Exception as e:
            logger.error(f"Error fetching unacknowledged alerts: {e}")
            return []
    
    def acknowledge_alert(
        self,
        alert_id: UUID,
        acknowledged_by: str,
    ) -> bool:
        """
        Acknowledge a latency alert.
        
        Requirements: 18.4
        
        Args:
            alert_id: Alert ID to acknowledge
            acknowledged_by: Name/ID of person acknowledging
        
        Returns:
            True if successful, False otherwise
        """
        try:
            alert = self.db.query(SystemLatencyAlert)\
                .filter(SystemLatencyAlert.id == alert_id)\
                .first()
            
            if not alert:
                logger.warning(f"Alert {alert_id} not found")
                return False
            
            alert.acknowledged = True
            alert.acknowledged_at = datetime.utcnow()
            alert.acknowledged_by = acknowledged_by
            
            self.db.commit()
            
            logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
            return True
            
        except Exception as e:
            logger.error(f"Error acknowledging alert: {e}")
            self.db.rollback()
            return False
    
    # Daily Performance Reports (Requirement 18.5)
    
    def generate_daily_report(
        self,
        report_date: Optional[datetime] = None,
    ) -> DailyPerformanceReport:
        """
        Generate daily performance report.
        
        Requirements: 18.5
        
        Args:
            report_date: Date for report (defaults to yesterday)
        
        Returns:
            Created DailyPerformanceReport instance
        """
        try:
            if report_date is None:
                report_date = datetime.utcnow().replace(
                    hour=0, minute=0, second=0, microsecond=0
                ) - timedelta(days=1)
            
            start_date = report_date
            end_date = report_date + timedelta(days=1)
            
            # Voice pipeline metrics
            pipeline_metrics = self._calculate_pipeline_metrics(start_date, end_date)
            
            # STT accuracy metrics
            stt_metrics = self._calculate_stt_metrics(start_date, end_date)
            
            # Transaction metrics
            transaction_metrics = self._calculate_transaction_metrics(start_date, end_date)
            
            # System health metrics
            system_metrics = self._calculate_system_metrics(start_date, end_date)
            
            # Create report
            report = DailyPerformanceReport(
                report_date=report_date,
                # Voice pipeline
                avg_total_latency_ms=pipeline_metrics.get("avg_total_latency_ms"),
                avg_stt_latency_ms=pipeline_metrics.get("avg_stt_latency_ms"),
                avg_translation_latency_ms=pipeline_metrics.get("avg_translation_latency_ms"),
                avg_tts_latency_ms=pipeline_metrics.get("avg_tts_latency_ms"),
                max_latency_ms=pipeline_metrics.get("max_latency_ms"),
                min_latency_ms=pipeline_metrics.get("min_latency_ms"),
                total_voice_messages=pipeline_metrics.get("total_voice_messages", 0),
                # STT accuracy
                total_transcriptions=stt_metrics.get("total_transcriptions", 0),
                total_corrections=stt_metrics.get("total_corrections", 0),
                correction_rate=stt_metrics.get("correction_rate"),
                avg_confidence_score=stt_metrics.get("avg_confidence_score"),
                # Transactions
                total_conversations=transaction_metrics.get("total_conversations", 0),
                completed_transactions=transaction_metrics.get("completed_transactions", 0),
                abandoned_transactions=transaction_metrics.get("abandoned_transactions", 0),
                completion_rate=transaction_metrics.get("completion_rate"),
                abandonment_rate=transaction_metrics.get("abandonment_rate"),
                # System health
                total_alerts=system_metrics.get("total_alerts", 0),
                service_availability=system_metrics.get("service_availability"),
                # Full report data
                report_data={
                    "pipeline_metrics": pipeline_metrics,
                    "stt_metrics": stt_metrics,
                    "transaction_metrics": transaction_metrics,
                    "system_metrics": system_metrics,
                }
            )
            
            self.db.add(report)
            self.db.commit()
            self.db.refresh(report)
            
            logger.info(
                f"Generated daily performance report for {report_date.date()}: "
                f"{pipeline_metrics.get('total_voice_messages', 0)} messages, "
                f"{transaction_metrics.get('completed_transactions', 0)} transactions"
            )
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating daily report: {e}")
            self.db.rollback()
            raise
    
    def _calculate_pipeline_metrics(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """Calculate voice pipeline metrics for date range."""
        try:
            query = self.db.query(VoicePipelineMetric)\
                .filter(VoicePipelineMetric.created_at >= start_date)\
                .filter(VoicePipelineMetric.created_at < end_date)
            
            total_count = query.count()
            
            if total_count == 0:
                return {
                    "total_voice_messages": 0,
                    "avg_total_latency_ms": None,
                    "avg_stt_latency_ms": None,
                    "avg_translation_latency_ms": None,
                    "avg_tts_latency_ms": None,
                    "max_latency_ms": None,
                    "min_latency_ms": None,
                }
            
            # Calculate averages
            avg_metrics = self.db.query(
                func.avg(VoicePipelineMetric.total_latency_ms).label("avg_total"),
                func.avg(VoicePipelineMetric.stt_latency_ms).label("avg_stt"),
                func.avg(VoicePipelineMetric.translation_latency_ms).label("avg_translation"),
                func.avg(VoicePipelineMetric.tts_latency_ms).label("avg_tts"),
                func.max(VoicePipelineMetric.total_latency_ms).label("max_latency"),
                func.min(VoicePipelineMetric.total_latency_ms).label("min_latency"),
            ).filter(VoicePipelineMetric.created_at >= start_date)\
             .filter(VoicePipelineMetric.created_at < end_date)\
             .first()
            
            return {
                "total_voice_messages": total_count,
                "avg_total_latency_ms": float(avg_metrics.avg_total) if avg_metrics.avg_total else None,
                "avg_stt_latency_ms": float(avg_metrics.avg_stt) if avg_metrics.avg_stt else None,
                "avg_translation_latency_ms": float(avg_metrics.avg_translation) if avg_metrics.avg_translation else None,
                "avg_tts_latency_ms": float(avg_metrics.avg_tts) if avg_metrics.avg_tts else None,
                "max_latency_ms": float(avg_metrics.max_latency) if avg_metrics.max_latency else None,
                "min_latency_ms": float(avg_metrics.min_latency) if avg_metrics.min_latency else None,
            }
            
        except Exception as e:
            logger.error(f"Error calculating pipeline metrics: {e}")
            return {}
    
    def _calculate_stt_metrics(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """Calculate STT accuracy metrics for date range."""
        try:
            query = self.db.query(STTAccuracyMetric)\
                .filter(STTAccuracyMetric.created_at >= start_date)\
                .filter(STTAccuracyMetric.created_at < end_date)
            
            total_count = query.count()
            
            if total_count == 0:
                return {
                    "total_transcriptions": 0,
                    "total_corrections": 0,
                    "correction_rate": None,
                    "avg_confidence_score": None,
                }
            
            corrected_count = query.filter(STTAccuracyMetric.was_corrected == True).count()
            
            avg_confidence = self.db.query(
                func.avg(STTAccuracyMetric.confidence_score)
            ).filter(STTAccuracyMetric.created_at >= start_date)\
             .filter(STTAccuracyMetric.created_at < end_date)\
             .filter(STTAccuracyMetric.confidence_score.isnot(None))\
             .scalar()
            
            return {
                "total_transcriptions": total_count,
                "total_corrections": corrected_count,
                "correction_rate": (corrected_count / total_count) * 100.0,
                "avg_confidence_score": float(avg_confidence) if avg_confidence else None,
            }
            
        except Exception as e:
            logger.error(f"Error calculating STT metrics: {e}")
            return {}
    
    def _calculate_transaction_metrics(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """Calculate transaction metrics for date range."""
        try:
            query = self.db.query(TransactionMetric)\
                .filter(TransactionMetric.created_at >= start_date)\
                .filter(TransactionMetric.created_at < end_date)
            
            total_count = query.count()
            
            if total_count == 0:
                return {
                    "total_conversations": 0,
                    "completed_transactions": 0,
                    "abandoned_transactions": 0,
                    "completion_rate": None,
                    "abandonment_rate": None,
                }
            
            completed_count = query.filter(TransactionMetric.completed == True).count()
            abandoned_count = query.filter(TransactionMetric.abandoned == True).count()
            
            return {
                "total_conversations": total_count,
                "completed_transactions": completed_count,
                "abandoned_transactions": abandoned_count,
                "completion_rate": (completed_count / total_count) * 100.0,
                "abandonment_rate": (abandoned_count / total_count) * 100.0,
            }
            
        except Exception as e:
            logger.error(f"Error calculating transaction metrics: {e}")
            return {}
    
    def _calculate_system_metrics(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """Calculate system health metrics for date range."""
        try:
            alert_count = self.db.query(SystemLatencyAlert)\
                .filter(SystemLatencyAlert.created_at >= start_date)\
                .filter(SystemLatencyAlert.created_at < end_date)\
                .count()
            
            # Calculate service availability (simplified)
            # In production, this would be based on uptime monitoring
            # For now, we'll estimate based on alerts
            # Assume each alert represents 1 minute of degraded service
            total_minutes = 24 * 60  # 1 day
            degraded_minutes = min(alert_count, total_minutes)
            availability = ((total_minutes - degraded_minutes) / total_minutes) * 100.0
            
            return {
                "total_alerts": alert_count,
                "service_availability": availability,
            }
            
        except Exception as e:
            logger.error(f"Error calculating system metrics: {e}")
            return {}
    
    def get_recent_reports(
        self,
        days: int = 7,
    ) -> List[DailyPerformanceReport]:
        """
        Get recent daily performance reports.
        
        Requirements: 18.5
        
        Args:
            days: Number of days to retrieve
        
        Returns:
            List of recent reports
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            return self.db.query(DailyPerformanceReport)\
                .filter(DailyPerformanceReport.report_date >= cutoff_date)\
                .order_by(DailyPerformanceReport.report_date.desc())\
                .all()
                
        except Exception as e:
            logger.error(f"Error fetching recent reports: {e}")
            return []
