"""add_location_to_datasets

Revision ID: 6a1b2c3d4e5f
Revises: 5dd8395d8b24
Create Date: 2025-12-30 23:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '6a1b2c3d4e5f'
down_revision: Union[str, None] = '3fce7f10f30b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add location_type column to datasets table
    op.add_column(
        'datasets',
        sa.Column('location_type', sa.String(50), nullable=True)
    )
    
    # Add location_data JSONB column to datasets table
    op.add_column(
        'datasets',
        sa.Column('location_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    )
    
    # Create index on location_type for filtering
    op.create_index('idx_datasets_location_type', 'datasets', ['location_type'])


def downgrade() -> None:
    # Drop index
    op.drop_index('idx_datasets_location_type', table_name='datasets')
    
    # Remove location columns
    op.drop_column('datasets', 'location_data')
    op.drop_column('datasets', 'location_type')

