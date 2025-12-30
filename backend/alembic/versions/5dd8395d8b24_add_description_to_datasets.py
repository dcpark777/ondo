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
    op.add_column(
        'datasets',
        sa.Column('description', sa.Text(), nullable=True)
    )


def downgrade() -> None:
    # Remove description column
    op.drop_column('datasets', 'description')

