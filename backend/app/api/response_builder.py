"""
Shared response-building logic for dataset detail responses.

Single source of truth for:
- ACTION_KEY_TO_DIMENSION mapping
- Model-to-response converter functions
- build_dataset_detail_response() consolidation
"""

from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.schemas import (
    ActionResponse,
    ColumnResponse,
    DatasetDetailResponse,
    DimensionScoreResponse,
    ReasonResponse,
    ScoreHistoryResponse,
)
from app.models import (
    Dataset,
    DatasetAction,
    DatasetColumn,
    DatasetDimensionScore,
    DatasetReason,
    DatasetScoreHistory,
    DimensionKeyEnum,
    ReadinessStatusEnum,
)
from app.scoring.constants import ActionKey

# Single source of truth: maps action keys to dimension keys
ACTION_KEY_TO_DIMENSION = {
    # Ownership
    ActionKey.ASSIGN_OWNER: "ownership",
    ActionKey.ADD_OWNER_CONTACT: "ownership",
    # Documentation
    ActionKey.ADD_DESCRIPTION: "documentation",
    ActionKey.DOCUMENT_COLUMNS: "documentation",
    # Schema hygiene
    ActionKey.FIX_NAMING: "schema_hygiene",
    ActionKey.REDUCE_NULLABLE_COLUMNS: "schema_hygiene",
    ActionKey.REMOVE_LEGACY_COLUMNS: "schema_hygiene",
    # Data quality
    ActionKey.ADD_QUALITY_CHECKS: "data_quality",
    ActionKey.DEFINE_SLA: "data_quality",
    ActionKey.RESOLVE_FAILURES: "data_quality",
    # Stability
    ActionKey.PREVENT_BREAKING_CHANGES: "stability",
    ActionKey.ADD_CHANGELOG: "stability",
    ActionKey.MAINTAIN_COMPATIBILITY: "stability",
    # Operational
    ActionKey.DEFINE_INTENDED_USE: "operational",
    ActionKey.DOCUMENT_LIMITATIONS: "operational",
}

SCORE_HISTORY_LIMIT = 30


def dimension_score_to_response(dim_score: DatasetDimensionScore) -> DimensionScoreResponse:
    """Convert dimension score model to response schema.

    Contract v1: Returns stable shape with measured flag.
    """
    dimension_key_value = (
        dim_score.dimension_key.value
        if isinstance(dim_score.dimension_key, DimensionKeyEnum)
        else str(dim_score.dimension_key)
    )
    measured = bool(dim_score.measured)
    return DimensionScoreResponse(
        dimension_key=dimension_key_value,
        points_awarded=dim_score.points_awarded,
        max_points=dim_score.max_points,
        measured=measured,
        percentage=(dim_score.points_awarded / dim_score.max_points * 100)
        if dim_score.max_points > 0
        else 0.0,
    )


def reason_to_response(reason: DatasetReason) -> ReasonResponse:
    """Convert reason model to response schema."""
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


def action_to_response(action: DatasetAction) -> ActionResponse:
    """Convert action model to response schema."""
    return ActionResponse(
        id=action.id,
        action_key=action.action_key,
        title=action.title,
        description=action.description,
        points_gain=action.points_gain,
        url=action.url,
    )


def column_to_response(column: DatasetColumn) -> ColumnResponse:
    """Convert column model to response schema."""
    return ColumnResponse(
        id=column.id,
        name=column.name,
        description=column.description,
        type=column.type,
        nullable=bool(column.nullable) if column.nullable is not None else None,
    )


def score_history_to_response(history: DatasetScoreHistory) -> ScoreHistoryResponse:
    """Convert score history model to response schema."""
    return ScoreHistoryResponse(
        id=history.id,
        readiness_score=history.readiness_score,
        recorded_at=history.recorded_at,
        scoring_version=history.scoring_version,
    )


def build_dataset_detail_response(db: Session, dataset_id: UUID) -> DatasetDetailResponse:
    """Build a complete DatasetDetailResponse from the database.

    This is the single entry point used by datasets.py and ai.py to construct
    the detail response. Consolidates query + filter + build logic.

    Raises HTTPException 404 if dataset not found.
    """
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

    # Build measured-status lookup for filtering
    dimension_scores_dict = {
        ds.dimension_key.lower(): bool(ds.measured)
        for ds in dimension_scores
    }

    # Get reasons — filter out unmeasured dimensions
    all_reasons = (
        db.query(DatasetReason)
        .filter(DatasetReason.dataset_id == dataset_id)
        .order_by(DatasetReason.dimension_key, DatasetReason.points_lost.desc())
        .all()
    )
    reasons = [
        r for r in all_reasons
        if dimension_scores_dict.get(r.dimension_key.lower(), True)
    ]

    # Get actions — filter out unmeasured dimensions
    all_actions = (
        db.query(DatasetAction)
        .filter(DatasetAction.dataset_id == dataset_id)
        .order_by(DatasetAction.points_gain.desc())
        .all()
    )
    actions = [
        a for a in all_actions
        if dimension_scores_dict.get(
            ACTION_KEY_TO_DIMENSION.get(a.action_key, ""), True
        )
    ]

    # Get columns
    columns = (
        db.query(DatasetColumn)
        .filter(DatasetColumn.dataset_id == dataset_id)
        .order_by(DatasetColumn.name)
        .all()
    )

    # Get score history (most recent first)
    score_history = (
        db.query(DatasetScoreHistory)
        .filter(DatasetScoreHistory.dataset_id == dataset_id)
        .order_by(DatasetScoreHistory.recorded_at.desc())
        .limit(SCORE_HISTORY_LIMIT)
        .all()
    )

    return DatasetDetailResponse(
        id=dataset.id,
        full_name=dataset.full_name,
        display_name=dataset.display_name,
        description=dataset.description,
        owner_name=dataset.owner_name,
        owner_contact=dataset.owner_contact,
        intended_use=dataset.intended_use,
        limitations=dataset.limitations,
        location_type=dataset.location_type,
        location_data=dataset.location_data,
        created_at=dataset.created_at,
        created_by=dataset.created_by,
        last_seen_at=dataset.last_seen_at,
        last_scored_at=dataset.last_scored_at,
        last_updated_at=dataset.last_updated_at,
        updated_by=dataset.updated_by,
        data_size_bytes=dataset.data_size_bytes,
        file_count=dataset.file_count,
        partition_keys=dataset.partition_keys,
        sla_hours=dataset.sla_hours,
        producing_job=dataset.producing_job,
        readiness_score=dataset.readiness_score,
        readiness_status=dataset.readiness_status.value
        if isinstance(dataset.readiness_status, ReadinessStatusEnum)
        else str(dataset.readiness_status),
        dimension_scores=[dimension_score_to_response(ds) for ds in dimension_scores],
        reasons=[reason_to_response(r) for r in reasons],
        actions=[action_to_response(a) for a in actions],
        columns=[column_to_response(c) for c in columns],
        score_history=[score_history_to_response(h) for h in score_history],
    )
