"""Add user preferences and voiceprint tables

Revision ID: 002
Revises: 001
Create Date: 2024-01-26 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create user_preferences table
    op.create_table(
        'user_preferences',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('speech_rate', sa.Float(), nullable=False, server_default='0.85'),
        sa.Column('volume_boost', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('offline_mode', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('favorite_contacts', postgresql.ARRAY(postgresql.UUID()), nullable=False, server_default='{}'),
        sa.Column('additional_settings', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )

    # Create voiceprints table
    op.create_table(
        'voiceprints',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('embedding_data', sa.LargeBinary(), nullable=False),
        sa.Column('encryption_algorithm', sa.String(length=50), nullable=False, server_default='AES-256'),
        sa.Column('sample_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )


def downgrade() -> None:
    op.drop_table('voiceprints')
    op.drop_table('user_preferences')
