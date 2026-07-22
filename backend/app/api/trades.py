from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from typing import List, Optional
from uuid import UUID
import json

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.models import User, Trade, Strategy, TradeImage, TradeMarketSnapshot
from app.schemas.schemas import (
    TradeCreate, TradeUpdate, TradeResponse, 
    StrategyCreate, StrategyResponse, TradeImageResponse
)
from app.services.google_drive import drive_service
from app.services.pivots import calculate_pivots_for_date
from app.services.market_reference import MarketReferenceEngine

router = APIRouter(prefix="/trades", tags=["Trading Journal"])

reference_engine = MarketReferenceEngine()

# ==========================================
# Calculations Helper
# ==========================================
def calculate_trade_analytics(data: dict) -> dict:
    """Helper to automatically compute financial parameters from entry/exit prices."""
    entry = data.get("entry_price")
    sl = data.get("stop_loss")
    target = data.get("target_price")
    exit_p = data.get("exit_price")
    qty = data.get("quantity", 1.0)
    direction = data.get("direction", "BUY").upper()
    
    analytics = data.get("analytics", {})
    if not isinstance(analytics, dict):
        analytics = {}
        
    net_profit = data.get("net_profit")
    
    # Calculate Risk
    risk_per_unit = 0.0
    if entry and sl:
        if direction == "BUY":
            risk_per_unit = float(entry) - float(sl)
        else:
            risk_per_unit = float(sl) - float(entry)
            
    risk_amount = risk_per_unit * float(qty)
    
    # Calculate Reward/Target Ratios
    if entry and target and risk_per_unit > 0:
        target_reward = float(target) - float(entry) if direction == "BUY" else float(entry) - float(target)
        analytics["rr"] = round(target_reward / risk_per_unit, 2)
        
    # Calculate Net Profit & R-multiple if exited
    if entry and exit_p:
        unit_pnl = float(exit_p) - float(entry) if direction == "BUY" else float(entry) - float(exit_p)
        net_profit = round(unit_pnl * float(qty), 2)
        
        # Calculate R-Multiple
        if risk_amount > 0:
            analytics["r_multiple"] = round(net_profit / risk_amount, 2)
        else:
            analytics["r_multiple"] = 0.0
            
    data["net_profit"] = net_profit
    data["analytics"] = analytics
    return data

# ==========================================
# Strategy Routes
# ==========================================

@router.get("/strategies", response_model=List[StrategyResponse])
def list_strategies(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    return db.query(Strategy).filter(Strategy.user_id == current_user.id).all()

@router.post("/strategies", response_model=StrategyResponse, status_code=status.HTTP_201_CREATED)
def create_strategy(
    strategy_in: StrategyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_strategy = Strategy(
        **strategy_in.model_dump(),
        user_id=current_user.id
    )
    db.add(db_strategy)
    db.commit()
    db.refresh(db_strategy)
    return db_strategy

# ==========================================
# Trade Routes
# ==========================================

@router.get("", response_model=List[TradeResponse])
def get_trades(
    market: Optional[str] = None,
    symbol: Optional[str] = None,
    status_filter: Optional[str] = None,
    strategy_id: Optional[UUID] = None,
    tag: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Trade).options(joinedload(Trade.images), joinedload(Trade.market_snapshot)).filter(Trade.user_id == current_user.id)
    
    if market:
        query = query.filter(Trade.market.ilike(f"%{market}%"))
    if symbol:
        query = query.filter(Trade.symbol.ilike(f"%{symbol}%"))
    if status_filter:
        query = query.filter(Trade.status == status_filter.upper())
    if strategy_id:
        query = query.filter(Trade.strategy_id == strategy_id)
    if tag:
        # PostgreSQL array search: ANY
        query = query.filter(Trade.tags.any(tag))
        
    return query.order_by(desc(Trade.trade_date), desc(Trade.trade_time)).offset(skip).limit(limit).all()

@router.post("", response_model=TradeResponse, status_code=status.HTTP_201_CREATED)
def create_trade(
    trade_in: TradeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    trade_dict = trade_in.model_dump(by_alias=True)
    
    # Pre-calculate risk parameters
    trade_dict = calculate_trade_analytics(trade_dict)
    
    db_trade = Trade(
        user_id=current_user.id,
        trade_date=trade_dict["trade_date"],
        trade_time=trade_dict["trade_time"],
        market=trade_dict["market"],
        symbol=trade_dict["symbol"].upper(),
        direction=trade_dict["direction"].upper(),
        status=trade_dict["status"].upper(),
        entry_price=trade_dict["entry_price"],
        stop_loss=trade_dict["stop_loss"],
        target_price=trade_dict["target_price"],
        exit_price=trade_dict["exit_price"],
        quantity=trade_dict["quantity"],
        net_profit=trade_dict["net_profit"],
        setup=trade_dict["setup"],
        psychology=trade_dict["psychology"],
        notes=trade_dict["notes"],
        analytics=trade_dict["analytics"],
        metadata_=trade_dict.get("metadata") or trade_dict.get("metadata_") or {},
        tags=trade_dict["tags"],
        strategy_id=trade_dict["strategy_id"],
        trading_type=trade_dict.get("trading_type"),
        segment=trade_dict.get("segment"),
        r_multiple=trade_dict.get("r_multiple") or trade_dict.get("analytics", {}).get("r_multiple"),
        holding_minutes=trade_dict.get("holding_minutes") or trade_dict.get("analytics", {}).get("holding_minutes"),
        confidence_rating=trade_dict.get("confidence_rating") or trade_dict.get("psychology", {}).get("confidence")
    )
    
    db.add(db_trade)
    db.commit()
    db.refresh(db_trade)
    
    # Save a snapshot of live market reference levels for the trade
    try:
        snapshot_data = reference_engine.get_market_data(db, db_trade.symbol, db_trade.market, current_user)
        if snapshot_data:
            db_snapshot = TradeMarketSnapshot(
                trade_id=db_trade.id,
                symbol=db_trade.symbol,
                live_price=snapshot_data.live_price,
                trueday_open=snapshot_data.trueday_open,
                previous_trueday_open=snapshot_data.previous_trueday_open,
                indian_midnight_open=snapshot_data.indian_midnight_open,
                previous_day_high=snapshot_data.previous_day_high,
                previous_day_low=snapshot_data.previous_day_low,
                previous_day_close=snapshot_data.previous_day_close,
                current_day_high=snapshot_data.current_day_high,
                current_day_low=snapshot_data.current_day_low,
                daily_range=snapshot_data.daily_range,
                cpr_levels=snapshot_data.cpr_levels,
                camarilla_levels=snapshot_data.camarilla_levels
            )
            db.add(db_snapshot)
            db.commit()
            db.refresh(db_trade)
    except Exception as e:
        print(f"Error capturing trade market snapshot: {e}")
    try:
        from app.api.dashboard import clear_dashboard_cache
        clear_dashboard_cache(current_user.id)
    except Exception as e:
        print(f"Error clearing cache: {e}")
        
    return db_trade

@router.get("/calculate-pivots")
def get_calculated_pivots(
    symbol: str,
    market: str,
    date: str,
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint to fetch pivots calculation for a symbol and date.
    """
    res = calculate_pivots_for_date(symbol, market, date)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Could not calculate pivots for this symbol/date."
        )
    return res

@router.get("/{trade_id}", response_model=TradeResponse)
def get_trade_by_id(
    trade_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    trade = db.query(Trade).filter(Trade.id == trade_id, Trade.user_id == current_user.id).first()
    if not trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trade not found"
        )
    return trade

@router.put("/{trade_id}", response_model=TradeResponse)
def update_trade(
    trade_id: UUID,
    trade_in: TradeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    trade = db.query(Trade).filter(Trade.id == trade_id, Trade.user_id == current_user.id).first()
    if not trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trade not found"
        )
        
    update_data = trade_in.model_dump(exclude_unset=True, by_alias=True)
    
    # Extract existing values to merge calculations
    full_data = {
        "direction": update_data.get("direction", trade.direction),
        "entry_price": update_data.get("entry_price", trade.entry_price),
        "stop_loss": update_data.get("stop_loss", trade.stop_loss),
        "target_price": update_data.get("target_price", trade.target_price),
        "exit_price": update_data.get("exit_price", trade.exit_price),
        "quantity": update_data.get("quantity", trade.quantity),
        "net_profit": update_data.get("net_profit", trade.net_profit),
        "analytics": update_data.get("analytics", trade.analytics)
    }
    
    calculated_data = calculate_trade_analytics(full_data)
    update_data["net_profit"] = calculated_data["net_profit"]
    update_data["analytics"] = calculated_data["analytics"]
    
    for field, value in update_data.items():
        if field == "metadata":
            setattr(trade, "metadata_", value)
        else:
            setattr(trade, field, value)
            
    db.commit()
    db.refresh(trade)
    
    try:
        from app.api.dashboard import clear_dashboard_cache
        clear_dashboard_cache(current_user.id)
    except Exception as e:
        print(f"Error clearing cache: {e}")
        
    return trade

@router.delete("/{trade_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_trade(
    trade_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    trade = db.query(Trade).filter(Trade.id == trade_id, Trade.user_id == current_user.id).first()
    if not trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trade not found"
        )
        
    # Clean up screenshots from Google Drive / Local Storage first
    for image in trade.images:
        drive_service.delete_image(image.google_file_id, user_id=current_user.id, db=db)
        
    db.delete(trade)
    db.commit()
    
    try:
        from app.api.dashboard import clear_dashboard_cache
        clear_dashboard_cache(current_user.id)
    except Exception as e:
        print(f"Error clearing cache: {e}")
        
    return None

# ==========================================
# Image Management Routes
# ==========================================

@router.post("/{trade_id}/images", response_model=TradeImageResponse, status_code=status.HTTP_201_CREATED)
def upload_trade_image(
    trade_id: UUID,
    category: str = Form(...),
    caption: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    trade = db.query(Trade).filter(Trade.id == trade_id, Trade.user_id == current_user.id).first()
    if not trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trade not found"
        )
        
    upload_res = drive_service.upload_image(file, category, user_id=current_user.id, db=db)
    
    db_image = TradeImage(
        trade_id=trade_id,
        category=category,
        google_file_id=upload_res["file_id"],
        file_url=upload_res["file_url"],
        caption=caption,
        extra_data={"filename": file.filename, "content_type": file.content_type}
    )
    
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    return db_image

@router.delete("/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_trade_image(
    image_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    image = db.query(TradeImage).join(Trade).filter(
        TradeImage.id == image_id, 
        Trade.user_id == current_user.id
    ).first()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
        
    drive_service.delete_image(image.google_file_id, user_id=current_user.id, db=db)
    db.delete(image)
    db.commit()
    return None
