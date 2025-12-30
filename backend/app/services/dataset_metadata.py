"""
Utilities for building metadata dicts from Dataset models for scoring.
"""

from typing import Any, Dict, List, Optional

from app.models import Dataset


def build_metadata_from_dataset(
    dataset: Dataset, columns: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Build metadata dictionary from Dataset model for scoring engine.

    Args:
        dataset: Dataset model instance
        columns: Optional list of column metadata dicts
                 Each dict should have: name, description (optional), nullable (optional)

    Returns:
        Metadata dict ready for scoring engine
    """
    metadata = {
        "owner_name": dataset.owner_name,
        "owner_contact": dataset.owner_contact,
        "description": None,  # Not stored in Dataset model currently
        "columns": columns or [],
        "intended_use": dataset.intended_use,
        "limitations": dataset.limitations,
        # Default values for optional fields
        "has_freshness_checks": False,
        "has_volume_checks": False,
        "dbt_test_count": 0,
        "has_sla": False,
        "breaking_changes_30d": None,
        "has_release_notes": False,
        "has_versioning": False,
        "backward_compatible": None,
    }

    return metadata

