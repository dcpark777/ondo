"""
SQLAlchemy models for Ondo MVP.
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Column,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    BigInteger,
    String,
    Text,
    TIMESTAMP,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR, UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class ReadinessStatusEnum(PyEnum):
    """Readiness status enum matching scoring engine."""

    DRAFT = "draft"
    INTERNAL = "internal"
    PRODUCTION_READY = "production_ready"
    GOLD = "gold"


class DimensionKeyEnum(PyEnum):
    """Dimension keys for scoring."""

    OWNERSHIP = "ownership"
    DOCUMENTATION = "documentation"
    SCHEMA_HYGIENE = "schema_hygiene"
    DATA_QUALITY = "data_quality"
    STABILITY = "stability"
    OPERATIONAL = "operational"


class Dataset(Base):
    """Main dataset table."""

    __tablename__ = "datasets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String(255), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)  # Dataset description for AI assist
    owner_name = Column(String(255), nullable=True, index=True)
    owner_contact = Column(String(255), nullable=True)
    intended_use = Column(Text, nullable=True)
    limitations = Column(Text, nullable=True)
    location_type = Column(String(50), nullable=True, index=True)  # e.g., 's3', 'databricks', 'snowflake', 'bigquery'
    location_data = Column(JSONB, nullable=True)  # Type-specific location data as JSON
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    created_by = Column(String(255), nullable=True)  # User who created the dataset
    last_seen_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)
    last_scored_at = Column(TIMESTAMP(timezone=True), nullable=True)
    last_updated_at = Column(TIMESTAMP(timezone=True), nullable=True)  # When dataset was last updated/modified
    updated_by = Column(String(255), nullable=True)  # User who last updated the dataset
    data_size_bytes = Column(BigInteger, nullable=True)  # Dataset size in bytes
    file_count = Column(Integer, nullable=True)  # Number of files (if applicable)
    partition_keys = Column(JSONB, nullable=True)  # Array of partition key column names
    sla_hours = Column(Integer, nullable=True)  # SLA in hours (e.g., 24 for daily, 1 for hourly)
    producing_job = Column(String(255), nullable=True)  # Job/pipeline that produces this dataset
    readiness_score = Column(Integer, nullable=False, default=0, index=True)
    readiness_status = Column(
        String(50),  # Store as string, validate in application code
        nullable=False,
        default=ReadinessStatusEnum.DRAFT.value,
        index=True,
    )

    classification = Column(String(50), nullable=True, index=True)  # public, internal, confidential, restricted
    domain = Column(String(100), nullable=True, index=True)  # e.g., analytics, finance, engineering
    search_vector = Column(TSVECTOR, nullable=True)  # Full-text search vector (auto-updated by trigger)

    # Relationships
    dimension_scores = relationship(
        "DatasetDimensionScore", back_populates="dataset", cascade="all, delete-orphan"
    )
    tags = relationship(
        "DatasetTag", back_populates="dataset", cascade="all, delete-orphan"
    )
    reasons = relationship(
        "DatasetReason", back_populates="dataset", cascade="all, delete-orphan"
    )
    actions = relationship(
        "DatasetAction", back_populates="dataset", cascade="all, delete-orphan"
    )
    columns = relationship(
        "DatasetColumn", back_populates="dataset", cascade="all, delete-orphan"
    )
    score_history = relationship(
        "DatasetScoreHistory", back_populates="dataset", cascade="all, delete-orphan"
    )
    upstream_lineage = relationship(
        "DatasetLineage",
        foreign_keys="DatasetLineage.downstream_dataset_id",
        back_populates="downstream_dataset",
        cascade="all, delete-orphan"
    )
    downstream_lineage = relationship(
        "DatasetLineage",
        foreign_keys="DatasetLineage.upstream_dataset_id",
        back_populates="upstream_dataset",
        cascade="all, delete-orphan"
    )
    quality_rules = relationship(
        "QualityRule", back_populates="dataset", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_datasets_status_score", "readiness_status", "readiness_score"),
        Index("idx_datasets_owner", "owner_name"),
    )


class DatasetDimensionScore(Base):
    """Dimension scores for each dataset."""

    __tablename__ = "dataset_dimension_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(
        UUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dimension_key = Column(
        String(50),  # Store as string, validate in application code
        nullable=False,
        index=True,
    )
    points_awarded = Column(Integer, nullable=False)
    max_points = Column(Integer, nullable=False)
    measured = Column(
        Integer, nullable=False, default=1, server_default="1"
    )  # Boolean: 1=True, 0=False (using Integer for SQLite compatibility)

    # Relationships
    dataset = relationship("Dataset", back_populates="dimension_scores")

    __table_args__ = (
        UniqueConstraint("dataset_id", "dimension_key", name="uq_dataset_dimension"),
        Index("idx_dimension_scores_dataset_dimension", "dataset_id", "dimension_key"),
    )


class DatasetReason(Base):
    """Reasons for point losses in scoring."""

    __tablename__ = "dataset_reasons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(
        UUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dimension_key = Column(
        String(50),  # Store as string, validate in application code
        nullable=False,
        index=True,
    )
    reason_code = Column(String(100), nullable=False, index=True)
    message = Column(Text, nullable=False)
    points_lost = Column(Integer, nullable=False)

    # Relationships
    dataset = relationship("Dataset", back_populates="reasons")

    __table_args__ = (
        Index("idx_reasons_dataset_dimension", "dataset_id", "dimension_key"),
    )


class DatasetAction(Base):
    """Recommended actions to improve dataset score."""

    __tablename__ = "dataset_actions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(
        UUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action_key = Column(String(100), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    points_gain = Column(Integer, nullable=False)
    url = Column(String(500), nullable=True)

    # Relationships
    dataset = relationship("Dataset", back_populates="actions")

    __table_args__ = (
        Index("idx_actions_dataset_key", "dataset_id", "action_key"),
    )


class DatasetColumn(Base):
    """Column metadata for datasets."""

    __tablename__ = "dataset_columns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(
        UUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    type = Column(String(100), nullable=True)  # Column data type
    nullable = Column(
        Integer, nullable=True
    )  # Boolean: 1=True, 0=False, NULL=unknown (using Integer for SQLite compatibility)
    last_seen_at = Column(
        TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow
    )

    # Relationships
    dataset = relationship("Dataset", back_populates="columns")
    upstream_lineage = relationship(
        "ColumnLineage",
        foreign_keys="ColumnLineage.downstream_column_id",
        back_populates="downstream_column",
        cascade="all, delete-orphan"
    )
    downstream_lineage = relationship(
        "ColumnLineage",
        foreign_keys="ColumnLineage.upstream_column_id",
        back_populates="upstream_column",
        cascade="all, delete-orphan"
    )
    profiles = relationship(
        "ColumnProfile", back_populates="column", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("dataset_id", "name", name="uq_dataset_column"),
        Index("idx_columns_dataset_name", "dataset_id", "name"),
    )


class DatasetScoreHistory(Base):
    """Historical record of dataset scores."""

    __tablename__ = "dataset_score_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(
        UUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    readiness_score = Column(Integer, nullable=False, index=True)
    recorded_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    scoring_version = Column(String(50), nullable=False, default="v1")

    # Relationships
    dataset = relationship("Dataset", back_populates="score_history")

    __table_args__ = (
        Index("idx_score_history_dataset_recorded", "dataset_id", "recorded_at"),
    )


class DatasetLineage(Base):
    """Lineage relationships between datasets (upstream -> downstream)."""

    __tablename__ = "dataset_lineage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    upstream_dataset_id = Column(
        UUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    downstream_dataset_id = Column(
        UUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    transformation_type = Column(
        String(50), nullable=True
    )  # e.g., 'join', 'filter', 'aggregate', 'transform', 'union'
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    upstream_dataset = relationship(
        "Dataset",
        foreign_keys=[upstream_dataset_id],
        back_populates="downstream_lineage"
    )
    downstream_dataset = relationship(
        "Dataset",
        foreign_keys=[downstream_dataset_id],
        back_populates="upstream_lineage"
    )

    __table_args__ = (
        UniqueConstraint("upstream_dataset_id", "downstream_dataset_id", name="uq_dataset_lineage"),
        Index("idx_lineage_upstream", "upstream_dataset_id"),
        Index("idx_lineage_downstream", "downstream_dataset_id"),
    )


class ColumnLineage(Base):
    """Lineage relationships between columns (upstream -> downstream)."""

    __tablename__ = "column_lineage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    upstream_column_id = Column(
        UUID(as_uuid=True),
        ForeignKey("dataset_columns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    downstream_column_id = Column(
        UUID(as_uuid=True),
        ForeignKey("dataset_columns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    transformation_expression = Column(
        Text, nullable=True
    )  # Optional SQL or transformation expression
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    upstream_column = relationship(
        "DatasetColumn",
        foreign_keys=[upstream_column_id],
        back_populates="downstream_lineage"
    )
    downstream_column = relationship(
        "DatasetColumn",
        foreign_keys=[downstream_column_id],
        back_populates="upstream_lineage"
    )

    __table_args__ = (
        UniqueConstraint("upstream_column_id", "downstream_column_id", name="uq_column_lineage"),
        Index("idx_column_lineage_upstream", "upstream_column_id"),
        Index("idx_column_lineage_downstream", "downstream_column_id"),
    )


class DatasetTag(Base):
    """Tags for datasets."""

    __tablename__ = "dataset_tags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(
        UUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tag = Column(String(100), nullable=False, index=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    dataset = relationship("Dataset", back_populates="tags")

    __table_args__ = (
        UniqueConstraint("dataset_id", "tag", name="uq_dataset_tag"),
    )


class QualityRule(Base):
    """Quality rules for datasets."""

    __tablename__ = "quality_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(
        UUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    rule_type = Column(String(50), nullable=False)
    column_name = Column(String(255), nullable=True)
    parameters = Column(JSONB, nullable=True)
    severity = Column(String(20), nullable=False, default="warning", server_default="warning")
    enabled = Column(Integer, nullable=False, default=1, server_default="1")
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)
    created_by = Column(String(255), nullable=True)

    # Relationships
    dataset = relationship("Dataset", back_populates="quality_rules")
    executions = relationship(
        "QualityRuleExecution", back_populates="rule", cascade="all, delete-orphan"
    )


class QualityRuleExecution(Base):
    """Execution results for quality rules."""

    __tablename__ = "quality_rule_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_id = Column(
        UUID(as_uuid=True),
        ForeignKey("quality_rules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dataset_id = Column(
        UUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    passed = Column(Integer, nullable=False)  # 1=True, 0=False
    records_checked = Column(Integer, nullable=True)
    records_failed = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    executed_at = Column(
        TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow, index=True
    )

    # Relationships
    rule = relationship("QualityRule", back_populates="executions")
    dataset = relationship("Dataset")


class GlossaryTerm(Base):
    """Business glossary term."""

    __tablename__ = "glossary_terms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False, index=True)
    definition = Column(Text, nullable=False)
    domain = Column(String(100), nullable=True, index=True)
    owner = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False, default="draft", server_default="draft")
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    column_links = relationship(
        "GlossaryColumnLink", back_populates="term", cascade="all, delete-orphan"
    )


class GlossaryColumnLink(Base):
    """Link between glossary term and dataset column."""

    __tablename__ = "glossary_column_links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    term_id = Column(
        UUID(as_uuid=True),
        ForeignKey("glossary_terms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    column_id = Column(
        UUID(as_uuid=True),
        ForeignKey("dataset_columns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    term = relationship("GlossaryTerm", back_populates="column_links")
    column = relationship("DatasetColumn")

    __table_args__ = (
        UniqueConstraint("term_id", "column_id", name="uq_glossary_column_link"),
    )


class DatasetWatch(Base):
    """Dataset watch subscriptions."""

    __tablename__ = "dataset_watches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(
        UUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(String(255), nullable=False, index=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    dataset = relationship("Dataset")

    __table_args__ = (
        UniqueConstraint("dataset_id", "user_id", name="uq_dataset_watch"),
    )


class Notification(Base):
    """User notifications."""

    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(
        UUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(String(255), nullable=False, index=True)
    notification_type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    read = Column(Integer, nullable=False, default=0, server_default="0")
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow, index=True)

    # Relationships
    dataset = relationship("Dataset")


class ColumnProfile(Base):
    """Profiling statistics for a dataset column."""

    __tablename__ = "column_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    column_id = Column(
        UUID(as_uuid=True),
        ForeignKey("dataset_columns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dataset_id = Column(
        UUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    row_count = Column(Integer, nullable=True)
    null_count = Column(Integer, nullable=True)
    null_percentage = Column(Float, nullable=True)
    distinct_count = Column(Integer, nullable=True)
    distinct_percentage = Column(Float, nullable=True)
    min_value = Column(String(255), nullable=True)
    max_value = Column(String(255), nullable=True)
    mean_value = Column(Float, nullable=True)
    median_value = Column(Float, nullable=True)
    stddev_value = Column(Float, nullable=True)
    min_length = Column(Integer, nullable=True)
    max_length = Column(Integer, nullable=True)
    avg_length = Column(Float, nullable=True)
    top_values = Column(JSONB, nullable=True)  # [{"value": "X", "count": 100}]
    sample_values = Column(JSONB, nullable=True)
    profiled_at = Column(
        TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow, index=True
    )

    # Relationships
    column = relationship("DatasetColumn", back_populates="profiles")
    dataset = relationship("Dataset")

    __table_args__ = (
        Index("idx_column_profiles_dataset_profiled", "dataset_id", "profiled_at"),
        Index("idx_column_profiles_column_profiled", "column_id", "profiled_at"),
    )

