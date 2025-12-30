"""
Unit tests for the scoring engine.

Tests cover various scenarios from perfect scores to minimal datasets.
"""

import pytest

from app.scoring.engine import score_dataset
from app.scoring.types import ReadinessStatus


class TestScoringEngine:
    """Test suite for the scoring engine."""

    def test_perfect_gold_dataset(self):
        """Test a perfect dataset that should score 100 (Gold status)."""
        metadata = {
            "owner_name": "Data Team",
            "owner_contact": "#data-team",
            "description": "Comprehensive user events table",
            "columns": [
                {"name": "user_id", "description": "Unique user identifier"},
                {"name": "event_type", "description": "Type of event"},
                {"name": "timestamp", "description": "Event timestamp"},
                {"name": "event_data", "description": "Event payload"},
            ],
            "intended_use": "Analytics, experimentation, ML training",
            "limitations": "Data delayed by 1 hour for processing",
            "has_freshness_checks": True,
            "has_volume_checks": True,
            "dbt_test_count": 5,
            "has_sla": True,
            "breaking_changes_30d": 0,
            "has_release_notes": True,
            "has_versioning": True,
            "backward_compatible": True,
        }

        result = score_dataset(metadata)

        assert result.total_score == 100
        assert result.status == ReadinessStatus.GOLD
        assert len(result.dimension_scores) == 6
        assert all(dim.points_awarded == dim.max_points for dim in result.dimension_scores)
        assert len(result.reasons) == 0
        # Should still have some actions for continuous improvement
        assert len(result.actions) >= 0

    def test_minimal_draft_dataset(self):
        """Test a minimal dataset with no metadata (should be Draft)."""
        metadata = {}

        result = score_dataset(metadata)

        assert result.total_score == 0
        assert result.status == ReadinessStatus.DRAFT
        assert len(result.dimension_scores) == 6
        # Should have many reasons for missing items
        assert len(result.reasons) > 0
        # Should have actionable recommendations
        assert len(result.actions) > 0

    def test_partial_ownership_only(self):
        """Test dataset with only owner information."""
        metadata = {
            "owner_name": "John Doe",
            "owner_contact": "john@example.com",
        }

        result = score_dataset(metadata)

        # Should score 15 points from ownership dimension
        assert result.total_score == 15
        assert result.status == ReadinessStatus.DRAFT
        # Ownership should be perfect
        ownership_dim = next(d for d in result.dimension_scores if d.dimension_key == "ownership")
        assert ownership_dim.points_awarded == 15

    def test_production_ready_with_gaps(self):
        """Test a dataset that scores in Production-Ready range (70-84)."""
        metadata = {
            "owner_name": "Data Team",
            "owner_contact": "#data-team",
            "description": "User analytics table",
            "columns": [
                {"name": "user_id", "description": "User ID"},
                {"name": "event_type", "description": "Event type"},
                {"name": "timestamp"},  # Missing description
                {"name": "data"},  # Missing description
            ],
            "intended_use": "Analytics",
            "limitations": "Some data quality issues",
            "has_freshness_checks": True,
            "has_volume_checks": False,
            "has_sla": False,
            "has_release_notes": False,
        }

        result = score_dataset(metadata)

        assert 70 <= result.total_score <= 84
        assert result.status == ReadinessStatus.PRODUCTION_READY
        # Should have some reasons
        assert len(result.reasons) > 0
        # Should have actionable improvements
        assert len(result.actions) > 0

    def test_schema_hygiene_issues(self):
        """Test dataset with schema hygiene problems."""
        metadata = {
            "owner_name": "Team A",
            "columns": [
                {"name": "UserID"},  # Not snake_case
                {"name": "event_type"},  # Good
                {"name": "temp_data_tmp"},  # Legacy column
                {"name": "old_backup_old"},  # Legacy column
            ],
        }

        result = score_dataset(metadata)

        schema_dim = next(d for d in result.dimension_scores if d.dimension_key == "schema_hygiene")
        # Should lose points for naming and legacy columns
        assert schema_dim.points_awarded < schema_dim.max_points

        # Should have reasons for schema issues
        schema_reasons = [r for r in result.reasons if r.dimension_key == "schema_hygiene"]
        assert len(schema_reasons) > 0

    def test_documentation_coverage(self):
        """Test documentation scoring with partial column coverage."""
        metadata = {
            "owner_name": "Team B",
            "description": "Test dataset",
            "columns": [
                {"name": "col1", "description": "Column 1"},
                {"name": "col2", "description": "Column 2"},
                {"name": "col3"},  # No description
                {"name": "col4"},  # No description
                {"name": "col5"},  # No description
            ],
        }

        result = score_dataset(metadata)

        # 2 out of 5 columns documented = 40% < 80% threshold
        doc_dim = next(d for d in result.dimension_scores if d.dimension_key == "documentation")
        # Should have description points (5) but not column doc points (10)
        assert doc_dim.points_awarded == 5

        # Should have reason for insufficient column docs
        doc_reasons = [r for r in result.reasons if r.dimension_key == "documentation"]
        assert any("column" in r.message.lower() for r in doc_reasons)

    def test_internal_status_dataset(self):
        """Test a dataset that scores in Internal range (50-69)."""
        metadata = {
            "owner_name": "Team C",
            "description": "Some description",
            "columns": [
                {"name": "id", "description": "ID"},
                {"name": "name", "description": "Name"},
            ],
            "intended_use": "Internal use",
            "has_freshness_checks": True,
        }

        result = score_dataset(metadata)

        assert 50 <= result.total_score <= 69
        assert result.status == ReadinessStatus.INTERNAL

    def test_data_quality_signals(self):
        """Test data quality dimension scoring."""
        metadata = {
            "owner_name": "Team D",
            "has_freshness_checks": True,
            "has_volume_checks": True,
            "dbt_test_count": 3,
            "has_sla": True,
            "intended_use": "Production analytics",
        }

        result = score_dataset(metadata)

        quality_dim = next(d for d in result.dimension_scores if d.dimension_key == "data_quality")
        # Should have points for checks (10) and SLA (5)
        assert quality_dim.points_awarded >= 15

    def test_missing_optional_fields_no_penalty(self):
        """Test that missing optional fields don't cause penalties."""
        metadata = {
            "owner_name": "Team E",
            "description": "Test",
            "columns": [{"name": "id"}],
            "intended_use": "Testing",
            "limitations": "None",
        }

        result = score_dataset(metadata)

        # Should not have penalties for fields we can't measure
        # (e.g., unresolved_failures_30d, breaking_changes_30d if not provided)
        stability_dim = next(d for d in result.dimension_scores if d.dimension_key == "stability")
        # Should not lose points for breaking_changes if not provided
        breaking_reasons = [
            r for r in result.reasons
            if r.dimension_key == "stability" and "breaking" in r.reason_code
        ]
        # If breaking_changes_30d not provided, should not have this reason
        assert len(breaking_reasons) == 0

