"""Usage metrics API endpoints."""
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Dataset, DatasetView

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["usage"])


@router.post("/datasets/{dataset_id}/views", status_code=201)
def record_view(
    dataset_id: UUID,
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db),
):
    """Record a dataset view."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    view = DatasetView(dataset_id=dataset_id, user_id=user_id, viewed_at=datetime.utcnow())
    db.add(view)
    db.commit()
    return {"recorded": True}


@router.get("/datasets/{dataset_id}/views/stats")
def get_view_stats(
    dataset_id: UUID,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """Get view statistics for a dataset."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    since = datetime.utcnow() - timedelta(days=days)

    total_views = (
        db.query(func.count(DatasetView.id))
        .filter(DatasetView.dataset_id == dataset_id, DatasetView.viewed_at >= since)
        .scalar()
    )

    unique_viewers = (
        db.query(func.count(func.distinct(DatasetView.user_id)))
        .filter(DatasetView.dataset_id == dataset_id, DatasetView.viewed_at >= since)
        .scalar()
    )

    # Daily view counts
    daily_views = (
        db.query(
            func.date_trunc('day', DatasetView.viewed_at).label('day'),
            func.count(DatasetView.id).label('count'),
        )
        .filter(DatasetView.dataset_id == dataset_id, DatasetView.viewed_at >= since)
        .group_by(func.date_trunc('day', DatasetView.viewed_at))
        .order_by(func.date_trunc('day', DatasetView.viewed_at))
        .all()
    )

    # Recent viewers
    recent_viewers = (
        db.query(DatasetView.user_id, func.max(DatasetView.viewed_at).label('last_viewed'))
        .filter(DatasetView.dataset_id == dataset_id, DatasetView.viewed_at >= since)
        .group_by(DatasetView.user_id)
        .order_by(func.max(DatasetView.viewed_at).desc())
        .limit(10)
        .all()
    )

    return {
        "dataset_id": str(dataset_id),
        "days": days,
        "total_views": total_views or 0,
        "unique_viewers": unique_viewers or 0,
        "daily_views": [
            {"date": row.day.isoformat() if row.day else None, "count": row.count}
            for row in daily_views
        ],
        "recent_viewers": [
            {"user_id": row.user_id, "last_viewed": row.last_viewed.isoformat() if row.last_viewed else None}
            for row in recent_viewers
        ],
    }


@router.get("/datasets/popular")
def get_popular_datasets(
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Get most viewed datasets."""
    since = datetime.utcnow() - timedelta(days=days)

    popular = (
        db.query(
            DatasetView.dataset_id,
            func.count(DatasetView.id).label('view_count'),
            func.count(func.distinct(DatasetView.user_id)).label('unique_viewers'),
        )
        .filter(DatasetView.viewed_at >= since)
        .group_by(DatasetView.dataset_id)
        .order_by(func.count(DatasetView.id).desc())
        .limit(limit)
        .all()
    )

    if not popular:
        return {"days": days, "datasets": []}

    dataset_ids = [row.dataset_id for row in popular]
    datasets = db.query(Dataset).filter(Dataset.id.in_(dataset_ids)).all()
    ds_map = {ds.id: ds for ds in datasets}

    results = []
    for row in popular:
        ds = ds_map.get(row.dataset_id)
        if ds:
            results.append({
                "id": str(ds.id),
                "full_name": ds.full_name,
                "display_name": ds.display_name,
                "readiness_score": ds.readiness_score,
                "readiness_status": ds.readiness_status,
                "view_count": row.view_count,
                "unique_viewers": row.unique_viewers,
            })

    return {"days": days, "datasets": results}
