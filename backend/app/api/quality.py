"""
Quality rules API endpoints.
"""

import logging
from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.api.schemas import (
    BatchExecutionRequest,
    QualityRuleCreate,
    QualityRuleExecutionCreate,
    QualityRuleExecutionResponse,
    QualityRuleResponse,
    QualityRuleUpdate,
)
from app.db import get_db
from app.models import Dataset, QualityRule, QualityRuleExecution

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/datasets", tags=["quality"])


def _rule_to_response(
    rule: QualityRule,
    latest_execution: QualityRuleExecution | None = None,
) -> QualityRuleResponse:
    """Convert a QualityRule model to a response schema."""
    latest_exec_resp = None
    if latest_execution:
        latest_exec_resp = QualityRuleExecutionResponse(
            id=latest_execution.id,
            rule_id=latest_execution.rule_id,
            dataset_id=latest_execution.dataset_id,
            passed=bool(latest_execution.passed),
            records_checked=latest_execution.records_checked,
            records_failed=latest_execution.records_failed,
            error_message=latest_execution.error_message,
            executed_at=latest_execution.executed_at,
        )

    return QualityRuleResponse(
        id=rule.id,
        dataset_id=rule.dataset_id,
        name=rule.name,
        description=rule.description,
        rule_type=rule.rule_type,
        column_name=rule.column_name,
        parameters=rule.parameters,
        severity=rule.severity,
        enabled=bool(rule.enabled),
        created_at=rule.created_at,
        created_by=rule.created_by,
        latest_execution=latest_exec_resp,
    )


def _get_dataset_or_404(db: Session, dataset_id: UUID) -> Dataset:
    """Get dataset by ID or raise 404."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset


def _get_rule_or_404(
    db: Session, dataset_id: UUID, rule_id: UUID
) -> QualityRule:
    """Get quality rule by ID within dataset, or raise 404."""
    rule = (
        db.query(QualityRule)
        .filter(QualityRule.id == rule_id, QualityRule.dataset_id == dataset_id)
        .first()
    )
    if not rule:
        raise HTTPException(status_code=404, detail="Quality rule not found")
    return rule


@router.get(
    "/{dataset_id}/quality-rules",
    response_model=List[QualityRuleResponse],
)
def list_quality_rules(
    dataset_id: UUID,
    db: Session = Depends(get_db),
) -> List[QualityRuleResponse]:
    """List all quality rules for a dataset with their latest execution status."""
    _get_dataset_or_404(db, dataset_id)

    # Subquery to get the latest execution per rule
    latest_exec_subq = (
        db.query(
            QualityRuleExecution.rule_id,
            func.max(QualityRuleExecution.executed_at).label("max_executed_at"),
        )
        .filter(QualityRuleExecution.dataset_id == dataset_id)
        .group_by(QualityRuleExecution.rule_id)
        .subquery()
    )

    # Get all rules for the dataset
    rules = (
        db.query(QualityRule)
        .filter(QualityRule.dataset_id == dataset_id)
        .order_by(QualityRule.created_at)
        .all()
    )

    # Get latest executions for all rules in this dataset
    latest_executions = (
        db.query(QualityRuleExecution)
        .join(
            latest_exec_subq,
            (QualityRuleExecution.rule_id == latest_exec_subq.c.rule_id)
            & (
                QualityRuleExecution.executed_at
                == latest_exec_subq.c.max_executed_at
            ),
        )
        .all()
    )

    # Build a map of rule_id -> latest execution
    exec_map = {exe.rule_id: exe for exe in latest_executions}

    return [
        _rule_to_response(rule, exec_map.get(rule.id))
        for rule in rules
    ]


@router.post(
    "/{dataset_id}/quality-rules",
    response_model=QualityRuleResponse,
    status_code=201,
)
def create_quality_rule(
    dataset_id: UUID,
    body: QualityRuleCreate,
    db: Session = Depends(get_db),
) -> QualityRuleResponse:
    """Create a new quality rule for a dataset."""
    _get_dataset_or_404(db, dataset_id)

    valid_rule_types = {
        "not_null", "unique", "range", "regex", "custom_sql", "accepted_values"
    }
    if body.rule_type not in valid_rule_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid rule_type. Must be one of: {', '.join(sorted(valid_rule_types))}",
        )

    valid_severities = {"error", "warning", "info"}
    if body.severity not in valid_severities:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid severity. Must be one of: {', '.join(sorted(valid_severities))}",
        )

    rule = QualityRule(
        dataset_id=dataset_id,
        name=body.name,
        description=body.description,
        rule_type=body.rule_type,
        column_name=body.column_name,
        parameters=body.parameters,
        severity=body.severity,
        enabled=1 if body.enabled else 0,
        created_by=body.created_by,
        created_at=datetime.utcnow(),
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    logger.info("Created quality rule %s for dataset %s", rule.id, dataset_id)
    return _rule_to_response(rule)


@router.put(
    "/{dataset_id}/quality-rules/{rule_id}",
    response_model=QualityRuleResponse,
)
def update_quality_rule(
    dataset_id: UUID,
    rule_id: UUID,
    body: QualityRuleUpdate,
    db: Session = Depends(get_db),
) -> QualityRuleResponse:
    """Update an existing quality rule."""
    rule = _get_rule_or_404(db, dataset_id, rule_id)

    if body.rule_type is not None:
        valid_rule_types = {
            "not_null", "unique", "range", "regex", "custom_sql", "accepted_values"
        }
        if body.rule_type not in valid_rule_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid rule_type. Must be one of: {', '.join(sorted(valid_rule_types))}",
            )
        rule.rule_type = body.rule_type

    if body.severity is not None:
        valid_severities = {"error", "warning", "info"}
        if body.severity not in valid_severities:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid severity. Must be one of: {', '.join(sorted(valid_severities))}",
            )
        rule.severity = body.severity

    if body.name is not None:
        rule.name = body.name
    if body.description is not None:
        rule.description = body.description
    if body.column_name is not None:
        rule.column_name = body.column_name
    if body.parameters is not None:
        rule.parameters = body.parameters
    if body.enabled is not None:
        rule.enabled = 1 if body.enabled else 0

    db.commit()
    db.refresh(rule)
    logger.info("Updated quality rule %s", rule_id)

    # Fetch latest execution
    latest_exec = (
        db.query(QualityRuleExecution)
        .filter(QualityRuleExecution.rule_id == rule_id)
        .order_by(desc(QualityRuleExecution.executed_at))
        .first()
    )

    return _rule_to_response(rule, latest_exec)


@router.delete(
    "/{dataset_id}/quality-rules/{rule_id}",
    status_code=204,
)
def delete_quality_rule(
    dataset_id: UUID,
    rule_id: UUID,
    db: Session = Depends(get_db),
) -> None:
    """Delete a quality rule and all its execution history."""
    rule = _get_rule_or_404(db, dataset_id, rule_id)
    db.delete(rule)
    db.commit()
    logger.info("Deleted quality rule %s from dataset %s", rule_id, dataset_id)


@router.post(
    "/{dataset_id}/quality-rules/{rule_id}/execute",
    response_model=QualityRuleExecutionResponse,
    status_code=201,
)
def record_execution(
    dataset_id: UUID,
    rule_id: UUID,
    body: QualityRuleExecutionCreate,
    db: Session = Depends(get_db),
) -> QualityRuleExecutionResponse:
    """Record an execution result for a quality rule."""
    _get_dataset_or_404(db, dataset_id)
    _get_rule_or_404(db, dataset_id, rule_id)

    execution = QualityRuleExecution(
        rule_id=rule_id,
        dataset_id=dataset_id,
        passed=1 if body.passed else 0,
        records_checked=body.records_checked,
        records_failed=body.records_failed,
        error_message=body.error_message,
        executed_at=datetime.utcnow(),
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)
    logger.info("Recorded execution for rule %s: passed=%s", rule_id, body.passed)

    return QualityRuleExecutionResponse(
        id=execution.id,
        rule_id=execution.rule_id,
        dataset_id=execution.dataset_id,
        passed=bool(execution.passed),
        records_checked=execution.records_checked,
        records_failed=execution.records_failed,
        error_message=execution.error_message,
        executed_at=execution.executed_at,
    )


@router.post(
    "/{dataset_id}/quality-rules/execute-batch",
    response_model=List[QualityRuleExecutionResponse],
    status_code=201,
)
def record_batch_execution(
    dataset_id: UUID,
    body: BatchExecutionRequest,
    db: Session = Depends(get_db),
) -> List[QualityRuleExecutionResponse]:
    """Record execution results for multiple quality rules at once."""
    _get_dataset_or_404(db, dataset_id)

    results: list[QualityRuleExecutionResponse] = []
    now = datetime.utcnow()

    for item in body.executions:
        # Validate rule exists for this dataset
        rule = (
            db.query(QualityRule)
            .filter(
                QualityRule.id == item.rule_id,
                QualityRule.dataset_id == dataset_id,
            )
            .first()
        )
        if not rule:
            raise HTTPException(
                status_code=404,
                detail=f"Quality rule {item.rule_id} not found for dataset {dataset_id}",
            )

        execution = QualityRuleExecution(
            rule_id=item.rule_id,
            dataset_id=dataset_id,
            passed=1 if item.passed else 0,
            records_checked=item.records_checked,
            records_failed=item.records_failed,
            error_message=item.error_message,
            executed_at=now,
        )
        db.add(execution)
        db.flush()

        results.append(
            QualityRuleExecutionResponse(
                id=execution.id,
                rule_id=execution.rule_id,
                dataset_id=execution.dataset_id,
                passed=bool(execution.passed),
                records_checked=execution.records_checked,
                records_failed=execution.records_failed,
                error_message=execution.error_message,
                executed_at=execution.executed_at,
            )
        )

    db.commit()
    logger.info(
        "Recorded %d batch executions for dataset %s",
        len(results),
        dataset_id,
    )
    return results


@router.get(
    "/{dataset_id}/quality-rules/{rule_id}/history",
    response_model=List[QualityRuleExecutionResponse],
)
def get_execution_history(
    dataset_id: UUID,
    rule_id: UUID,
    limit: int = 30,
    db: Session = Depends(get_db),
) -> List[QualityRuleExecutionResponse]:
    """Get execution history for a quality rule."""
    _get_rule_or_404(db, dataset_id, rule_id)

    executions = (
        db.query(QualityRuleExecution)
        .filter(
            QualityRuleExecution.rule_id == rule_id,
            QualityRuleExecution.dataset_id == dataset_id,
        )
        .order_by(desc(QualityRuleExecution.executed_at))
        .limit(limit)
        .all()
    )

    return [
        QualityRuleExecutionResponse(
            id=exe.id,
            rule_id=exe.rule_id,
            dataset_id=exe.dataset_id,
            passed=bool(exe.passed),
            records_checked=exe.records_checked,
            records_failed=exe.records_failed,
            error_message=exe.error_message,
            executed_at=exe.executed_at,
        )
        for exe in executions
    ]
