"""
Notifications and watches API endpoints.
"""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.schemas import NotificationResponse
from app.db import get_db
from app.models import Dataset, DatasetWatch, Notification

logger = logging.getLogger(__name__)

router = APIRouter(tags=["notifications"])


# Watch endpoints
@router.get("/api/datasets/{dataset_id}/watch")
def check_watch(
    dataset_id: UUID,
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db),
):
    """Check if user is watching a dataset."""
    watch = (
        db.query(DatasetWatch)
        .filter(
            DatasetWatch.dataset_id == dataset_id,
            DatasetWatch.user_id == user_id,
        )
        .first()
    )
    return {"watching": watch is not None}


@router.post("/api/datasets/{dataset_id}/watch")
def start_watching(
    dataset_id: UUID,
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db),
):
    """Start watching a dataset."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    existing = (
        db.query(DatasetWatch)
        .filter(
            DatasetWatch.dataset_id == dataset_id,
            DatasetWatch.user_id == user_id,
        )
        .first()
    )
    if existing:
        return {"watching": True}

    watch = DatasetWatch(dataset_id=dataset_id, user_id=user_id)
    db.add(watch)
    db.commit()

    logger.info("User %s started watching dataset %s", user_id, dataset_id)
    return {"watching": True}


@router.delete("/api/datasets/{dataset_id}/watch")
def stop_watching(
    dataset_id: UUID,
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db),
):
    """Stop watching a dataset."""
    watch = (
        db.query(DatasetWatch)
        .filter(
            DatasetWatch.dataset_id == dataset_id,
            DatasetWatch.user_id == user_id,
        )
        .first()
    )
    if watch:
        db.delete(watch)
        db.commit()
        logger.info("User %s stopped watching dataset %s", user_id, dataset_id)

    return {"watching": False}


# Notification endpoints
@router.get("/api/notifications", response_model=List[NotificationResponse])
def list_notifications(
    user_id: str = Query(..., description="User ID"),
    unread_only: bool = Query(False, description="Only show unread"),
    db: Session = Depends(get_db),
):
    """List notifications for a user."""
    query = db.query(Notification).filter(Notification.user_id == user_id)

    if unread_only:
        query = query.filter(Notification.read == 0)

    notifications = query.order_by(Notification.created_at.desc()).limit(50).all()

    return [
        NotificationResponse(
            id=n.id,
            dataset_id=n.dataset_id,
            user_id=n.user_id,
            notification_type=n.notification_type,
            title=n.title,
            message=n.message,
            read=n.read == 1,
            created_at=n.created_at,
        )
        for n in notifications
    ]


@router.post("/api/notifications/{notification_id}/read")
def mark_as_read(
    notification_id: UUID,
    db: Session = Depends(get_db),
):
    """Mark a notification as read."""
    notification = (
        db.query(Notification).filter(Notification.id == notification_id).first()
    )
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.read = 1
    db.commit()
    return {"status": "read"}


@router.post("/api/notifications/read-all")
def mark_all_as_read(
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db),
):
    """Mark all notifications as read for a user."""
    db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.read == 0,
    ).update({Notification.read: 1})
    db.commit()

    logger.info("Marked all notifications as read for user %s", user_id)
    return {"status": "ok"}
