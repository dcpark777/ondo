"""add_quality_rules

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-02-21 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c2d3e4f5a6b7'
down_revision: Union[str, None] = 'b1c2d3e4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create quality_rules table
    op.create_table(
        'quality_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('dataset_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('datasets.id', ondelete='CASCADE'),
                  nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('rule_type', sa.String(50), nullable=False),
        sa.Column('column_name', sa.String(255), nullable=True),
        sa.Column('parameters', postgresql.JSONB, nullable=True),
        sa.Column('severity', sa.String(20), nullable=False,
                  server_default='warning'),
        sa.Column('enabled', sa.Integer, nullable=False, server_default='1'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True),
                  nullable=False, server_default=sa.func.now()),
        sa.Column('created_by', sa.String(255), nullable=True),
    )

    # Create quality_rule_executions table
    op.create_table(
        'quality_rule_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('rule_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('quality_rules.id', ondelete='CASCADE'),
                  nullable=False, index=True),
        sa.Column('dataset_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('datasets.id', ondelete='CASCADE'),
                  nullable=False, index=True),
        sa.Column('passed', sa.Integer, nullable=False),
        sa.Column('records_checked', sa.Integer, nullable=True),
        sa.Column('records_failed', sa.Integer, nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('executed_at', sa.TIMESTAMP(timezone=True),
                  nullable=False, server_default=sa.func.now(), index=True),
    )


def downgrade() -> None:
    op.drop_table('quality_rule_executions')
    op.drop_table('quality_rules')
