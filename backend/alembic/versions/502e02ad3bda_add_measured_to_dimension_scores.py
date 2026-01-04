"""add_measured_to_dimension_scores

Revision ID: 502e02ad3bda
Revises: 001_initial
Create Date: 2025-12-30 22:56:08.580567

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.exc import ProgrammingError


# revision identifiers, used by Alembic.
revision: str = '502e02ad3bda'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add measured column to dataset_dimension_scores table
    # Use Integer (1=True, 0=False) for SQLite/PostgreSQL compatibility
    # Note: This column was already added in the initial migration (001_initial_schema.py)
    # This migration is kept for historical compatibility but is now a no-op
    # Check if column exists using raw SQL, then add only if it doesn't exist
    conn = op.get_bind()
    
    # Check if column exists
    result = conn.execute(sa.text("""
        SELECT COUNT(*) 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'dataset_dimension_scores' 
        AND column_name = 'measured'
    """))
    
    column_exists = result.scalar() > 0
    
    if not column_exists:
        # Column doesn't exist, add it
        op.add_column(
            'dataset_dimension_scores',
            sa.Column('measured', sa.Integer(), nullable=False, server_default='1')
        )
    # If column exists, do nothing (no-op)


def downgrade() -> None:
    # Remove measured column
    op.drop_column('dataset_dimension_scores', 'measured')

