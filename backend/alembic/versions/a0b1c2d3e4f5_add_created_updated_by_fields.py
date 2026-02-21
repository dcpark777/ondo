"""add_created_updated_by_fields

Revision ID: a0b1c2d3e4f5
Revises: 9b0c1d2e3f4a
Create Date: 2026-01-05 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a0b1c2d3e4f5'
down_revision: Union[str, None] = '9b0c1d2e3f4a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if created_at column exists
    conn = op.get_bind()
    result = conn.execute(sa.text("""
        SELECT COUNT(*) 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'datasets' 
        AND column_name = 'created_at'
    """))
    column_exists = result.scalar() > 0
    
    if not column_exists:
        op.add_column(
            'datasets',
            sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now())
        )
        op.create_index('idx_datasets_created_at', 'datasets', ['created_at'])
    
    # Add created_by column
    op.add_column(
        'datasets',
        sa.Column('created_by', sa.String(255), nullable=True)
    )
    
    # Add updated_by column
    op.add_column(
        'datasets',
        sa.Column('updated_by', sa.String(255), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('datasets', 'updated_by')
    op.drop_column('datasets', 'created_by')
    
    # Only drop created_at if it was added by this migration
    conn = op.get_bind()
    result = conn.execute(sa.text("""
        SELECT COUNT(*) 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'datasets' 
        AND column_name = 'created_at'
    """))
    column_exists = result.scalar() > 0
    
    if column_exists:
        op.drop_index('idx_datasets_created_at', table_name='datasets')
        op.drop_column('datasets', 'created_at')

