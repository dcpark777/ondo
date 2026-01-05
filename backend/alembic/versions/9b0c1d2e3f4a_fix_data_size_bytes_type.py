"""fix_data_size_bytes_type

Revision ID: 9b0c1d2e3f4a
Revises: 8a9b0c1d2e3f
Create Date: 2026-01-05 19:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9b0c1d2e3f4a'
down_revision: Union[str, None] = '8a9b0c1d2e3f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Alter data_size_bytes from integer to bigint
    op.alter_column('datasets', 'data_size_bytes',
                    type_=sa.BigInteger(),
                    existing_type=sa.Integer(),
                    existing_nullable=True)


def downgrade() -> None:
    # Revert back to integer (may fail if values are too large)
    op.alter_column('datasets', 'data_size_bytes',
                    type_=sa.Integer(),
                    existing_type=sa.BigInteger(),
                    existing_nullable=True)

