"""
Operational Metadata dimension scorer.

Total: 10 points
- +5 intended use cases defined
- +5 known limitations defined
"""

from typing import Dict, List

from app.scoring.types import Action, DimensionScore, Reason


def score_operational(
    metadata: Dict,
) -> tuple[DimensionScore, List[Reason], List[Action]]:
    """
    Score the Operational Metadata dimension.

    Args:
        metadata: Dataset metadata dict with keys:
            - intended_use: Optional[str] - intended use cases
            - limitations: Optional[str] - known limitations

    Returns:
        Tuple of (DimensionScore, reasons, actions)
    """
    max_points = 10
    points_awarded = 0
    reasons: List[Reason] = []
    actions: List[Action] = []

    intended_use = metadata.get("intended_use")
    limitations = metadata.get("limitations")

    # +5 intended use cases defined
    if intended_use and intended_use.strip():
        points_awarded += 5
    else:
        reasons.append(
            Reason(
                dimension_key="operational",
                reason_code="missing_intended_use",
                message="Intended use cases not defined",
                points_lost=5,
            )
        )
        actions.append(
            Action(
                action_key="define_intended_use",
                title="Define intended use cases",
                description="Document the intended use cases and consumers for this dataset",
                points_gain=5,
                dimension_key="operational",
            )
        )

    # +5 known limitations defined
    if limitations and limitations.strip():
        points_awarded += 5
    else:
        reasons.append(
            Reason(
                dimension_key="operational",
                reason_code="missing_limitations",
                message="Known limitations not documented",
                points_lost=5,
            )
        )
        actions.append(
            Action(
                action_key="document_limitations",
                title="Document known limitations",
                description="Document any known limitations, caveats, or constraints for this dataset",
                points_gain=5,
                dimension_key="operational",
            )
        )

    dimension_score = DimensionScore(
        dimension_key="operational",
        points_awarded=points_awarded,
        max_points=max_points,
    )

    return dimension_score, reasons, actions

