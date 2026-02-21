"""
Dataset API endpoints.
"""

import logging
from typing import List, Optional
from uuid import UUID

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.api.response_builder import build_dataset_detail_response, column_to_response
from app.api.schemas import (
    ColumnLineageItem,
    ColumnLineageResponse,
    DatasetDetailResponse,
    DatasetLineageItem,
    DatasetLineageResponse,
    DatasetListItem,
    DatasetListResponse,
    UpdateMetadataRequest,
    UpdateOwnerRequest,
)
from app.db import get_db
from app.models import (
    ColumnLineage,
    Dataset,
    DatasetColumn,
    DatasetLineage,
    ReadinessStatusEnum,
)
from app.services.dataset_metadata import build_metadata_from_dataset
from app.services.scoring_service import score_and_save_dataset
from app.services.schema_generator import (
    columns_to_avro_schema,
    generate_protobuf_schema,
    generate_python_schema,
    generate_scala_schema,
)

router = APIRouter(prefix="/api/datasets", tags=["datasets"])


@router.get("", response_model=DatasetListResponse)
def list_datasets(
    status: Optional[str] = Query(None, description="Filter by readiness status (comma-separated for multiple)"),
    owner: Optional[str] = Query(None, description="Filter by owner name (comma-separated for multiple)"),
    location_type: Optional[str] = Query(None, description="Filter by location type (comma-separated for multiple)"),
    q: Optional[str] = Query(None, description="Search in full_name and display_name"),
    db: Session = Depends(get_db),
):
    """
    List datasets with optional filtering.

    Query parameters:
    - status: Filter by readiness status (comma-separated: draft, internal, production_ready, gold)
    - owner: Filter by owner name (comma-separated for multiple)
    - location_type: Filter by location type (comma-separated: s3, snowflake, databricks, bigquery, hive)
    - q: Search query for full_name and display_name
    """
    query = db.query(Dataset)

    # Filter by status (supports multiple comma-separated values)
    if status:
        valid_statuses = ["draft", "internal", "production_ready", "gold"]
        status_list = [s.strip().lower() for s in status.split(",")]
        invalid_statuses = [s for s in status_list if s not in valid_statuses]
        if invalid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status(es): {', '.join(invalid_statuses)}. Must be one of: {', '.join(valid_statuses)}",
            )
        query = query.filter(Dataset.readiness_status.in_(status_list))

    # Filter by owner (supports multiple comma-separated values)
    if owner:
        owner_list = [o.strip() for o in owner.split(",")]
        query = query.filter(Dataset.owner_name.in_(owner_list))

    # Filter by location type (supports multiple comma-separated values)
    if location_type:
        location_list = [l.strip().lower() for l in location_type.split(",")]
        query = query.filter(Dataset.location_type.in_(location_list))

    # Search query (supports comma-separated dataset names for exact matching)
    if q:
        # Check if it's comma-separated (multi-select) or single search term
        if ',' in q:
            # Multi-select: exact match on full_name or display_name
            dataset_names = [name.strip() for name in q.split(",")]
            query = query.filter(
                or_(
                    Dataset.full_name.in_(dataset_names),
                    Dataset.display_name.in_(dataset_names),
                )
            )
        else:
            # Single search term: partial match (LIKE)
            search_filter = or_(
                Dataset.full_name.ilike(f"%{q}%"),
                Dataset.display_name.ilike(f"%{q}%"),
            )
            query = query.filter(search_filter)

    # Get total count before pagination
    total = query.count()

    # Order by score descending
    datasets = query.order_by(Dataset.readiness_score.desc()).all()

    # Convert to response schemas
    dataset_items = [
        DatasetListItem(
            id=ds.id,
            full_name=ds.full_name,
            display_name=ds.display_name,
            owner_name=ds.owner_name,
            readiness_score=ds.readiness_score,
            readiness_status=ds.readiness_status.value if isinstance(ds.readiness_status, ReadinessStatusEnum) else str(ds.readiness_status),
            last_scored_at=ds.last_scored_at,
            location_type=ds.location_type,
            location_data=ds.location_data,
        )
        for ds in datasets
    ]

    return DatasetListResponse(datasets=dataset_items, total=total)


@router.get("/{dataset_id}", response_model=DatasetDetailResponse)
def get_dataset(dataset_id: UUID, db: Session = Depends(get_db)):
    """
    Get detailed information about a dataset.

    Includes:
    - Basic metadata
    - Readiness score and status
    - Dimension scores breakdown
    - Reasons for point losses
    - Recommended actions
    - Score history
    """
    return build_dataset_detail_response(db, dataset_id)


@router.post("/{dataset_id}/owner", response_model=DatasetDetailResponse)
def update_owner(
    dataset_id: UUID,
    request: UpdateOwnerRequest,
    db: Session = Depends(get_db),
):
    """
    Update dataset owner and contact information.
    Triggers re-scoring and saves score history.
    """
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        logger.warning("Dataset not found for owner update: %s", dataset_id)
        raise HTTPException(status_code=404, detail="Dataset not found")

    logger.info("Updating owner for dataset %s", dataset_id)
    # Update owner fields
    if request.owner_name is not None:
        dataset.owner_name = request.owner_name
    if request.owner_contact is not None:
        dataset.owner_contact = request.owner_contact

    # Build metadata for scoring (using existing columns if available)
    metadata = build_metadata_from_dataset(dataset, columns=[])

    # Re-score the dataset (this saves history and updates actions)
    score_and_save_dataset(db, dataset, metadata)

    db.commit()
    db.refresh(dataset)

    return build_dataset_detail_response(db, dataset_id)


@router.post("/{dataset_id}/metadata", response_model=DatasetDetailResponse)
def update_metadata(
    dataset_id: UUID,
    request: UpdateMetadataRequest,
    db: Session = Depends(get_db),
):
    """
    Update dataset metadata (display_name, intended_use, limitations).
    Triggers re-scoring and saves score history.
    """
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        logger.warning("Dataset not found for metadata update: %s", dataset_id)
        raise HTTPException(status_code=404, detail="Dataset not found")

    logger.info("Updating metadata for dataset %s", dataset_id)
    # Update metadata fields
    if request.display_name is not None:
        dataset.display_name = request.display_name
    if request.intended_use is not None:
        dataset.intended_use = request.intended_use
    if request.limitations is not None:
        dataset.limitations = request.limitations

    # Build metadata for scoring (using existing columns if available)
    metadata = build_metadata_from_dataset(dataset, columns=[])

    # Re-score the dataset (this saves history and updates actions)
    score_and_save_dataset(db, dataset, metadata)

    db.commit()
    db.refresh(dataset)

    return build_dataset_detail_response(db, dataset_id)


@router.get("/{dataset_id}/schema/protobuf")
def get_protobuf_schema(dataset_id: UUID, db: Session = Depends(get_db)):
    """
    Generate Protocol Buffers schema for a dataset.
    """
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Get columns
    columns = (
        db.query(DatasetColumn)
        .filter(DatasetColumn.dataset_id == dataset_id)
        .order_by(DatasetColumn.name)
        .all()
    )

    if not columns:
        raise HTTPException(
            status_code=400, detail="Dataset has no columns. Cannot generate schema."
        )

    # Convert columns to response format
    column_responses = [column_to_response(c) for c in columns]

    # Generate namespace from dataset name
    namespace = ".".join(dataset.full_name.split(".")[:-1]) if "." in dataset.full_name else "com.example"

    # Convert to Avro schema
    avro_schema = columns_to_avro_schema(
        dataset_name=dataset.display_name or dataset.full_name,
        namespace=namespace,
        columns=column_responses,
        description=dataset.description,
    )

    # Generate protobuf schema
    try:
        proto_schema, proto_tests = generate_protobuf_schema(avro_schema)
        return {
            "schema": proto_schema,
            "test_code": proto_tests,
            "format": "protobuf",
            "dataset_name": dataset.display_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate protobuf schema: {str(e)}")


@router.get("/{dataset_id}/schema/scala")
def get_scala_schema(dataset_id: UUID, db: Session = Depends(get_db)):
    """
    Generate Java classes for a dataset (Scala-compatible).
    """
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Get columns
    columns = (
        db.query(DatasetColumn)
        .filter(DatasetColumn.dataset_id == dataset_id)
        .order_by(DatasetColumn.name)
        .all()
    )

    if not columns:
        raise HTTPException(
            status_code=400, detail="Dataset has no columns. Cannot generate schema."
        )

    # Convert columns to response format
    column_responses = [column_to_response(c) for c in columns]

    # Generate namespace from dataset name
    namespace = ".".join(dataset.full_name.split(".")[:-1]) if "." in dataset.full_name else "com.example"

    # Convert to Avro schema
    avro_schema = columns_to_avro_schema(
        dataset_name=dataset.display_name or dataset.full_name,
        namespace=namespace,
        columns=column_responses,
        description=dataset.description,
    )

    # Generate Scala schema
    try:
        scala_schema, scala_tests = generate_scala_schema(avro_schema)
        return {
            "schema": scala_schema,
            "test_code": scala_tests,
            "format": "scala",
            "dataset_name": dataset.display_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate Scala schema: {str(e)}")


@router.get("/{dataset_id}/schema/python")
def get_python_schema(dataset_id: UUID, db: Session = Depends(get_db)):
    """
    Generate Python dataclass for a dataset.
    """
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Get columns
    columns = (
        db.query(DatasetColumn)
        .filter(DatasetColumn.dataset_id == dataset_id)
        .order_by(DatasetColumn.name)
        .all()
    )

    if not columns:
        raise HTTPException(
            status_code=400, detail="Dataset has no columns. Cannot generate schema."
        )

    # Convert columns to response format
    column_responses = [column_to_response(c) for c in columns]

    # Generate namespace from dataset name
    namespace = ".".join(dataset.full_name.split(".")[:-1]) if "." in dataset.full_name else "com.example"

    # Convert to Avro schema
    avro_schema = columns_to_avro_schema(
        dataset_name=dataset.display_name or dataset.full_name,
        namespace=namespace,
        columns=column_responses,
        description=dataset.description,
    )

    # Generate Python schema
    try:
        python_schema, python_tests = generate_python_schema(avro_schema)
        return {
            "schema": python_schema,
            "test_code": python_tests,
            "format": "python",
            "dataset_name": dataset.display_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate Python schema: {str(e)}")


@router.get("/{dataset_id}/lineage", response_model=DatasetLineageResponse)
def get_dataset_lineage(dataset_id: UUID, db: Session = Depends(get_db)):
    """
    Get dataset lineage (upstream and downstream relationships).
    """
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Get upstream lineage with joined datasets (fixes N+1)
    upstream_lineage = (
        db.query(DatasetLineage)
        .options(joinedload(DatasetLineage.upstream_dataset))
        .filter(DatasetLineage.downstream_dataset_id == dataset_id)
        .all()
    )

    upstream_items = []
    for lineage in upstream_lineage:
        upstream_ds = lineage.upstream_dataset
        if upstream_ds:
            upstream_items.append(
                DatasetLineageItem(
                    id=upstream_ds.id,
                    full_name=upstream_ds.full_name,
                    display_name=upstream_ds.display_name or upstream_ds.full_name,
                    transformation_type=lineage.transformation_type,
                )
            )

    # Get downstream lineage with joined datasets (fixes N+1)
    downstream_lineage = (
        db.query(DatasetLineage)
        .options(joinedload(DatasetLineage.downstream_dataset))
        .filter(DatasetLineage.upstream_dataset_id == dataset_id)
        .all()
    )

    downstream_items = []
    for lineage in downstream_lineage:
        downstream_ds = lineage.downstream_dataset
        if downstream_ds:
            downstream_items.append(
                DatasetLineageItem(
                    id=downstream_ds.id,
                    full_name=downstream_ds.full_name,
                    display_name=downstream_ds.display_name or downstream_ds.full_name,
                    transformation_type=lineage.transformation_type,
                )
            )

    return DatasetLineageResponse(upstream=upstream_items, downstream=downstream_items)


@router.get("/{dataset_id}/columns/{column_id}/lineage", response_model=ColumnLineageResponse)
def get_column_lineage(dataset_id: UUID, column_id: UUID, db: Session = Depends(get_db)):
    """
    Get column-level lineage (upstream and downstream relationships).
    """
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    column = db.query(DatasetColumn).filter(
        DatasetColumn.id == column_id,
        DatasetColumn.dataset_id == dataset_id
    ).first()
    if not column:
        raise HTTPException(status_code=404, detail="Column not found")

    # Get upstream lineage with joined columns and datasets (fixes N+1)
    upstream_lineage = (
        db.query(ColumnLineage)
        .options(joinedload(ColumnLineage.upstream_column).joinedload(DatasetColumn.dataset))
        .filter(ColumnLineage.downstream_column_id == column_id)
        .all()
    )

    upstream_items = []
    for lineage in upstream_lineage:
        upstream_col = lineage.upstream_column
        if upstream_col and upstream_col.dataset:
            upstream_items.append(
                ColumnLineageItem(
                    id=lineage.id,
                    upstream_column_id=lineage.upstream_column_id,
                    downstream_column_id=lineage.downstream_column_id,
                    upstream_column_name=upstream_col.name,
                    upstream_dataset_id=upstream_col.dataset.id,
                    upstream_dataset_name=upstream_col.dataset.display_name or upstream_col.dataset.full_name,
                    downstream_column_name=column.name,
                    downstream_dataset_id=dataset.id,
                    downstream_dataset_name=dataset.display_name or dataset.full_name,
                    transformation_expression=lineage.transformation_expression,
                    created_at=lineage.created_at,
                )
            )

    # Get downstream lineage with joined columns and datasets (fixes N+1)
    downstream_lineage = (
        db.query(ColumnLineage)
        .options(joinedload(ColumnLineage.downstream_column).joinedload(DatasetColumn.dataset))
        .filter(ColumnLineage.upstream_column_id == column_id)
        .all()
    )

    downstream_items = []
    for lineage in downstream_lineage:
        downstream_col = lineage.downstream_column
        if downstream_col and downstream_col.dataset:
            downstream_items.append(
                ColumnLineageItem(
                    id=lineage.id,
                    upstream_column_id=lineage.upstream_column_id,
                    downstream_column_id=lineage.downstream_column_id,
                    upstream_column_name=column.name,
                    upstream_dataset_id=dataset.id,
                    upstream_dataset_name=dataset.display_name or dataset.full_name,
                    downstream_column_name=downstream_col.name,
                    downstream_dataset_id=downstream_col.dataset.id,
                    downstream_dataset_name=downstream_col.dataset.display_name or downstream_col.dataset.full_name,
                    transformation_expression=lineage.transformation_expression,
                    created_at=lineage.created_at,
                )
            )

    return ColumnLineageResponse(upstream=upstream_items, downstream=downstream_items)
