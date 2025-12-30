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
    DatasetColumn,
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
                {"name": "user_id", "type": "uuid", "description": "Unique user identifier (UUID)", "nullable": False},
                {"name": "email", "type": "varchar(255)", "description": "User email address", "nullable": False},
                {"name": "created_at", "type": "timestamp", "description": "Account creation timestamp", "nullable": False},
                {"name": "updated_at", "type": "timestamp", "description": "Last update timestamp", "nullable": True},
                {"name": "status", "type": "varchar(50)", "description": "Account status (active, inactive, suspended)", "nullable": False},
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
                {"name": "event_id", "type": "uuid", "description": "Unique event identifier", "nullable": False},
                {"name": "user_id", "type": "uuid", "description": "User who triggered the event", "nullable": False},
                {"name": "event_type", "type": "varchar(100)", "description": "Type of event (click, view, etc.)", "nullable": False},
                {"name": "timestamp", "type": "timestamp", "description": "Event timestamp", "nullable": False},
                {"name": "properties", "type": "jsonb", "description": "Event properties and metadata", "nullable": True},
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
                {"name": "log_id", "type": "bigint", "description": "Log entry identifier", "nullable": False},
                {"name": "timestamp", "type": "timestamp", "description": "Log timestamp", "nullable": False},
                {"name": "level", "type": "varchar(20)", "description": "Log level (INFO, WARN, ERROR)", "nullable": False},
                {"name": "message", "type": "text", "description": "Log message content", "nullable": True},
                {"name": "temp_data_tmp", "type": "text", "description": None, "nullable": True},  # Legacy column
                {"name": "old_backup_old", "type": "text", "description": None, "nullable": True},  # Legacy column
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
                {"name": "date", "type": "date", "description": "Transaction date", "nullable": False},
                {"name": "revenue_amount", "type": "decimal(15,2)", "description": "Total revenue in USD", "nullable": False},
                {"name": "transaction_count", "type": "integer", "description": "Number of transactions", "nullable": False},
                {"name": "region", "type": "varchar(100)", "description": "Geographic region", "nullable": True},
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
                {"name": "experiment_id", "type": "uuid", "description": "Experiment identifier", "nullable": False},
                {"name": "variant", "type": "varchar(10)", "description": "Test variant (A or B)", "nullable": False},
                {"name": "metric_value", "type": "numeric", "description": "Metric value for the experiment", "nullable": True},
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
            description=config.get("description"),  # Add description field
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
                measured=1 if dim_score.measured else 0,  # Store as integer (1=True, 0=False)
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

        # Create columns if provided in metadata
        columns = metadata.get("columns", [])
        if columns:
            for col in columns:
                db_column = DatasetColumn(
                    dataset_id=dataset.id,
                    name=col.get("name", ""),
                    description=col.get("description"),
                    type=col.get("type"),
                    nullable=1 if col.get("nullable") is True else (0 if col.get("nullable") is False else None),
                    last_seen_at=datetime.utcnow(),
                )
                db.add(db_column)

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
        # readiness_status is already a string, not an enum
        status_str = dataset.readiness_status if isinstance(dataset.readiness_status, str) else dataset.readiness_status.value
        print(f"  - {dataset.full_name}: {dataset.readiness_score}/100 ({status_str})")

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

