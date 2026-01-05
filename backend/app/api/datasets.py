"""
Dataset API endpoints.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.api.schemas import (
    ActionResponse,
    ColumnResponse,
    DatasetDetailResponse,
    DatasetListItem,
    DatasetListResponse,
    DimensionScoreResponse,
    ReasonResponse,
    ScoreHistoryResponse,
    UpdateMetadataRequest,
    UpdateOwnerRequest,
    DatasetLineageResponse,
    ColumnLineageResponse,
    DatasetLineageItem,
    ColumnLineageItem,
)
from app.db import get_db
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
from app.services.dataset_metadata import build_metadata_from_dataset
from app.services.scoring_service import score_and_save_dataset
from app.services.schema_generator import (
    columns_to_avro_schema,
    generate_protobuf_schema,
    generate_scala_schema,
    generate_python_schema,
)

router = APIRouter(prefix="/api/datasets", tags=["datasets"])


def _dimension_score_to_response(dim_score: DatasetDimensionScore) -> DimensionScoreResponse:
    """Convert dimension score model to response schema.
    
    Contract v1: Returns stable shape with measured flag.
    """
    # dimension_key is stored as string, convert to value if it's an enum
    dimension_key_value = (
        dim_score.dimension_key.value
        if isinstance(dim_score.dimension_key, DimensionKeyEnum)
        else str(dim_score.dimension_key)
    )
    # Convert measured from integer (1/0) to boolean
    measured = bool(dim_score.measured) if hasattr(dim_score, "measured") else True
    return DimensionScoreResponse(
        dimension_key=dimension_key_value,
        points_awarded=dim_score.points_awarded,
        max_points=dim_score.max_points,
        measured=measured,
        percentage=(dim_score.points_awarded / dim_score.max_points * 100)
        if dim_score.max_points > 0
        else 0.0,
    )


def _reason_to_response(reason: DatasetReason) -> ReasonResponse:
    """Convert reason model to response schema."""
    # dimension_key is stored as string, convert to value if it's an enum
    dimension_key_value = (
        reason.dimension_key.value
        if isinstance(reason.dimension_key, DimensionKeyEnum)
        else str(reason.dimension_key)
    )
    return ReasonResponse(
        id=reason.id,
        dimension_key=dimension_key_value,
        reason_code=reason.reason_code,
        message=reason.message,
        points_lost=reason.points_lost,
    )


def _action_to_response(action: DatasetAction) -> ActionResponse:
    """Convert action model to response schema."""
    return ActionResponse(
        id=action.id,
        action_key=action.action_key,
        title=action.title,
        description=action.description,
        points_gain=action.points_gain,
        url=action.url,
    )


def _column_to_response(column: DatasetColumn) -> ColumnResponse:
    """Convert column model to response schema."""
    return ColumnResponse(
        id=column.id,
        name=column.name,
        description=column.description,
        type=column.type,
        nullable=bool(column.nullable) if column.nullable is not None else None,
    )


def _score_history_to_response(history: DatasetScoreHistory) -> ScoreHistoryResponse:
    """Convert score history model to response schema."""
    return ScoreHistoryResponse(
        id=history.id,
        readiness_score=history.readiness_score,
        recorded_at=history.recorded_at,
        scoring_version=history.scoring_version,
    )


@router.get("", response_model=DatasetListResponse)
def list_datasets(
    status: Optional[str] = Query(None, description="Filter by readiness status (comma-separated for multiple)"),
    owner: Optional[str] = Query(None, description="Filter by owner name"),
    q: Optional[str] = Query(None, description="Search in full_name and display_name"),
    db: Session = Depends(get_db),
):
    """
    List datasets with optional filtering.

    Query parameters:
    - status: Filter by readiness status (comma-separated: draft, internal, production_ready, gold)
    - owner: Filter by owner name
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

    # Filter by owner
    if owner:
        query = query.filter(Dataset.owner_name.ilike(f"%{owner}%"))

    # Search query
    if q:
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
    # Get dataset
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Get dimension scores
    dimension_scores = (
        db.query(DatasetDimensionScore)
        .filter(DatasetDimensionScore.dataset_id == dataset_id)
        .order_by(DatasetDimensionScore.dimension_key)
        .all()
    )

    # Get dimension scores to check measured status
    dimension_scores_dict = {
        ds.dimension_key.lower(): bool(ds.measured) if hasattr(ds, "measured") else True
        for ds in dimension_scores
    }

    # Get reasons - filter out reasons for unmeasured dimensions
    all_reasons = (
        db.query(DatasetReason)
        .filter(DatasetReason.dataset_id == dataset_id)
        .order_by(DatasetReason.dimension_key, DatasetReason.points_lost.desc())
        .all()
    )
    # Only include reasons for measured dimensions
    reasons = [
        r for r in all_reasons
        if dimension_scores_dict.get(r.dimension_key.lower(), True)
    ]

    # Helper to map action_key to dimension_key
    def get_dimension_key_from_action_key(action_key: str) -> Optional[str]:
        """Map action_key constant to dimension_key."""
        from app.scoring.constants import ActionKey
        
        mapping = {
            # Ownership
            ActionKey.ASSIGN_OWNER: "ownership",
            ActionKey.ADD_OWNER_CONTACT: "ownership",
            # Documentation
            ActionKey.ADD_DESCRIPTION: "documentation",
            ActionKey.DOCUMENT_COLUMNS: "documentation",
            # Schema hygiene
            ActionKey.FIX_NAMING: "schema_hygiene",
            ActionKey.REDUCE_NULLABLE_COLUMNS: "schema_hygiene",
            ActionKey.REMOVE_LEGACY_COLUMNS: "schema_hygiene",
            # Data quality
            ActionKey.ADD_QUALITY_CHECKS: "data_quality",
            ActionKey.DEFINE_SLA: "data_quality",
            ActionKey.RESOLVE_FAILURES: "data_quality",
            # Stability
            ActionKey.PREVENT_BREAKING_CHANGES: "stability",
            ActionKey.ADD_CHANGELOG: "stability",
            ActionKey.MAINTAIN_COMPATIBILITY: "stability",
            # Operational
            ActionKey.DEFINE_INTENDED_USE: "operational",
            ActionKey.DOCUMENT_LIMITATIONS: "operational",
        }
        return mapping.get(action_key)

    # Get actions - filter out actions for unmeasured dimensions
    all_actions = (
        db.query(DatasetAction)
        .filter(DatasetAction.dataset_id == dataset_id)
        .order_by(DatasetAction.points_gain.desc())
        .all()
    )
    # Only include actions for measured dimensions
    actions = [
        a for a in all_actions
        if dimension_scores_dict.get(
            get_dimension_key_from_action_key(a.action_key) or "", True
        )
    ]

    # Get columns (schema)
    columns = (
        db.query(DatasetColumn)
        .filter(DatasetColumn.dataset_id == dataset_id)
        .order_by(DatasetColumn.name)
        .all()
    )

    # Get score history (most recent first)
    score_history = (
        db.query(DatasetScoreHistory)
        .filter(DatasetScoreHistory.dataset_id == dataset_id)
        .order_by(DatasetScoreHistory.recorded_at.desc())
        .limit(30)  # Limit to last 30 entries
        .all()
    )

    # Build response
    return DatasetDetailResponse(
        id=dataset.id,
        full_name=dataset.full_name,
        display_name=dataset.display_name,
        description=dataset.description if hasattr(dataset, "description") else None,
        owner_name=dataset.owner_name,
        owner_contact=dataset.owner_contact,
        intended_use=dataset.intended_use,
        limitations=dataset.limitations,
        location_type=dataset.location_type if hasattr(dataset, "location_type") else None,
        location_data=dataset.location_data if hasattr(dataset, "location_data") else None,
        last_seen_at=dataset.last_seen_at,
        last_scored_at=dataset.last_scored_at,
        readiness_score=dataset.readiness_score,
        readiness_status=dataset.readiness_status.value if isinstance(dataset.readiness_status, ReadinessStatusEnum) else str(dataset.readiness_status),
        dimension_scores=[_dimension_score_to_response(ds) for ds in dimension_scores],
        reasons=[_reason_to_response(r) for r in reasons],
        actions=[_action_to_response(a) for a in actions],
        columns=[_column_to_response(c) for c in columns],
        score_history=[_score_history_to_response(h) for h in score_history],
    )


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
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Update owner fields
    if request.owner_name is not None:
        dataset.owner_name = request.owner_name
    if request.owner_contact is not None:
        dataset.owner_contact = request.owner_contact

    # Build metadata for scoring (using existing columns if available)
    # Note: In a real system, we'd fetch column metadata from a separate table
    # For MVP, we'll use empty columns list
    metadata = build_metadata_from_dataset(dataset, columns=[])

    # Re-score the dataset (this saves history and updates actions)
    score_and_save_dataset(db, dataset, metadata)

    db.commit()
    db.refresh(dataset)

    # Return updated dataset detail
    return get_dataset(dataset_id, db)


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
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Update metadata fields
    if request.display_name is not None:
        dataset.display_name = request.display_name
    if request.intended_use is not None:
        dataset.intended_use = request.intended_use
    if request.limitations is not None:
        dataset.limitations = request.limitations

    # Build metadata for scoring (using existing columns if available)
    # Note: In a real system, we'd fetch column metadata from a separate table
    # For MVP, we'll use empty columns list
    metadata = build_metadata_from_dataset(dataset, columns=[])

    # Re-score the dataset (this saves history and updates actions)
    score_and_save_dataset(db, dataset, metadata)

    db.commit()
    db.refresh(dataset)

    # Return updated dataset detail
    return get_dataset(dataset_id, db)



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
    column_responses = [_column_to_response(c) for c in columns]

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
    Note: Avrotize doesn't have direct Scala support, so Java classes are generated
    which Scala can use directly.
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
    column_responses = [_column_to_response(c) for c in columns]

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
    column_responses = [_column_to_response(c) for c in columns]

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

    # Get upstream lineage (datasets this dataset depends on)
    upstream_lineage = (
        db.query(DatasetLineage)
        .filter(DatasetLineage.downstream_dataset_id == dataset_id)
        .all()
    )
    
    upstream_items = []
    for lineage in upstream_lineage:
        upstream_dataset = db.query(Dataset).filter(Dataset.id == lineage.upstream_dataset_id).first()
        if upstream_dataset:
            upstream_items.append(
                DatasetLineageItem(
                    id=upstream_dataset.id,
                    full_name=upstream_dataset.full_name,
                    display_name=upstream_dataset.display_name or upstream_dataset.full_name,
                    transformation_type=lineage.transformation_type,
                )
            )

    # Get downstream lineage (datasets that depend on this dataset)
    downstream_lineage = (
        db.query(DatasetLineage)
        .filter(DatasetLineage.upstream_dataset_id == dataset_id)
        .all()
    )
    
    downstream_items = []
    for lineage in downstream_lineage:
        downstream_dataset = db.query(Dataset).filter(Dataset.id == lineage.downstream_dataset_id).first()
        if downstream_dataset:
            downstream_items.append(
                DatasetLineageItem(
                    id=downstream_dataset.id,
                    full_name=downstream_dataset.full_name,
                    display_name=downstream_dataset.display_name or downstream_dataset.full_name,
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

    # Get upstream lineage (columns this column depends on)
    upstream_lineage = (
        db.query(ColumnLineage)
        .filter(ColumnLineage.downstream_column_id == column_id)
        .all()
    )
    
    upstream_items = []
    for lineage in upstream_lineage:
        upstream_column = db.query(DatasetColumn).filter(DatasetColumn.id == lineage.upstream_column_id).first()
        if upstream_column:
            upstream_dataset = db.query(Dataset).filter(Dataset.id == upstream_column.dataset_id).first()
            if upstream_dataset:
                upstream_items.append(
                    ColumnLineageItem(
                        id=lineage.id,
                        upstream_column_id=lineage.upstream_column_id,
                        downstream_column_id=lineage.downstream_column_id,
                        upstream_column_name=upstream_column.name,
                        upstream_dataset_id=upstream_dataset.id,
                        upstream_dataset_name=upstream_dataset.display_name or upstream_dataset.full_name,
                        downstream_column_name=column.name,
                        downstream_dataset_id=dataset.id,
                        downstream_dataset_name=dataset.display_name or dataset.full_name,
                        transformation_expression=lineage.transformation_expression,
                        created_at=lineage.created_at,
                    )
                )

    # Get downstream lineage (columns that depend on this column)
    downstream_lineage = (
        db.query(ColumnLineage)
        .filter(ColumnLineage.upstream_column_id == column_id)
        .all()
    )
    
    downstream_items = []
    for lineage in downstream_lineage:
        downstream_column = db.query(DatasetColumn).filter(DatasetColumn.id == lineage.downstream_column_id).first()
        if downstream_column:
            downstream_dataset = db.query(Dataset).filter(Dataset.id == downstream_column.dataset_id).first()
            if downstream_dataset:
                downstream_items.append(
                    ColumnLineageItem(
                        id=lineage.id,
                        upstream_column_id=lineage.upstream_column_id,
                        downstream_column_id=lineage.downstream_column_id,
                        upstream_column_name=column.name,
                        upstream_dataset_id=dataset.id,
                        upstream_dataset_name=dataset.display_name or dataset.full_name,
                        downstream_column_name=downstream_column.name,
                        downstream_dataset_id=downstream_dataset.id,
                        downstream_dataset_name=downstream_dataset.display_name or downstream_dataset.full_name,
                        transformation_expression=lineage.transformation_expression,
                        created_at=lineage.created_at,
                    )
                )

    return ColumnLineageResponse(upstream=upstream_items, downstream=downstream_items)
