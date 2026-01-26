"""fix_conversation_status_enum_values

Revision ID: 2d00688db6d4
Revises: 002
Create Date: 2026-01-26 19:59:30.427765

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2d00688db6d4'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # The simplest approach is to recreate the enum with lowercase values
    # First, alter the column to use text temporarily
    op.execute("ALTER TABLE conversations ALTER COLUMN status TYPE text")
    
    # Drop the old enum type
    op.execute("DROP TYPE conversationstatus")
    
    # Create the new enum type with lowercase values
    op.execute("CREATE TYPE conversationstatus AS ENUM ('active', 'completed', 'abandoned')")
    
    # Update the data to lowercase
    op.execute("UPDATE conversations SET status = LOWER(status)")
    
    # Alter the column back to use the enum type
    op.execute("ALTER TABLE conversations ALTER COLUMN status TYPE conversationstatus USING status::conversationstatus")


def downgrade() -> None:
    # Revert to uppercase enum values
    # First, alter the column to use text temporarily
    op.execute("ALTER TABLE conversations ALTER COLUMN status TYPE text")
    
    # Drop the lowercase enum type
    op.execute("DROP TYPE conversationstatus")
    
    # Create the enum type with uppercase values
    op.execute("CREATE TYPE conversationstatus AS ENUM ('ACTIVE', 'COMPLETED', 'ABANDONED')")
    
    # Update the data to uppercase
    op.execute("UPDATE conversations SET status = UPPER(status)")
    
    # Alter the column back to use the enum type
    op.execute("ALTER TABLE conversations ALTER COLUMN status TYPE conversationstatus USING status::conversationstatus")
