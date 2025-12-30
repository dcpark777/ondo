"""
Schema Hygiene dimension scorer.

Total: 15 points
- +5 naming conventions pass (snake_case, consistent)
- +5 nullable ratio under threshold (v1: use "unknown" if nullability not available; don't penalize)
- +5 no "legacy"/unused columns (heuristic: columns ending _tmp, _old, deprecated)
"""

import re
from typing import Dict, List

from app.scoring.types import Action, DimensionScore, Reason


def score_schema_hygiene(
    metadata: Dict,
) -> tuple[DimensionScore, List[Reason], List[Action]]:
    """
    Score the Schema Hygiene dimension.

    Args:
        metadata: Dataset metadata dict with keys:
            - columns: Optional[List[Dict]] - list of column metadata
                Each column dict may have:
                - name: str
                - nullable: Optional[bool] - if None, we don't penalize

    Returns:
        Tuple of (DimensionScore, reasons, actions)
    """
    max_points = 15
    points_awarded = 0
    reasons: List[Reason] = []
    actions: List[Action] = []

    columns = metadata.get("columns", [])

    if not columns:
        # No column information - return zero score but no penalties
        dimension_score = DimensionScore(
            dimension_key="schema_hygiene",
            points_awarded=0,
            max_points=max_points,
        )
        return dimension_score, reasons, actions

    # +5 naming conventions pass (snake_case, consistent)
    naming_issues = []
    snake_case_pattern = re.compile(r"^[a-z][a-z0-9_]*$")

    for col in columns:
        col_name = col.get("name", "")
        if col_name and not snake_case_pattern.match(col_name):
            naming_issues.append(col_name)

    if not naming_issues:
        points_awarded += 5
    else:
        reasons.append(
            Reason(
                dimension_key="schema_hygiene",
                reason_code="naming_convention_violations",
                message=f"{len(naming_issues)} columns violate snake_case naming (e.g., {naming_issues[0] if naming_issues else 'N/A'})",
                points_lost=5,
            )
        )
        actions.append(
            Action(
                action_key="fix_naming",
                title="Fix column naming conventions",
                description=f"Rename {len(naming_issues)} columns to follow snake_case convention",
                points_gain=5,
                dimension_key="schema_hygiene",
            )
        )

    # +5 nullable ratio under threshold (v1: use "unknown" if nullability not available; don't penalize)
    nullable_info_available = any(
        col.get("nullable") is not None for col in columns
    )
    if nullable_info_available:
        nullable_count = sum(1 for col in columns if col.get("nullable") is True)
        total_columns = len(columns)
        nullable_ratio = nullable_count / total_columns if total_columns > 0 else 0

        # Threshold: if more than 50% of columns are nullable, it's a concern
        if nullable_ratio <= 0.5:
            points_awarded += 5
        else:
            reasons.append(
                Reason(
                    dimension_key="schema_hygiene",
                    reason_code="high_nullable_ratio",
                    message=f"{int(nullable_ratio * 100)}% of columns are nullable (threshold: 50%)",
                    points_lost=5,
                )
            )
            actions.append(
                Action(
                    action_key="reduce_nullable_columns",
                    title="Reduce nullable columns",
                    description="Review and make columns non-nullable where appropriate to improve data quality",
                    points_gain=5,
                    dimension_key="schema_hygiene",
                )
            )
    # If nullable info not available, don't penalize (as per v1 requirements)

    # +5 no "legacy"/unused columns
    legacy_patterns = ["_tmp", "_old", "_deprecated", "_backup", "_archive"]
    legacy_columns = []

    for col in columns:
        col_name = col.get("name", "").lower()
        if any(col_name.endswith(pattern) for pattern in legacy_patterns):
            legacy_columns.append(col.get("name"))

    if not legacy_columns:
        points_awarded += 5
    else:
        reasons.append(
            Reason(
                dimension_key="schema_hygiene",
                reason_code="legacy_columns_detected",
                message=f"{len(legacy_columns)} legacy/unused columns detected (ending in _tmp, _old, etc.)",
                points_lost=5,
            )
        )
        actions.append(
            Action(
                action_key="remove_legacy_columns",
                title="Remove legacy columns",
                description=f"Remove or rename {len(legacy_columns)} legacy columns to clean up schema",
                points_gain=5,
                dimension_key="schema_hygiene",
            )
        )

    dimension_score = DimensionScore(
        dimension_key="schema_hygiene",
        points_awarded=points_awarded,
        max_points=max_points,
    )

    return dimension_score, reasons, actions

