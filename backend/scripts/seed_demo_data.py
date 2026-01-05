"""
Seed script for demo data.

Creates sample datasets with varied scores for demonstration purposes.
"""

import sys
import random
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
    DatasetLineage,
    ColumnLineage,
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
        db.query(ColumnLineage).delete()
        db.query(DatasetLineage).delete()
        db.query(DatasetScoreHistory).delete()
        db.query(DatasetAction).delete()
        db.query(DatasetReason).delete()
        db.query(DatasetDimensionScore).delete()
        db.query(DatasetColumn).delete()
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
            "data_size_bytes": 1073741824,  # 1 GB
            "file_count": 12,
            "partition_keys": ["created_at"],
            "sla_hours": 24,
            "producing_job": "user_ingestion_pipeline",
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
            "data_size_bytes": 5368709120,  # 5 GB
            "file_count": 365,
            "partition_keys": ["timestamp", "event_type"],
            "sla_hours": 1,
            "producing_job": "event_streaming_pipeline",
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
            "data_size_bytes": 2147483648,  # 2 GB
            "file_count": 720,
            "partition_keys": ["timestamp"],
            "sla_hours": 1,
            "producing_job": "log_aggregation_job",
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
            "data_size_bytes": 52428800,  # 50 MB
            "file_count": 365,
            "partition_keys": ["date", "region"],
            "sla_hours": 24,
            "producing_job": "revenue_aggregation_daily",
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
            "data_size_bytes": 10485760,  # 10 MB
            "file_count": 30,
            "partition_keys": ["experiment_id"],
            "sla_hours": 6,
            "producing_job": "ab_test_analysis_pipeline",
        },
        {
            "name": "analytics.product_catalog",
            "display_name": "Product Catalog",
            "owner_name": "Product Team",
            "owner_contact": "product-data@example.com",
            "description": "Complete product catalog with pricing and inventory information",
            "intended_use": "Product analytics, inventory management, pricing analysis",
            "limitations": "Pricing updates may lag by up to 15 minutes",
            "columns": [
                {"name": "product_id", "type": "uuid", "description": "Unique product identifier", "nullable": False},
                {"name": "product_name", "type": "varchar(255)", "description": "Product name", "nullable": False},
                {"name": "category", "type": "varchar(100)", "description": "Product category", "nullable": False},
                {"name": "price", "type": "decimal(10,2)", "description": "Product price in USD", "nullable": False},
                {"name": "in_stock", "type": "boolean", "description": "Whether product is in stock", "nullable": False},
                {"name": "created_at", "type": "timestamp", "description": "Product creation date", "nullable": False},
            ],
            "has_freshness_checks": True,
            "has_volume_checks": True,
            "dbt_test_count": 5,
            "has_sla": True,
            "breaking_changes_30d": 0,
            "has_release_notes": True,
            "data_size_bytes": 268435456,  # 256 MB
            "file_count": 1,
            "partition_keys": ["category"],
            "sla_hours": 6,
            "producing_job": "product_catalog_sync",
        },
        {
            "name": "ml.feature_store",
            "display_name": "ML Feature Store",
            "owner_name": "ML Engineering Team",
            "owner_contact": "#ml-eng",
            "description": "Pre-computed features for machine learning models",
            "intended_use": "Model training, feature serving",
            "limitations": "Features computed daily, may not reflect real-time changes",
            "columns": [
                {"name": "feature_id", "type": "uuid", "description": "Feature identifier", "nullable": False},
                {"name": "user_id", "type": "uuid", "description": "User identifier", "nullable": False},
                {"name": "feature_vector", "type": "array", "description": "Feature vector values", "nullable": False},
                {"name": "computed_at", "type": "timestamp", "description": "Feature computation timestamp", "nullable": False},
                {"name": "model_version", "type": "varchar(50)", "description": "Model version used", "nullable": True},
            ],
            "has_freshness_checks": True,
            "has_volume_checks": False,
            "has_sla": True,
            "breaking_changes_30d": 0,
            "has_release_notes": False,
            "data_size_bytes": 10737418240,  # 10 GB
            "file_count": 90,
            "partition_keys": ["computed_at"],
            "sla_hours": 24,
            "producing_job": "feature_computation_pipeline",
        },
        {
            "name": "analytics.customer_segments",
            "display_name": "Customer Segments",
            "owner_name": "Marketing Team",
            "owner_contact": "marketing-data@example.com",
            "description": "Customer segmentation and cohort analysis data",
            "intended_use": "Marketing campaigns, personalization",
            "limitations": "Segments updated weekly",
            "columns": [
                {"name": "customer_id", "type": "uuid", "description": "Customer identifier", "nullable": False},
                {"name": "segment", "type": "varchar(50)", "description": "Customer segment name", "nullable": False},
                {"name": "cohort_month", "type": "date", "description": "Cohort month", "nullable": False},
                {"name": "lifetime_value", "type": "decimal(12,2)", "description": "Customer lifetime value", "nullable": True},
                {"name": "last_purchase_date", "type": "date", "description": "Last purchase date", "nullable": True},
            ],
            "has_freshness_checks": False,
            "has_volume_checks": False,
            "has_sla": False,
            "breaking_changes_30d": 1,
            "has_release_notes": False,
            "data_size_bytes": 104857600,  # 100 MB
            "file_count": 52,
            "partition_keys": ["cohort_month", "segment"],
            "sla_hours": 168,  # Weekly
            "producing_job": "customer_segmentation_weekly",
        },
        {
            "name": "analytics.page_views",
            "display_name": "Page Views",
            "owner_name": "Analytics Team",
            "owner_contact": "analytics@example.com",
            "description": "Website page view tracking data",
            "intended_use": "Web analytics, user behavior analysis",
            "limitations": "Real-time data may have slight delays",
            "columns": [
                {"name": "view_id", "type": "uuid", "description": "Unique page view identifier", "nullable": False},
                {"name": "user_id", "type": "uuid", "description": "User identifier", "nullable": True},
                {"name": "page_url", "type": "varchar(500)", "description": "Page URL", "nullable": False},
                {"name": "timestamp", "type": "timestamp", "description": "Page view timestamp", "nullable": False},
                {"name": "session_id", "type": "uuid", "description": "Session identifier", "nullable": True},
            ],
            "has_freshness_checks": True,
            "has_volume_checks": True,
            "has_sla": False,
            "breaking_changes_30d": 2,
            "has_release_notes": False,
            "data_size_bytes": 21474836480,  # 20 GB
            "file_count": 730,
            "partition_keys": ["timestamp"],
            "sla_hours": 1,
            "producing_job": "page_view_tracking_stream",
        },
        {
            "name": "analytics.orders",
            "display_name": "Order Data",
            "owner_name": "E-commerce Team",
            "owner_contact": "#ecommerce-data",
            "description": "Customer order and transaction data",
            "intended_use": "Order analytics, fulfillment tracking",
            "limitations": "Refunds processed separately",
            "columns": [
                {"name": "order_id", "type": "uuid", "description": "Unique order identifier", "nullable": False},
                {"name": "customer_id", "type": "uuid", "description": "Customer identifier", "nullable": False},
                {"name": "order_date", "type": "timestamp", "description": "Order placement timestamp", "nullable": False},
                {"name": "total_amount", "type": "decimal(12,2)", "description": "Order total amount", "nullable": False},
                {"name": "status", "type": "varchar(50)", "description": "Order status", "nullable": False},
                {"name": "shipping_address", "type": "text", "description": "Shipping address", "nullable": True},
            ],
            "has_freshness_checks": True,
            "has_volume_checks": True,
            "dbt_test_count": 12,
            "has_sla": True,
            "breaking_changes_30d": 0,
            "has_release_notes": True,
            "has_versioning": True,
            "data_size_bytes": 536870912,  # 512 MB
            "file_count": 180,
            "partition_keys": ["order_date"],
            "sla_hours": 6,
            "producing_job": "order_processing_pipeline",
        },
        {
            "name": "staging.api_logs",
            "display_name": "API Request Logs",
            "owner_name": "Platform Team",
            "owner_contact": "platform@example.com",
            "description": "API request and response logs for monitoring",
            "intended_use": "API monitoring, debugging, performance analysis",
            "limitations": "Logs retained for 30 days only",
            "columns": [
                {"name": "log_id", "type": "bigint", "description": "Log entry identifier", "nullable": False},
                {"name": "request_id", "type": "uuid", "description": "Request identifier", "nullable": False},
                {"name": "endpoint", "type": "varchar(200)", "description": "API endpoint", "nullable": False},
                {"name": "method", "type": "varchar(10)", "description": "HTTP method", "nullable": False},
                {"name": "status_code", "type": "integer", "description": "HTTP status code", "nullable": False},
                {"name": "response_time_ms", "type": "integer", "description": "Response time in milliseconds", "nullable": True},
                {"name": "timestamp", "type": "timestamp", "description": "Request timestamp", "nullable": False},
            ],
            "has_freshness_checks": False,
            "has_volume_checks": False,
            "has_sla": False,
            "breaking_changes_30d": 3,
            "has_release_notes": False,
            "data_size_bytes": 4294967296,  # 4 GB
            "file_count": 1440,
            "partition_keys": ["timestamp", "endpoint"],
            "sla_hours": 1,
            "producing_job": "api_log_aggregator",
        },
        {
            "name": "analytics.user_activity",
            "display_name": "User Activity Summary",
            "owner_name": "Analytics Team",
            "owner_contact": "analytics@example.com",
            "description": "Daily aggregated user activity metrics",
            "intended_use": "User engagement analysis, reporting",
            "limitations": "Aggregated data, not real-time",
            "columns": [
                {"name": "user_id", "type": "uuid", "description": "User identifier", "nullable": False},
                {"name": "activity_date", "type": "date", "description": "Activity date", "nullable": False},
                {"name": "sessions_count", "type": "integer", "description": "Number of sessions", "nullable": False},
                {"name": "page_views", "type": "integer", "description": "Total page views", "nullable": False},
                {"name": "time_spent_minutes", "type": "integer", "description": "Time spent in minutes", "nullable": True},
            ],
            "has_freshness_checks": True,
            "has_volume_checks": True,
            "dbt_test_count": 6,
            "has_sla": True,
            "breaking_changes_30d": 0,
            "has_release_notes": True,
            "data_size_bytes": 209715200,  # 200 MB
            "file_count": 365,
            "partition_keys": ["activity_date"],
            "sla_hours": 24,
            "producing_job": "user_activity_aggregation",
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
        # Generate a random last_updated_at within the last 7 days
        days_ago = random.randint(0, 7)
        hours_ago = random.randint(0, 23)
        last_updated = datetime.utcnow() - timedelta(days=days_ago, hours=hours_ago)
        
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
            last_updated_at=last_updated,
            data_size_bytes=config.get("data_size_bytes"),
            file_count=config.get("file_count"),
            partition_keys=config.get("partition_keys"),
            sla_hours=config.get("sla_hours"),
            producing_job=config.get("producing_job"),
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

    # Create example lineage relationships
    print("\n🔗 Creating lineage relationships...")
    create_example_lineage(db, created_datasets)
    
    return created_datasets


def create_example_lineage(db: Session, datasets: list[Dataset]):
    """Create example lineage relationships between datasets and columns.
    
    Args:
        db: Database session
        datasets: List of created datasets
    """
    # Create a mapping of dataset full_name to dataset object
    dataset_map = {ds.full_name: ds for ds in datasets}
    
    # Dataset-level lineage examples:
    # 1. analytics.events depends on analytics.users (events table joins with users)
    if "analytics.events" in dataset_map and "analytics.users" in dataset_map:
        events_ds = dataset_map["analytics.events"]
        users_ds = dataset_map["analytics.users"]
        lineage = DatasetLineage(
            upstream_dataset_id=users_ds.id,
            downstream_dataset_id=events_ds.id,
            transformation_type="join",
        )
        db.add(lineage)
        print(f"  ✓ {users_ds.display_name} → {events_ds.display_name} (join)")
    
    # 2. analytics.revenue depends on analytics.events (revenue calculated from events)
    if "analytics.revenue" in dataset_map and "analytics.events" in dataset_map:
        revenue_ds = dataset_map["analytics.revenue"]
        events_ds = dataset_map["analytics.events"]
        lineage = DatasetLineage(
            upstream_dataset_id=events_ds.id,
            downstream_dataset_id=revenue_ds.id,
            transformation_type="aggregate",
        )
        db.add(lineage)
        print(f"  ✓ {events_ds.display_name} → {revenue_ds.display_name} (aggregate)")
    
    # 3. analytics.revenue also depends on analytics.users (for user segmentation)
    if "analytics.revenue" in dataset_map and "analytics.users" in dataset_map:
        revenue_ds = dataset_map["analytics.revenue"]
        users_ds = dataset_map["analytics.users"]
        lineage = DatasetLineage(
            upstream_dataset_id=users_ds.id,
            downstream_dataset_id=revenue_ds.id,
            transformation_type="join",
        )
        db.add(lineage)
        print(f"  ✓ {users_ds.display_name} → {revenue_ds.display_name} (join)")

    # 4. analytics.user_activity depends on analytics.page_views (aggregate page views)
    if "analytics.user_activity" in dataset_map and "analytics.page_views" in dataset_map:
        activity_ds = dataset_map["analytics.user_activity"]
        page_views_ds = dataset_map["analytics.page_views"]
        lineage = DatasetLineage(
            upstream_dataset_id=page_views_ds.id,
            downstream_dataset_id=activity_ds.id,
            transformation_type="aggregate",
        )
        db.add(lineage)
        print(f"  ✓ {page_views_ds.display_name} → {activity_ds.display_name} (aggregate)")

    # 5. analytics.customer_segments depends on analytics.users (user segmentation)
    if "analytics.customer_segments" in dataset_map and "analytics.users" in dataset_map:
        segments_ds = dataset_map["analytics.customer_segments"]
        users_ds = dataset_map["analytics.users"]
        lineage = DatasetLineage(
            upstream_dataset_id=users_ds.id,
            downstream_dataset_id=segments_ds.id,
            transformation_type="transform",
        )
        db.add(lineage)
        print(f"  ✓ {users_ds.display_name} → {segments_ds.display_name} (transform)")

    # 6. analytics.revenue depends on analytics.orders (revenue calculated from orders)
    if "analytics.revenue" in dataset_map and "analytics.orders" in dataset_map:
        revenue_ds = dataset_map["analytics.revenue"]
        orders_ds = dataset_map["analytics.orders"]
        lineage = DatasetLineage(
            upstream_dataset_id=orders_ds.id,
            downstream_dataset_id=revenue_ds.id,
            transformation_type="aggregate",
        )
        db.add(lineage)
        print(f"  ✓ {orders_ds.display_name} → {revenue_ds.display_name} (aggregate)")

    # 7. ml.feature_store depends on analytics.users (features derived from user data)
    if "ml.feature_store" in dataset_map and "analytics.users" in dataset_map:
        features_ds = dataset_map["ml.feature_store"]
        users_ds = dataset_map["analytics.users"]
        lineage = DatasetLineage(
            upstream_dataset_id=users_ds.id,
            downstream_dataset_id=features_ds.id,
            transformation_type="feature_engineering",
        )
        db.add(lineage)
        print(f"  ✓ {users_ds.display_name} → {features_ds.display_name} (feature_engineering)")

    # 8. analytics.user_activity depends on analytics.users (user activity joins with user data)
    if "analytics.user_activity" in dataset_map and "analytics.users" in dataset_map:
        activity_ds = dataset_map["analytics.user_activity"]
        users_ds = dataset_map["analytics.users"]
        lineage = DatasetLineage(
            upstream_dataset_id=users_ds.id,
            downstream_dataset_id=activity_ds.id,
            transformation_type="join",
        )
        db.add(lineage)
        print(f"  ✓ {users_ds.display_name} → {activity_ds.display_name} (join)")
    
    db.flush()
    
    # Column-level lineage examples:
    # Get columns for each dataset and create a lookup map
    column_map = {}  # (dataset_full_name, column_name) -> DatasetColumn
    for dataset in datasets:
        columns = db.query(DatasetColumn).filter(DatasetColumn.dataset_id == dataset.id).all()
        for col in columns:
            column_map[(dataset.full_name, col.name)] = col
    
    # 1. events.user_id depends on users.user_id
    if "analytics.events" in dataset_map and "analytics.users" in dataset_map:
        events_ds = dataset_map["analytics.events"]
        users_ds = dataset_map["analytics.users"]
        
        events_user_id_col = column_map.get(("analytics.events", "user_id"))
        users_user_id_col = column_map.get(("analytics.users", "user_id"))
        
        if events_user_id_col and users_user_id_col:
            lineage = ColumnLineage(
                upstream_column_id=users_user_id_col.id,
                downstream_column_id=events_user_id_col.id,
                transformation_expression="JOIN users ON events.user_id = users.user_id",
            )
            db.add(lineage)
            print(f"  ✓ Column: {users_ds.display_name}.user_id → {events_ds.display_name}.user_id")
    
    # 2. revenue.revenue_amount depends on events (aggregated)
    if "analytics.revenue" in dataset_map and "analytics.events" in dataset_map:
        revenue_ds = dataset_map["analytics.revenue"]
        events_ds = dataset_map["analytics.events"]
        
        revenue_amount_col = column_map.get(("analytics.revenue", "revenue_amount"))
        events_properties_col = column_map.get(("analytics.events", "properties"))
        
        if revenue_amount_col and events_properties_col:
            lineage = ColumnLineage(
                upstream_column_id=events_properties_col.id,
                downstream_column_id=revenue_amount_col.id,
                transformation_expression="SUM(events.properties->>'amount')",
            )
            db.add(lineage)
            print(f"  ✓ Column: {events_ds.display_name}.properties → {revenue_ds.display_name}.revenue_amount")
    
    # 3. revenue.transaction_count depends on events (count aggregation)
    if "analytics.revenue" in dataset_map and "analytics.events" in dataset_map:
        revenue_ds = dataset_map["analytics.revenue"]
        events_ds = dataset_map["analytics.events"]
        
        transaction_count_col = column_map.get(("analytics.revenue", "transaction_count"))
        events_event_id_col = column_map.get(("analytics.events", "event_id"))
        
        if transaction_count_col and events_event_id_col:
            lineage = ColumnLineage(
                upstream_column_id=events_event_id_col.id,
                downstream_column_id=transaction_count_col.id,
                transformation_expression="COUNT(events.event_id)",
            )
            db.add(lineage)
            print(f"  ✓ Column: {events_ds.display_name}.event_id → {revenue_ds.display_name}.transaction_count")
    
    # 4. events.timestamp might be used in revenue.date (date extraction)
    if "analytics.revenue" in dataset_map and "analytics.events" in dataset_map:
        revenue_ds = dataset_map["analytics.revenue"]
        events_ds = dataset_map["analytics.events"]
        
        revenue_date_col = column_map.get(("analytics.revenue", "date"))
        events_timestamp_col = column_map.get(("analytics.events", "timestamp"))
        
        if revenue_date_col and events_timestamp_col:
            lineage = ColumnLineage(
                upstream_column_id=events_timestamp_col.id,
                downstream_column_id=revenue_date_col.id,
                transformation_expression="DATE(events.timestamp)",
            )
            db.add(lineage)
            print(f"  ✓ Column: {events_ds.display_name}.timestamp → {revenue_ds.display_name}.date")

    # Column lineage: page_views -> user_activity
    if "analytics.page_views" in dataset_map and "analytics.user_activity" in dataset_map:
        page_views_ds = dataset_map["analytics.page_views"]
        activity_ds = dataset_map["analytics.user_activity"]
        
        activity_page_views_col = column_map.get(("analytics.user_activity", "page_views"))
        page_views_view_id_col = column_map.get(("analytics.page_views", "view_id"))
        
        if activity_page_views_col and page_views_view_id_col:
            lineage = ColumnLineage(
                upstream_column_id=page_views_view_id_col.id,
                downstream_column_id=activity_page_views_col.id,
                transformation_expression="COUNT(view_id)",
            )
            db.add(lineage)
            print(f"  ✓ Column: {page_views_ds.display_name}.view_id → {activity_ds.display_name}.page_views")

    # Column lineage: users -> customer_segments
    if "analytics.users" in dataset_map and "analytics.customer_segments" in dataset_map:
        users_ds = dataset_map["analytics.users"]
        segments_ds = dataset_map["analytics.customer_segments"]
        
        segments_customer_id_col = column_map.get(("analytics.customer_segments", "customer_id"))
        users_user_id_col = column_map.get(("analytics.users", "user_id"))
        
        if segments_customer_id_col and users_user_id_col:
            lineage = ColumnLineage(
                upstream_column_id=users_user_id_col.id,
                downstream_column_id=segments_customer_id_col.id,
                transformation_expression="user_id",
            )
            db.add(lineage)
            print(f"  ✓ Column: {users_ds.display_name}.user_id → {segments_ds.display_name}.customer_id")

    # Column lineage: orders -> revenue
    if "analytics.orders" in dataset_map and "analytics.revenue" in dataset_map:
        orders_ds = dataset_map["analytics.orders"]
        revenue_ds = dataset_map["analytics.revenue"]
        
        revenue_amount_col = column_map.get(("analytics.revenue", "revenue_amount"))
        orders_total_amount_col = column_map.get(("analytics.orders", "total_amount"))
        
        if revenue_amount_col and orders_total_amount_col:
            lineage = ColumnLineage(
                upstream_column_id=orders_total_amount_col.id,
                downstream_column_id=revenue_amount_col.id,
                transformation_expression="SUM(total_amount)",
            )
            db.add(lineage)
            print(f"  ✓ Column: {orders_ds.display_name}.total_amount → {revenue_ds.display_name}.revenue_amount")
    
    db.commit()
    print("✅ Lineage relationships created successfully!")


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

