"""Add audit logs table

Revision ID: 003
Revises: 002
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    """Create audit_logs table"""
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('event_category', sa.String(length=100), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('resource_type', sa.String(length=100), nullable=False),
        sa.Column('resource_id_hash', sa.String(length=64), nullable=True),
        sa.Column('actor_id_hash', sa.String(length=64), nullable=True),
        sa.Column('result', sa.String(length=50), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('ip_address_anonymized', sa.String(length=50), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for efficient querying
    op.create_index('idx_audit_timestamp_event_type', 'audit_logs', ['timestamp', 'event_type'])
    op.create_index('idx_audit_actor_timestamp', 'audit_logs', ['actor_id_hash', 'timestamp'])
    op.create_index('idx_audit_resource', 'audit_logs', ['resource_type', 'resource_id_hash'])
    op.create_index(op.f('ix_audit_logs_timestamp'), 'audit_logs', ['timestamp'])
    op.create_index(op.f('ix_audit_logs_event_type'), 'audit_logs', ['event_type'])
    op.create_index(op.f('ix_audit_logs_event_category'), 'audit_logs', ['event_category'])
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'])
    op.create_index(op.f('ix_audit_logs_resource_id_hash'), 'audit_logs', ['resource_id_hash'])
    op.create_index(op.f('ix_audit_logs_actor_id_hash'), 'audit_logs', ['actor_id_hash'])


def downgrade():
    """Drop audit_logs table"""
    op.drop_index(op.f('ix_audit_logs_actor_id_hash'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_resource_id_hash'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_action'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_event_category'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_event_type'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_timestamp'), table_name='audit_logs')
    op.drop_index('idx_audit_resource', table_name='audit_logs')
    op.drop_index('idx_audit_actor_timestamp', table_name='audit_logs')
    op.drop_index('idx_audit_timestamp_event_type', table_name='audit_logs')
    op.drop_table('audit_logs')
