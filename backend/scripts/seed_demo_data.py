"""
Seed script for demo data.

Creates sample datasets with varied scores for demonstration purposes.
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session

from app.db import SessionLocal, engine
from app.models import (
    Dataset,
    DatasetAction,
    DatasetDimensionScore,
    DatasetReason,
    DatasetScoreHistory,
    DimensionKeyEnum,
    ReadinessStatusEnum,
)
from app.scoring.engine import score_dataset
from app.scoring.types import ReadinessStatus as ScoringReadinessStatus


def _map_scoring_status_to_model_status(scoring_status: ScoringReadinessStatus) -> ReadinessStatusEnum:
    """Map scoring engine ReadinessStatus to model ReadinessStatusEnum."""
    # Map by value to ensure correct conversion
    status_map = {
        ScoringReadinessStatus.DRAFT.value: ReadinessStatusEnum.DRAFT,
        ScoringReadinessStatus.INTERNAL.value: ReadinessStatusEnum.INTERNAL,
        ScoringReadinessStatus.PRODUCTION_READY.value: ReadinessStatusEnum.PRODUCTION_READY,
        ScoringReadinessStatus.GOLD.value: ReadinessStatusEnum.GOLD,
    }
    return status_map[scoring_status.value]


def create_demo_datasets(db: Session, force: bool = False):
    """Create demo datasets with varied scores.
    
    Args:
        db: Database session
        force: If True, clear existing data before seeding. If False, skip if data exists.
    """
    
    # Check if data already exists
    existing_count = db.query(Dataset).count()
    if existing_count > 0 and not force:
        print(f"ℹ️  Database already contains {existing_count} datasets. Skipping seed.")
        print("   Use --force flag or clear data manually to re-seed.")
        return []
    
    # Clear existing data if forcing
    if force:
        print("🗑️  Clearing existing data...")
        db.query(DatasetScoreHistory).delete()
        db.query(DatasetAction).delete()
        db.query(DatasetReason).delete()
        db.query(DatasetDimensionScore).delete()
        db.query(Dataset).delete()
        db.commit()

    datasets_config = [
        {
            "name": "analytics.users",
            "display_name": "Users Table",
            "owner_name": "Data Team",
            "owner_contact": "#data-team",
            "description": "Comprehensive user profile and account information",
            "intended_use": "Analytics, user segmentation, ML training",
            "limitations": "Data delayed by 1 hour for processing",
            "columns": [
                {"name": "user_id", "description": "Unique user identifier (UUID)"},
                {"name": "email", "description": "User email address"},
                {"name": "created_at", "description": "Account creation timestamp"},
                {"name": "updated_at", "description": "Last update timestamp"},
                {"name": "status", "description": "Account status (active, inactive, suspended)"},
            ],
            "has_freshness_checks": True,
            "has_volume_checks": True,
            "dbt_test_count": 8,
            "has_sla": True,
            "breaking_changes_30d": 0,
            "has_release_notes": True,
            "has_versioning": True,
            "backward_compatible": True,
        },
        {
            "name": "analytics.events",
            "display_name": "User Events",
            "owner_name": "Analytics Team",
            "owner_contact": "analytics@example.com",
            "description": "User interaction events and tracking data",
            "intended_use": "Analytics, experimentation",
            "limitations": "Some events may be delayed up to 5 minutes",
            "columns": [
                {"name": "event_id", "description": "Unique event identifier"},
                {"name": "user_id", "description": "User who triggered the event"},
                {"name": "event_type", "description": "Type of event (click, view, etc.)"},
                {"name": "timestamp", "description": "Event timestamp"},
                {"name": "properties"},  # Missing description
            ],
            "has_freshness_checks": True,
            "has_volume_checks": False,
            "has_sla": False,
            "breaking_changes_30d": 1,
            "has_release_notes": False,
        },
        {
            "name": "staging.raw_logs",
            "display_name": "Raw Application Logs",
            "owner_name": None,  # Missing owner
            "description": None,  # Missing description
            "columns": [
                {"name": "log_id"},
                {"name": "timestamp"},
                {"name": "level"},
                {"name": "message"},
                {"name": "temp_data_tmp"},  # Legacy column
                {"name": "old_backup_old"},  # Legacy column
            ],
            "has_freshness_checks": False,
            "has_volume_checks": False,
        },
        {
            "name": "analytics.revenue",
            "display_name": "Revenue Metrics",
            "owner_name": "Finance Team",
            "owner_contact": "#finance-data",
            "description": "Daily revenue and transaction metrics",
            "intended_use": "Financial reporting, forecasting",
            "limitations": "Revenue data finalized at end of day",
            "columns": [
                {"name": "date", "description": "Transaction date"},
                {"name": "revenue_amount", "description": "Total revenue in USD"},
                {"name": "transaction_count", "description": "Number of transactions"},
                {"name": "region", "description": "Geographic region"},
            ],
            "has_freshness_checks": True,
            "has_sla": True,
            "breaking_changes_30d": 0,
            "has_release_notes": True,
        },
        {
            "name": "experiments.ab_test_results",
            "display_name": "A/B Test Results",
            "owner_name": "Experimentation Team",
            "description": "Results from A/B tests and experiments",
            "intended_use": "Experiment analysis",
            "columns": [
                {"name": "experiment_id", "description": "Experiment identifier"},
                {"name": "variant", "description": "Test variant (A or B)"},
                {"name": "metric_value"},  # Missing description
            ],
            "has_freshness_checks": False,
        },
    ]

    created_datasets = []

    for config in datasets_config:
        # Prepare metadata for scoring
        metadata = {
            "owner_name": config.get("owner_name"),
            "owner_contact": config.get("owner_contact"),
            "description": config.get("description"),
            "columns": config.get("columns", []),
            "intended_use": config.get("intended_use"),
            "limitations": config.get("limitations"),
            "has_freshness_checks": config.get("has_freshness_checks", False),
            "has_volume_checks": config.get("has_volume_checks", False),
            "dbt_test_count": config.get("dbt_test_count", 0),
            "has_sla": config.get("has_sla", False),
            "breaking_changes_30d": config.get("breaking_changes_30d"),
            "has_release_notes": config.get("has_release_notes", False),
            "has_versioning": config.get("has_versioning", False),
            "backward_compatible": config.get("backward_compatible"),
        }

        # Score the dataset
        score_result = score_dataset(metadata)

        # Create dataset record
        dataset = Dataset(
            full_name=config["name"],
            display_name=config["display_name"],
            owner_name=config.get("owner_name"),
            owner_contact=config.get("owner_contact"),
            intended_use=config.get("intended_use"),
            limitations=config.get("limitations"),
            last_seen_at=datetime.utcnow(),
            last_scored_at=datetime.utcnow(),
            readiness_score=score_result.total_score,
            readiness_status=score_result.status.value,  # Pass value string directly
        )
        db.add(dataset)
        db.flush()  # Get the ID

        # Create dimension scores
        for dim_score in score_result.dimension_scores:
            db_dim_score = DatasetDimensionScore(
                dataset_id=dataset.id,
                dimension_key=dim_score.dimension_key.lower(),  # Pass value string directly
                points_awarded=dim_score.points_awarded,
                max_points=dim_score.max_points,
            )
            db.add(db_dim_score)

        # Create reasons
        for reason in score_result.reasons:
            db_reason = DatasetReason(
                dataset_id=dataset.id,
                dimension_key=reason.dimension_key.lower(),  # Pass value string directly
                reason_code=reason.reason_code,
                message=reason.message,
                points_lost=reason.points_lost,
            )
            db.add(db_reason)

        # Create actions
        for action in score_result.actions:
            db_action = DatasetAction(
                dataset_id=dataset.id,
                action_key=action.action_key,
                title=action.title,
                description=action.description,
                points_gain=action.points_gain,
                url=action.url,
            )
            db.add(db_action)

        # Create score history entry
        history = DatasetScoreHistory(
            dataset_id=dataset.id,
            readiness_score=score_result.total_score,
            recorded_at=datetime.utcnow(),
            scoring_version="v1",
        )
        db.add(history)

        # Create some historical entries (simulate score changes over time)
        base_score = score_result.total_score
        for days_ago in [7, 14, 30]:
            historical_score = max(0, base_score - (days_ago // 7) * 2)  # Simulate gradual improvement
            history_entry = DatasetScoreHistory(
                dataset_id=dataset.id,
                readiness_score=historical_score,
                recorded_at=datetime.utcnow() - timedelta(days=days_ago),
                scoring_version="v1",
            )
            db.add(history_entry)

        created_datasets.append(dataset)

    db.commit()

    print(f"✅ Created {len(created_datasets)} demo datasets:")
    for dataset in created_datasets:
        print(f"  - {dataset.full_name}: {dataset.readiness_score}/100 ({dataset.readiness_status.value})")

    return created_datasets


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed demo data for Ondo")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Clear existing data before seeding",
    )
    args = parser.parse_args()
    
    print("🌱 Seeding demo data...")
    db = SessionLocal()
    try:
        create_demo_datasets(db, force=args.force)
        print("✅ Demo data seeded successfully!")
    except Exception as e:
        print(f"❌ Error seeding data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

