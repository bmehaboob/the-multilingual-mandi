"""Add feedback tables

Revision ID: 005
Revises: 004
Create Date: 2024-01-15 10:00:00.000000

Requirements: 20.1, 20.2, 22.1, 22.3, 22.4
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create satisfaction_rating enum
    satisfaction_rating_enum = postgresql.ENUM(
        'very_dissatisfied',
        'dissatisfied',
        'neutral',
        'satisfied',
        'very_satisfied',
        name='satisfactionrating',
        create_type=True
    )
    satisfaction_rating_enum.create(op.get_bind(), checkfirst=True)
    
    # Create transcription_feedback table
    op.create_table(
        'transcription_feedback',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('audio_hash', sa.String(64), nullable=True),
        sa.Column('incorrect_transcription', sa.Text(), nullable=False),
        sa.Column('correct_transcription', sa.Text(), nullable=False),
        sa.Column('language', sa.String(10), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('dialect', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    )
    
    # Create negotiation_feedback table
    op.create_table(
        'negotiation_feedback',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('suggestion_id', sa.String(100), nullable=True),
        sa.Column('suggested_price', sa.Float(), nullable=True),
        sa.Column('suggested_message', sa.Text(), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('was_helpful', sa.Boolean(), nullable=False),
        sa.Column('was_culturally_appropriate', sa.Boolean(), nullable=True),
        sa.Column('was_used', sa.Boolean(), nullable=True),
        sa.Column('feedback_text', sa.Text(), nullable=True),
        sa.Column('commodity', sa.String(100), nullable=True),
        sa.Column('market_average', sa.Float(), nullable=True),
        sa.Column('language', sa.String(10), nullable=True),
        sa.Column('region', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    )
    
    # Create satisfaction_surveys table
    op.create_table(
        'satisfaction_surveys',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('survey_type', sa.String(50), nullable=False),
        sa.Column('transaction_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('overall_rating', satisfaction_rating_enum, nullable=False),
        sa.Column('voice_translation_rating', sa.Integer(), nullable=True),
        sa.Column('price_oracle_rating', sa.Integer(), nullable=True),
        sa.Column('negotiation_assistant_rating', sa.Integer(), nullable=True),
        sa.Column('price_oracle_helpful', sa.Boolean(), nullable=True),
        sa.Column('negotiation_suggestions_helpful', sa.Boolean(), nullable=True),
        sa.Column('negotiation_culturally_appropriate', sa.Boolean(), nullable=True),
        sa.Column('feedback_text', sa.Text(), nullable=True),
        sa.Column('language', sa.String(10), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    )
    
    # Create translation_feedback table
    op.create_table(
        'translation_feedback',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('source_text', sa.Text(), nullable=False),
        sa.Column('translated_text', sa.Text(), nullable=False),
        sa.Column('source_language', sa.String(10), nullable=False),
        sa.Column('target_language', sa.String(10), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('was_accurate', sa.Boolean(), nullable=False),
        sa.Column('preserved_meaning', sa.Boolean(), nullable=True),
        sa.Column('corrected_translation', sa.Text(), nullable=True),
        sa.Column('feedback_text', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    )
    
    # Create price_oracle_feedback table
    op.create_table(
        'price_oracle_feedback',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('transaction_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('commodity', sa.String(100), nullable=False),
        sa.Column('quoted_price', sa.Float(), nullable=True),
        sa.Column('market_average', sa.Float(), nullable=True),
        sa.Column('price_verdict', sa.String(20), nullable=True),
        sa.Column('was_helpful', sa.Boolean(), nullable=False),
        sa.Column('was_accurate', sa.Boolean(), nullable=True),
        sa.Column('influenced_decision', sa.Boolean(), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('feedback_text', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    )
    
    # Create indexes for common queries
    op.create_index('ix_transcription_feedback_user_id', 'transcription_feedback', ['user_id'])
    op.create_index('ix_transcription_feedback_language', 'transcription_feedback', ['language'])
    op.create_index('ix_transcription_feedback_created_at', 'transcription_feedback', ['created_at'])
    
    op.create_index('ix_negotiation_feedback_user_id', 'negotiation_feedback', ['user_id'])
    op.create_index('ix_negotiation_feedback_conversation_id', 'negotiation_feedback', ['conversation_id'])
    op.create_index('ix_negotiation_feedback_created_at', 'negotiation_feedback', ['created_at'])
    
    op.create_index('ix_satisfaction_surveys_user_id', 'satisfaction_surveys', ['user_id'])
    op.create_index('ix_satisfaction_surveys_survey_type', 'satisfaction_surveys', ['survey_type'])
    op.create_index('ix_satisfaction_surveys_created_at', 'satisfaction_surveys', ['created_at'])
    
    op.create_index('ix_translation_feedback_user_id', 'translation_feedback', ['user_id'])
    op.create_index('ix_translation_feedback_created_at', 'translation_feedback', ['created_at'])
    
    op.create_index('ix_price_oracle_feedback_user_id', 'price_oracle_feedback', ['user_id'])
    op.create_index('ix_price_oracle_feedback_commodity', 'price_oracle_feedback', ['commodity'])
    op.create_index('ix_price_oracle_feedback_created_at', 'price_oracle_feedback', ['created_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_price_oracle_feedback_created_at', 'price_oracle_feedback')
    op.drop_index('ix_price_oracle_feedback_commodity', 'price_oracle_feedback')
    op.drop_index('ix_price_oracle_feedback_user_id', 'price_oracle_feedback')
    
    op.drop_index('ix_translation_feedback_created_at', 'translation_feedback')
    op.drop_index('ix_translation_feedback_user_id', 'translation_feedback')
    
    op.drop_index('ix_satisfaction_surveys_created_at', 'satisfaction_surveys')
    op.drop_index('ix_satisfaction_surveys_survey_type', 'satisfaction_surveys')
    op.drop_index('ix_satisfaction_surveys_user_id', 'satisfaction_surveys')
    
    op.drop_index('ix_negotiation_feedback_created_at', 'negotiation_feedback')
    op.drop_index('ix_negotiation_feedback_conversation_id', 'negotiation_feedback')
    op.drop_index('ix_negotiation_feedback_user_id', 'negotiation_feedback')
    
    op.drop_index('ix_transcription_feedback_created_at', 'transcription_feedback')
    op.drop_index('ix_transcription_feedback_language', 'transcription_feedback')
    op.drop_index('ix_transcription_feedback_user_id', 'transcription_feedback')
    
    # Drop tables
    op.drop_table('price_oracle_feedback')
    op.drop_table('translation_feedback')
    op.drop_table('satisfaction_surveys')
    op.drop_table('negotiation_feedback')
    op.drop_table('transcription_feedback')
    
    # Drop enum
    satisfaction_rating_enum = postgresql.ENUM(
        'very_dissatisfied',
        'dissatisfied',
        'neutral',
        'satisfied',
        'very_satisfied',
        name='satisfactionrating'
    )
    satisfaction_rating_enum.drop(op.get_bind(), checkfirst=True)
