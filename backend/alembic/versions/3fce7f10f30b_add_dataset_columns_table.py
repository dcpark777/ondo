"""add_dataset_columns_table

Revision ID: 3fce7f10f30b
Revises: 502e02ad3bda
Create Date: 2025-12-30 23:08:01.481837

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '3fce7f10f30b'
down_revision: Union[str, None] = '5dd8395d8b24'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create dataset_columns table
    op.create_table(
        'dataset_columns',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('dataset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('type', sa.String(100), nullable=True),
        sa.Column('nullable', sa.Integer(), nullable=True),
        sa.Column('last_seen_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('dataset_id', 'name', name='uq_dataset_column'),
    )
    op.create_index('ix_dataset_columns_dataset_id', 'dataset_columns', ['dataset_id'])
    op.create_index('idx_columns_dataset_name', 'dataset_columns', ['dataset_id', 'name'])


def downgrade() -> None:
    op.drop_index('idx_columns_dataset_name', 'dataset_columns')
    op.drop_index('ix_dataset_columns_dataset_id', 'dataset_columns')
    op.drop_table('dataset_columns')

