"""add_dataset_metadata_fields

Revision ID: 8a9b0c1d2e3f
Revises: 7f8a9b0c1d2e
Create Date: 2026-01-04 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '8a9b0c1d2e3f'
down_revision: Union[str, None] = '7f8a9b0c1d2e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new metadata fields to datasets table
    op.add_column(
        'datasets',
        sa.Column('last_updated_at', sa.TIMESTAMP(timezone=True), nullable=True)
    )
    op.add_column(
        'datasets',
        sa.Column('data_size_bytes', sa.BigInteger(), nullable=True)
    )
    op.add_column(
        'datasets',
        sa.Column('file_count', sa.Integer(), nullable=True)
    )
    op.add_column(
        'datasets',
        sa.Column('partition_keys', postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    )
    op.add_column(
        'datasets',
        sa.Column('sla_hours', sa.Integer(), nullable=True)
    )
    op.add_column(
        'datasets',
        sa.Column('producing_job', sa.String(255), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('datasets', 'producing_job')
    op.drop_column('datasets', 'sla_hours')
    op.drop_column('datasets', 'partition_keys')
    op.drop_column('datasets', 'file_count')
    op.drop_column('datasets', 'data_size_bytes')
    op.drop_column('datasets', 'last_updated_at')

