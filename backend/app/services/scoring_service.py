"""
Service for scoring datasets and persisting results.
"""

from datetime import datetime
from typing import Dict

from sqlalchemy.orm import Session

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
from app.scoring.engine import score_dataset


def score_and_save_dataset(
    db: Session,
    dataset: Dataset,
    metadata: Dict,
) -> Dataset:
    """
    Score a dataset and save all scoring results to the database.

    Args:
        db: Database session
        dataset: Dataset model instance
        metadata: Metadata dict for scoring engine

    Returns:
        Updated dataset with score and status
    """
    # Score the dataset
    score_result = score_dataset(metadata)

    # Update dataset with score
    dataset.readiness_score = score_result.total_score
    dataset.readiness_status = score_result.status.value  # Pass value string directly
    dataset.last_scored_at = datetime.utcnow()

    # Delete existing dimension scores, reasons, actions, and columns
    db.query(DatasetDimensionScore).filter(
        DatasetDimensionScore.dataset_id == dataset.id
    ).delete()
    db.query(DatasetReason).filter(DatasetReason.dataset_id == dataset.id).delete()
    db.query(DatasetAction).filter(DatasetAction.dataset_id == dataset.id).delete()
    db.query(DatasetColumn).filter(DatasetColumn.dataset_id == dataset.id).delete()

    # Create dimension scores
    for dim_score in score_result.dimension_scores:
        db_dim_score = DatasetDimensionScore(
            dataset_id=dataset.id,
            dimension_key=dim_score.dimension_key.lower(),  # Pass value string directly
            points_awarded=dim_score.points_awarded,
            max_points=dim_score.max_points,
            measured=1 if dim_score.measured else 0,  # Store as integer (1=True, 0=False)
        )
        db.add(db_dim_score)

    # Create reasons
    for reason in score_result.reasons:
        db_reason = DatasetReason(
            dataset_id=dataset.id,
            dimension_key=reason.dimension_key.lower(),  # Pass value string directly
            reason_code=reason.reason_code,
            message=reason.message,
            points_lost=reason.points_lost,
        )
        db.add(db_reason)

    # Create actions
    for action in score_result.actions:
        db_action = DatasetAction(
            dataset_id=dataset.id,
            action_key=action.action_key,
            title=action.title,
            description=action.description,
            points_gain=action.points_gain,
            url=action.url,
        )
        db.add(db_action)

    # Create columns if provided in metadata
    columns = metadata.get("columns", [])
    if columns:
        for col in columns:
            db_column = DatasetColumn(
                dataset_id=dataset.id,
                name=col.get("name", ""),
                description=col.get("description"),
                type=col.get("type"),
                nullable=1 if col.get("nullable") is True else (0 if col.get("nullable") is False else None),
                last_seen_at=datetime.utcnow(),
            )
            db.add(db_column)

    # Create score history entry
    history = DatasetScoreHistory(
        dataset_id=dataset.id,
        readiness_score=score_result.total_score,
        recorded_at=datetime.utcnow(),
        scoring_version="v1",
    )
    db.add(history)

    return dataset

