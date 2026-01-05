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
    owner_name: Optional[str] = None
    readiness_score: int
    readiness_status: str
    last_scored_at: Optional[datetime] = None

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
    last_seen_at: datetime
    last_scored_at: Optional[datetime] = None
    readiness_score: int
    readiness_status: str
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
    upstream_dataset_name: str
    downstream_column_name: str
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

