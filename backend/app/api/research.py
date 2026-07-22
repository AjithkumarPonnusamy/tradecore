from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.models import User, ResearchNotebook, FactorData, CustomStudy
from app.schemas.schemas import (
    ResearchNotebookCreate, ResearchNotebookUpdate, ResearchNotebookResponse,
    FactorDataResponse, CustomStudyResponse
)

router = APIRouter(prefix="/research", tags=["Research Schema"])

# ------------------------------------------------------------------------------
# Research Notebooks
# ------------------------------------------------------------------------------
@router.get("/notebooks", response_model=List[ResearchNotebookResponse])
def get_research_notebooks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all research notebooks owned by the authenticated user."""
    return db.query(ResearchNotebook).filter(ResearchNotebook.user_id == current_user.id).order_by(ResearchNotebook.updated_at.desc()).all()


@router.post("/notebooks", response_model=ResearchNotebookResponse, status_code=status.HTTP_201_CREATED)
def create_research_notebook(
    notebook_in: ResearchNotebookCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new research notebook."""
    notebook = ResearchNotebook(
        user_id=current_user.id,
        title=notebook_in.title,
        description=notebook_in.description,
        notebook_data=notebook_in.notebook_data
    )
    db.add(notebook)
    db.commit()
    db.refresh(notebook)
    return notebook


@router.get("/notebooks/{notebook_id}", response_model=ResearchNotebookResponse)
def get_research_notebook(
    notebook_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific research notebook by ID."""
    notebook = db.query(ResearchNotebook).filter(
        ResearchNotebook.id == notebook_id,
        ResearchNotebook.user_id == current_user.id
    ).first()
    if not notebook:
        raise HTTPException(status_code=404, detail="Research notebook not found")
    return notebook


@router.put("/notebooks/{notebook_id}", response_model=ResearchNotebookResponse)
def update_research_notebook(
    notebook_id: UUID,
    notebook_in: ResearchNotebookUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a research notebook."""
    notebook = db.query(ResearchNotebook).filter(
        ResearchNotebook.id == notebook_id,
        ResearchNotebook.user_id == current_user.id
    ).first()
    if not notebook:
        raise HTTPException(status_code=404, detail="Research notebook not found")

    if notebook_in.title is not None:
        notebook.title = notebook_in.title
    if notebook_in.description is not None:
        notebook.description = notebook_in.description
    if notebook_in.notebook_data is not None:
        notebook.notebook_data = notebook_in.notebook_data

    db.commit()
    db.refresh(notebook)
    return notebook


@router.delete("/notebooks/{notebook_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_research_notebook(
    notebook_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a research notebook."""
    notebook = db.query(ResearchNotebook).filter(
        ResearchNotebook.id == notebook_id,
        ResearchNotebook.user_id == current_user.id
    ).first()
    if not notebook:
        raise HTTPException(status_code=404, detail="Research notebook not found")

    db.delete(notebook)
    db.commit()
    return None

# ------------------------------------------------------------------------------
# Factor Data & Custom Studies
# ------------------------------------------------------------------------------
@router.get("/factors", response_model=List[FactorDataResponse])
def get_factor_data(
    symbol: Optional[str] = Query(None),
    factor_name: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Query quantitative factor dataset by symbol and factor name."""
    query = db.query(FactorData)
    if symbol:
        query = query.filter(FactorData.symbol == symbol)
    if factor_name:
        query = query.filter(FactorData.factor_name == factor_name)
    return query.order_by(FactorData.date.desc()).limit(200).all()


@router.get("/studies", response_model=List[CustomStudyResponse])
def get_custom_studies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get custom studies owned by user or marked public."""
    return db.query(CustomStudy).filter(
        (CustomStudy.user_id == current_user.id) | (CustomStudy.is_public == True)
    ).all()
