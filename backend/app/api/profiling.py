"""
Data profiling API endpoints.
"""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.schemas import (
    ColumnProfileResponse,
    SubmitProfilesRequest,
)
from app.db import get_db
from app.models import ColumnProfile, Dataset, DatasetColumn

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/datasets", tags=["profiling"])


def _profile_to_response(profile: ColumnProfile, column_name: str) -> ColumnProfileResponse:
    """Convert a ColumnProfile ORM object to a ColumnProfileResponse."""
    return ColumnProfileResponse(
        id=profile.id,
        column_id=profile.column_id,
        dataset_id=profile.dataset_id,
        column_name=column_name,
        row_count=profile.row_count,
        null_count=profile.null_count,
        null_percentage=profile.null_percentage,
        distinct_count=profile.distinct_count,
        distinct_percentage=profile.distinct_percentage,
        min_value=profile.min_value,
        max_value=profile.max_value,
        mean_value=profile.mean_value,
        median_value=profile.median_value,
        stddev_value=profile.stddev_value,
        min_length=profile.min_length,
        max_length=profile.max_length,
        avg_length=profile.avg_length,
        top_values=profile.top_values,
        sample_values=profile.sample_values,
        profiled_at=profile.profiled_at,
    )


@router.get("/{dataset_id}/profiles", response_model=List[ColumnProfileResponse])
def get_profiles(dataset_id: UUID, db: Session = Depends(get_db)):
    """
    Get the latest profile for each column in a dataset.

    Returns the most recent profiling result per column.
    """
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Subquery to get max profiled_at per column_id for this dataset
    latest_subq = (
        db.query(
            ColumnProfile.column_id,
            func.max(ColumnProfile.profiled_at).label("max_profiled_at"),
        )
        .filter(ColumnProfile.dataset_id == dataset_id)
        .group_by(ColumnProfile.column_id)
        .subquery()
    )

    # Join back to get the full profile rows
    profiles = (
        db.query(ColumnProfile, DatasetColumn.name)
        .join(DatasetColumn, ColumnProfile.column_id == DatasetColumn.id)
        .join(
            latest_subq,
            (ColumnProfile.column_id == latest_subq.c.column_id)
            & (ColumnProfile.profiled_at == latest_subq.c.max_profiled_at),
        )
        .filter(ColumnProfile.dataset_id == dataset_id)
        .order_by(DatasetColumn.name)
        .all()
    )

    return [_profile_to_response(profile, col_name) for profile, col_name in profiles]


@router.post("/{dataset_id}/profiles", response_model=List[ColumnProfileResponse])
def submit_profiles(
    dataset_id: UUID,
    request: SubmitProfilesRequest,
    db: Session = Depends(get_db),
):
    """
    Submit profiling results for a dataset.

    Each item in the profiles list matches a column by name.
    Creates a new profiling snapshot for each column.
    """
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    if not request.profiles:
        raise HTTPException(status_code=400, detail="No profiles provided")

    # Load all columns for this dataset, keyed by name
    columns = (
        db.query(DatasetColumn)
        .filter(DatasetColumn.dataset_id == dataset_id)
        .all()
    )
    column_by_name = {col.name: col for col in columns}

    now = datetime.utcnow()
    created_profiles: list[tuple[ColumnProfile, str]] = []
    unknown_columns: list[str] = []

    for profile_data in request.profiles:
        col = column_by_name.get(profile_data.column_name)
        if not col:
            unknown_columns.append(profile_data.column_name)
            continue

        profile = ColumnProfile(
            column_id=col.id,
            dataset_id=dataset_id,
            row_count=profile_data.row_count,
            null_count=profile_data.null_count,
            null_percentage=profile_data.null_percentage,
            distinct_count=profile_data.distinct_count,
            distinct_percentage=profile_data.distinct_percentage,
            min_value=profile_data.min_value,
            max_value=profile_data.max_value,
            mean_value=profile_data.mean_value,
            median_value=profile_data.median_value,
            stddev_value=profile_data.stddev_value,
            min_length=profile_data.min_length,
            max_length=profile_data.max_length,
            avg_length=profile_data.avg_length,
            top_values=profile_data.top_values,
            sample_values=profile_data.sample_values,
            profiled_at=now,
        )
        db.add(profile)
        created_profiles.append((profile, profile_data.column_name))

    if unknown_columns:
        logger.warning(
            "Unknown columns in profiling submission for dataset %s: %s",
            dataset_id,
            unknown_columns,
        )

    if not created_profiles:
        raise HTTPException(
            status_code=400,
            detail=f"No matching columns found. Unknown columns: {unknown_columns}",
        )

    db.commit()

    # Refresh to get generated IDs
    for profile, _ in created_profiles:
        db.refresh(profile)

    logger.info(
        "Submitted %d profiles for dataset %s (skipped %d unknown columns)",
        len(created_profiles),
        dataset_id,
        len(unknown_columns),
    )

    return [_profile_to_response(profile, col_name) for profile, col_name in created_profiles]


@router.get("/{dataset_id}/profiles/history", response_model=List[ColumnProfileResponse])
def get_profile_history(
    dataset_id: UUID,
    column_name: str = Query(..., description="Column name to get history for"),
    limit: int = Query(10, ge=1, le=100, description="Number of historical profiles to return"),
    db: Session = Depends(get_db),
):
    """
    Get profiling history for a specific column.

    Returns historical profiling snapshots ordered by profiled_at descending.
    """
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Find the column by name
    column = (
        db.query(DatasetColumn)
        .filter(
            DatasetColumn.dataset_id == dataset_id,
            DatasetColumn.name == column_name,
        )
        .first()
    )
    if not column:
        raise HTTPException(status_code=404, detail=f"Column '{column_name}' not found")

    # Get historical profiles
    profiles = (
        db.query(ColumnProfile)
        .filter(
            ColumnProfile.column_id == column.id,
            ColumnProfile.dataset_id == dataset_id,
        )
        .order_by(ColumnProfile.profiled_at.desc())
        .limit(limit)
        .all()
    )

    return [_profile_to_response(p, column_name) for p in profiles]
