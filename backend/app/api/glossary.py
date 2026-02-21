"""
Business glossary API endpoints.
"""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.schemas import (
    ColumnGlossaryTermResponse,
    GlossaryTermCreate,
    GlossaryTermResponse,
    GlossaryTermUpdate,
)
from app.db import get_db
from app.models import DatasetColumn, GlossaryColumnLink, GlossaryTerm

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/glossary", tags=["glossary"])


@router.get("", response_model=List[GlossaryTermResponse])
def list_terms(
    q: Optional[str] = Query(None, description="Search in name and definition"),
    domain: Optional[str] = Query(None, description="Filter by domain"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
):
    """List glossary terms with optional search/filter."""
    query = db.query(GlossaryTerm)

    if q:
        query = query.filter(
            GlossaryTerm.name.ilike(f"%{q}%")
            | GlossaryTerm.definition.ilike(f"%{q}%")
        )
    if domain:
        query = query.filter(GlossaryTerm.domain == domain)
    if status:
        query = query.filter(GlossaryTerm.status == status)

    terms = query.order_by(GlossaryTerm.name).all()

    # Preload linked column counts
    result = []
    for term in terms:
        linked_count = (
            db.query(GlossaryColumnLink)
            .filter(GlossaryColumnLink.term_id == term.id)
            .count()
        )
        result.append(
            GlossaryTermResponse(
                id=term.id,
                name=term.name,
                definition=term.definition,
                domain=term.domain,
                owner=term.owner,
                status=term.status,
                created_at=term.created_at,
                updated_at=term.updated_at,
                linked_columns_count=linked_count,
                linked_columns=[],
            )
        )
    return result


@router.post("", response_model=GlossaryTermResponse, status_code=201)
def create_term(
    request: GlossaryTermCreate,
    db: Session = Depends(get_db),
):
    """Create a new glossary term."""
    existing = (
        db.query(GlossaryTerm).filter(GlossaryTerm.name == request.name).first()
    )
    if existing:
        raise HTTPException(
            status_code=409, detail=f"Term '{request.name}' already exists"
        )

    term = GlossaryTerm(
        name=request.name,
        definition=request.definition,
        domain=request.domain,
        owner=request.owner,
        status=request.status or "draft",
    )
    db.add(term)
    db.commit()
    db.refresh(term)

    logger.info("Created glossary term: %s", term.name)
    return GlossaryTermResponse(
        id=term.id,
        name=term.name,
        definition=term.definition,
        domain=term.domain,
        owner=term.owner,
        status=term.status,
        created_at=term.created_at,
        updated_at=term.updated_at,
        linked_columns_count=0,
        linked_columns=[],
    )


@router.get("/{term_id}", response_model=GlossaryTermResponse)
def get_term(term_id: UUID, db: Session = Depends(get_db)):
    """Get glossary term detail with linked columns."""
    term = db.query(GlossaryTerm).filter(GlossaryTerm.id == term_id).first()
    if not term:
        raise HTTPException(status_code=404, detail="Term not found")

    # Get linked columns with dataset info
    links = (
        db.query(GlossaryColumnLink, DatasetColumn)
        .join(DatasetColumn, GlossaryColumnLink.column_id == DatasetColumn.id)
        .filter(GlossaryColumnLink.term_id == term_id)
        .all()
    )

    linked_columns = []
    for link, col in links:
        dataset = col.dataset
        linked_columns.append(
            {
                "link_id": str(link.id),
                "column_id": str(col.id),
                "column_name": col.name,
                "dataset_id": str(col.dataset_id),
                "dataset_name": dataset.display_name if dataset else "Unknown",
            }
        )

    return GlossaryTermResponse(
        id=term.id,
        name=term.name,
        definition=term.definition,
        domain=term.domain,
        owner=term.owner,
        status=term.status,
        created_at=term.created_at,
        updated_at=term.updated_at,
        linked_columns_count=len(linked_columns),
        linked_columns=linked_columns,
    )


@router.put("/{term_id}", response_model=GlossaryTermResponse)
def update_term(
    term_id: UUID,
    request: GlossaryTermUpdate,
    db: Session = Depends(get_db),
):
    """Update a glossary term."""
    term = db.query(GlossaryTerm).filter(GlossaryTerm.id == term_id).first()
    if not term:
        raise HTTPException(status_code=404, detail="Term not found")

    if request.name is not None:
        term.name = request.name
    if request.definition is not None:
        term.definition = request.definition
    if request.domain is not None:
        term.domain = request.domain or None
    if request.owner is not None:
        term.owner = request.owner or None
    if request.status is not None:
        valid_statuses = ["draft", "approved", "deprecated"]
        if request.status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
            )
        term.status = request.status

    from datetime import datetime

    term.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(term)

    logger.info("Updated glossary term: %s", term.name)
    return get_term(term_id, db)


@router.delete("/{term_id}", status_code=204)
def delete_term(term_id: UUID, db: Session = Depends(get_db)):
    """Delete a glossary term."""
    term = db.query(GlossaryTerm).filter(GlossaryTerm.id == term_id).first()
    if not term:
        raise HTTPException(status_code=404, detail="Term not found")

    db.delete(term)
    db.commit()
    logger.info("Deleted glossary term: %s", term.name)


@router.post("/{term_id}/columns/{column_id}", status_code=201)
def link_term_to_column(
    term_id: UUID, column_id: UUID, db: Session = Depends(get_db)
):
    """Link a glossary term to a column."""
    term = db.query(GlossaryTerm).filter(GlossaryTerm.id == term_id).first()
    if not term:
        raise HTTPException(status_code=404, detail="Term not found")

    column = db.query(DatasetColumn).filter(DatasetColumn.id == column_id).first()
    if not column:
        raise HTTPException(status_code=404, detail="Column not found")

    existing = (
        db.query(GlossaryColumnLink)
        .filter(
            GlossaryColumnLink.term_id == term_id,
            GlossaryColumnLink.column_id == column_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Link already exists")

    link = GlossaryColumnLink(term_id=term_id, column_id=column_id)
    db.add(link)
    db.commit()

    logger.info("Linked term %s to column %s", term_id, column_id)
    return {"status": "linked"}


@router.delete("/{term_id}/columns/{column_id}", status_code=204)
def unlink_term_from_column(
    term_id: UUID, column_id: UUID, db: Session = Depends(get_db)
):
    """Unlink a glossary term from a column."""
    link = (
        db.query(GlossaryColumnLink)
        .filter(
            GlossaryColumnLink.term_id == term_id,
            GlossaryColumnLink.column_id == column_id,
        )
        .first()
    )
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    db.delete(link)
    db.commit()
    logger.info("Unlinked term %s from column %s", term_id, column_id)


# --- Column-centric glossary endpoints ---

columns_router = APIRouter(prefix="/api/columns", tags=["glossary"])


@columns_router.get(
    "/{column_id}/glossary-terms",
    response_model=List[ColumnGlossaryTermResponse],
)
def get_column_glossary_terms(column_id: UUID, db: Session = Depends(get_db)):
    """Return all glossary terms linked to a specific column."""
    column = db.query(DatasetColumn).filter(DatasetColumn.id == column_id).first()
    if not column:
        raise HTTPException(status_code=404, detail="Column not found")

    links = (
        db.query(GlossaryColumnLink, GlossaryTerm)
        .join(GlossaryTerm, GlossaryColumnLink.term_id == GlossaryTerm.id)
        .filter(GlossaryColumnLink.column_id == column_id)
        .order_by(GlossaryTerm.name)
        .all()
    )

    return [
        ColumnGlossaryTermResponse(
            term_id=term.id,
            term_name=term.name,
            term_definition=term.definition,
            domain=term.domain,
        )
        for _link, term in links
    ]
