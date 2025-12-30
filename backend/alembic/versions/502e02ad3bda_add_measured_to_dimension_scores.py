"""add_measured_to_dimension_scores

Revision ID: 502e02ad3bda
Revises: 001_initial
Create Date: 2025-12-30 22:56:08.580567

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '502e02ad3bda'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add measured column to dataset_dimension_scores table
    # Use Integer (1=True, 0=False) for SQLite/PostgreSQL compatibility
    op.add_column(
        'dataset_dimension_scores',
        sa.Column('measured', sa.Integer(), nullable=False, server_default='1')
    )


def downgrade() -> None:
    # Remove measured column
    op.drop_column('dataset_dimension_scores', 'measured')

