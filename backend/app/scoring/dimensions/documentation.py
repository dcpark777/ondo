"""
Documentation Quality dimension scorer.

Total: 20 points
- +5 dataset description present
- +5 description updated within 90 days (omitted in v1, redistributed)
- +10 >=80% columns documented
"""

from typing import Dict, List

from app.scoring.constants import ActionKey, ReasonCode
from app.scoring.types import Action, DimensionScore, Reason


def score_documentation(
    metadata: Dict,
) -> tuple[DimensionScore, List[Reason], List[Action]]:
    """
    Score the Documentation Quality dimension.

    Args:
        metadata: Dataset metadata dict with keys:
            - description: Optional[str] - dataset description
            - columns: Optional[List[Dict]] - list of column metadata
                Each column dict may have:
                - name: str
                - description: Optional[str]

    Returns:
        Tuple of (DimensionScore, reasons, actions)
    """
    max_points = 20
    points_awarded = 0
    reasons: List[Reason] = []
    actions: List[Action] = []

    description = metadata.get("description")
    columns = metadata.get("columns", [])

    # +5 dataset description present
    if description and description.strip():
        points_awarded += 5
    else:
        reasons.append(
            Reason(
                dimension_key="documentation",
                reason_code=ReasonCode.MISSING_DESCRIPTION,
                message="Dataset description is missing",
                points_lost=5,
            )
        )
        actions.append(
            Action(
                action_key=ActionKey.ADD_DESCRIPTION,
                title="Add dataset description",
                description="Write a clear description explaining what this dataset contains and its purpose",
                points_gain=5,
                dimension_key="documentation",
            )
        )

    # +10 >=80% columns documented
    if columns:
        documented_count = sum(
            1
            for col in columns
            if col.get("description") and col.get("description", "").strip()
        )
        total_columns = len(columns)
        documented_ratio = documented_count / total_columns if total_columns > 0 else 0

        if documented_ratio >= 0.8:
            points_awarded += 10
        else:
            undocumented_count = total_columns - documented_count
            points_lost = 10
            reasons.append(
                Reason(
                    dimension_key="documentation",
                    reason_code=ReasonCode.INSUFFICIENT_COLUMN_DOCS,
                    message=f"Only {int(documented_ratio * 100)}% of columns documented ({undocumented_count} columns missing docs)",
                    points_lost=points_lost,
                )
            )
            actions.append(
                Action(
                    action_key=ActionKey.DOCUMENT_COLUMNS,
                    title="Document missing columns",
                    description=f"Add descriptions for {undocumented_count} undocumented columns (target: 80% coverage)",
                    points_gain=10,
                    dimension_key="documentation",
                )
            )
    else:
        # No column information available - don't penalize
        # In v1, we mark as "not measured yet"
        pass

    # Determine if measured: True if we have column info, False if no columns provided
    measured = len(columns) > 0 if columns else True  # Description is always measurable
    
    dimension_score = DimensionScore(
        dimension_key="documentation",
        points_awarded=points_awarded,
        max_points=max_points,
        measured=measured,
    )

    return dimension_score, reasons, actions

