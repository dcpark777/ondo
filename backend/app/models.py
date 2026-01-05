"""
SQLAlchemy models for Ondo MVP.
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Column,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    TIMESTAMP,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
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
    last_seen_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)
    last_scored_at = Column(TIMESTAMP(timezone=True), nullable=True)
    last_updated_at = Column(TIMESTAMP(timezone=True), nullable=True)  # When dataset was last updated/modified
    data_size_bytes = Column(Integer, nullable=True)  # Dataset size in bytes
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

    # Relationships
    dimension_scores = relationship(
        "DatasetDimensionScore", back_populates="dataset", cascade="all, delete-orphan"
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

