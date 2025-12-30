"""
Ownership & Accountability dimension scorer.

Total: 15 points
- +10 owner present
- +5 escalation/contact present
"""

from typing import Dict, List, Optional

from app.scoring.types import Action, DimensionScore, Reason


def score_ownership(
    metadata: Dict,
) -> tuple[DimensionScore, List[Reason], List[Action]]:
    """
    Score the Ownership & Accountability dimension.

    Args:
        metadata: Dataset metadata dict with keys:
            - owner_name: Optional[str]
            - owner_contact: Optional[str]

    Returns:
        Tuple of (DimensionScore, reasons, actions)
    """
    max_points = 15
    points_awarded = 0
    reasons: List[Reason] = []
    actions: List[Action] = []

    owner_name = metadata.get("owner_name")
    owner_contact = metadata.get("owner_contact")

    # +10 owner present
    if owner_name:
        points_awarded += 10
    else:
        reasons.append(
            Reason(
                dimension_key="ownership",
                reason_code="missing_owner",
                message="No owner assigned",
                points_lost=10,
            )
        )
        actions.append(
            Action(
                action_key="assign_owner",
                title="Assign dataset owner",
                description="Assign a clear owner responsible for this dataset",
                points_gain=10,
                dimension_key="ownership",
            )
        )

    # +5 escalation/contact present
    if owner_contact:
        points_awarded += 5
    else:
        if owner_name:
            # Only suggest adding contact if owner exists
            reasons.append(
                Reason(
                    dimension_key="ownership",
                    reason_code="missing_contact",
                    message="Owner contact/escalation channel not defined",
                    points_lost=5,
                )
            )
            actions.append(
                Action(
                    action_key="add_owner_contact",
                    title="Add owner contact information",
                    description="Add escalation channel (Slack, email, etc.) for the owner",
                    points_gain=5,
                    dimension_key="ownership",
                )
            )
        else:
            # If no owner, don't penalize for missing contact
            pass

    dimension_score = DimensionScore(
        dimension_key="ownership",
        points_awarded=points_awarded,
        max_points=max_points,
    )

    return dimension_score, reasons, actions

