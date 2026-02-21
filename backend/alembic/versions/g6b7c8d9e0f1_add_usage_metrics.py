"""Add usage metrics (dataset_views table).

Revision ID: g6b7c8d9e0f1
Revises: f5a6b7c8d9e0
Create Date: 2026-02-21
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "g6b7c8d9e0f1"
down_revision = "f5a6b7c8d9e0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dataset_views",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "dataset_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("datasets.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("user_id", sa.String(255), nullable=False, index=True),
        sa.Column(
            "viewed_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            index=True,
        ),
    )
    op.create_index(
        "idx_dataset_views_dataset_viewed",
        "dataset_views",
        ["dataset_id", "viewed_at"],
    )


def downgrade() -> None:
    op.drop_index("idx_dataset_views_dataset_viewed", table_name="dataset_views")
    op.drop_table("dataset_views")
