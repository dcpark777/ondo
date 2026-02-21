"""
Audit logging service.
"""

import logging
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import AuditLog

logger = logging.getLogger(__name__)


def log_audit(
    db: Session,
    dataset_id: Optional[UUID],
    action: str,
    actor: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Create an audit log entry.

    Args:
        db: Database session
        dataset_id: Optional dataset UUID (nullable for global events)
        action: Action identifier (e.g., 'dataset.scored', 'owner.updated')
        actor: User ID or 'system'
        details: Action-specific metadata as JSON
    """
    entry = AuditLog(
        dataset_id=dataset_id,
        action=action,
        actor=actor,
        details=details,
    )
    db.add(entry)
    db.flush()
    logger.info("Audit log: %s on dataset %s by %s", action, dataset_id, actor or "system")
