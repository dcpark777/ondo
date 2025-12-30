"""
Stability & Change Management dimension scorer.

Total: 20 points
- +10 no breaking changes in last 30 days (v1: based on schema diff history; if not implemented, omit and redistribute points)
- +5 changes documented/versioned (v1: presence of "release notes" field; otherwise action)
- +5 backward compatibility respected (v1: heuristic via schema diff rules)
"""

from typing import Dict, List

from app.scoring.constants import ActionKey, ReasonCode
from app.scoring.types import Action, DimensionScore, Reason


def score_stability(
    metadata: Dict,
) -> tuple[DimensionScore, List[Reason], List[Action]]:
    """
    Score the Stability & Change Management dimension.

    Args:
        metadata: Dataset metadata dict with keys:
            - breaking_changes_30d: Optional[int] - breaking changes in last 30 days
            - has_release_notes: Optional[bool] - presence of release notes/changelog
            - has_versioning: Optional[bool] - versioning system in place
            - backward_compatible: Optional[bool] - backward compatibility status

    Returns:
        Tuple of (DimensionScore, reasons, actions)
    """
    max_points = 20
    points_awarded = 0
    reasons: List[Reason] = []
    actions: List[Action] = []

    # +10 no breaking changes in last 30 days
    breaking_changes = metadata.get("breaking_changes_30d")
    if breaking_changes is not None:
        if breaking_changes == 0:
            points_awarded += 10
        else:
            reasons.append(
                Reason(
                    dimension_key="stability",
                    reason_code=ReasonCode.BREAKING_CHANGES_DETECTED,
                    message=f"{breaking_changes} breaking changes in last 30 days",
                    points_lost=10,
                )
            )
            actions.append(
                Action(
                    action_key=ActionKey.PREVENT_BREAKING_CHANGES,
                    title="Prevent breaking changes",
                    description="Review change management process to avoid breaking changes that impact downstream consumers",
                    points_gain=10,
                    dimension_key="stability",
                )
            )
    # If not provided, don't penalize (redistribute: we'll give partial credit for other signals)

    # +5 changes documented/versioned
    has_release_notes = metadata.get("has_release_notes", False)
    has_versioning = metadata.get("has_versioning", False)
    has_changelog = has_release_notes or has_versioning

    if has_changelog:
        points_awarded += 5
    else:
        reasons.append(
            Reason(
                dimension_key="stability",
                reason_code=ReasonCode.MISSING_CHANGELOG,
                message="Changes are not documented or versioned",
                points_lost=5,
            )
        )
        actions.append(
            Action(
                action_key=ActionKey.ADD_CHANGELOG,
                title="Document schema changes",
                description="Maintain release notes or changelog to document schema changes and versions",
                points_gain=5,
                dimension_key="stability",
            )
        )

    # +5 backward compatibility respected
    backward_compatible = metadata.get("backward_compatible")
    if backward_compatible is not None:
        if backward_compatible:
            points_awarded += 5
        else:
            reasons.append(
                Reason(
                    dimension_key="stability",
                    reason_code=ReasonCode.BACKWARD_INCOMPATIBLE,
                    message="Schema changes break backward compatibility",
                    points_lost=5,
                )
            )
            actions.append(
                Action(
                    action_key=ActionKey.MAINTAIN_COMPATIBILITY,
                    title="Maintain backward compatibility",
                    description="Ensure schema changes maintain backward compatibility for existing consumers",
                    points_gain=5,
                    dimension_key="stability",
                )
            )
    # If not provided, don't penalize (as per v1 requirements)

    # Determine if measured: True if we have any stability metadata
    measured = (
        breaking_changes is not None
        or has_release_notes
        or has_versioning
        or backward_compatible is not None
    )

    # If not measured, don't penalize - remove all reasons and actions
    if not measured:
        reasons = []
        actions = []

    dimension_score = DimensionScore(
        dimension_key="stability",
        points_awarded=points_awarded,
        max_points=max_points,
        measured=measured,
    )

    return dimension_score, reasons, actions

