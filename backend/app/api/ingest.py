"""
Mock ingestion endpoint for demo data.
"""

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas import DatasetDetailResponse
from app.db import get_db
from app.models import Dataset, ReadinessStatusEnum
from app.services.scoring_service import score_and_save_dataset

router = APIRouter(prefix="/api/ingest", tags=["ingest"])


def _create_mock_datasets() -> List[dict]:
    """
    Create 10 realistic datasets with varying readiness attributes.

    Returns:
        List of dataset metadata dictionaries
    """
    return [
        {
            "full_name": "analytics.users",
            "display_name": "Users Table",
            "owner_name": "Data Team",
            "owner_contact": "#data-team",
            "description": "Comprehensive user profile and account information. Contains user demographics, preferences, and account settings.",
            "intended_use": "Analytics, user segmentation, ML training, personalization",
            "limitations": "Data delayed by 1 hour for processing. Some historical data may be incomplete.",
            "columns": [
                {"name": "user_id", "description": "Unique user identifier (UUID)"},
                {"name": "email", "description": "User email address (verified)"},
                {"name": "created_at", "description": "Account creation timestamp"},
                {"name": "updated_at", "description": "Last profile update timestamp"},
                {"name": "status", "description": "Account status (active, inactive, suspended)"},
                {"name": "preferences", "description": "JSON object with user preferences"},
            ],
            "has_freshness_checks": True,
            "has_volume_checks": True,
            "dbt_test_count": 12,
            "has_sla": True,
            "breaking_changes_30d": 0,
            "has_release_notes": True,
            "has_versioning": True,
            "backward_compatible": True,
        },
        {
            "full_name": "analytics.events",
            "display_name": "User Events",
            "owner_name": "Analytics Team",
            "owner_contact": "analytics@example.com",
            "description": "User interaction events and tracking data from web and mobile applications",
            "intended_use": "Analytics, experimentation, funnel analysis",
            "limitations": "Some events may be delayed up to 5 minutes. High-volume table with retention policy.",
            "columns": [
                {"name": "event_id", "description": "Unique event identifier"},
                {"name": "user_id", "description": "User who triggered the event"},
                {"name": "event_type", "description": "Type of event (click, view, purchase, etc.)"},
                {"name": "timestamp", "description": "Event timestamp (UTC)"},
                {"name": "properties"},  # Missing description
                {"name": "session_id", "description": "User session identifier"},
            ],
            "has_freshness_checks": True,
            "has_volume_checks": False,
            "has_sla": False,
            "breaking_changes_30d": 1,
            "has_release_notes": False,
        },
        {
            "full_name": "staging.raw_logs",
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
                {"name": "deprecated_field"},  # Legacy column
            ],
            "has_freshness_checks": False,
            "has_volume_checks": False,
        },
        {
            "full_name": "analytics.revenue",
            "display_name": "Revenue Metrics",
            "owner_name": "Finance Team",
            "owner_contact": "#finance-data",
            "description": "Daily revenue and transaction metrics aggregated by region and product",
            "intended_use": "Financial reporting, forecasting, executive dashboards",
            "limitations": "Revenue data finalized at end of day. Historical corrections may occur.",
            "columns": [
                {"name": "date", "description": "Transaction date"},
                {"name": "revenue_amount", "description": "Total revenue in USD"},
                {"name": "transaction_count", "description": "Number of transactions"},
                {"name": "region", "description": "Geographic region code"},
                {"name": "product_category", "description": "Product category identifier"},
            ],
            "has_freshness_checks": True,
            "has_sla": True,
            "breaking_changes_30d": 0,
            "has_release_notes": True,
        },
        {
            "full_name": "experiments.ab_test_results",
            "display_name": "A/B Test Results",
            "owner_name": "Experimentation Team",
            "description": "Results from A/B tests and experiments with statistical significance",
            "intended_use": "Experiment analysis, decision making",
            "columns": [
                {"name": "experiment_id", "description": "Experiment identifier"},
                {"name": "variant", "description": "Test variant (A or B)"},
                {"name": "metric_value"},  # Missing description
                {"name": "sample_size", "description": "Number of participants"},
            ],
            "has_freshness_checks": False,
        },
        {
            "full_name": "analytics.page_views",
            "display_name": "Page Views",
            "owner_name": "Product Analytics",
            "owner_contact": "#product-analytics",
            "description": "Page view events tracked across all web properties",
            "intended_use": "Content analytics, user journey analysis",
            "limitations": "Does not include mobile app views",
            "columns": [
                {"name": "view_id", "description": "Unique page view identifier"},
                {"name": "user_id", "description": "User identifier (nullable for anonymous)"},
                {"name": "page_path", "description": "URL path of the page"},
                {"name": "timestamp", "description": "View timestamp"},
                {"name": "referrer", "description": "HTTP referrer URL"},
                {"name": "device_type", "description": "Device category (desktop, mobile, tablet)"},
            ],
            "has_freshness_checks": True,
            "has_volume_checks": True,
            "dbt_test_count": 6,
            "has_sla": True,
            "breaking_changes_30d": 0,
            "has_release_notes": True,
        },
        {
            "full_name": "warehouse.inventory",
            "display_name": "Inventory Levels",
            "owner_name": "Operations",
            "description": "Current inventory levels by warehouse and SKU",
            "intended_use": "Inventory management, supply chain planning",
            "limitations": "Updated hourly. May not reflect real-time stock levels.",
            "columns": [
                {"name": "warehouse_id", "description": "Warehouse identifier"},
                {"name": "sku", "description": "Stock keeping unit"},
                {"name": "quantity", "description": "Available quantity"},
                {"name": "reserved_quantity", "description": "Reserved for orders"},
                {"name": "last_updated", "description": "Last inventory update timestamp"},
            ],
            "has_freshness_checks": True,
            "has_sla": True,
            "breaking_changes_30d": 0,
            "has_release_notes": False,
        },
        {
            "full_name": "marketing.campaigns",
            "display_name": "Marketing Campaigns",
            "owner_name": None,  # Missing owner
            "description": "Marketing campaign metadata and performance",
            "columns": [
                {"name": "campaign_id", "description": "Campaign identifier"},
                {"name": "campaign_name", "description": "Campaign display name"},
                {"name": "start_date", "description": "Campaign start date"},
                {"name": "end_date", "description": "Campaign end date"},
                {"name": "budget"},  # Missing description
                {"name": "status"},  # Missing description
            ],
            "has_freshness_checks": False,
            "has_volume_checks": False,
        },
        {
            "full_name": "analytics.conversions",
            "display_name": "Conversion Events",
            "owner_name": "Growth Team",
            "owner_contact": "#growth",
            "description": "Tracked conversion events including purchases, signups, and key actions",
            "intended_use": "Conversion funnel analysis, ROI calculation",
            "limitations": "Attribution window is 30 days. Some conversions may be delayed.",
            "columns": [
                {"name": "conversion_id", "description": "Unique conversion identifier"},
                {"name": "user_id", "description": "User who converted"},
                {"name": "conversion_type", "description": "Type of conversion (purchase, signup, etc.)"},
                {"name": "conversion_value", "description": "Monetary value of conversion"},
                {"name": "timestamp", "description": "Conversion timestamp"},
                {"name": "attribution_source", "description": "Marketing channel attribution"},
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
            "full_name": "legacy.old_transactions",
            "display_name": "Legacy Transactions",
            "owner_name": "Legacy Systems",
            "description": "Historical transaction data from legacy system (deprecated)",
            "intended_use": "Historical analysis only",
            "limitations": "No longer updated. Use analytics.transactions for current data.",
            "columns": [
                {"name": "txn_id"},
                {"name": "amount"},
                {"name": "date"},
                {"name": "old_format_data_tmp"},  # Legacy column
                {"name": "backup_old"},  # Legacy column
            ],
            "has_freshness_checks": False,
            "has_volume_checks": False,
            "has_sla": False,
        },
    ]


@router.post("/mock", response_model=dict)
def ingest_mock_data(db: Session = Depends(get_db)):
    """
    Ingest 10 mock datasets with varying readiness attributes.

    This endpoint:
    1. Creates 10 realistic datasets
    2. Scores each dataset using the scoring engine
    3. Saves all scoring results (dimension scores, reasons, actions)
    4. Records score history

    Returns:
        Summary of ingested datasets
    """
    # Get mock dataset configurations
    datasets_config = _create_mock_datasets()

    created_datasets = []
    errors = []

    for config in datasets_config:
        try:
            # Check if dataset already exists
            existing = (
                db.query(Dataset)
                .filter(Dataset.full_name == config["full_name"])
                .first()
            )
            if existing:
                # Update existing dataset
                dataset = existing
                dataset.display_name = config["display_name"]
                dataset.owner_name = config.get("owner_name")
                dataset.owner_contact = config.get("owner_contact")
                dataset.intended_use = config.get("intended_use")
                dataset.limitations = config.get("limitations")
                dataset.last_seen_at = datetime.utcnow()
            else:
                # Create new dataset
                dataset = Dataset(
                    full_name=config["full_name"],
                    display_name=config["display_name"],
                    owner_name=config.get("owner_name"),
                    owner_contact=config.get("owner_contact"),
                    intended_use=config.get("intended_use"),
                    limitations=config.get("limitations"),
                    last_seen_at=datetime.utcnow(),
                    readiness_score=0,  # Will be updated by scoring
                    readiness_status=ReadinessStatusEnum.DRAFT,
                )
                db.add(dataset)
                db.flush()  # Get the ID

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

            # Score and save
            dataset = score_and_save_dataset(db, dataset, metadata)
            db.commit()

            created_datasets.append(
                {
                    "id": str(dataset.id),
                    "full_name": dataset.full_name,
                    "display_name": dataset.display_name,
                    "readiness_score": dataset.readiness_score,
                    "readiness_status": dataset.readiness_status.value,
                }
            )

        except Exception as e:
            errors.append(
                {
                    "full_name": config.get("full_name", "unknown"),
                    "error": str(e),
                }
            )
            db.rollback()

    return {
        "ingested": len(created_datasets),
        "errors": len(errors),
        "datasets": created_datasets,
        "error_details": errors if errors else None,
    }

