"""
Example usage of the scoring engine.

This demonstrates how to use score_dataset() with various metadata inputs.
"""

from app.scoring.engine import score_dataset
from app.scoring.types import ReadinessStatus


def example_perfect_dataset() -> None:
    """Example: Perfect Gold dataset."""
    metadata = {
        "owner_name": "Data Team",
        "owner_contact": "#data-team",
        "description": "Comprehensive user events table",
        "columns": [
            {"name": "user_id", "description": "Unique user identifier"},
            {"name": "event_type", "description": "Type of event"},
            {"name": "timestamp", "description": "Event timestamp"},
        ],
        "intended_use": "Analytics, experimentation, ML training",
        "limitations": "Data delayed by 1 hour for processing",
        "has_freshness_checks": True,
        "has_volume_checks": True,
        "has_sla": True,
        "breaking_changes_30d": 0,
        "has_release_notes": True,
        "backward_compatible": True,
    }

    result = score_dataset(metadata)
    print(f"Score: {result.total_score}/100")
    print(f"Status: {result.status.value}")
    print(f"\nDimension Scores:")
    for dim in result.dimension_scores:
        print(f"  {dim.dimension_key}: {dim.points_awarded}/{dim.max_points}")
    print(f"\nReasons ({len(result.reasons)}):")
    for reason in result.reasons:
        print(f"  -{reason.points_lost} {reason.message}")
    print(f"\nActions ({len(result.actions)}):")
    for action in result.actions:
        print(f"  +{action.points_gain} {action.title}")


def example_minimal_dataset() -> None:
    """Example: Minimal dataset with no metadata."""
    metadata = {}

    result = score_dataset(metadata)
    print(f"\nMinimal Dataset:")
    print(f"Score: {result.total_score}/100")
    print(f"Status: {result.status.value}")
    print(f"Reasons: {len(result.reasons)}")
    print(f"Actions: {len(result.actions)}")


if __name__ == "__main__":
    example_perfect_dataset()
    example_minimal_dataset()

