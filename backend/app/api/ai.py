"""
AI assist endpoints for generating dataset and column descriptions.

Safety: Only uses metadata, never raw data values.
"""

from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.config import settings

router = APIRouter(prefix="/api/ai", tags=["ai"])


class DatasetDescriptionRequest(BaseModel):
    """Request for dataset description generation."""

    full_name: str
    display_name: Optional[str] = None
    owner_name: Optional[str] = None
    intended_use: Optional[str] = None
    limitations: Optional[str] = None
    column_names: Optional[List[str]] = None


class DatasetDescriptionResponse(BaseModel):
    """Response with suggested dataset description."""

    suggested_description: str


class ColumnDescriptionsRequest(BaseModel):
    """Request for column descriptions generation."""

    dataset_name: str
    column_names: List[str]
    existing_descriptions: Optional[dict[str, str]] = None


class ColumnDescriptionsResponse(BaseModel):
    """Response with suggested column descriptions."""

    suggested_descriptions: dict[str, str]


def _generate_dataset_description(request: DatasetDescriptionRequest) -> str:
    """
    Generate a dataset description based on metadata.

    Safety: Only uses metadata, never raw data values.

    In production, this would call an LLM API (OpenAI, Anthropic, etc.).
    For MVP, we use a template-based approach.
    """
    parts = []

    # Start with dataset name
    if request.display_name:
        parts.append(f"This dataset contains {request.display_name.lower()}.")
    else:
        parts.append(f"This dataset contains data from {request.full_name}.")

    # Add intended use if available
    if request.intended_use:
        parts.append(f"Intended use cases: {request.intended_use}.")

    # Add column context if available
    if request.column_names:
        column_count = len(request.column_names)
        parts.append(
            f"The dataset includes {column_count} column{'s' if column_count != 1 else ''}."
        )

    # Add limitations if available
    if request.limitations:
        parts.append(f"Limitations: {request.limitations}.")

    # Add owner context if available
    if request.owner_name:
        parts.append(f"Maintained by {request.owner_name}.")

    # Fallback if no metadata
    if len(parts) == 1:
        parts.append(
            "This dataset is used for data analysis and reporting. "
            "Please add more metadata to improve this description."
        )

    return " ".join(parts)


def _generate_column_descriptions(
    request: ColumnDescriptionsRequest,
) -> Dict[str, str]:
    """
    Generate column descriptions based on column names and context.

    Safety: Only uses metadata (column names), never raw data values.

    In production, this would call an LLM API (OpenAI, Anthropic, etc.).
    For MVP, we use a template-based approach with heuristics.
    """
    descriptions = {}

    for column_name in request.column_names:
        # Skip if already has description
        if (
            request.existing_descriptions
            and column_name in request.existing_descriptions
            and request.existing_descriptions[column_name]
        ):
            continue

        # Generate description based on column name patterns
        col_lower = column_name.lower()

        # Common patterns
        if col_lower.endswith("_id") or col_lower == "id":
            descriptions[column_name] = f"Unique identifier for {request.dataset_name} records."
        elif col_lower.endswith("_at") or col_lower in ["timestamp", "created", "updated"]:
            descriptions[column_name] = "Timestamp indicating when this record was created or last updated."
        elif col_lower.endswith("_name") or col_lower == "name":
            descriptions[column_name] = "Name or label for this entity."
        elif col_lower.endswith("_email") or col_lower == "email":
            descriptions[column_name] = "Email address associated with this record."
        elif col_lower.endswith("_type") or col_lower == "type":
            descriptions[column_name] = "Type or category classification for this record."
        elif col_lower.endswith("_status") or col_lower == "status":
            descriptions[column_name] = "Current status of this record."
        elif col_lower.endswith("_count") or col_lower.endswith("_total"):
            descriptions[column_name] = "Numeric count or total value."
        elif col_lower.endswith("_amount") or col_lower.endswith("_value"):
            descriptions[column_name] = "Monetary amount or numeric value."
        elif col_lower.startswith("is_") or col_lower.startswith("has_"):
            descriptions[column_name] = f"Boolean flag indicating whether {col_lower.replace('is_', '').replace('has_', '')} is present or true."
        elif col_lower.endswith("_url") or col_lower == "url":
            descriptions[column_name] = "URL or web address."
        else:
            # Generic description based on column name
            # Convert snake_case to readable text
            readable = column_name.replace("_", " ").title()
            descriptions[column_name] = f"{readable} field in {request.dataset_name}."

    return descriptions


@router.post("/dataset-description", response_model=DatasetDescriptionResponse)
def generate_dataset_description(
    request: DatasetDescriptionRequest,
) -> DatasetDescriptionResponse:
    """
    Generate a suggested dataset description based on metadata.

    Safety: Only uses metadata (name, owner, intended use, column names).
    Never uses raw data values.

    Returns suggested text only - never auto-applies.
    """
    if not settings.ai_assist_enabled:
        raise HTTPException(
            status_code=403,
            detail="AI assist is not enabled. Set AI_ASSIST_ENABLED=true to enable.",
        )

    suggested = _generate_dataset_description(request)

    return DatasetDescriptionResponse(suggested_description=suggested)


@router.post("/column-descriptions", response_model=ColumnDescriptionsResponse)
def generate_column_descriptions(
    request: ColumnDescriptionsRequest,
) -> ColumnDescriptionsResponse:
    """
    Generate suggested column descriptions based on column names and context.

    Safety: Only uses metadata (column names, dataset name).
    Never uses raw data values.

    Returns suggested text only - never auto-applies.
    """
    if not settings.ai_assist_enabled:
        raise HTTPException(
            status_code=403,
            detail="AI assist is not enabled. Set AI_ASSIST_ENABLED=true to enable.",
        )

    suggested = _generate_column_descriptions(request)

    return ColumnDescriptionsResponse(suggested_descriptions=suggested)

