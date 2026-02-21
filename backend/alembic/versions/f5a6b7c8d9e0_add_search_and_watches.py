"""Add search vector, watches, and notifications.

Revision ID: f5a6b7c8d9e0
Revises: e4f5a6b7c8d9
Create Date: 2026-02-21
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "f5a6b7c8d9e0"
down_revision = "e4f5a6b7c8d9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Phase 7: Full-text search
    op.add_column(
        "datasets",
        sa.Column("search_vector", postgresql.TSVECTOR(), nullable=True),
    )
    op.create_index(
        "idx_datasets_search_vector",
        "datasets",
        ["search_vector"],
        postgresql_using="gin",
    )

    # Create trigger function
    op.execute("""
        CREATE OR REPLACE FUNCTION datasets_search_vector_update() RETURNS trigger AS $$
        BEGIN
            NEW.search_vector :=
                setweight(to_tsvector('english', coalesce(NEW.display_name, '')), 'A') ||
                setweight(to_tsvector('english', coalesce(NEW.full_name, '')), 'A') ||
                setweight(to_tsvector('english', coalesce(NEW.description, '')), 'B') ||
                setweight(to_tsvector('english', coalesce(NEW.owner_name, '')), 'C') ||
                setweight(to_tsvector('english', coalesce(NEW.domain, '')), 'C');
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Create trigger
    op.execute("""
        CREATE TRIGGER datasets_search_vector_trigger
        BEFORE INSERT OR UPDATE ON datasets
        FOR EACH ROW EXECUTE FUNCTION datasets_search_vector_update();
    """)

    # Backfill existing rows
    op.execute("""
        UPDATE datasets SET search_vector =
            setweight(to_tsvector('english', coalesce(display_name, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(full_name, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(description, '')), 'B') ||
            setweight(to_tsvector('english', coalesce(owner_name, '')), 'C') ||
            setweight(to_tsvector('english', coalesce(domain, '')), 'C');
    """)

    # Phase 8: Watches
    op.create_table(
        "dataset_watches",
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
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("dataset_id", "user_id", name="uq_dataset_watch"),
    )

    # Phase 8: Notifications
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "dataset_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("datasets.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("user_id", sa.String(255), nullable=False, index=True),
        sa.Column("notification_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("read", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            index=True,
        ),
    )


def downgrade() -> None:
    op.drop_table("notifications")
    op.drop_table("dataset_watches")
    op.execute("DROP TRIGGER IF EXISTS datasets_search_vector_trigger ON datasets")
    op.execute("DROP FUNCTION IF EXISTS datasets_search_vector_update()")
    op.drop_index("idx_datasets_search_vector", table_name="datasets")
    op.drop_column("datasets", "search_vector")
