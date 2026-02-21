"""add_tags_and_classification

Revision ID: b1c2d3e4f5a6
Revises: a0b1c2d3e4f5
Create Date: 2026-02-21 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, None] = 'a0b1c2d3e4f5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add classification and domain to datasets table
    op.add_column(
        'datasets',
        sa.Column('classification', sa.String(50), nullable=True)
    )
    op.add_column(
        'datasets',
        sa.Column('domain', sa.String(100), nullable=True)
    )
    op.create_index('idx_datasets_classification', 'datasets', ['classification'])
    op.create_index('idx_datasets_domain', 'datasets', ['domain'])

    # Create dataset_tags table
    op.create_table(
        'dataset_tags',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('dataset_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('datasets.id', ondelete='CASCADE'),
                  nullable=False, index=True),
        sa.Column('tag', sa.String(100), nullable=False, index=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True),
                  nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('dataset_id', 'tag', name='uq_dataset_tag'),
    )


def downgrade() -> None:
    op.drop_table('dataset_tags')
    op.drop_index('idx_datasets_domain', table_name='datasets')
    op.drop_index('idx_datasets_classification', table_name='datasets')
    op.drop_column('datasets', 'domain')
    op.drop_column('datasets', 'classification')
