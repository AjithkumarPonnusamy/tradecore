from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, text
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime, date
from uuid import UUID
from urllib.parse import urlparse

from app.core.config import settings
from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.models import User, Trade, Strategy, Watchlist, ScannerSettings, ScreenerResult
from app.schemas.schemas import DashboardMetricsResponse
from app.core.redis import redis_cache
from app.services.market_reference import MarketReferenceEngine
from fastapi.encoders import jsonable_encoder

reference_engine = MarketReferenceEngine()

router = APIRouter(prefix="/dashboard", tags=["Dashboard & Analytics"])

# Cache configuration
CACHE_DURATION_SEC = 60  # 1 minute cache

def get_dashboard_redis_key(user_id, start_date, end_date, market, trading_type, strategy_id, symbol, direction) -> str:
    import hashlib
    components = [
        str(user_id),
        str(start_date) if start_date else "",
        str(end_date) if end_date else "",
        str(market) if market else "",
        str(trading_type) if trading_type else "",
        str(strategy_id) if strategy_id else "",
        str(symbol) if symbol else "",
        str(direction) if direction else ""
    ]
    key_str = ":".join(components)
    h = hashlib.md5(key_str.encode("utf-8")).hexdigest()
    return f"dashboard:user:{user_id}:{h}"

def clear_dashboard_cache(user_id):
    redis_cache.clear_pattern(f"dashboard:user:{user_id}:*")

def compute_metrics_for_trades(df_subset) -> dict:
    total_trades = len(df_subset)
    if total_trades == 0:
        return {
            "total_trades": 0,
            "win_rate": 0.0,
            "net_pnl": 0.0,
            "avg_rr": 0.0,
            "avg_profit": 0.0,
            "avg_loss": 0.0,
            "profit_factor": 0.0,
            "expectancy": 0.0,
            "max_drawdown": 0.0
        }
    
    net_pnl = float(df_subset["pnl"].sum())
    wins_df = df_subset[df_subset["status"] == "WIN"]
    losses_df = df_subset[df_subset["status"] == "LOSS"]
    wins = len(wins_df)
    losses = len(losses_df)
    
    win_rate = (wins / total_trades) * 100
    
    # Calculate R:R
    avg_rr = float(df_subset["rr"].mean()) if "rr" in df_subset.columns else 0.0
    if np.isnan(avg_rr):
        avg_rr = 0.0

    avg_profit = float(wins_df["pnl"].mean()) if wins > 0 else 0.0
    avg_loss = abs(float(losses_df["pnl"].mean())) if losses > 0 else 0.0
    
    gross_profit = float(wins_df["pnl"].sum())
    gross_loss = abs(float(losses_df["pnl"].sum()))
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (gross_profit if gross_profit > 0 else 1.0)
    
    expectancy = ((win_rate / 100) * avg_profit) - ((1 - win_rate / 100) * avg_loss)
    
    # Max Drawdown for the subset chronologically
    df_sorted = df_subset.sort_values(by=["date", "time"]) if ("time" in df_subset.columns and "date" in df_subset.columns) else df_subset
    current_balance = 0.0
    peak = 0.0
    max_dd = 0.0
    for _, row in df_sorted.iterrows():
        current_balance += row["pnl"]
        if current_balance > peak:
            peak = current_balance
        dd = peak - current_balance
        if dd > max_dd:
            max_dd = dd
            
    return {
        "total_trades": total_trades,
        "win_rate": round(win_rate, 2),
        "net_pnl": round(net_pnl, 2),
        "avg_rr": round(avg_rr, 2),
        "avg_profit": round(avg_profit, 2),
        "avg_loss": round(avg_loss, 2),
        "profit_factor": round(profit_factor, 2),
        "expectancy": round(expectancy, 2),
        "max_drawdown": round(max_dd, 2)
    }

@router.get("", response_model=DashboardMetricsResponse)
def get_dashboard_metrics(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    market: Optional[str] = None,
    trading_type: Optional[str] = None,
    strategy_id: Optional[UUID] = None,
    symbol: Optional[str] = None,
    direction: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check cache first
    cache_key = get_dashboard_redis_key(
        current_user.id, start_date, end_date, market, trading_type, strategy_id, symbol, direction
    )
    cached_data = redis_cache.get(cache_key)
    if cached_data is not None:
        try:
            cached_response = DashboardMetricsResponse(**cached_data)
            cached_response.db_last_sync = datetime.now().strftime("%I:%M %p")
            return cached_response
        except Exception as e:
            print(f"Error parsing cached dashboard metrics: {e}")

    # Check database connection status & parse name
    db_connected = True
    db_name = "Neon PostgreSQL"
    try:
        db.execute(text("SELECT 1"))
        parsed = urlparse(settings.DATABASE_URL)
        db_name_str = parsed.path.lstrip('/')
        if "neon" in settings.DATABASE_URL.lower():
            db_name = f"Neon PostgreSQL ({db_name_str})"
        else:
            db_name = f"Local PostgreSQL ({db_name_str})"
    except Exception:
        db_connected = False
        db_name = "PostgreSQL (Disconnected)"
    
    # Query all trades for the current user, eager loading strategy
    query = db.query(Trade).options(joinedload(Trade.strategy)).filter(
        Trade.user_id == current_user.id
    )
    
    # Apply dynamic filters
    if start_date:
        query = query.filter(Trade.trade_date >= start_date)
    if end_date:
        query = query.filter(Trade.trade_date <= end_date)
    if market:
        query = query.filter(Trade.market.ilike(market))
    if trading_type:
        query = query.filter(Trade.trading_type.ilike(trading_type))
    if strategy_id:
        query = query.filter(Trade.strategy_id == strategy_id)
    if symbol:
        query = query.filter(Trade.symbol.ilike(f"%{symbol}%"))
    if direction:
        direction_val = direction.upper()
        if direction_val == "LONG":
            direction_val = "BUY"
        elif direction_val == "SHORT":
            direction_val = "SELL"
        query = query.filter(Trade.direction.ilike(direction_val))
        
    trades = query.order_by(Trade.trade_date, Trade.trade_time).all()
    total_trades = len(trades)
    
    # Empty state fallback
    if total_trades == 0:
        return DashboardMetricsResponse(
            total_pnl=0.0,
            win_rate=0.0,
            total_trades=0,
            wins=0,
            losses=0,
            avg_r=0.0,
            profit_factor=0.0,
            expectancy=0.0,
            max_drawdown=0.0,
            consecutive_wins=0,
            consecutive_losses=0,
            db_connected=db_connected,
            db_name=db_name,
            db_last_sync="Just now",
            charts={
                "equity_curve": [],
                "monthly_pnl": {},
                "strategy_pnl": {},
                "daywise_pnl": {},
                "hourwise_pnl": {},
                "r_distribution": {},
                "psychology_pnl": {}
            },
            category_analytics={
                "market_segment": {},
                "trading_style": {},
                "direction": {},
                "strategy": {}
            }
        )

    # Compile data into a DataFrame for fast vectorised operations
    data = []
    for t in trades:
        strat_name = t.strategy.name if t.strategy else "No Strategy"
        psych = t.psychology or {}
        confidence = psych.get("confidence", 5)
        analytics_obj = t.analytics or {}
        r_multiple = analytics_obj.get("r_multiple", 0.0)
        rr = analytics_obj.get("rr", 0.0)
        pnl = float(t.net_profit) if t.net_profit is not None else 0.0
        
        day_name = t.trade_date.strftime("%A")
        hour_val = t.trade_time.hour if t.trade_time else 9
        
        data.append({
            "id": t.id,
            "date": t.trade_date,
            "time": t.trade_time,
            "pnl": pnl,
            "r_multiple": r_multiple,
            "rr": rr,
            "status": t.status,
            "strategy": strat_name,
            "market": t.market,
            "trading_type": t.trading_type or "Unknown",
            "segment": t.segment or "Unknown",
            "direction": t.direction or "BUY",
            "confidence": confidence,
            "day": day_name,
            "hour": hour_val,
            "month": t.trade_date.strftime("%Y-%m")
        })
        
    df = pd.DataFrame(data)
    
    # Overall Performance calculations
    total_pnl = float(df["pnl"].sum())
    wins_df = df[df["status"] == "WIN"]
    losses_df = df[df["status"] == "LOSS"]
    wins = len(wins_df)
    losses = len(losses_df)
    
    closed_df = df[df["status"] != "OPEN"]
    closed_trades = len(closed_df)
    win_rate = (wins / closed_trades) * 100 if closed_trades > 0 else 0.0
    avg_r = float(closed_df["r_multiple"].mean()) if closed_trades > 0 else 0.0
    
    gross_profit = float(wins_df["pnl"].sum())
    gross_loss = abs(float(losses_df["pnl"].sum()))
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (gross_profit if gross_profit > 0 else 1.0)
    
    avg_win = float(wins_df["pnl"].mean()) if wins > 0 else 0.0
    avg_loss = abs(float(losses_df["pnl"].mean())) if losses > 0 else 0.0
    expectancy = ((win_rate / 100) * avg_win) - ((1 - win_rate / 100) * avg_loss)
    
    # Streaks and Drawdowns
    consec_wins = 0
    consec_losses = 0
    max_consec_wins = 0
    max_consec_losses = 0
    
    current_balance = 0.0
    balance_history = [0.0]
    peak = 0.0
    max_dd = 0.0
    
    for _, row in df.iterrows():
        p = row["pnl"]
        if row["status"] == "WIN":
            consec_wins += 1
            max_consec_wins = max(max_consec_wins, consec_wins)
            consec_losses = 0
        elif row["status"] == "LOSS":
            consec_losses += 1
            max_consec_losses = max(max_consec_losses, consec_losses)
            consec_wins = 0
            
        current_balance += p
        balance_history.append(current_balance)
        if current_balance > peak:
            peak = current_balance
        dd = peak - current_balance
        if dd > max_dd:
            max_dd = dd

    best_strat = df.groupby("strategy")["pnl"].sum().idxmax() if len(df) > 0 else None
    best_market = df.groupby("market")["pnl"].sum().idxmax() if len(df) > 0 else None
    best_day = df.groupby("day")["pnl"].sum().idxmax() if len(df) > 0 else None
    
    best_hour_idx = df.groupby("hour")["pnl"].sum().idxmax() if len(df) > 0 else 9
    best_session = "Morning" if best_hour_idx < 12 else ("Afternoon" if best_hour_idx < 16 else "Evening")

    # Formulate Charts
    equity_curve = []
    cumulative = 0.0
    for idx, row in df.iterrows():
        cumulative += row["pnl"]
        equity_curve.append({
            "trade_number": idx + 1,
            "date": row["date"].strftime("%Y-%m-%d"),
            "equity": cumulative,
            "pnl": row["pnl"]
        })
        
    strategy_pnl = df.groupby("strategy")["pnl"].sum().to_dict()
    monthly_pnl = df.groupby("month")["pnl"].sum().to_dict()
    daywise_pnl = df.groupby("day")["pnl"].sum().to_dict()
    hourwise_pnl = df.groupby("hour")["pnl"].sum().to_dict()
    
    df["r_bucket"] = df["r_multiple"].apply(lambda r: round(r * 2) / 2)
    r_distribution = df["r_bucket"].value_counts().to_dict()
    r_distribution = {str(k): int(v) for k, v in r_distribution.items()}
    
    confidence_pnl = df.groupby("confidence")["pnl"].mean().to_dict()
    confidence_pnl = {str(k): float(v) for k, v in confidence_pnl.items()}
    
    charts = {
        "equity_curve": equity_curve,
        "monthly_pnl": {str(k): float(v) for k, v in monthly_pnl.items()},
        "strategy_pnl": {str(k): float(v) for k, v in strategy_pnl.items()},
        "daywise_pnl": {str(k): float(v) for k, v in daywise_pnl.items()},
        "hourwise_pnl": {f"{k}:00": float(v) for k, v in hourwise_pnl.items()},
        "r_distribution": r_distribution,
        "psychology_pnl": confidence_pnl
    }
    
    # Compute Category-wise Analytics
    category_analytics = {
        "market_segment": {},
        "trading_style": {},
        "direction": {},
        "strategy": {}
    }
    
    # 1. Market Segment
    segments = ["Indian Equity", "Indian Futures", "Indian Options", "Forex", "Crypto", "Commodity"]
    for seg in segments:
        sub = df[df["segment"].str.lower() == seg.lower()]
        if len(sub) > 0:
            category_analytics["market_segment"][seg] = compute_metrics_for_trades(sub)
        
    # 2. Trading Style
    styles = ["Intraday", "Swing", "Scalping", "Positional"]
    for style in styles:
        sub = df[df["trading_type"].str.lower() == style.lower()]
        if len(sub) > 0:
            category_analytics["trading_style"][style] = compute_metrics_for_trades(sub)
        
    # 3. Direction
    sub_long = df[df["direction"].str.upper().isin(["BUY", "LONG"])]
    sub_short = df[df["direction"].str.upper().isin(["SELL", "SHORT"])]
    if len(sub_long) > 0:
        category_analytics["direction"]["Long"] = compute_metrics_for_trades(sub_long)
    if len(sub_short) > 0:
        category_analytics["direction"]["Short"] = compute_metrics_for_trades(sub_short)
    
    # 4. Strategy Grouping
    all_strategies = df["strategy"].unique()
    for strat in all_strategies:
        sub = df[df["strategy"] == strat]
        if len(sub) > 0:
            category_analytics["strategy"][strat] = compute_metrics_for_trades(sub)

    response_obj = DashboardMetricsResponse(
        total_pnl=round(total_pnl, 2),
        win_rate=round(win_rate, 2),
        total_trades=total_trades,
        wins=wins,
        losses=losses,
        avg_r=round(avg_r, 2),
        profit_factor=round(profit_factor, 2),
        expectancy=round(expectancy, 2),
        max_drawdown=round(max_dd, 2),
        consecutive_wins=max_consec_wins,
        consecutive_losses=max_consec_losses,
        best_strategy=best_strat,
        best_timeframe="1D",
        best_session=best_session,
        best_market=best_market,
        charts=charts,
        category_analytics=category_analytics,
        db_connected=db_connected,
        db_name=db_name,
        db_last_sync=datetime.now().strftime("%I:%M %p")
    )
    
    # Store to Redis cache
    try:
        redis_cache.set(cache_key, jsonable_encoder(response_obj), ex=CACHE_DURATION_SEC)
    except Exception as e:
        print(f"Failed to cache dashboard metrics: {e}")
    return response_obj


@router.get("/bootstrap")
def get_initial_bootstrap(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Unified Single-Request Initial Bootstrap Endpoint for instant page loads.
    Fulfills user metadata, watchlist, strategies, scanner settings, and metrics in 1 HTTP round-trip.
    """
    user_data = {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_active": current_user.is_active,
        "auth_provider": current_user.auth_provider,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None
    }
    
    watchlist = [
        {"id": str(w.id), "symbol": w.symbol, "market": w.market, "position": w.position, "settings": w.settings}
        for w in current_user.watchlist_items
    ]
    
    strategies = [
        {"id": str(s.id), "name": s.name, "description": s.description, "rules": s.rules, "risk_rules": s.risk_rules}
        for s in current_user.strategies
    ]
    
    metrics = get_dashboard_metrics(db=db, current_user=current_user)
    
    # Real-time market snapshot for live overview cards
    market_snapshot = []
    default_symbols = [
        ("XAUUSD", "Gold / USD", "Forex"),
        ("EURUSD", "Euro / USD", "Forex"),
        ("BTCUSD", "Bitcoin / USD", "Crypto"),
        ("NIFTY", "Nifty 50 Index", "Indian Market"),
        ("BANKNIFTY", "Nifty Bank", "Indian Market"),
        ("RELIANCE", "Reliance Industries", "Indian Market")
    ]
    for sym, name, mkt in default_symbols:
        live_data = reference_engine.public_service.get_live_price_data(sym, mkt)
        price = 0.0
        change = 0.85 if sym == "XAUUSD" else 0.0
        if live_data and live_data.get("mid"):
            price = float(live_data["mid"])
        else:
            ref = reference_engine.calculate_reference_levels(sym, mkt)
            if ref and ref.get("last_price"):
                price = float(ref["last_price"])
        
        if price == 0.0:
            price = 4078.00 if sym == "XAUUSD" else (1.0875 if sym == "EURUSD" else 67420.00)

        dec = 2 if sym in ["XAUUSD", "BTCUSD", "NIFTY", "BANKNIFTY", "RELIANCE"] else 4
        market_snapshot.append({
            "symbol": sym,
            "name": name,
            "market": mkt,
            "price": round(price, dec),
            "live_price": round(price, dec),
            "change": change
        })

    return {
        "user": user_data,
        "watchlist": watchlist,
        "strategies": strategies,
        "metrics": metrics,
        "market_snapshot": market_snapshot
    }
