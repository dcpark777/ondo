"""add_column_profiles

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
Create Date: 2026-02-21 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'd3e4f5a6b7c8'
down_revision: Union[str, None] = 'c2d3e4f5a6b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'column_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('column_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('dataset_columns.id', ondelete='CASCADE'),
                  nullable=False, index=True),
        sa.Column('dataset_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('datasets.id', ondelete='CASCADE'),
                  nullable=False, index=True),
        sa.Column('row_count', sa.Integer, nullable=True),
        sa.Column('null_count', sa.Integer, nullable=True),
        sa.Column('null_percentage', sa.Float, nullable=True),
        sa.Column('distinct_count', sa.Integer, nullable=True),
        sa.Column('distinct_percentage', sa.Float, nullable=True),
        sa.Column('min_value', sa.String(255), nullable=True),
        sa.Column('max_value', sa.String(255), nullable=True),
        sa.Column('mean_value', sa.Float, nullable=True),
        sa.Column('median_value', sa.Float, nullable=True),
        sa.Column('stddev_value', sa.Float, nullable=True),
        sa.Column('min_length', sa.Integer, nullable=True),
        sa.Column('max_length', sa.Integer, nullable=True),
        sa.Column('avg_length', sa.Float, nullable=True),
        sa.Column('top_values', postgresql.JSONB, nullable=True),
        sa.Column('sample_values', postgresql.JSONB, nullable=True),
        sa.Column('profiled_at', sa.TIMESTAMP(timezone=True),
                  nullable=False, server_default=sa.func.now(), index=True),
    )

    # Composite index for efficient queries by dataset + profiled_at
    op.create_index(
        'idx_column_profiles_dataset_profiled',
        'column_profiles',
        ['dataset_id', 'profiled_at'],
    )

    # Composite index for history lookups by column + profiled_at
    op.create_index(
        'idx_column_profiles_column_profiled',
        'column_profiles',
        ['column_id', 'profiled_at'],
    )


def downgrade() -> None:
    op.drop_index('idx_column_profiles_column_profiled', table_name='column_profiles')
    op.drop_index('idx_column_profiles_dataset_profiled', table_name='column_profiles')
    op.drop_table('column_profiles')
