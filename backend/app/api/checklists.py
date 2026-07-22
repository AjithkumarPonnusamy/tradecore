from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.models import User, TechnicalChecklist, ConfirmationChecklist
from app.schemas.schemas import (
    TechnicalChecklistCreate, TechnicalChecklistUpdate, TechnicalChecklistResponse,
    ConfirmationChecklistCreate, ConfirmationChecklistUpdate, ConfirmationChecklistResponse
)

router = APIRouter(prefix="/checklists", tags=["Checklists Engine"])

# Default list of Technical Checklist items
DEFAULT_TECHNICAL = [
    "Liquidity Sweep",
    "EMA Confirmation",
    "CPR Support",
    "CPR Resistance",
    "Camarilla Reversal",
    "Asian Range Break",
    "London Open",
    "New York Open",
    "Fibonacci Zone",
    "SMC Confirmation"
]

# Default list of Confirmation Checklist items
DEFAULT_CONFIRMATION = [
    "Trend Confirmation",
    "Higher Timeframe Bias",
    "News Checked",
    "Risk Calculated",
    "RR Valid",
    "Volume Confirmation",
    "Session Confirmation"
]

def seed_technical_checklists(db: Session, user_id: UUID) -> List[TechnicalChecklist]:
    items = []
    for idx, name in enumerate(DEFAULT_TECHNICAL):
        item = TechnicalChecklist(
            user_id=user_id,
            name=name,
            is_enabled=True,
            order_idx=idx
        )
        db.add(item)
        items.append(item)
    db.commit()
    for item in items:
        db.refresh(item)
    return items

def seed_confirmation_checklists(db: Session, user_id: UUID) -> List[ConfirmationChecklist]:
    items = []
    for idx, name in enumerate(DEFAULT_CONFIRMATION):
        item = ConfirmationChecklist(
            user_id=user_id,
            name=name,
            is_enabled=True,
            order_idx=idx
        )
        db.add(item)
        items.append(item)
    db.commit()
    for item in items:
        db.refresh(item)
    return items

# ==========================================
# Technical Checklist Routes
# ==========================================

@router.get("/technical", response_model=List[TechnicalChecklistResponse])
def get_technical_checklists(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    items = db.query(TechnicalChecklist).filter(
        TechnicalChecklist.user_id == current_user.id
    ).order_by(TechnicalChecklist.order_idx).all()
    
    if not items:
        # Seed default items for this user
        items = seed_technical_checklists(db, current_user.id)
        
    return items

@router.post("/technical", response_model=TechnicalChecklistResponse, status_code=status.HTTP_201_CREATED)
def create_technical_checklist_item(
    item_in: TechnicalChecklistCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Determine the max order_idx
    max_order = db.query(TechnicalChecklist.order_idx).filter(
        TechnicalChecklist.user_id == current_user.id
    ).order_by(TechnicalChecklist.order_idx.desc()).first()
    
    next_order = (max_order[0] + 1) if max_order else 0
    
    db_item = TechnicalChecklist(
        user_id=current_user.id,
        name=item_in.name,
        is_enabled=item_in.is_enabled,
        order_idx=next_order
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.put("/technical/{item_id}", response_model=TechnicalChecklistResponse)
def update_technical_checklist_item(
    item_id: UUID,
    item_in: TechnicalChecklistUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_item = db.query(TechnicalChecklist).filter(
        TechnicalChecklist.id == item_id,
        TechnicalChecklist.user_id == current_user.id
    ).first()
    
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Technical checklist item not found"
        )
        
    update_data = item_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_item, key, value)
        
    db.commit()
    db.refresh(db_item)
    return db_item

@router.delete("/technical/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_technical_checklist_item(
    item_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_item = db.query(TechnicalChecklist).filter(
        TechnicalChecklist.id == item_id,
        TechnicalChecklist.user_id == current_user.id
    ).first()
    
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Technical checklist item not found"
        )
        
    db.delete(db_item)
    db.commit()
    return None

@router.post("/technical/reorder", response_model=List[TechnicalChecklistResponse])
def reorder_technical_checklist_items(
    ordered_ids: List[UUID],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    for idx, item_id in enumerate(ordered_ids):
        db.query(TechnicalChecklist).filter(
            TechnicalChecklist.id == item_id,
            TechnicalChecklist.user_id == current_user.id
        ).update({"order_idx": idx})
        
    db.commit()
    
    return db.query(TechnicalChecklist).filter(
        TechnicalChecklist.user_id == current_user.id
    ).order_by(TechnicalChecklist.order_idx).all()

# ==========================================
# Confirmation Checklist Routes
# ==========================================

@router.get("/confirmation", response_model=List[ConfirmationChecklistResponse])
def get_confirmation_checklists(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    items = db.query(ConfirmationChecklist).filter(
        ConfirmationChecklist.user_id == current_user.id
    ).order_by(ConfirmationChecklist.order_idx).all()
    
    if not items:
        # Seed default items for this user
        items = seed_confirmation_checklists(db, current_user.id)
        
    return items

@router.post("/confirmation", response_model=ConfirmationChecklistResponse, status_code=status.HTTP_201_CREATED)
def create_confirmation_checklist_item(
    item_in: ConfirmationChecklistCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    max_order = db.query(ConfirmationChecklist.order_idx).filter(
        ConfirmationChecklist.user_id == current_user.id
    ).order_by(ConfirmationChecklist.order_idx.desc()).first()
    
    next_order = (max_order[0] + 1) if max_order else 0
    
    db_item = ConfirmationChecklist(
        user_id=current_user.id,
        name=item_in.name,
        is_enabled=item_in.is_enabled,
        order_idx=next_order
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.put("/confirmation/{item_id}", response_model=ConfirmationChecklistResponse)
def update_confirmation_checklist_item(
    item_id: UUID,
    item_in: ConfirmationChecklistUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_item = db.query(ConfirmationChecklist).filter(
        ConfirmationChecklist.id == item_id,
        ConfirmationChecklist.user_id == current_user.id
    ).first()
    
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Confirmation checklist item not found"
        )
        
    update_data = item_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_item, key, value)
        
    db.commit()
    db.refresh(db_item)
    return db_item

@router.delete("/confirmation/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_confirmation_checklist_item(
    item_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_item = db.query(ConfirmationChecklist).filter(
        ConfirmationChecklist.id == item_id,
        ConfirmationChecklist.user_id == current_user.id
    ).first()
    
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Confirmation checklist item not found"
        )
        
    db.delete(db_item)
    db.commit()
    return None

@router.post("/confirmation/reorder", response_model=List[ConfirmationChecklistResponse])
def reorder_confirmation_checklist_items(
    ordered_ids: List[UUID],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    for idx, item_id in enumerate(ordered_ids):
        db.query(ConfirmationChecklist).filter(
            ConfirmationChecklist.id == item_id,
            ConfirmationChecklist.user_id == current_user.id
        ).update({"order_idx": idx})
        
    db.commit()
    
    return db.query(ConfirmationChecklist).filter(
        ConfirmationChecklist.user_id == current_user.id
    ).order_by(ConfirmationChecklist.order_idx).all()
