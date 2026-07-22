from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.models import User, Watchlist, ScreenerResult
from app.schemas.schemas import WatchlistCreate, WatchlistResponse, WatchlistUpdate, ScreenerResultResponse
from app.services.market_data import AliceBlueService

from pydantic import BaseModel

router = APIRouter(prefix="/screener", tags=["Market Screener"])

# Instantiate market data service
market_data_service = AliceBlueService()

class WatchlistReorder(BaseModel):
    item_ids: List[UUID]

@router.get("/scan", response_model=List[ScreenerResultResponse])
def run_scanner(
    timeframe: str = "1d",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Scans symbols on the user's watchlist. If empty, scans nothing.
    Computes EMA, Camarilla, CPR, SMC, and Harmonic setups.
    """
    watchlist_items = db.query(Watchlist).filter(Watchlist.user_id == current_user.id).all()
    
    symbols_to_scan = []
    if watchlist_items:
        watchlist_items.sort(key=lambda x: (not x.settings.get("pinned", False) if isinstance(x.settings, dict) else True, x.position, x.created_at))
        for item in watchlist_items:
            symbols_to_scan.append({"symbol": item.symbol, "market": item.market})
        
    results = []
    for item in symbols_to_scan:
        try:
            # Perform technical scan using the Yahoo Finance service
            scan_data = market_data_service.scan_symbol(item["symbol"], item["market"], timeframe)
            
            # Save or construct temporary ScreenerResult object
            # If pattern is detected (i.e. not "None" / "None Detected")
            if scan_data["pattern"] and scan_data["pattern"] != "None":
                db_res = ScreenerResult(
                    id=uuid4(),
                    scanned_at=datetime.utcnow(),
                    symbol=scan_data["symbol"],
                    market=scan_data["market"],
                    pattern=scan_data["pattern"],
                    timeframe=scan_data["timeframe"],
                    entry_price=scan_data["entry_price"],
                    stop_loss=scan_data["stop_loss"],
                    target_price=scan_data["target_price"],
                    confidence_score=scan_data["confidence_score"]
                )
                results.append(db_res)
        except Exception as e:
            print(f"Error scanning {item['symbol']}: {e}")
            
    return results

# ==========================================
# Watchlist CRUD
# ==========================================

@router.get("/watchlist", response_model=List[WatchlistResponse])
def get_watchlist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    items = db.query(Watchlist).filter(Watchlist.user_id == current_user.id).all()
    items.sort(key=lambda x: (not x.settings.get("pinned", False) if isinstance(x.settings, dict) else True, x.position, x.created_at))
    return items

@router.post("/watchlist", response_model=WatchlistResponse, status_code=status.HTTP_201_CREATED)
def add_to_watchlist(
    item_in: WatchlistCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if already in watchlist
    existing = db.query(Watchlist).filter(
        Watchlist.user_id == current_user.id,
        Watchlist.symbol == item_in.symbol.upper(),
        Watchlist.market == item_in.market
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Symbol is already in your watchlist."
        )
        
    from sqlalchemy import func
    max_pos = db.query(func.max(Watchlist.position)).filter(Watchlist.user_id == current_user.id).scalar()
    next_position = (max_pos or 0) + 1

    db_item = Watchlist(
        user_id=current_user.id,
        symbol=item_in.symbol.upper(),
        market=item_in.market,
        position=next_position,
        settings=item_in.settings
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.put("/watchlist/reorder", status_code=status.HTTP_200_OK)
def reorder_watchlist(
    reorder_in: WatchlistReorder,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    for index, item_id in enumerate(reorder_in.item_ids):
        db.query(Watchlist).filter(
            Watchlist.id == item_id,
            Watchlist.user_id == current_user.id
        ).update({Watchlist.position: index})
    db.commit()
    return {"status": "success", "message": "Watchlist reordered successfully."}

@router.post("/watchlist/import", response_model=List[WatchlistResponse], status_code=status.HTTP_201_CREATED)
def import_default_watchlist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Clear existing watchlist first to ensure clean import
    db.query(Watchlist).filter(Watchlist.user_id == current_user.id).delete()
    
    defaults = [
        {"symbol": "XAUUSD", "market": "Forex"},
        {"symbol": "GBPUSD", "market": "Forex"},
        {"symbol": "EURUSD", "market": "Forex"},
        {"symbol": "NIFTY", "market": "Indian Market"},
        {"symbol": "BANKNIFTY", "market": "Indian Market"},
        {"symbol": "BTCUSD", "market": "Forex"},
    ]
    
    created_items = []
    for idx, item in enumerate(defaults):
        db_item = Watchlist(
            user_id=current_user.id,
            symbol=item["symbol"],
            market=item["market"],
            position=idx,
            settings={}
        )
        db.add(db_item)
        created_items.append(db_item)
        
    db.commit()
    for item in created_items:
        db.refresh(item)
    return created_items

@router.put("/watchlist/{item_id}", response_model=WatchlistResponse)
def update_watchlist_item(
    item_id: UUID,
    item_in: WatchlistUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    item = db.query(Watchlist).filter(
        Watchlist.id == item_id,
        Watchlist.user_id == current_user.id
    ).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist item not found"
        )
        
    update_data = item_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)
        
    db.commit()
    db.refresh(item)
    return item

@router.delete("/watchlist/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_watchlist(
    item_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    item = db.query(Watchlist).filter(
        Watchlist.id == item_id,
        Watchlist.user_id == current_user.id
    ).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist item not found"
        )
        
    db.delete(item)
    db.commit()
    return None
