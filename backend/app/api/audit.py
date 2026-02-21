"""
Audit log API endpoints.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.schemas import AuditLogListResponse, AuditLogResponse
from app.db import get_db
from app.models import AuditLog, Dataset

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("", response_model=AuditLogListResponse)
def list_audit_log(
    dataset_id: Optional[UUID] = Query(None, description="Filter by dataset ID"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    actor: Optional[str] = Query(None, description="Filter by actor"),
    limit: int = Query(50, ge=1, le=200, description="Max results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db),
):
    """
    List audit log entries with optional filters.
    """
    query = db.query(AuditLog)

    if dataset_id is not None:
        query = query.filter(AuditLog.dataset_id == dataset_id)
    if action is not None:
        query = query.filter(AuditLog.action == action)
    if actor is not None:
        query = query.filter(AuditLog.actor == actor)

    total = query.count()

    entries = (
        query.order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return AuditLogListResponse(
        entries=[
            AuditLogResponse(
                id=e.id,
                dataset_id=e.dataset_id,
                action=e.action,
                actor=e.actor,
                details=e.details,
                created_at=e.created_at,
            )
            for e in entries
        ],
        total=total,
    )


@router.get("/datasets/{dataset_id}", response_model=AuditLogListResponse)
def get_dataset_audit_log(
    dataset_id: UUID,
    limit: int = Query(50, ge=1, le=200, description="Max results to return"),
    db: Session = Depends(get_db),
):
    """
    List audit log entries for a specific dataset.
    """
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    query = db.query(AuditLog).filter(AuditLog.dataset_id == dataset_id)
    total = query.count()

    entries = (
        query.order_by(AuditLog.created_at.desc())
        .limit(limit)
        .all()
    )

    return AuditLogListResponse(
        entries=[
            AuditLogResponse(
                id=e.id,
                dataset_id=e.dataset_id,
                action=e.action,
                actor=e.actor,
                details=e.details,
                created_at=e.created_at,
            )
            for e in entries
        ],
        total=total,
    )
