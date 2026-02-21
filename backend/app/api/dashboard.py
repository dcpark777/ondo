"""
Dashboard API endpoints.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import (
    Dataset,
    DatasetAction,
    DatasetDimensionScore,
    DatasetScoreHistory,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary")
def get_dashboard_summary(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get dashboard summary with aggregate statistics.

    Returns:
    - total_datasets, average_score
    - status_distribution: count per status
    - score_distribution: count in buckets
    - top_actions: top 5 recommended actions by potential point gain
    - lowest_scoring: 5 datasets needing most attention
    - recently_scored: 5 most recently scored datasets
    - dimension_health: average percentage per dimension (measured only)
    """
    # Total datasets and average score
    total_datasets = db.query(func.count(Dataset.id)).scalar() or 0
    average_score = db.query(func.avg(Dataset.readiness_score)).scalar() or 0

    # Status distribution
    status_rows = (
        db.query(Dataset.readiness_status, func.count(Dataset.id))
        .group_by(Dataset.readiness_status)
        .all()
    )
    status_distribution = {status: count for status, count in status_rows}

    # Score distribution in buckets
    score_buckets = {
        "0-24": 0,
        "25-49": 0,
        "50-69": 0,
        "70-84": 0,
        "85-100": 0,
    }
    all_scores = db.query(Dataset.readiness_score).all()
    for (score,) in all_scores:
        if score < 25:
            score_buckets["0-24"] += 1
        elif score < 50:
            score_buckets["25-49"] += 1
        elif score < 70:
            score_buckets["50-69"] += 1
        elif score < 85:
            score_buckets["70-84"] += 1
        else:
            score_buckets["85-100"] += 1

    # Top actions by total potential point gain across all datasets
    top_actions_rows = (
        db.query(
            DatasetAction.action_key,
            DatasetAction.title,
            func.sum(DatasetAction.points_gain).label("total_gain"),
            func.count(DatasetAction.id).label("dataset_count"),
        )
        .group_by(DatasetAction.action_key, DatasetAction.title)
        .order_by(func.sum(DatasetAction.points_gain).desc())
        .limit(5)
        .all()
    )
    top_actions = [
        {
            "action_key": row.action_key,
            "title": row.title,
            "total_gain": int(row.total_gain),
            "dataset_count": int(row.dataset_count),
        }
        for row in top_actions_rows
    ]

    # Lowest scoring datasets
    lowest_scoring_rows = (
        db.query(Dataset)
        .order_by(Dataset.readiness_score.asc())
        .limit(5)
        .all()
    )
    lowest_scoring = [
        {
            "id": str(ds.id),
            "display_name": ds.display_name,
            "full_name": ds.full_name,
            "readiness_score": ds.readiness_score,
            "readiness_status": ds.readiness_status,
        }
        for ds in lowest_scoring_rows
    ]

    # Recently scored datasets
    recently_scored_rows = (
        db.query(Dataset)
        .filter(Dataset.last_scored_at.isnot(None))
        .order_by(Dataset.last_scored_at.desc())
        .limit(5)
        .all()
    )
    recently_scored = [
        {
            "id": str(ds.id),
            "display_name": ds.display_name,
            "full_name": ds.full_name,
            "readiness_score": ds.readiness_score,
            "readiness_status": ds.readiness_status,
            "last_scored_at": ds.last_scored_at.isoformat() if ds.last_scored_at else None,
        }
        for ds in recently_scored_rows
    ]

    # Dimension health: average percentage per dimension (measured only)
    dimension_rows = (
        db.query(
            DatasetDimensionScore.dimension_key,
            func.avg(
                DatasetDimensionScore.points_awarded * 100.0 / DatasetDimensionScore.max_points
            ).label("avg_percentage"),
            func.count(DatasetDimensionScore.id).label("count"),
        )
        .filter(DatasetDimensionScore.measured == 1)
        .filter(DatasetDimensionScore.max_points > 0)
        .group_by(DatasetDimensionScore.dimension_key)
        .all()
    )
    dimension_health = {
        row.dimension_key: round(float(row.avg_percentage), 1)
        for row in dimension_rows
    }

    return {
        "total_datasets": total_datasets,
        "average_score": round(float(average_score), 1),
        "status_distribution": status_distribution,
        "score_distribution": score_buckets,
        "top_actions": top_actions,
        "lowest_scoring": lowest_scoring,
        "recently_scored": recently_scored,
        "dimension_health": dimension_health,
    }


@router.get("/trends")
def get_dashboard_trends(
    days: int = Query(30, ge=1, le=365, description="Number of days for trend data"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get daily average score trend over the specified number of days.
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # Get daily average scores
    trend_rows = (
        db.query(
            func.date(DatasetScoreHistory.recorded_at).label("date"),
            func.avg(DatasetScoreHistory.readiness_score).label("avg_score"),
            func.count(DatasetScoreHistory.id).label("count"),
        )
        .filter(DatasetScoreHistory.recorded_at >= cutoff_date)
        .group_by(func.date(DatasetScoreHistory.recorded_at))
        .order_by(func.date(DatasetScoreHistory.recorded_at))
        .all()
    )

    trends = [
        {
            "date": str(row.date),
            "avg_score": round(float(row.avg_score), 1),
            "count": int(row.count),
        }
        for row in trend_rows
    ]

    return {
        "days": days,
        "trends": trends,
    }
