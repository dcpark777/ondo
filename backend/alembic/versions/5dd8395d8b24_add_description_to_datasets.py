"""add_description_to_datasets

Revision ID: 5dd8395d8b24
Revises: 502e02ad3bda
Create Date: 2025-12-30 23:02:12.626292

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5dd8395d8b24'
down_revision: Union[str, None] = '502e02ad3bda'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add description column to datasets table
    # Note: This column may already exist in the initial migration
    # Check if column exists before adding
    conn = op.get_bind()
    
    # Check if column exists
    result = conn.execute(sa.text("""
        SELECT COUNT(*) 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'datasets' 
        AND column_name = 'description'
    """))
    
    column_exists = result.scalar() > 0
    
    if not column_exists:
        # Column doesn't exist, add it
        op.add_column(
            'datasets',
            sa.Column('description', sa.Text(), nullable=True)
        )
    # If column exists, do nothing (no-op)


def downgrade() -> None:
    # Remove description column
    op.drop_column('datasets', 'description')

