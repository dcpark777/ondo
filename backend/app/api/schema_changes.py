"""
Schema change detection API endpoints.
"""

import hashlib
import json
import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.schemas import (
    SchemaChangeResponse,
    SchemaSnapshotResponse,
    SchemaSnapshotResult,
)
from app.db import get_db
from app.models import (
    Dataset,
    DatasetColumn,
    DatasetWatch,
    Notification,
    SchemaChange,
    SchemaSnapshot,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["schema-changes"])


@router.get(
    "/api/datasets/{dataset_id}/schema/changes",
    response_model=List[SchemaChangeResponse],
)
def list_schema_changes(
    dataset_id: UUID,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """List recent schema changes for a dataset."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    changes = (
        db.query(SchemaChange)
        .filter(SchemaChange.dataset_id == dataset_id)
        .order_by(SchemaChange.detected_at.desc())
        .limit(limit)
        .all()
    )

    return [
        SchemaChangeResponse(
            id=c.id,
            dataset_id=c.dataset_id,
            change_type=c.change_type,
            column_name=c.column_name,
            old_value=c.old_value,
            new_value=c.new_value,
            detected_at=c.detected_at,
        )
        for c in changes
    ]


@router.get(
    "/api/datasets/{dataset_id}/schema/snapshots",
    response_model=List[SchemaSnapshotResponse],
)
def list_schema_snapshots(
    dataset_id: UUID,
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List schema snapshots for a dataset."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    snapshots = (
        db.query(SchemaSnapshot)
        .filter(SchemaSnapshot.dataset_id == dataset_id)
        .order_by(SchemaSnapshot.created_at.desc())
        .limit(limit)
        .all()
    )

    return [
        SchemaSnapshotResponse(
            id=s.id,
            dataset_id=s.dataset_id,
            columns_hash=s.columns_hash,
            column_count=len(s.column_data) if s.column_data else 0,
            created_at=s.created_at,
        )
        for s in snapshots
    ]


@router.post(
    "/api/datasets/{dataset_id}/schema/snapshot",
    response_model=SchemaSnapshotResult,
)
def take_schema_snapshot(
    dataset_id: UUID,
    db: Session = Depends(get_db),
):
    """Take a schema snapshot and detect changes from previous snapshot."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # 1. Get current dataset columns from DB
    columns = (
        db.query(DatasetColumn)
        .filter(DatasetColumn.dataset_id == dataset_id)
        .all()
    )

    # 2. Build column data sorted by name
    column_data = sorted(
        [
            {
                "name": col.name,
                "type": col.type,
                "nullable": bool(col.nullable) if col.nullable is not None else None,
                "description": col.description,
            }
            for col in columns
        ],
        key=lambda c: c["name"],
    )

    # 3. Hash the column data with SHA256
    columns_hash = hashlib.sha256(
        json.dumps(column_data, sort_keys=True).encode()
    ).hexdigest()

    # 4. Compare with most recent snapshot
    previous_snapshot = (
        db.query(SchemaSnapshot)
        .filter(SchemaSnapshot.dataset_id == dataset_id)
        .order_by(SchemaSnapshot.created_at.desc())
        .first()
    )

    changes: List[SchemaChange] = []

    if previous_snapshot and previous_snapshot.columns_hash != columns_hash:
        changes = _compute_changes(
            dataset_id, previous_snapshot.column_data, column_data, db
        )
    elif previous_snapshot is None and len(column_data) > 0:
        # First snapshot with columns — record all as added
        for col in column_data:
            change = SchemaChange(
                dataset_id=dataset_id,
                change_type="column_added",
                column_name=col["name"],
                old_value=None,
                new_value=col["type"] or "unknown",
            )
            db.add(change)
            changes.append(change)

    # 5. Create notifications for watchers
    if changes:
        _notify_watchers(db, dataset_id, dataset.display_name, changes)

    # 6. Save the new snapshot
    snapshot = SchemaSnapshot(
        dataset_id=dataset_id,
        columns_hash=columns_hash,
        column_data=column_data,
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)

    # Refresh changes to get IDs
    for change in changes:
        db.refresh(change)

    logger.info(
        "Schema snapshot taken for dataset %s: %d changes detected",
        dataset_id,
        len(changes),
    )

    return SchemaSnapshotResult(
        snapshot_id=snapshot.id,
        changes_detected=len(changes),
        changes=[
            SchemaChangeResponse(
                id=c.id,
                dataset_id=c.dataset_id,
                change_type=c.change_type,
                column_name=c.column_name,
                old_value=c.old_value,
                new_value=c.new_value,
                detected_at=c.detected_at,
            )
            for c in changes
        ],
    )


def _compute_changes(
    dataset_id: UUID,
    old_column_data: list,
    new_column_data: list,
    db: Session,
) -> List[SchemaChange]:
    """Compute the diff between old and new column data."""
    old_by_name = {col["name"]: col for col in old_column_data}
    new_by_name = {col["name"]: col for col in new_column_data}

    old_names = set(old_by_name.keys())
    new_names = set(new_by_name.keys())

    changes: List[SchemaChange] = []

    # Added columns
    for name in sorted(new_names - old_names):
        change = SchemaChange(
            dataset_id=dataset_id,
            change_type="column_added",
            column_name=name,
            old_value=None,
            new_value=new_by_name[name].get("type") or "unknown",
        )
        db.add(change)
        changes.append(change)

    # Removed columns
    for name in sorted(old_names - new_names):
        change = SchemaChange(
            dataset_id=dataset_id,
            change_type="column_removed",
            column_name=name,
            old_value=old_by_name[name].get("type") or "unknown",
            new_value=None,
        )
        db.add(change)
        changes.append(change)

    # Changed columns (type or nullable)
    for name in sorted(old_names & new_names):
        old_col = old_by_name[name]
        new_col = new_by_name[name]

        if old_col.get("type") != new_col.get("type"):
            change = SchemaChange(
                dataset_id=dataset_id,
                change_type="column_type_changed",
                column_name=name,
                old_value=old_col.get("type") or "unknown",
                new_value=new_col.get("type") or "unknown",
            )
            db.add(change)
            changes.append(change)

        if old_col.get("nullable") != new_col.get("nullable"):
            change = SchemaChange(
                dataset_id=dataset_id,
                change_type="column_nullable_changed",
                column_name=name,
                old_value=str(old_col.get("nullable")),
                new_value=str(new_col.get("nullable")),
            )
            db.add(change)
            changes.append(change)

    return changes


def _notify_watchers(
    db: Session,
    dataset_id: UUID,
    dataset_name: str,
    changes: List[SchemaChange],
) -> None:
    """Create notifications for all watchers of this dataset."""
    watchers = (
        db.query(DatasetWatch)
        .filter(DatasetWatch.dataset_id == dataset_id)
        .all()
    )

    if not watchers:
        return

    # Build a summary message
    change_summary_parts = []
    for change in changes[:5]:  # Limit to first 5 in the message
        if change.change_type == "column_added":
            change_summary_parts.append(f"+ {change.column_name} ({change.new_value})")
        elif change.change_type == "column_removed":
            change_summary_parts.append(f"- {change.column_name}")
        elif change.change_type == "column_type_changed":
            change_summary_parts.append(
                f"~ {change.column_name}: {change.old_value} -> {change.new_value}"
            )
        elif change.change_type == "column_nullable_changed":
            change_summary_parts.append(
                f"? {change.column_name}: nullable {change.old_value} -> {change.new_value}"
            )

    remaining = len(changes) - 5
    if remaining > 0:
        change_summary_parts.append(f"...and {remaining} more")

    message = f"Schema changes detected:\n" + "\n".join(change_summary_parts)

    for watcher in watchers:
        notification = Notification(
            dataset_id=dataset_id,
            user_id=watcher.user_id,
            notification_type="schema_change",
            title=f"Schema changed: {dataset_name}",
            message=message,
        )
        db.add(notification)

    logger.info(
        "Created %d notifications for schema changes on dataset %s",
        len(watchers),
        dataset_id,
    )
