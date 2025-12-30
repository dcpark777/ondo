"""
Main scoring engine orchestrator.

Implements the deterministic readiness scoring algorithm.
"""

from typing import Dict

from app.scoring.dimensions import (
    score_data_quality,
    score_documentation,
    score_operational,
    score_ownership,
    score_schema_hygiene,
    score_stability,
)
from app.scoring.types import Action, DimensionScore, Reason, ScoreResult


def score_dataset(metadata: Dict) -> ScoreResult:
    """
    Score a dataset for readiness.

    This is a pure function that takes dataset metadata and returns
    a complete scoring result including total score, status, dimension
    breakdowns, reasons for point losses, and recommended actions.

    Args:
        metadata: Dictionary containing dataset metadata. Expected keys:
            - owner_name: Optional[str]
            - owner_contact: Optional[str]
            - description: Optional[str]
            - columns: Optional[List[Dict]] - column metadata
            - intended_use: Optional[str]
            - limitations: Optional[str]
            - has_freshness_checks: Optional[bool]
            - has_volume_checks: Optional[bool]
            - dbt_test_count: Optional[int]
            - has_sla: Optional[bool]
            - unresolved_failures_30d: Optional[int]
            - breaking_changes_30d: Optional[int]
            - has_release_notes: Optional[bool]
            - has_versioning: Optional[bool]
            - backward_compatible: Optional[bool]

    Returns:
        ScoreResult containing:
            - total_score: int (0-100)
            - status: ReadinessStatus
            - dimension_scores: List[DimensionScore]
            - reasons: List[Reason]
            - actions: List[Action]

    Example:
        >>> metadata = {
        ...     "owner_name": "Data Team",
        ...     "owner_contact": "#data-team",
        ...     "description": "User events table",
        ...     "columns": [
        ...         {"name": "user_id", "description": "User identifier"},
        ...         {"name": "event_type", "description": "Type of event"}
        ...     ],
        ...     "intended_use": "Analytics, experimentation",
        ...     "limitations": "Data delayed by 1 hour"
        ... }
        >>> result = score_dataset(metadata)
        >>> result.total_score
        85
        >>> result.status
        <ReadinessStatus.GOLD: 'gold'>
    """
    # Score each dimension
    ownership_score, ownership_reasons, ownership_actions = score_ownership(metadata)
    doc_score, doc_reasons, doc_actions = score_documentation(metadata)
    schema_score, schema_reasons, schema_actions = score_schema_hygiene(metadata)
    quality_score, quality_reasons, quality_actions = score_data_quality(metadata)
    stability_score, stability_reasons, stability_actions = score_stability(metadata)
    operational_score, operational_reasons, operational_actions = score_operational(
        metadata
    )

    # Collect all dimension scores
    dimension_scores = [
        ownership_score,
        doc_score,
        schema_score,
        quality_score,
        stability_score,
        operational_score,
    ]

    # Calculate total score
    total_score = sum(dim.points_awarded for dim in dimension_scores)

    # Determine status
    status = ScoreResult.determine_status(total_score)

    # Collect all reasons and actions
    all_reasons = (
        ownership_reasons
        + doc_reasons
        + schema_reasons
        + quality_reasons
        + stability_reasons
        + operational_reasons
    )

    all_actions = (
        ownership_actions
        + doc_actions
        + schema_actions
        + quality_actions
        + stability_actions
        + operational_actions
    )

    return ScoreResult(
        total_score=total_score,
        status=status,
        dimension_scores=dimension_scores,
        reasons=all_reasons,
        actions=all_actions,
    )

