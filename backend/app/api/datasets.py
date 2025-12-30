"""
Dataset API endpoints.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.api.schemas import (
    ActionResponse,
    DatasetDetailResponse,
    DatasetListItem,
    DatasetListResponse,
    DimensionScoreResponse,
    ReasonResponse,
    ScoreHistoryResponse,
    UpdateMetadataRequest,
    UpdateOwnerRequest,
)
from app.db import get_db
from app.models import (
    Dataset,
    DatasetAction,
    DatasetDimensionScore,
    DatasetReason,
    DatasetScoreHistory,
    DimensionKeyEnum,
    ReadinessStatusEnum,
)
from app.services.dataset_metadata import build_metadata_from_dataset
from app.services.scoring_service import score_and_save_dataset

router = APIRouter(prefix="/api/datasets", tags=["datasets"])


def _dimension_score_to_response(dim_score: DatasetDimensionScore) -> DimensionScoreResponse:
    """Convert dimension score model to response schema."""
    # dimension_key is stored as string, convert to value if it's an enum
    dimension_key_value = (
        dim_score.dimension_key.value
        if isinstance(dim_score.dimension_key, DimensionKeyEnum)
        else str(dim_score.dimension_key)
    )
    return DimensionScoreResponse(
        dimension_key=dimension_key_value,
        points_awarded=dim_score.points_awarded,
        max_points=dim_score.max_points,
        percentage=(dim_score.points_awarded / dim_score.max_points * 100)
        if dim_score.max_points > 0
        else 0.0,
    )


def _reason_to_response(reason: DatasetReason) -> ReasonResponse:
    """Convert reason model to response schema."""
    # dimension_key is stored as string, convert to value if it's an enum
    dimension_key_value = (
        reason.dimension_key.value
        if isinstance(reason.dimension_key, DimensionKeyEnum)
        else str(reason.dimension_key)
    )
    return ReasonResponse(
        id=reason.id,
        dimension_key=dimension_key_value,
        reason_code=reason.reason_code,
        message=reason.message,
        points_lost=reason.points_lost,
    )


def _action_to_response(action: DatasetAction) -> ActionResponse:
    """Convert action model to response schema."""
    return ActionResponse(
        id=action.id,
        action_key=action.action_key,
        title=action.title,
        description=action.description,
        points_gain=action.points_gain,
        dimension_key=None,  # Note: dimension_key not stored in actions table
        url=action.url,
    )


def _score_history_to_response(history: DatasetScoreHistory) -> ScoreHistoryResponse:
    """Convert score history model to response schema."""
    return ScoreHistoryResponse(
        id=history.id,
        readiness_score=history.readiness_score,
        recorded_at=history.recorded_at,
        scoring_version=history.scoring_version,
    )


@router.get("", response_model=DatasetListResponse)
def list_datasets(
    status: Optional[str] = Query(None, description="Filter by readiness status"),
    owner: Optional[str] = Query(None, description="Filter by owner name"),
    q: Optional[str] = Query(None, description="Search in full_name and display_name"),
    db: Session = Depends(get_db),
):
    """
    List datasets with optional filtering.

    Query parameters:
    - status: Filter by readiness status (draft, internal, production_ready, gold)
    - owner: Filter by owner name
    - q: Search query for full_name and display_name
    """
    query = db.query(Dataset)

    # Filter by status
    if status:
        status_value = status.lower()
        valid_statuses = ["draft", "internal", "production_ready", "gold"]
        if status_value not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status: {status}. Must be one of: {', '.join(valid_statuses)}",
            )
        query = query.filter(Dataset.readiness_status == status_value)

    # Filter by owner
    if owner:
        query = query.filter(Dataset.owner_name.ilike(f"%{owner}%"))

    # Search query
    if q:
        search_filter = or_(
            Dataset.full_name.ilike(f"%{q}%"),
            Dataset.display_name.ilike(f"%{q}%"),
        )
        query = query.filter(search_filter)

    # Get total count before pagination
    total = query.count()

    # Order by score descending
    datasets = query.order_by(Dataset.readiness_score.desc()).all()

    # Convert to response schemas
    dataset_items = [
        DatasetListItem(
            id=ds.id,
            full_name=ds.full_name,
            display_name=ds.display_name,
            owner_name=ds.owner_name,
            readiness_score=ds.readiness_score,
            readiness_status=ds.readiness_status.value if isinstance(ds.readiness_status, ReadinessStatusEnum) else str(ds.readiness_status),
            last_scored_at=ds.last_scored_at,
        )
        for ds in datasets
    ]

    return DatasetListResponse(datasets=dataset_items, total=total)


@router.get("/{dataset_id}", response_model=DatasetDetailResponse)
def get_dataset(dataset_id: UUID, db: Session = Depends(get_db)):
    """
    Get detailed information about a dataset.

    Includes:
    - Basic metadata
    - Readiness score and status
    - Dimension scores breakdown
    - Reasons for point losses
    - Recommended actions
    - Score history
    """
    # Get dataset
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Get dimension scores
    dimension_scores = (
        db.query(DatasetDimensionScore)
        .filter(DatasetDimensionScore.dataset_id == dataset_id)
        .order_by(DatasetDimensionScore.dimension_key)
        .all()
    )

    # Get reasons
    reasons = (
        db.query(DatasetReason)
        .filter(DatasetReason.dataset_id == dataset_id)
        .order_by(DatasetReason.dimension_key, DatasetReason.points_lost.desc())
        .all()
    )

    # Get actions
    actions = (
        db.query(DatasetAction)
        .filter(DatasetAction.dataset_id == dataset_id)
        .order_by(DatasetAction.points_gain.desc())
        .all()
    )

    # Get score history (most recent first)
    score_history = (
        db.query(DatasetScoreHistory)
        .filter(DatasetScoreHistory.dataset_id == dataset_id)
        .order_by(DatasetScoreHistory.recorded_at.desc())
        .limit(30)  # Limit to last 30 entries
        .all()
    )

    # Build response
    return DatasetDetailResponse(
        id=dataset.id,
        full_name=dataset.full_name,
        display_name=dataset.display_name,
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
        score_history=[_score_history_to_response(h) for h in score_history],
    )


@router.post("/{dataset_id}/owner", response_model=DatasetDetailResponse)
def update_owner(
    dataset_id: UUID,
    request: UpdateOwnerRequest,
    db: Session = Depends(get_db),
):
    """
    Update dataset owner and contact information.
    Triggers re-scoring and saves score history.
    """
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Update owner fields
    if request.owner_name is not None:
        dataset.owner_name = request.owner_name
    if request.owner_contact is not None:
        dataset.owner_contact = request.owner_contact

    # Build metadata for scoring (using existing columns if available)
    # Note: In a real system, we'd fetch column metadata from a separate table
    # For MVP, we'll use empty columns list
    metadata = build_metadata_from_dataset(dataset, columns=[])

    # Re-score the dataset (this saves history and updates actions)
    score_and_save_dataset(db, dataset, metadata)

    db.commit()
    db.refresh(dataset)

    # Return updated dataset detail
    return get_dataset(dataset_id, db)


@router.post("/{dataset_id}/metadata", response_model=DatasetDetailResponse)
def update_metadata(
    dataset_id: UUID,
    request: UpdateMetadataRequest,
    db: Session = Depends(get_db),
):
    """
    Update dataset metadata (display_name, intended_use, limitations).
    Triggers re-scoring and saves score history.
    """
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Update metadata fields
    if request.display_name is not None:
        dataset.display_name = request.display_name
    if request.intended_use is not None:
        dataset.intended_use = request.intended_use
    if request.limitations is not None:
        dataset.limitations = request.limitations

    # Build metadata for scoring (using existing columns if available)
    # Note: In a real system, we'd fetch column metadata from a separate table
    # For MVP, we'll use empty columns list
    metadata = build_metadata_from_dataset(dataset, columns=[])

    # Re-score the dataset (this saves history and updates actions)
    score_and_save_dataset(db, dataset, metadata)

    db.commit()
    db.refresh(dataset)

    # Return updated dataset detail
    return get_dataset(dataset_id, db)

