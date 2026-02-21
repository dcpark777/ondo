"""Bulk operations API endpoints."""
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Dataset, DatasetTag

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/bulk", tags=["bulk"])


class BulkTagRequest(BaseModel):
    dataset_ids: List[UUID]
    tags: List[str]
    mode: str = Field(default="add", description="add, remove, or replace")


class BulkClassificationRequest(BaseModel):
    dataset_ids: List[UUID]
    classification: Optional[str] = None
    domain: Optional[str] = None


class BulkOperationResult(BaseModel):
    updated: int
    dataset_ids: List[str]


@router.post("/tags", response_model=BulkOperationResult)
def bulk_update_tags(
    body: BulkTagRequest,
    db: Session = Depends(get_db),
):
    """Bulk add, remove, or replace tags on multiple datasets."""
    if not body.dataset_ids:
        raise HTTPException(status_code=400, detail="No dataset IDs provided")

    if body.mode not in ("add", "remove", "replace"):
        raise HTTPException(status_code=400, detail="mode must be 'add', 'remove', or 'replace'")

    # Verify datasets exist
    datasets = db.query(Dataset).filter(Dataset.id.in_(body.dataset_ids)).all()
    found_ids = {ds.id for ds in datasets}

    updated_ids = []
    for dataset_id in body.dataset_ids:
        if dataset_id not in found_ids:
            continue

        if body.mode == "replace":
            db.query(DatasetTag).filter(DatasetTag.dataset_id == dataset_id).delete()
            for tag in body.tags:
                tag = tag.strip()
                if tag:
                    db.add(DatasetTag(dataset_id=dataset_id, tag=tag))
        elif body.mode == "add":
            existing_tags = {
                t.tag for t in db.query(DatasetTag).filter(DatasetTag.dataset_id == dataset_id).all()
            }
            for tag in body.tags:
                tag = tag.strip()
                if tag and tag not in existing_tags:
                    db.add(DatasetTag(dataset_id=dataset_id, tag=tag))
        elif body.mode == "remove":
            for tag in body.tags:
                db.query(DatasetTag).filter(
                    DatasetTag.dataset_id == dataset_id, DatasetTag.tag == tag.strip()
                ).delete()

        updated_ids.append(str(dataset_id))

    db.commit()
    logger.info("Bulk %s tags on %d datasets", body.mode, len(updated_ids))
    return BulkOperationResult(updated=len(updated_ids), dataset_ids=updated_ids)


@router.post("/classification", response_model=BulkOperationResult)
def bulk_update_classification(
    body: BulkClassificationRequest,
    db: Session = Depends(get_db),
):
    """Bulk update classification and/or domain on multiple datasets."""
    if not body.dataset_ids:
        raise HTTPException(status_code=400, detail="No dataset IDs provided")

    if body.classification is not None:
        valid = ["public", "internal", "confidential", "restricted", ""]
        if body.classification not in valid:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid classification. Must be one of: {', '.join(v for v in valid if v)}",
            )

    datasets = db.query(Dataset).filter(Dataset.id.in_(body.dataset_ids)).all()

    updated_ids = []
    for ds in datasets:
        if body.classification is not None:
            ds.classification = body.classification or None
        if body.domain is not None:
            ds.domain = body.domain or None
        updated_ids.append(str(ds.id))

    db.commit()
    logger.info("Bulk classification update on %d datasets", len(updated_ids))
    return BulkOperationResult(updated=len(updated_ids), dataset_ids=updated_ids)
