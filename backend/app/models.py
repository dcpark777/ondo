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
from sqlalchemy.dialects.postgresql import UUID
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
    last_seen_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)
    last_scored_at = Column(TIMESTAMP(timezone=True), nullable=True)
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

