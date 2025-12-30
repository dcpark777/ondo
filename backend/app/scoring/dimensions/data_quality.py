"""
Data Quality Signals dimension scorer.

Total: 20 points
- +10 freshness/volume checks exist (v1: presence flags; dbt tests count)
- +5 SLA defined (v1: use intended_use or metadata; otherwise action item)
- +5 no unresolved failures last 30 days (v1: omit unless you build incident ingestion)
"""

from typing import Dict, List

from app.scoring.types import Action, DimensionScore, Reason


def score_data_quality(
    metadata: Dict,
) -> tuple[DimensionScore, List[Reason], List[Action]]:
    """
    Score the Data Quality Signals dimension.

    Args:
        metadata: Dataset metadata dict with keys:
            - has_freshness_checks: Optional[bool] - presence of freshness checks
            - has_volume_checks: Optional[bool] - presence of volume checks
            - dbt_test_count: Optional[int] - number of dbt tests
            - intended_use: Optional[str] - can indicate SLA requirements
            - has_sla: Optional[bool] - explicit SLA flag
            - unresolved_failures_30d: Optional[int] - failures in last 30 days (v1: omit)

    Returns:
        Tuple of (DimensionScore, reasons, actions)
    """
    max_points = 20
    points_awarded = 0
    reasons: List[Reason] = []
    actions: List[Action] = []

    # +10 freshness/volume checks exist
    has_freshness = metadata.get("has_freshness_checks", False)
    has_volume = metadata.get("has_volume_checks", False)
    dbt_test_count = metadata.get("dbt_test_count", 0)

    has_quality_checks = has_freshness or has_volume or (dbt_test_count > 0)

    if has_quality_checks:
        points_awarded += 10
    else:
        reasons.append(
            Reason(
                dimension_key="data_quality",
                reason_code="missing_quality_checks",
                message="No freshness or volume checks configured",
                points_lost=10,
            )
        )
        actions.append(
            Action(
                action_key="add_quality_checks",
                title="Add data quality checks",
                description="Configure freshness and volume checks (e.g., dbt tests) to monitor data quality",
                points_gain=10,
                dimension_key="data_quality",
            )
        )

    # +5 SLA defined
    has_sla = metadata.get("has_sla", False)
    intended_use = metadata.get("intended_use")
    # If intended_use is present and meaningful, consider it a proxy for SLA awareness
    has_sla_proxy = bool(intended_use and intended_use.strip())

    if has_sla or has_sla_proxy:
        points_awarded += 5
    else:
        reasons.append(
            Reason(
                dimension_key="data_quality",
                reason_code="missing_sla",
                message="No SLA or intended use defined",
                points_lost=5,
            )
        )
        actions.append(
            Action(
                action_key="define_sla",
                title="Define data SLA",
                description="Define service level agreement or intended use cases for this dataset",
                points_gain=5,
                dimension_key="data_quality",
            )
        )

    # +5 no unresolved failures last 30 days
    # v1: omit unless incident ingestion is built
    # We'll check if the field exists and is > 0, but won't penalize if not provided
    unresolved_failures = metadata.get("unresolved_failures_30d")
    if unresolved_failures is not None:
        if unresolved_failures == 0:
            points_awarded += 5
        else:
            reasons.append(
                Reason(
                    dimension_key="data_quality",
                    reason_code="unresolved_failures",
                    message=f"{unresolved_failures} unresolved data quality failures in last 30 days",
                    points_lost=5,
                )
            )
            actions.append(
                Action(
                    action_key="resolve_failures",
                    title="Resolve data quality failures",
                    description=f"Investigate and resolve {unresolved_failures} outstanding data quality failures",
                    points_gain=5,
                    dimension_key="data_quality",
                )
            )
    # If not provided, don't penalize (as per v1 requirements)

    dimension_score = DimensionScore(
        dimension_key="data_quality",
        points_awarded=points_awarded,
        max_points=max_points,
    )

    return dimension_score, reasons, actions

