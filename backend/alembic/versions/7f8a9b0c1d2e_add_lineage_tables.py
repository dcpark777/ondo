"""add_lineage_tables

Revision ID: 7f8a9b0c1d2e
Revises: 6a1b2c3d4e5f
Create Date: 2026-01-04 19:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '7f8a9b0c1d2e'
down_revision: Union[str, None] = '6a1b2c3d4e5f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create dataset_lineage table
    op.create_table(
        'dataset_lineage',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('upstream_dataset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('downstream_dataset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('transformation_type', sa.String(50), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['upstream_dataset_id'], ['datasets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['downstream_dataset_id'], ['datasets.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('upstream_dataset_id', 'downstream_dataset_id', name='uq_dataset_lineage'),
    )
    op.create_index('ix_dataset_lineage_upstream_dataset_id', 'dataset_lineage', ['upstream_dataset_id'])
    op.create_index('ix_dataset_lineage_downstream_dataset_id', 'dataset_lineage', ['downstream_dataset_id'])
    op.create_index('idx_lineage_upstream', 'dataset_lineage', ['upstream_dataset_id'])
    op.create_index('idx_lineage_downstream', 'dataset_lineage', ['downstream_dataset_id'])

    # Create column_lineage table
    op.create_table(
        'column_lineage',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('upstream_column_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('downstream_column_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('transformation_expression', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['upstream_column_id'], ['dataset_columns.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['downstream_column_id'], ['dataset_columns.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('upstream_column_id', 'downstream_column_id', name='uq_column_lineage'),
    )
    op.create_index('ix_column_lineage_upstream_column_id', 'column_lineage', ['upstream_column_id'])
    op.create_index('ix_column_lineage_downstream_column_id', 'column_lineage', ['downstream_column_id'])
    op.create_index('idx_column_lineage_upstream', 'column_lineage', ['upstream_column_id'])
    op.create_index('idx_column_lineage_downstream', 'column_lineage', ['downstream_column_id'])


def downgrade() -> None:
    # Drop column_lineage table and indexes
    op.drop_index('idx_column_lineage_downstream', table_name='column_lineage')
    op.drop_index('idx_column_lineage_upstream', table_name='column_lineage')
    op.drop_index('ix_column_lineage_downstream_column_id', table_name='column_lineage')
    op.drop_index('ix_column_lineage_upstream_column_id', table_name='column_lineage')
    op.drop_table('column_lineage')

    # Drop dataset_lineage table and indexes
    op.drop_index('idx_lineage_downstream', table_name='dataset_lineage')
    op.drop_index('idx_lineage_upstream', table_name='dataset_lineage')
    op.drop_index('ix_dataset_lineage_downstream_dataset_id', table_name='dataset_lineage')
    op.drop_index('ix_dataset_lineage_upstream_dataset_id', table_name='dataset_lineage')
    op.drop_table('dataset_lineage')

