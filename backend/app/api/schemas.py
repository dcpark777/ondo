"""
Pydantic schemas for API request/response validation.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# Base schemas
class DimensionScoreResponse(BaseModel):
    """Dimension score response."""

    dimension_key: str
    points_awarded: int
    max_points: int
    percentage: float

    class Config:
        from_attributes = True


class ReasonResponse(BaseModel):
    """Reason for point loss."""

    id: UUID
    dimension_key: str
    reason_code: str
    message: str
    points_lost: int

    class Config:
        from_attributes = True


class ActionResponse(BaseModel):
    """Recommended action to improve score."""

    id: UUID
    action_key: str
    title: str
    description: str
    points_gain: int
    url: Optional[str] = None

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
    owner_name: Optional[str] = None
    owner_contact: Optional[str] = None
    intended_use: Optional[str] = None
    limitations: Optional[str] = None
    last_seen_at: datetime
    last_scored_at: Optional[datetime] = None
    readiness_score: int
    readiness_status: str
    dimension_scores: List[DimensionScoreResponse]
    reasons: List[ReasonResponse]
    actions: List[ActionResponse]
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

