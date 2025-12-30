"""
Type definitions for scoring results.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class ReadinessStatus(str, Enum):
    """Dataset readiness status based on score."""

    DRAFT = "draft"  # 0-49
    INTERNAL = "internal"  # 50-69
    PRODUCTION_READY = "production_ready"  # 70-84
    GOLD = "gold"  # 85-100


@dataclass
class DimensionScore:
    """Score for a single dimension."""

    dimension_key: str
    points_awarded: int
    max_points: int

    @property
    def percentage(self) -> float:
        """Calculate percentage score for this dimension."""
        if self.max_points == 0:
            return 0.0
        return (self.points_awarded / self.max_points) * 100


@dataclass
class Reason:
    """Reason for point loss in a dimension."""

    dimension_key: str
    reason_code: str
    message: str
    points_lost: int


@dataclass
class Action:
    """Recommended action to improve score."""

    action_key: str
    title: str
    description: str
    points_gain: int
    dimension_key: str
    url: Optional[str] = None


@dataclass
class ScoreResult:
    """Complete scoring result for a dataset."""

    total_score: int
    status: ReadinessStatus
    dimension_scores: List[DimensionScore]
    reasons: List[Reason]
    actions: List[Action]

    @classmethod
    def determine_status(cls, score: int) -> ReadinessStatus:
        """Determine readiness status from total score."""
        if score >= 85:
            return ReadinessStatus.GOLD
        elif score >= 70:
            return ReadinessStatus.PRODUCTION_READY
        elif score >= 50:
            return ReadinessStatus.INTERNAL
        else:
            return ReadinessStatus.DRAFT

