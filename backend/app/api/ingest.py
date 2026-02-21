"""
Ingestion endpoints for datasets.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.schemas import DatasetDetailResponse, MetadataIngestRequest
from app.db import get_db
from app.models import (
    Dataset,
    DatasetColumn,
    DatasetLineage,
    DatasetTag,
    ReadinessStatusEnum,
)
from app.services.dbt_parser import (
    DbtParseError,
    merge_model_data,
    parse_catalog,
    parse_manifest,
)
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

    logger.info("Starting mock data ingestion (%d datasets)", len(datasets_config))
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
            logger.error("Failed to ingest dataset %s: %s", config.get("full_name", "unknown"), e)
            errors.append(
                {
                    "full_name": config.get("full_name", "unknown"),
                    "error": str(e),
                }
            )
            db.rollback()

    logger.info("Mock ingestion complete: %d ingested, %d errors", len(created_datasets), len(errors))
    return {
        "ingested": len(created_datasets),
        "errors": len(errors),
        "datasets": created_datasets,
        "error_details": errors if errors else None,
    }


def _upsert_dataset(
    db: Session,
    full_name: str,
    fields: Dict[str, Any],
) -> tuple[Dataset, bool]:
    """
    Upsert a dataset by full_name.

    Args:
        db: Database session
        full_name: Unique dataset identifier
        fields: Dict of fields to set on the dataset

    Returns:
        Tuple of (dataset, is_new) where is_new indicates creation vs update
    """
    existing = (
        db.query(Dataset)
        .filter(Dataset.full_name == full_name)
        .first()
    )

    if existing:
        # Update existing dataset with provided fields
        for key, value in fields.items():
            if value is not None and hasattr(existing, key):
                setattr(existing, key, value)
        existing.last_seen_at = datetime.utcnow()
        return existing, False
    else:
        # Create new dataset
        dataset = Dataset(
            full_name=full_name,
            display_name=fields.get("display_name") or full_name.split(".")[-1],
            last_seen_at=datetime.utcnow(),
            readiness_score=0,
            readiness_status=ReadinessStatusEnum.DRAFT,
        )
        # Set optional fields
        for key, value in fields.items():
            if value is not None and hasattr(dataset, key):
                setattr(dataset, key, value)
        db.add(dataset)
        db.flush()
        return dataset, True


def _upsert_columns(
    db: Session,
    dataset: Dataset,
    columns: List[Dict[str, Any]],
) -> None:
    """
    Upsert columns for a dataset by name.

    Args:
        db: Database session
        dataset: Dataset model instance
        columns: List of column dicts with name, description, type, nullable
    """
    for col_data in columns:
        col_name = col_data.get("name", "")
        if not col_name:
            continue

        existing_col = (
            db.query(DatasetColumn)
            .filter(
                DatasetColumn.dataset_id == dataset.id,
                DatasetColumn.name == col_name,
            )
            .first()
        )

        if existing_col:
            # Update existing column
            if col_data.get("description") is not None:
                existing_col.description = col_data["description"]
            if col_data.get("type") is not None:
                existing_col.type = col_data["type"]
            if col_data.get("nullable") is not None:
                existing_col.nullable = (
                    1 if col_data["nullable"] is True
                    else (0 if col_data["nullable"] is False else None)
                )
            existing_col.last_seen_at = datetime.utcnow()
        else:
            # Create new column
            db_column = DatasetColumn(
                dataset_id=dataset.id,
                name=col_name,
                description=col_data.get("description"),
                type=col_data.get("type"),
                nullable=(
                    1 if col_data.get("nullable") is True
                    else (0 if col_data.get("nullable") is False else None)
                ),
                last_seen_at=datetime.utcnow(),
            )
            db.add(db_column)


def _extract_lineage_from_manifest(
    db: Session,
    manifest_data: Dict[str, Any],
    manifest_models: Dict[str, Any],
) -> int:
    """
    Extract lineage relationships from manifest parent_map.

    Args:
        db: Database session
        manifest_data: Raw manifest JSON data
        manifest_models: Parsed models from parse_manifest()

    Returns:
        Number of lineage relationships created
    """
    parent_map = manifest_data.get("parent_map", {})
    if not parent_map:
        return 0

    # Build a lookup from unique_id to full_name
    unique_id_to_full_name = {
        uid: model["full_name"] for uid, model in manifest_models.items()
    }

    lineage_count = 0

    for child_uid, parent_uids in parent_map.items():
        # Only process model nodes
        if child_uid not in unique_id_to_full_name:
            continue

        child_full_name = unique_id_to_full_name[child_uid]
        child_dataset = (
            db.query(Dataset)
            .filter(Dataset.full_name == child_full_name)
            .first()
        )
        if not child_dataset:
            continue

        for parent_uid in parent_uids:
            # Parent can be a model or a source
            if parent_uid in unique_id_to_full_name:
                parent_full_name = unique_id_to_full_name[parent_uid]
            elif parent_uid.startswith("source."):
                # Parse source unique_id: source.<project>.<source_name>.<table_name>
                parts = parent_uid.split(".")
                if len(parts) >= 4:
                    parent_full_name = f"{parts[2]}.{parts[3]}"
                elif len(parts) == 3:
                    parent_full_name = f"{parts[1]}.{parts[2]}"
                else:
                    continue
            else:
                # Skip non-model, non-source parents (e.g., tests, seeds)
                continue

            parent_dataset = (
                db.query(Dataset)
                .filter(Dataset.full_name == parent_full_name)
                .first()
            )
            if not parent_dataset:
                continue

            # Check if lineage relationship already exists
            existing_lineage = (
                db.query(DatasetLineage)
                .filter(
                    DatasetLineage.upstream_dataset_id == parent_dataset.id,
                    DatasetLineage.downstream_dataset_id == child_dataset.id,
                )
                .first()
            )
            if not existing_lineage:
                lineage = DatasetLineage(
                    upstream_dataset_id=parent_dataset.id,
                    downstream_dataset_id=child_dataset.id,
                    transformation_type="dbt",
                )
                db.add(lineage)
                lineage_count += 1

    return lineage_count


@router.post("/dbt", response_model=dict)
async def ingest_dbt(
    manifest: UploadFile = File(...),
    catalog: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    """
    Ingest datasets from dbt manifest.json and optional catalog.json.

    This endpoint:
    1. Parses dbt manifest to extract models
    2. Optionally parses catalog for column type information
    3. Merges manifest and catalog data
    4. Upserts datasets and columns
    5. Extracts lineage from manifest parent_map
    6. Scores each dataset

    Args:
        manifest: dbt manifest.json file (required)
        catalog: dbt catalog.json file (optional)

    Returns:
        Summary with ingested count and per-dataset scores
    """
    # Parse manifest
    try:
        manifest_content = await manifest.read()
        manifest_data = json.loads(manifest_content)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid manifest JSON: {e}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read manifest file: {e}")

    try:
        manifest_models = parse_manifest(manifest_data)
    except DbtParseError as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse manifest: {e}")

    if not manifest_models:
        raise HTTPException(status_code=400, detail="No models found in manifest")

    # Parse catalog if provided
    catalog_columns: Dict[str, Dict[str, Any]] = {}
    if catalog is not None:
        try:
            catalog_content = await catalog.read()
            catalog_data = json.loads(catalog_content)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid catalog JSON: {e}")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to read catalog file: {e}")

        try:
            catalog_columns = parse_catalog(catalog_data)
        except DbtParseError as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse catalog: {e}")

    # Merge manifest and catalog data
    datasets_config = merge_model_data(manifest_models, catalog_columns)

    logger.info("Starting dbt ingestion (%d models)", len(datasets_config))
    ingested_datasets = []
    errors = []

    for config in datasets_config:
        try:
            # Upsert dataset
            fields = {
                "display_name": config.get("display_name"),
                "owner_name": config.get("owner_name"),
                "owner_contact": config.get("owner_contact"),
                "description": config.get("description"),
                "intended_use": config.get("intended_use"),
                "limitations": config.get("limitations"),
            }
            dataset, is_new = _upsert_dataset(db, config["full_name"], fields)

            # Upsert columns from merged data
            columns = config.get("columns", [])
            if columns:
                _upsert_columns(db, dataset, columns)

            # Prepare metadata for scoring
            metadata = {
                "owner_name": config.get("owner_name"),
                "owner_contact": config.get("owner_contact"),
                "description": config.get("description"),
                "columns": columns,
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

            dataset = score_and_save_dataset(db, dataset, metadata)
            db.commit()

            ingested_datasets.append(
                {
                    "full_name": dataset.full_name,
                    "score": dataset.readiness_score,
                }
            )

        except Exception as e:
            logger.error(
                "Failed to ingest dbt model %s: %s",
                config.get("full_name", "unknown"),
                e,
            )
            errors.append(
                {
                    "full_name": config.get("full_name", "unknown"),
                    "error": str(e),
                }
            )
            db.rollback()

    # Extract lineage from parent_map (after all datasets are created)
    try:
        lineage_count = _extract_lineage_from_manifest(db, manifest_data, manifest_models)
        db.commit()
        logger.info("Extracted %d lineage relationships from manifest", lineage_count)
    except Exception as e:
        logger.error("Failed to extract lineage: %s", e)
        db.rollback()
        lineage_count = 0

    logger.info(
        "dbt ingestion complete: %d ingested, %d errors",
        len(ingested_datasets),
        len(errors),
    )

    result = {
        "ingested": len(ingested_datasets),
        "datasets": ingested_datasets,
        "lineage_relationships": lineage_count,
    }
    if errors:
        result["errors"] = errors
    return result


@router.post("/metadata", response_model=dict)
def ingest_metadata(
    request: MetadataIngestRequest,
    db: Session = Depends(get_db),
):
    """
    Ingest or update datasets from generic metadata.

    This endpoint:
    1. Accepts a list of dataset metadata items
    2. Upserts each dataset by full_name
    3. Sets all provided fields (owner, description, classification, etc.)
    4. Replaces tags if provided
    5. Scores each dataset

    Args:
        request: MetadataIngestRequest with list of dataset items

    Returns:
        Summary with ingested/updated counts and per-dataset scores
    """
    logger.info("Starting metadata ingestion (%d datasets)", len(request.datasets))
    created_count = 0
    updated_count = 0
    result_datasets = []
    errors = []

    for item in request.datasets:
        try:
            # Build fields dict from the ingest item
            fields: Dict[str, Any] = {}
            if item.display_name is not None:
                fields["display_name"] = item.display_name
            if item.owner_name is not None:
                fields["owner_name"] = item.owner_name
            if item.description is not None:
                fields["description"] = item.description
            if item.classification is not None:
                fields["classification"] = item.classification
            if item.domain is not None:
                fields["domain"] = item.domain
            if item.location_type is not None:
                fields["location_type"] = item.location_type
            if item.location_data is not None:
                fields["location_data"] = item.location_data

            # Upsert dataset
            dataset, is_new = _upsert_dataset(db, item.full_name, fields)
            if is_new:
                created_count += 1
            else:
                updated_count += 1

            # Replace tags if provided
            if item.tags is not None:
                # Delete existing tags
                db.query(DatasetTag).filter(
                    DatasetTag.dataset_id == dataset.id
                ).delete()
                # Add new tags
                for tag_value in item.tags:
                    db_tag = DatasetTag(
                        dataset_id=dataset.id,
                        tag=tag_value,
                    )
                    db.add(db_tag)

            # Upsert columns if provided
            if item.columns is not None:
                columns_data = [
                    {
                        "name": col.name,
                        "description": col.description,
                        "type": col.type,
                        "nullable": col.nullable,
                    }
                    for col in item.columns
                ]
                _upsert_columns(db, dataset, columns_data)

            # Prepare metadata for scoring
            # Build columns list for the scoring engine
            scoring_columns = []
            if item.columns is not None:
                scoring_columns = [
                    {
                        "name": col.name,
                        "description": col.description,
                        "type": col.type,
                    }
                    for col in item.columns
                ]
            else:
                # Use existing columns from DB if not provided in request
                existing_cols = (
                    db.query(DatasetColumn)
                    .filter(DatasetColumn.dataset_id == dataset.id)
                    .all()
                )
                scoring_columns = [
                    {
                        "name": col.name,
                        "description": col.description,
                        "type": col.type,
                    }
                    for col in existing_cols
                ]

            metadata = {
                "owner_name": dataset.owner_name,
                "description": dataset.description,
                "columns": scoring_columns,
            }

            dataset = score_and_save_dataset(db, dataset, metadata)
            db.commit()

            result_datasets.append(
                {
                    "full_name": dataset.full_name,
                    "score": dataset.readiness_score,
                    "status": "created" if is_new else "updated",
                }
            )

        except Exception as e:
            logger.error(
                "Failed to ingest metadata for %s: %s",
                item.full_name,
                e,
            )
            errors.append(
                {
                    "full_name": item.full_name,
                    "error": str(e),
                }
            )
            db.rollback()

    logger.info(
        "Metadata ingestion complete: %d created, %d updated, %d errors",
        created_count,
        updated_count,
        len(errors),
    )

    result = {
        "ingested": created_count,
        "updated": updated_count,
        "datasets": result_datasets,
    }
    if errors:
        result["errors"] = errors
    return result

