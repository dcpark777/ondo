"""
AI assist endpoints for generating dataset and column descriptions.

Safety: Only uses metadata, never raw data values.
"""

from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.schemas import DatasetDetailResponse
from app.config import settings
from app.db import get_db
from app.models import ReadinessStatusEnum

router = APIRouter(prefix="/api/ai", tags=["ai"])


class DatasetDescriptionRequest(BaseModel):
    """Request for dataset description generation.
    
    Safety: Only uses metadata (table/column names), never raw data values.
    """

    full_name: str
    display_name: Optional[str] = None
    owner_name: Optional[str] = None
    intended_use: Optional[str] = None
    limitations: Optional[str] = None
    column_names: Optional[List[str]] = None  # Column names only, no data


class DatasetDescriptionResponse(BaseModel):
    """Response with suggested dataset description."""

    suggested_description: str


class ColumnDescriptionsRequest(BaseModel):
    """Request for column descriptions generation.
    
    Safety: Only uses metadata (column names), never raw data values.
    """

    dataset_name: str
    column_names: List[str]  # Column names only, no data
    existing_descriptions: Optional[dict[str, str]] = None


class ColumnDescriptionsResponse(BaseModel):
    """Response with suggested column descriptions."""

    suggested_descriptions: dict[str, str]


def _generate_dataset_description(request: DatasetDescriptionRequest) -> str:
    """
    Generate a dataset description based on metadata (table/column names only).

    Safety: Only uses metadata, never raw data values.

    In production, this would call an LLM API (OpenAI, Anthropic, etc.).
    For MVP, we use a template-based approach with intelligent inference.
    """
    parts = []

    # Parse dataset name to infer purpose
    full_name_parts = request.full_name.split(".")
    schema = full_name_parts[-2] if len(full_name_parts) > 1 else None
    table_name = full_name_parts[-1] if full_name_parts else request.full_name

    # Start with dataset name - infer purpose from name
    if request.display_name:
        display = request.display_name
    else:
        # Convert snake_case or camelCase to readable
        display = table_name.replace("_", " ").replace("-", " ").title()

    # Infer purpose from schema/table name patterns
    purpose_hint = ""
    if schema:
        schema_lower = schema.lower()
        if "analytics" in schema_lower or "analytics" in table_name.lower():
            purpose_hint = "analytics and reporting"
        elif "staging" in schema_lower or "raw" in schema_lower:
            purpose_hint = "staging and data preparation"
        elif "warehouse" in schema_lower:
            purpose_hint = "data warehousing"
        elif "experiments" in schema_lower or "ab_test" in table_name.lower():
            purpose_hint = "experimentation and A/B testing"
        elif "marketing" in schema_lower:
            purpose_hint = "marketing analytics"
        else:
            purpose_hint = "data analysis"

    # Build description
    parts.append(f"This dataset contains {display.lower()} data for {purpose_hint}.")

    # Add column context if available - infer data types and purpose
    if request.column_names:
        column_count = len(request.column_names)
        # Analyze column names to infer content
        has_user_id = any("user" in col.lower() and "id" in col.lower() for col in request.column_names)
        has_timestamp = any("timestamp" in col.lower() or col.lower().endswith("_at") for col in request.column_names)
        has_event = any("event" in col.lower() for col in request.column_names)

        if has_user_id and has_event:
            parts.append("The dataset tracks user events and interactions.")
        elif has_user_id:
            parts.append("The dataset contains user-related information.")
        elif has_timestamp:
            parts.append("The dataset includes temporal data with timestamps.")

        parts.append(f"It consists of {column_count} column{'s' if column_count != 1 else ''}.")

    # Add intended use if available
    if request.intended_use:
        parts.append(f"Intended use cases: {request.intended_use}.")

    # Add limitations if available
    if request.limitations:
        parts.append(f"Limitations: {request.limitations}.")

    # Add owner context if available
    if request.owner_name:
        parts.append(f"Maintained by {request.owner_name}.")

    # Fallback if minimal metadata
    if len(parts) == 1:
        parts.append(
            "This dataset is used for data analysis and reporting. "
            "Please add more metadata to improve this description."
        )

    return " ".join(parts)


def _generate_column_descriptions(
    request: ColumnDescriptionsRequest,
) -> Dict[str, str]:
    """
    Generate column descriptions based on column names and context.

    Safety: Only uses metadata (column names), never raw data values.

    In production, this would call an LLM API (OpenAI, Anthropic, etc.).
    For MVP, we use a template-based approach with heuristics.
    """
    descriptions = {}

    for column_name in request.column_names:
        # Skip if already has description
        if (
            request.existing_descriptions
            and column_name in request.existing_descriptions
            and request.existing_descriptions[column_name]
        ):
            continue

        # Generate description based on column name patterns
        col_lower = column_name.lower()

        # Common patterns
        if col_lower.endswith("_id") or col_lower == "id":
            descriptions[column_name] = f"Unique identifier for {request.dataset_name} records."
        elif col_lower.endswith("_at") or col_lower in ["timestamp", "created", "updated"]:
            descriptions[column_name] = "Timestamp indicating when this record was created or last updated."
        elif col_lower.endswith("_name") or col_lower == "name":
            descriptions[column_name] = "Name or label for this entity."
        elif col_lower.endswith("_email") or col_lower == "email":
            descriptions[column_name] = "Email address associated with this record."
        elif col_lower.endswith("_type") or col_lower == "type":
            descriptions[column_name] = "Type or category classification for this record."
        elif col_lower.endswith("_status") or col_lower == "status":
            descriptions[column_name] = "Current status of this record."
        elif col_lower.endswith("_count") or col_lower.endswith("_total"):
            descriptions[column_name] = "Numeric count or total value."
        elif col_lower.endswith("_amount") or col_lower.endswith("_value"):
            descriptions[column_name] = "Monetary amount or numeric value."
        elif col_lower.startswith("is_") or col_lower.startswith("has_"):
            descriptions[column_name] = f"Boolean flag indicating whether {col_lower.replace('is_', '').replace('has_', '')} is present or true."
        elif col_lower.endswith("_url") or col_lower == "url":
            descriptions[column_name] = "URL or web address."
        else:
            # Generic description based on column name
            # Convert snake_case to readable text
            readable = column_name.replace("_", " ").title()
            descriptions[column_name] = f"{readable} field in {request.dataset_name}."

    return descriptions


@router.post("/dataset-description", response_model=DatasetDescriptionResponse)
def generate_dataset_description(
    request: DatasetDescriptionRequest,
) -> DatasetDescriptionResponse:
    """
    Generate a suggested dataset description based on metadata.

    Safety: Only uses metadata (name, owner, intended use, column names).
    Never uses raw data values.

    Returns suggested text only - never auto-applies.
    """
    if not settings.ai_assist_enabled:
        raise HTTPException(
            status_code=403,
            detail="AI assist is not enabled. Set AI_ASSIST_ENABLED=true to enable.",
        )

    suggested = _generate_dataset_description(request)

    return DatasetDescriptionResponse(suggested_description=suggested)


@router.post("/column-descriptions", response_model=ColumnDescriptionsResponse)
def generate_column_descriptions(
    request: ColumnDescriptionsRequest,
) -> ColumnDescriptionsResponse:
    """
    Generate suggested column descriptions for undocumented columns.

    Safety: Only uses metadata (column names, dataset name).
    Never uses raw data values.

    Returns suggested text only - never auto-applies.
    """
    if not settings.ai_assist_enabled:
        raise HTTPException(
            status_code=403,
            detail="AI assist is not enabled. Set AI_ASSIST_ENABLED=true to enable.",
        )

    suggested = _generate_column_descriptions(request)

    return ColumnDescriptionsResponse(suggested_descriptions=suggested)


class ApplyDescriptionRequest(BaseModel):
    """Request to apply AI-generated dataset description."""

    dataset_id: str
    description: str


class ApplyColumnDescriptionsRequest(BaseModel):
    """Request to apply AI-generated column descriptions."""

    dataset_id: str
    column_descriptions: dict[str, str]  # Map of column_name -> description


@router.post("/apply-description", response_model=DatasetDetailResponse)
def apply_dataset_description(
    request: ApplyDescriptionRequest,
    db: Session = Depends(get_db),
) -> DatasetDetailResponse:
    """
    Apply AI-generated dataset description and trigger rescore.

    Safety: Only updates metadata, never touches raw data.
    """
    if not settings.ai_assist_enabled:
        raise HTTPException(
            status_code=403,
            detail="AI assist is not enabled. Set AI_ASSIST_ENABLED=true to enable.",
        )

    from uuid import UUID
    from app.models import Dataset, DatasetColumn, ReadinessStatusEnum
    from app.services.dataset_metadata import build_metadata_from_dataset
    from app.services.scoring_service import score_and_save_dataset

    try:
        dataset_id = UUID(request.dataset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid dataset ID format")

    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Update description
    dataset.description = request.description

    # Build metadata for rescoring (columns from previous scoring if available)
    # In a real system, we'd fetch column metadata from a separate table
    metadata = build_metadata_from_dataset(dataset, columns=[])

    # Rescore the dataset
    score_and_save_dataset(db, dataset, metadata)

    db.commit()
    db.refresh(dataset)

    # Return updated dataset detail - build response directly to avoid circular dependency
    from app.api.datasets import (
        _action_to_response,
        _column_to_response,
        _dimension_score_to_response,
        _reason_to_response,
        _score_history_to_response,
    )
    from app.models import (
        DatasetAction,
        DatasetDimensionScore,
        DatasetReason,
        DatasetScoreHistory,
    )

    # Get related data
    columns = (
        db.query(DatasetColumn)
        .filter(DatasetColumn.dataset_id == dataset_id)
        .order_by(DatasetColumn.name)
        .all()
    )
    dimension_scores = (
        db.query(DatasetDimensionScore)
        .filter(DatasetDimensionScore.dataset_id == dataset_id)
        .order_by(DatasetDimensionScore.dimension_key)
        .all()
    )
    reasons = (
        db.query(DatasetReason)
        .filter(DatasetReason.dataset_id == dataset_id)
        .order_by(DatasetReason.dimension_key, DatasetReason.points_lost.desc())
        .all()
    )
    actions = (
        db.query(DatasetAction)
        .filter(DatasetAction.dataset_id == dataset_id)
        .order_by(DatasetAction.points_gain.desc())
        .all()
    )
    score_history = (
        db.query(DatasetScoreHistory)
        .filter(DatasetScoreHistory.dataset_id == dataset_id)
        .order_by(DatasetScoreHistory.recorded_at.desc())
        .limit(30)
        .all()
    )

    # Filter reasons/actions for measured dimensions
    dimension_scores_dict = {
        ds.dimension_key.lower(): bool(ds.measured) if hasattr(ds, "measured") else True
        for ds in dimension_scores
    }
    reasons = [r for r in reasons if dimension_scores_dict.get(r.dimension_key.lower(), True)]
    
    # Helper to map action_key to dimension_key
    from app.scoring.constants import ActionKey
    def get_dimension_key_from_action_key(action_key: str) -> Optional[str]:
        mapping = {
            ActionKey.ASSIGN_OWNER: "ownership",
            ActionKey.ADD_OWNER_CONTACT: "ownership",
            ActionKey.ADD_DESCRIPTION: "documentation",
            ActionKey.DOCUMENT_COLUMNS: "documentation",
            ActionKey.FIX_NAMING: "schema_hygiene",
            ActionKey.REDUCE_NULLABLE_COLUMNS: "schema_hygiene",
            ActionKey.REMOVE_LEGACY_COLUMNS: "schema_hygiene",
            ActionKey.ADD_QUALITY_CHECKS: "data_quality",
            ActionKey.DEFINE_SLA: "data_quality",
            ActionKey.RESOLVE_FAILURES: "data_quality",
            ActionKey.PREVENT_BREAKING_CHANGES: "stability",
            ActionKey.ADD_CHANGELOG: "stability",
            ActionKey.MAINTAIN_COMPATIBILITY: "stability",
            ActionKey.DEFINE_INTENDED_USE: "operational",
            ActionKey.DOCUMENT_LIMITATIONS: "operational",
        }
        return mapping.get(action_key)
    
    actions = [
        a for a in actions
        if dimension_scores_dict.get(get_dimension_key_from_action_key(a.action_key) or "", True)
    ]

    return DatasetDetailResponse(
        id=dataset.id,
        full_name=dataset.full_name,
        display_name=dataset.display_name,
        description=dataset.description if hasattr(dataset, "description") else None,
        owner_name=dataset.owner_name,
        owner_contact=dataset.owner_contact,
        intended_use=dataset.intended_use,
        limitations=dataset.limitations,
        last_seen_at=dataset.last_seen_at,
        last_scored_at=dataset.last_scored_at,
        readiness_score=dataset.readiness_score,
        readiness_status=dataset.readiness_status.value if isinstance(dataset.readiness_status, ReadinessStatusEnum) else str(dataset.readiness_status),
        dimension_scores=[_dimension_score_to_response(ds) for ds in dimension_scores],
        reasons=[_reason_to_response(r) for r in reasons],
        actions=[_action_to_response(a) for a in actions],
        columns=[_column_to_response(c) for c in columns],
        score_history=[_score_history_to_response(h) for h in score_history],
    )


@router.post("/apply-column-descriptions", response_model=DatasetDetailResponse)
def apply_column_descriptions(
    request: ApplyColumnDescriptionsRequest,
    db: Session = Depends(get_db),
) -> DatasetDetailResponse:
    """
    Apply AI-generated column descriptions and trigger rescore.

    Safety: Only updates metadata, never touches raw data.
    """
    if not settings.ai_assist_enabled:
        raise HTTPException(
            status_code=403,
            detail="AI assist is not enabled. Set AI_ASSIST_ENABLED=true to enable.",
        )

    from uuid import UUID
    from app.models import Dataset
    from app.services.dataset_metadata import build_metadata_from_dataset
    from app.services.scoring_service import score_and_save_dataset

    try:
        dataset_id = UUID(request.dataset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid dataset ID format")

    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Convert column descriptions to metadata format
    columns = [
        {"name": col_name, "description": desc}
        for col_name, desc in request.column_descriptions.items()
    ]

    # Build metadata with updated column descriptions
    metadata = build_metadata_from_dataset(dataset, columns=columns)

    # Rescore the dataset (this will use the new column descriptions)
    score_and_save_dataset(db, dataset, metadata)

    db.commit()
    db.refresh(dataset)

    # Return updated dataset detail - build response directly to avoid circular dependency
    from app.api.datasets import (
        _action_to_response,
        _column_to_response,
        _dimension_score_to_response,
        _reason_to_response,
        _score_history_to_response,
    )
    from app.models import (
        DatasetAction,
        DatasetDimensionScore,
        DatasetReason,
        DatasetScoreHistory,
        ReadinessStatusEnum,
    )

    # Get related data
    columns = (
        db.query(DatasetColumn)
        .filter(DatasetColumn.dataset_id == dataset_id)
        .order_by(DatasetColumn.name)
        .all()
    )
    dimension_scores = (
        db.query(DatasetDimensionScore)
        .filter(DatasetDimensionScore.dataset_id == dataset_id)
        .order_by(DatasetDimensionScore.dimension_key)
        .all()
    )
    reasons = (
        db.query(DatasetReason)
        .filter(DatasetReason.dataset_id == dataset_id)
        .order_by(DatasetReason.dimension_key, DatasetReason.points_lost.desc())
        .all()
    )
    actions = (
        db.query(DatasetAction)
        .filter(DatasetAction.dataset_id == dataset_id)
        .order_by(DatasetAction.points_gain.desc())
        .all()
    )
    score_history = (
        db.query(DatasetScoreHistory)
        .filter(DatasetScoreHistory.dataset_id == dataset_id)
        .order_by(DatasetScoreHistory.recorded_at.desc())
        .limit(30)
        .all()
    )

    # Filter reasons/actions for measured dimensions
    dimension_scores_dict = {
        ds.dimension_key.lower(): bool(ds.measured) if hasattr(ds, "measured") else True
        for ds in dimension_scores
    }
    reasons = [r for r in reasons if dimension_scores_dict.get(r.dimension_key.lower(), True)]
    
    # Helper to map action_key to dimension_key
    from app.scoring.constants import ActionKey
    def get_dimension_key_from_action_key(action_key: str) -> Optional[str]:
        mapping = {
            ActionKey.ASSIGN_OWNER: "ownership",
            ActionKey.ADD_OWNER_CONTACT: "ownership",
            ActionKey.ADD_DESCRIPTION: "documentation",
            ActionKey.DOCUMENT_COLUMNS: "documentation",
            ActionKey.FIX_NAMING: "schema_hygiene",
            ActionKey.REDUCE_NULLABLE_COLUMNS: "schema_hygiene",
            ActionKey.REMOVE_LEGACY_COLUMNS: "schema_hygiene",
            ActionKey.ADD_QUALITY_CHECKS: "data_quality",
            ActionKey.DEFINE_SLA: "data_quality",
            ActionKey.RESOLVE_FAILURES: "data_quality",
            ActionKey.PREVENT_BREAKING_CHANGES: "stability",
            ActionKey.ADD_CHANGELOG: "stability",
            ActionKey.MAINTAIN_COMPATIBILITY: "stability",
            ActionKey.DEFINE_INTENDED_USE: "operational",
            ActionKey.DOCUMENT_LIMITATIONS: "operational",
        }
        return mapping.get(action_key)
    
    actions = [
        a for a in actions
        if dimension_scores_dict.get(get_dimension_key_from_action_key(a.action_key) or "", True)
    ]

    return DatasetDetailResponse(
        id=dataset.id,
        full_name=dataset.full_name,
        display_name=dataset.display_name,
        description=dataset.description if hasattr(dataset, "description") else None,
        owner_name=dataset.owner_name,
        owner_contact=dataset.owner_contact,
        intended_use=dataset.intended_use,
        limitations=dataset.limitations,
        last_seen_at=dataset.last_seen_at,
        last_scored_at=dataset.last_scored_at,
        readiness_score=dataset.readiness_score,
        readiness_status=dataset.readiness_status.value if isinstance(dataset.readiness_status, ReadinessStatusEnum) else str(dataset.readiness_status),
        dimension_scores=[_dimension_score_to_response(ds) for ds in dimension_scores],
        reasons=[_reason_to_response(r) for r in reasons],
        actions=[_action_to_response(a) for a in actions],
        columns=[_column_to_response(c) for c in columns],
        score_history=[_score_history_to_response(h) for h in score_history],
    )

