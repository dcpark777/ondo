"""Initial schema

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enums (only if they don't exist)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE readiness_status_enum AS ENUM ('draft', 'internal', 'production_ready', 'gold');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE dimension_key_enum AS ENUM ('ownership', 'documentation', 'schema_hygiene', 'data_quality', 'stability', 'operational');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create datasets table
    op.create_table(
        'datasets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('full_name', sa.String(255), nullable=False, unique=True),
        sa.Column('display_name', sa.String(255), nullable=False),
        sa.Column('owner_name', sa.String(255), nullable=True),
        sa.Column('owner_contact', sa.String(255), nullable=True),
        sa.Column('intended_use', sa.Text(), nullable=True),
        sa.Column('limitations', sa.Text(), nullable=True),
        sa.Column('last_seen_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_scored_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('readiness_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('readiness_status', postgresql.ENUM('draft', 'internal', 'production_ready', 'gold', name='readiness_status_enum', create_type=False), nullable=False, server_default='draft'),
    )
    op.create_index('ix_datasets_full_name', 'datasets', ['full_name'])
    op.create_index('ix_datasets_readiness_score', 'datasets', ['readiness_score'])
    op.create_index('ix_datasets_readiness_status', 'datasets', ['readiness_status'])
    op.create_index('idx_datasets_status_score', 'datasets', ['readiness_status', 'readiness_score'])
    op.create_index('idx_datasets_owner', 'datasets', ['owner_name'])

    # Create dataset_dimension_scores table
    op.create_table(
        'dataset_dimension_scores',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('dataset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('dimension_key', postgresql.ENUM('ownership', 'documentation', 'schema_hygiene', 'data_quality', 'stability', 'operational', name='dimension_key_enum', create_type=False), nullable=False),
        sa.Column('points_awarded', sa.Integer(), nullable=False),
        sa.Column('max_points', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_dataset_dimension_scores_dataset_id', 'dataset_dimension_scores', ['dataset_id'])
    op.create_index('ix_dataset_dimension_scores_dimension_key', 'dataset_dimension_scores', ['dimension_key'])
    op.create_index('idx_dimension_scores_dataset_dimension', 'dataset_dimension_scores', ['dataset_id', 'dimension_key'])
    op.create_unique_constraint('uq_dataset_dimension', 'dataset_dimension_scores', ['dataset_id', 'dimension_key'])

    # Create dataset_reasons table
    op.create_table(
        'dataset_reasons',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('dataset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('dimension_key', postgresql.ENUM('ownership', 'documentation', 'schema_hygiene', 'data_quality', 'stability', 'operational', name='dimension_key_enum', create_type=False), nullable=False),
        sa.Column('reason_code', sa.String(100), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('points_lost', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_dataset_reasons_dataset_id', 'dataset_reasons', ['dataset_id'])
    op.create_index('ix_dataset_reasons_dimension_key', 'dataset_reasons', ['dimension_key'])
    op.create_index('ix_dataset_reasons_reason_code', 'dataset_reasons', ['reason_code'])
    op.create_index('idx_reasons_dataset_dimension', 'dataset_reasons', ['dataset_id', 'dimension_key'])

    # Create dataset_actions table
    op.create_table(
        'dataset_actions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('dataset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action_key', sa.String(100), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('points_gain', sa.Integer(), nullable=False),
        sa.Column('url', sa.String(500), nullable=True),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_dataset_actions_dataset_id', 'dataset_actions', ['dataset_id'])
    op.create_index('ix_dataset_actions_action_key', 'dataset_actions', ['action_key'])
    op.create_index('idx_actions_dataset_key', 'dataset_actions', ['dataset_id', 'action_key'])

    # Create dataset_score_history table
    op.create_table(
        'dataset_score_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('dataset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('readiness_score', sa.Integer(), nullable=False),
        sa.Column('recorded_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('scoring_version', sa.String(50), nullable=False, server_default='v1'),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_dataset_score_history_dataset_id', 'dataset_score_history', ['dataset_id'])
    op.create_index('ix_dataset_score_history_readiness_score', 'dataset_score_history', ['readiness_score'])
    op.create_index('ix_dataset_score_history_recorded_at', 'dataset_score_history', ['recorded_at'])
    op.create_index('idx_score_history_dataset_recorded', 'dataset_score_history', ['dataset_id', 'recorded_at'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('dataset_score_history')
    op.drop_table('dataset_actions')
    op.drop_table('dataset_reasons')
    op.drop_table('dataset_dimension_scores')
    op.drop_table('datasets')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS dimension_key_enum')
    op.execute('DROP TYPE IF EXISTS readiness_status_enum')

