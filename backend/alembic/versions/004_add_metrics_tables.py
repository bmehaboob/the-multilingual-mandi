"""Add metrics tracking tables

Revision ID: 004
Revises: 003
Create Date: 2024-01-15 10:00:00.000000

Requirements: 18.1, 18.2, 18.3, 18.4, 18.5
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create metrics tracking tables."""
    
    # Voice Pipeline Metrics table
    op.create_table(
        'voice_pipeline_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('language_detection_latency_ms', sa.Float(), nullable=True),
        sa.Column('stt_latency_ms', sa.Float(), nullable=True),
        sa.Column('translation_latency_ms', sa.Float(), nullable=True),
        sa.Column('tts_latency_ms', sa.Float(), nullable=True),
        sa.Column('total_latency_ms', sa.Float(), nullable=False),
        sa.Column('source_language', sa.String(10), nullable=True),
        sa.Column('target_language', sa.String(10), nullable=True),
        sa.Column('audio_duration_ms', sa.Float(), nullable=True),
        sa.Column('text_length', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
    )
    
    # Create indexes for voice pipeline metrics
    op.create_index('ix_voice_pipeline_metrics_user_id', 'voice_pipeline_metrics', ['user_id'])
    op.create_index('ix_voice_pipeline_metrics_created_at', 'voice_pipeline_metrics', ['created_at'])
    op.create_index('ix_voice_pipeline_metrics_total_latency', 'voice_pipeline_metrics', ['total_latency_ms'])
    
    # STT Accuracy Metrics table
    op.create_table(
        'stt_accuracy_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('original_transcription', sa.String(), nullable=False),
        sa.Column('corrected_transcription', sa.String(), nullable=True),
        sa.Column('was_corrected', sa.Boolean(), default=False, nullable=False),
        sa.Column('language', sa.String(10), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
    )
    
    # Create indexes for STT accuracy metrics
    op.create_index('ix_stt_accuracy_metrics_user_id', 'stt_accuracy_metrics', ['user_id'])
    op.create_index('ix_stt_accuracy_metrics_language', 'stt_accuracy_metrics', ['language'])
    op.create_index('ix_stt_accuracy_metrics_created_at', 'stt_accuracy_metrics', ['created_at'])
    op.create_index('ix_stt_accuracy_metrics_was_corrected', 'stt_accuracy_metrics', ['was_corrected'])
    
    # Transaction Metrics table
    op.create_table(
        'transaction_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('transaction_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('buyer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('seller_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('completed', sa.Boolean(), nullable=False),
        sa.Column('abandoned', sa.Boolean(), nullable=False),
        sa.Column('conversation_started_at', sa.DateTime(), nullable=False),
        sa.Column('conversation_ended_at', sa.DateTime(), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('commodity', sa.String(), nullable=True),
        sa.Column('agreed_price', sa.Float(), nullable=True),
        sa.Column('market_average', sa.Float(), nullable=True),
        sa.Column('abandonment_reason', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
    )
    
    # Create indexes for transaction metrics
    op.create_index('ix_transaction_metrics_conversation_id', 'transaction_metrics', ['conversation_id'])
    op.create_index('ix_transaction_metrics_buyer_id', 'transaction_metrics', ['buyer_id'])
    op.create_index('ix_transaction_metrics_seller_id', 'transaction_metrics', ['seller_id'])
    op.create_index('ix_transaction_metrics_created_at', 'transaction_metrics', ['created_at'])
    op.create_index('ix_transaction_metrics_completed', 'transaction_metrics', ['completed'])
    
    # System Latency Alerts table
    op.create_table(
        'system_latency_alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('alert_type', sa.String(), nullable=False),
        sa.Column('latency_ms', sa.Float(), nullable=False),
        sa.Column('threshold_ms', sa.Float(), default=10000, nullable=False),
        sa.Column('endpoint', sa.String(), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('acknowledged', sa.Boolean(), default=False, nullable=False),
        sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
        sa.Column('acknowledged_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
    )
    
    # Create indexes for system latency alerts
    op.create_index('ix_system_latency_alerts_created_at', 'system_latency_alerts', ['created_at'])
    op.create_index('ix_system_latency_alerts_acknowledged', 'system_latency_alerts', ['acknowledged'])
    op.create_index('ix_system_latency_alerts_alert_type', 'system_latency_alerts', ['alert_type'])
    
    # Daily Performance Reports table
    op.create_table(
        'daily_performance_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('report_date', sa.DateTime(), nullable=False),
        sa.Column('avg_total_latency_ms', sa.Float(), nullable=True),
        sa.Column('avg_stt_latency_ms', sa.Float(), nullable=True),
        sa.Column('avg_translation_latency_ms', sa.Float(), nullable=True),
        sa.Column('avg_tts_latency_ms', sa.Float(), nullable=True),
        sa.Column('max_latency_ms', sa.Float(), nullable=True),
        sa.Column('min_latency_ms', sa.Float(), nullable=True),
        sa.Column('total_voice_messages', sa.Integer(), default=0),
        sa.Column('total_transcriptions', sa.Integer(), default=0),
        sa.Column('total_corrections', sa.Integer(), default=0),
        sa.Column('correction_rate', sa.Float(), nullable=True),
        sa.Column('avg_confidence_score', sa.Float(), nullable=True),
        sa.Column('total_conversations', sa.Integer(), default=0),
        sa.Column('completed_transactions', sa.Integer(), default=0),
        sa.Column('abandoned_transactions', sa.Integer(), default=0),
        sa.Column('completion_rate', sa.Float(), nullable=True),
        sa.Column('abandonment_rate', sa.Float(), nullable=True),
        sa.Column('total_alerts', sa.Integer(), default=0),
        sa.Column('service_availability', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('report_data', postgresql.JSONB(), nullable=True),
    )
    
    # Create indexes for daily performance reports
    op.create_index('ix_daily_performance_reports_report_date', 'daily_performance_reports', ['report_date'])
    op.create_index('ix_daily_performance_reports_created_at', 'daily_performance_reports', ['created_at'])


def downgrade() -> None:
    """Drop metrics tracking tables."""
    op.drop_table('daily_performance_reports')
    op.drop_table('system_latency_alerts')
    op.drop_table('transaction_metrics')
    op.drop_table('stt_accuracy_metrics')
    op.drop_table('voice_pipeline_metrics')
