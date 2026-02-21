"""
Pydantic schemas for API request/response validation.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# Base schemas
class DimensionScoreResponse(BaseModel):
    """Dimension score response.
    
    Contract v1: Stable response shape for UI compatibility.
    """

    dimension_key: str
    points_awarded: int
    max_points: int
    measured: bool  # Whether this dimension was measured (vs. not applicable)
    percentage: float  # Calculated: (points_awarded / max_points) * 100

    class Config:
        from_attributes = True


class ReasonResponse(BaseModel):
    """Reason for point loss.
    
    Contract v1: Stable response shape with versioned reason_code constants.
    """

    id: UUID
    dimension_key: str
    reason_code: str  # Stable constant from ReasonCode class
    message: str
    points_lost: int

    class Config:
        from_attributes = True


class ActionResponse(BaseModel):
    """Recommended action to improve score.
    
    Contract v1: Stable response shape with versioned action_key constants.
    """

    id: UUID
    action_key: str  # Stable constant from ActionKey class
    title: str
    description: str
    points_gain: int
    url: Optional[str] = None  # Optional URL for action documentation

    class Config:
        from_attributes = True


class ScoreHistoryResponse(BaseModel):
    """Historical score entry."""

    id: UUID
    readiness_score: int
    recorded_at: datetime
    scoring_version: str

    class Config:
        from_attributes = True


class ColumnResponse(BaseModel):
    """Column metadata response."""

    id: UUID
    name: str
    description: Optional[str] = None
    type: Optional[str] = None
    nullable: Optional[bool] = None

    class Config:
        from_attributes = True


# Dataset list response
class DatasetListItem(BaseModel):
    """Dataset item in list response."""

    id: UUID
    full_name: str
    display_name: str
    description: Optional[str] = None
    owner_name: Optional[str] = None
    readiness_score: int
    readiness_status: str
    last_scored_at: Optional[datetime] = None
    location_type: Optional[str] = None
    location_data: Optional[Dict[str, Any]] = None
    classification: Optional[str] = None
    domain: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

    class Config:
        from_attributes = True


class DatasetListResponse(BaseModel):
    """Response for dataset list endpoint."""

    datasets: List[DatasetListItem]
    total: int


# Dataset detail response
class DatasetDetailResponse(BaseModel):
    """Complete dataset detail response."""

    id: UUID
    full_name: str
    display_name: str
    description: Optional[str] = None  # Dataset description
    owner_name: Optional[str] = None
    owner_contact: Optional[str] = None
    intended_use: Optional[str] = None
    limitations: Optional[str] = None
    location_type: Optional[str] = None  # e.g., 's3', 'databricks', 'snowflake', 'bigquery'
    location_data: Optional[Dict[str, Any]] = None  # Type-specific location data
    created_at: datetime
    created_by: Optional[str] = None
    last_seen_at: datetime
    last_scored_at: Optional[datetime] = None
    last_updated_at: Optional[datetime] = None  # When dataset was last updated/modified
    updated_by: Optional[str] = None
    data_size_bytes: Optional[int] = None  # Dataset size in bytes
    file_count: Optional[int] = None  # Number of files (if applicable)
    partition_keys: Optional[List[str]] = None  # Array of partition key column names
    sla_hours: Optional[int] = None  # SLA in hours (e.g., 24 for daily, 1 for hourly)
    producing_job: Optional[str] = None  # Job/pipeline that produces this dataset
    readiness_score: int
    readiness_status: str
    classification: Optional[str] = None
    domain: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    dimension_scores: List[DimensionScoreResponse]
    reasons: List[ReasonResponse]
    actions: List[ActionResponse]
    columns: List[ColumnResponse]  # Schema/columns
    score_history: List[ScoreHistoryResponse]

    class Config:
        from_attributes = True


# Request schemas
class UpdateOwnerRequest(BaseModel):
    """Request to update dataset owner."""

    owner_name: Optional[str] = Field(None, max_length=255)
    owner_contact: Optional[str] = Field(None, max_length=255)


class UpdateMetadataRequest(BaseModel):
    """Request to update dataset metadata."""

    display_name: Optional[str] = Field(None, max_length=255)
    intended_use: Optional[str] = None
    limitations: Optional[str] = None


class UpdateTagsRequest(BaseModel):
    """Request to replace all tags on a dataset."""

    tags: List[str] = Field(default_factory=list)


class UpdateClassificationRequest(BaseModel):
    """Request to update classification and domain."""

    classification: Optional[str] = Field(None, max_length=50)
    domain: Optional[str] = Field(None, max_length=100)


# Quality rule schemas
class QualityRuleCreate(BaseModel):
    """Request to create a quality rule."""

    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    rule_type: str = Field(..., max_length=50)
    column_name: Optional[str] = Field(None, max_length=255)
    parameters: Optional[Dict[str, Any]] = None
    severity: str = Field(default="warning", max_length=20)
    enabled: bool = True
    created_by: Optional[str] = Field(None, max_length=255)


class QualityRuleUpdate(BaseModel):
    """Request to update a quality rule."""

    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    rule_type: Optional[str] = Field(None, max_length=50)
    column_name: Optional[str] = Field(None, max_length=255)
    parameters: Optional[Dict[str, Any]] = None
    severity: Optional[str] = Field(None, max_length=20)
    enabled: Optional[bool] = None


class QualityRuleExecutionCreate(BaseModel):
    """Request to record a quality rule execution result."""

    passed: bool
    records_checked: Optional[int] = None
    records_failed: Optional[int] = None
    error_message: Optional[str] = None


class QualityRuleExecutionResponse(BaseModel):
    """Quality rule execution result response."""

    id: UUID
    rule_id: UUID
    dataset_id: UUID
    passed: bool
    records_checked: Optional[int] = None
    records_failed: Optional[int] = None
    error_message: Optional[str] = None
    executed_at: datetime

    class Config:
        from_attributes = True


class QualityRuleResponse(BaseModel):
    """Quality rule response with optional latest execution."""

    id: UUID
    dataset_id: UUID
    name: str
    description: Optional[str] = None
    rule_type: str
    column_name: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    severity: str
    enabled: bool
    created_at: datetime
    created_by: Optional[str] = None
    latest_execution: Optional[QualityRuleExecutionResponse] = None

    class Config:
        from_attributes = True


class BatchExecutionItem(BaseModel):
    """Single execution item in a batch request."""

    rule_id: UUID
    passed: bool
    records_checked: Optional[int] = None
    records_failed: Optional[int] = None
    error_message: Optional[str] = None


class BatchExecutionRequest(BaseModel):
    """Request to record batch quality rule execution results."""

    executions: List[BatchExecutionItem]


# Profiling schemas
class ColumnProfileSubmit(BaseModel):
    """Single column profile submission."""

    column_name: str
    row_count: Optional[int] = None
    null_count: Optional[int] = None
    null_percentage: Optional[float] = None
    distinct_count: Optional[int] = None
    distinct_percentage: Optional[float] = None
    min_value: Optional[str] = None
    max_value: Optional[str] = None
    mean_value: Optional[float] = None
    median_value: Optional[float] = None
    stddev_value: Optional[float] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    avg_length: Optional[float] = None
    top_values: Optional[List[Dict[str, Any]]] = None
    sample_values: Optional[List[Any]] = None


class ColumnProfileResponse(BaseModel):
    """Column profile response."""

    id: UUID
    column_id: UUID
    dataset_id: UUID
    column_name: str
    row_count: Optional[int] = None
    null_count: Optional[int] = None
    null_percentage: Optional[float] = None
    distinct_count: Optional[int] = None
    distinct_percentage: Optional[float] = None
    min_value: Optional[str] = None
    max_value: Optional[str] = None
    mean_value: Optional[float] = None
    median_value: Optional[float] = None
    stddev_value: Optional[float] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    avg_length: Optional[float] = None
    top_values: Optional[List[Dict[str, Any]]] = None
    sample_values: Optional[List[Any]] = None
    profiled_at: datetime

    class Config:
        from_attributes = True


class SubmitProfilesRequest(BaseModel):
    """Request to submit profiling results for a dataset."""

    profiles: List[ColumnProfileSubmit]


# Ingest schemas
class MetadataIngestColumn(BaseModel):
    """Column metadata for metadata ingest."""

    name: str
    description: Optional[str] = None
    type: Optional[str] = None
    nullable: Optional[bool] = None


class MetadataIngestItem(BaseModel):
    """Single dataset item for metadata ingest."""

    full_name: str
    display_name: Optional[str] = None
    owner_name: Optional[str] = None
    description: Optional[str] = None
    columns: Optional[List[MetadataIngestColumn]] = None
    classification: Optional[str] = None
    domain: Optional[str] = None
    tags: Optional[List[str]] = None
    location_type: Optional[str] = None
    location_data: Optional[Dict[str, Any]] = None


class MetadataIngestRequest(BaseModel):
    """Request body for metadata ingest endpoint."""

    datasets: List[MetadataIngestItem]


# Error response
class ErrorResponse(BaseModel):
    """Error response schema."""

    detail: str


# Lineage schemas
class DatasetLineageItem(BaseModel):
    """Dataset lineage relationship item."""

    id: UUID
    full_name: str
    display_name: str
    transformation_type: Optional[str] = None

    class Config:
        from_attributes = True


class ColumnLineageItem(BaseModel):
    """Column lineage relationship item."""

    id: UUID
    upstream_column_id: UUID
    downstream_column_id: UUID
    upstream_column_name: str
    upstream_dataset_id: UUID
    upstream_dataset_name: str
    downstream_column_name: str
    downstream_dataset_id: UUID
    downstream_dataset_name: str
    transformation_expression: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DatasetLineageResponse(BaseModel):
    """Response for dataset lineage endpoint."""

    upstream: List[DatasetLineageItem]  # Datasets that this dataset depends on
    downstream: List[DatasetLineageItem]  # Datasets that depend on this dataset


class ColumnLineageResponse(BaseModel):
    """Response for column lineage endpoint."""

    upstream: List[ColumnLineageItem]  # Columns that this column depends on
    downstream: List[ColumnLineageItem]  # Columns that depend on this column


# Glossary schemas
class GlossaryTermCreate(BaseModel):
    """Request to create a glossary term."""

    name: str = Field(..., max_length=255)
    definition: str
    domain: Optional[str] = Field(None, max_length=100)
    owner: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = Field(None, max_length=50)


class GlossaryTermUpdate(BaseModel):
    """Request to update a glossary term."""

    name: Optional[str] = Field(None, max_length=255)
    definition: Optional[str] = None
    domain: Optional[str] = Field(None, max_length=100)
    owner: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = Field(None, max_length=50)


class GlossaryTermResponse(BaseModel):
    """Glossary term response."""

    id: UUID
    name: str
    definition: str
    domain: Optional[str] = None
    owner: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    linked_columns_count: int = 0
    linked_columns: List[Dict[str, Any]] = Field(default_factory=list)

    class Config:
        from_attributes = True


class ColumnGlossaryTermResponse(BaseModel):
    """Glossary term linked to a column (lightweight response)."""

    term_id: UUID
    term_name: str
    term_definition: str
    domain: Optional[str] = None

    class Config:
        from_attributes = True


# Schema change detection schemas
class SchemaChangeResponse(BaseModel):
    """Schema change detection result."""

    id: UUID
    dataset_id: UUID
    change_type: str
    column_name: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    detected_at: datetime

    class Config:
        from_attributes = True


class SchemaSnapshotResponse(BaseModel):
    """Schema snapshot summary."""

    id: UUID
    dataset_id: UUID
    columns_hash: str
    column_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class SchemaSnapshotResult(BaseModel):
    """Result of taking a schema snapshot."""

    snapshot_id: UUID
    changes_detected: int
    changes: List[SchemaChangeResponse]


# Audit log schemas
class AuditLogResponse(BaseModel):
    """Audit log entry response."""

    id: UUID
    dataset_id: Optional[UUID] = None
    action: str
    actor: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """Response for audit log list endpoint."""

    entries: List[AuditLogResponse]
    total: int


# Notification schemas
class NotificationResponse(BaseModel):
    """Notification response."""

    id: UUID
    dataset_id: UUID
    user_id: str
    notification_type: str
    title: str
    message: str
    read: bool
    created_at: datetime

    class Config:
        from_attributes = True

