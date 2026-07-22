from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List

from app.core.database import get_db
from app.core.redis import redis_cache
from app.api.auth import get_current_user
from app.models.models import User, UserMarketPreferences, DashboardPreference
from app.schemas.schemas import (
    UserMarketPreferencesResponse, UserMarketPreferencesUpdate,
    DashboardPreferenceResponse, DashboardPreferenceUpdate
)
from app.services.market_reference import MarketReferenceEngine
from app.services.indicators import (
    calculate_cpr, calculate_standard_pivots, calculate_camarilla,
    cpr_levels_rounded, camarilla_levels_rounded,
)

router = APIRouter(prefix="/market", tags=["Market References"])

reference_engine = MarketReferenceEngine()

# Supported Forex pairs initially
DEFAULT_FOREX_FAVORITES = [
    "XAUUSD",
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "AUDUSD",
    "NZDUSD",
    "USDCAD",
    "USDCHF"
]

# Supported Indian assets initially
DEFAULT_INDIAN_FAVORITES = [
    "NIFTY",
    "BANKNIFTY",
    "FINNIFTY",
    "MIDCAP",
    "SENSEX",
    "RELIANCE",
    "TCS",
    "INFY",
    "HDFCBANK",
    "SBIN"
]

DEFAULT_FAVORITES = DEFAULT_FOREX_FAVORITES + DEFAULT_INDIAN_FAVORITES

DEFAULT_VISIBLE_LEVELS = {
    "show_trueday_open": True,
    "show_previous_trueday_open": True,
    "show_indian_midnight_open": True,
    "show_cpr": True,
    "show_camarilla": True,
    "show_prev_day_high_low": True,
    "show_prev_day_close": True,
    "show_daily_range": True
}

def seed_market_preferences(db: Session, user_id) -> UserMarketPreferences:
    db_prefs = UserMarketPreferences(
        user_id=user_id,
        favorite_symbols=DEFAULT_FAVORITES,
        visible_reference_levels=DEFAULT_VISIBLE_LEVELS,
        dashboard_layout={"columns": 3, "theme": "dark"}
    )
    db.add(db_prefs)
    db.commit()
    db.refresh(db_prefs)
    return db_prefs

@router.get("/reference")
def get_market_reference_levels(
    symbol: str,
    market: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get live prices, daily ranges, CPR and Camarilla levels, and NY/IST session opens.
    Data is cached efficiently in the database to optimize API rate limits.
    """
    db_item = reference_engine.get_market_data(db, symbol, market, current_user)
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Failed to retrieve market reference levels for the specified symbol."
        )
    
    import decimal
    def to_float(val):
        if val is None:
            return None
        if isinstance(val, decimal.Decimal):
            return float(val)
        return val

    res_dict = {
        "id": str(db_item.id),
        "symbol": db_item.symbol,
        "market": db_item.market,
        "live_price": to_float(db_item.live_price),
        "trueday_open": to_float(db_item.trueday_open),
        "previous_trueday_open": to_float(db_item.previous_trueday_open),
        "indian_midnight_open": to_float(db_item.indian_midnight_open),
        "previous_day_high": to_float(db_item.previous_day_high),
        "previous_day_low": to_float(db_item.previous_day_low),
        "previous_day_close": to_float(db_item.previous_day_close),
        "current_day_high": to_float(db_item.current_day_high),
        "current_day_low": to_float(db_item.current_day_low),
        "daily_range": to_float(db_item.daily_range),
        "cpr_levels": db_item.cpr_levels,
        "camarilla_levels": db_item.camarilla_levels,
        "timezone_info": db_item.timezone_info,
        "last_updated": db_item.last_updated.isoformat() if db_item.last_updated else None
    }

    # Fetch live detailed quote on-the-fly to ensure it's always real-time BBO!
    try:
        live_data = reference_engine.public_service.get_live_price_data(symbol, market)
        if live_data:
            # If the fallback returned dummy 1.0, keep the cached DB value if it exists and is not 1.0
            mid_val = live_data["mid"]
            if mid_val == 1.0 and db_item.live_price and float(db_item.live_price) != 1.0:
                mid_val = float(db_item.live_price)
                
            res_dict.update({
                "bid": live_data["bid"] if live_data["bid"] != 1.0 else mid_val,
                "ask": live_data["ask"] if live_data["ask"] != 1.0 else mid_val,
                "live_price": mid_val,
                "spread": live_data["spread"],
                "timestamp": live_data["timestamp"]
            })
        else:
            res_dict.update({
                "bid": res_dict["live_price"],
                "ask": res_dict["live_price"],
                "spread": 0.0,
                "timestamp": res_dict["last_updated"]
            })
    except Exception:
        res_dict.update({
            "bid": res_dict["live_price"],
            "ask": res_dict["live_price"],
            "spread": 0.0,
            "timestamp": res_dict["last_updated"]
        })
        
    return res_dict


@router.get("/batch")
def get_batch_market_data(
    layout_name: str = "default",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fetches live prices, change %, live status, and mini chart points for all user's favorite symbols in a layout.
    """
    from app.models.models import Watchlist
    watchlist_items = db.query(Watchlist).filter(Watchlist.user_id == current_user.id).all()
    watchlist_items.sort(key=lambda x: (not x.settings.get("pinned", False) if isinstance(x.settings, dict) else True, x.position, x.created_at))
    
    symbols = [item.symbol.upper() for item in watchlist_items]
    
    symbol_names = {
        "XAUUSD": "Gold Spot / US Dollar",
        "EURUSD": "Euro / US Dollar",
        "GBPUSD": "Pound / US Dollar",
        "USDJPY": "US Dollar / Japanese Yen",
        "AUDUSD": "Australian Dollar / US Dollar",
        "NZDUSD": "New Zealand Dollar / US Dollar",
        "USDCAD": "US Dollar / Canadian Dollar",
        "USDCHF": "US Dollar / Swiss Franc",
        "BTCUSD": "Bitcoin / US Dollar",
        "ETHUSD": "Ethereum / US Dollar",
        "NASDAQ": "NASDAQ 100 Index",
        "SPX500": "S&P 500 Index",
        "NIFTY": "Nifty 50 Index",
        "BANKNIFTY": "Nifty Bank Index",
        "FINNIFTY": "Nifty Financial Index",
        "MIDCAP": "Nifty Midcap 50 Index",
        "SENSEX": "BSE Sensex Index",
        "RELIANCE": "Reliance Industries",
        "TCS": "Tata Consultancy Services",
        "INFY": "Infosys Limited",
        "HDFCBANK": "HDFC Bank",
        "SBIN": "State Bank of India",
    }
    
    results = []
    
    for sym in symbols:
        sym_clean = sym.strip().upper()
        is_forex = sym_clean in ["EURUSD", "GBPUSD", "XAUUSD", "USDJPY", "AUDUSD", "NZDUSD", "USDCAD", "USDCHF", "BTCUSD", "ETHUSD", "NASDAQ", "SPX500"]
        market = "Forex" if is_forex else "Indian Market"
        
        # Get market data (stale fallback supported in reference_engine)
        db_item = reference_engine.get_market_data(db, sym_clean, market, current_user)
        if not db_item:
            continue
            
        import decimal
        def to_float(val):
            if val is None:
                return 0.0
            if isinstance(val, decimal.Decimal):
                return float(val)
            return float(val)
            
        # Determine live status: check last_updated age
        from datetime import datetime
        now = datetime.now()
        age_seconds = (now - db_item.last_updated).total_seconds()
        
        if age_seconds < 300: # 5 minutes
            status_str = "LIVE"
            using_cached_data = False
        elif age_seconds < 900: # 15 minutes
            status_str = "DELAYED"
            using_cached_data = True
        else:
            status_str = "OFFLINE"
            using_cached_data = True
            
        prev_close = to_float(db_item.previous_day_close)
        live_price = to_float(db_item.live_price)
        
        if prev_close != 0.0:
            change_pct = ((live_price - prev_close) / prev_close) * 100
        else:
            change_pct = 0.0
            
        # Fetch 7 days daily candles for sparkline with 5-minute caching
        cache_key_spark = f"sparkline:{sym_clean}:1d:7d"
        closes = redis_cache.get(cache_key_spark)
        if not closes:
            candles = reference_engine.public_service.get_historical_candles(sym_clean, market, timeframe="1d", period="7d")
            closes = [float(c["close"]) for c in candles] if candles else [prev_close, live_price]
            redis_cache.set(cache_key_spark, closes, ex=300)
        
        # Map to 100x30 SVG sparkline points
        points_str = ""
        if len(closes) > 1:
            min_c = min(closes)
            max_c = max(closes)
            c_range = max_c - min_c
            if c_range == 0:
                c_range = 1.0
            pts = []
            for idx, c_val in enumerate(closes):
                x = (idx / (len(closes) - 1)) * 100
                y = 30 - ((c_val - min_c) / c_range) * 20 - 5 # padding
                pts.append(f"{x:.1f},{y:.1f}")
            points_str = " ".join(pts)
        else:
            points_str = "0,15 100,15"
            
        results.append({
            "symbol": sym_clean,
            "name": symbol_names.get(sym_clean, sym_clean + " Spot"),
            "price": round(live_price, 4 if is_forex and not sym_clean in ["BTCUSD", "ETHUSD", "NASDAQ", "SPX500"] else 2),
            "change": round(change_pct, 2),
            "points": points_str,
            "isUp": change_pct >= 0.0,
            "status": status_str,
            "using_cached_data": using_cached_data,
            "last_updated": db_item.last_updated.isoformat(),
            "data_source": "Swissquote BBO" if is_forex else "Binance/Yahoo"
        })
        
    return results


@router.get("/swissquote/{symbol}")
def get_swissquote_live_price(symbol: str):
    """
    Fetch real-time Forex & Gold (XAUUSD) live quotes from Swissquote Public BBO feed.
    """
    sym_clean = symbol.strip().upper()
    data = reference_engine.public_service.get_live_price_data(sym_clean, "Forex")
    if not data:
        raise HTTPException(status_code=404, detail=f"Swissquote live data for {symbol} not found.")
    return {
        "symbol": sym_clean,
        "bid": data["bid"],
        "ask": data["ask"],
        "mid": data["mid"],
        "spread": data["spread"],
        "timestamp": data["timestamp"],
        "source": "Swissquote Public BBO Feed"
    }


@router.get("/forex-ladder/{symbol}")
def get_forex_ladder_data(symbol: str, db: Session = Depends(get_db)):
    """
    Backend deterministic calculation of real-time Forex & Gold (XAUUSD) prices,
    CPR levels (TC, Pivot, BC), Camarilla levels (H4, H3, L3, L4), CPR Width Type, and Daily Market Bias.
    """
    sym_clean = symbol.strip().upper()
    market = "Forex"

    # 1. Fetch live BBO quote from Swissquote
    live_data = reference_engine.public_service.get_live_price_data(sym_clean, market)
    if not live_data:
        raise HTTPException(status_code=404, detail=f"Market data for {symbol} not found.")

    bid = float(live_data.get("bid", 0.0))
    ask = float(live_data.get("ask", 0.0))
    mid = float(live_data.get("mid", (bid + ask) / 2 if (bid + ask) > 0 else 0.0))
    spread = float(live_data.get("spread", ask - bid if (bid and ask) else 0.0))
    ltp = mid if mid > 0 else (bid if bid > 0 else ask)

    # 2. Fetch daily OHLC reference levels for CPR & Camarilla
    ref = reference_engine.calculate_reference_levels(sym_clean, market)
    if not ref:
        raise HTTPException(status_code=404, detail=f"Reference levels for {symbol} not found.")

    prev_high = float(ref["previous_day_high"])
    prev_low = float(ref["previous_day_low"])
    prev_close = float(ref["previous_day_close"])

    # 3. Deterministic CPR Calculations
    cpr = calculate_cpr(prev_high, prev_low, prev_close)
    pivot = cpr["pivot"]
    bc = cpr["bc"]
    tc = cpr["tc"]
    cpr_top = max(tc, bc)
    cpr_bottom = min(tc, bc)
    
    cpr_width_pct = abs((cpr_top - cpr_bottom) / pivot) * 100 if pivot != 0 else 0.0

    # 4. Deterministic Camarilla Calculations
    cam = calculate_camarilla(prev_high, prev_low, prev_close)
    h4 = cam["h4"]
    h3 = cam["h3"]
    l3 = cam["l3"]
    l4 = cam["l4"]

    # 5. Deterministic Daily Market Bias Classification
    bias = "NEUTRAL"
    if ltp > cpr_top and ltp > h3:
        bias = "BULLISH"
    elif ltp < cpr_bottom and ltp < l3:
        bias = "BEARISH"

    # 6. CPR Structure Classification
    cpr_type = "NORMAL"
    if cpr_width_pct < 0.12:
        cpr_type = "NARROW (Trending Day Expected)"
    elif cpr_width_pct > 0.28:
        cpr_type = "WIDE (Sideways Day Expected)"

    is_gold_or_jpy = sym_clean in ["XAUUSD", "USDJPY"]
    dec = 2 if is_gold_or_jpy else 4

    return {
        "symbol": sym_clean,
        "ltp": round(ltp, dec),
        "bid": round(bid, dec),
        "ask": round(ask, dec),
        "spread": round(spread, dec),
        "source": "Swissquote Public BBO Feed",
        "bias": bias,
        "cprType": cpr_type,
        "cprWidthPct": round(cpr_width_pct, 4),
        "pivot": round(pivot, dec),
        "tc": round(tc, dec),
        "bc": round(bc, dec),
        "cprTop": round(cpr_top, dec),
        "cprBottom": round(cpr_bottom, dec),
        "h4": round(h4, dec),
        "h3": round(h3, dec),
        "l3": round(l3, dec),
        "l4": round(l4, dec),
        "dec": dec,
        "levels": [
            {"label": "H4", "name": "Camarilla Breakout Buy", "price": round(h4, dec), "type": "h4", "description": "Bullish Expansion Threshold"},
            {"label": "H3", "name": "Camarilla Resistance", "price": round(h3, dec), "type": "h3", "description": "Short Reversal / Supply Zone"},
            {"label": "TC", "name": "CPR Top Central", "price": round(tc, dec), "type": "tc", "description": "Upper CPR Boundary"},
            {"label": "P", "name": "CPR Central Pivot", "price": round(pivot, dec), "type": "pivot", "description": "Daily Mean Equilibrium"},
            {"label": "BC", "name": "CPR Bottom Central", "price": round(bc, dec), "type": "bc", "description": "Lower CPR Boundary"},
            {"label": "L3", "name": "Camarilla Support", "price": round(l3, dec), "type": "l3", "description": "Long Reversal / Demand Zone"},
            {"label": "L4", "name": "Camarilla Breakout Sell", "price": round(l4, dec), "type": "l4", "description": "Bearish Expansion Threshold"}
        ]
    }


@router.get("/preferences", response_model=UserMarketPreferencesResponse)
def get_user_market_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    prefs = db.query(UserMarketPreferences).filter(
        UserMarketPreferences.user_id == current_user.id
    ).first()
    
    if not prefs:
        prefs = seed_market_preferences(db, current_user.id)
        
    return prefs

@router.put("/preferences", response_model=UserMarketPreferencesResponse)
def update_user_market_preferences(
    prefs_in: UserMarketPreferencesUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    prefs = db.query(UserMarketPreferences).filter(
        UserMarketPreferences.user_id == current_user.id
    ).first()
    
    if not prefs:
        prefs = seed_market_preferences(db, current_user.id)
        
    update_data = prefs_in.model_dump(exclude_unset=True)
    
    if "favorite_symbols" in update_data and update_data["favorite_symbols"] is not None:
        prefs.favorite_symbols = update_data["favorite_symbols"]
    if "visible_reference_levels" in update_data and update_data["visible_reference_levels"] is not None:
        # Merge dictionary
        current_levels = dict(prefs.visible_reference_levels or {})
        current_levels.update(update_data["visible_reference_levels"])
        prefs.visible_reference_levels = current_levels
    if "dashboard_layout" in update_data and update_data["dashboard_layout"] is not None:
        current_layout = dict(prefs.dashboard_layout or {})
        current_layout.update(update_data["dashboard_layout"])
        prefs.dashboard_layout = current_layout
    if "broker_credentials" in update_data and update_data["broker_credentials"] is not None:
        current_credentials = dict(prefs.broker_credentials or {})
        current_credentials.update(update_data["broker_credentials"])
        prefs.broker_credentials = current_credentials
        
    db.commit()
    db.refresh(prefs)
    return prefs


# ==========================================
# Dashboard Preferences Management Endpoints
# ==========================================

def get_default_layout_preference(layout_name: str) -> dict:
    from app.core.config import settings
    all_widgets = settings.ADMIN_DEFAULT_WIDGETS
    default_vis = dict(settings.ADMIN_DEFAULT_WIDGET_VISIBILITY)
    
    if layout_name == "default":
        return {
            "selected_symbols": ["XAUUSD", "GBPUSD", "EURUSD", "NIFTY", "BANKNIFTY", "BTCUSD"],
            "widget_visibility": default_vis,
            "widget_order": all_widgets
        }
    elif layout_name == "Scalping":
        vis = {w: False for w in all_widgets}
        for w in ["livePriceFeed", "sessionMetrics", "cprLevels", "camarillaLevels", "watchlist", "aiInsights"]:
            vis[w] = True
        return {
            "selected_symbols": ["XAUUSD", "GBPUSD", "EURUSD"],
            "widget_visibility": vis,
            "widget_order": all_widgets
        }
    elif layout_name == "Swing Trading":
        vis = {w: False for w in all_widgets}
        for w in ["marketDashboard", "institutionalLevels", "analyticsOverview", "economicCalendar", "watchlist"]:
            vis[w] = True
        return {
            "selected_symbols": ["BTCUSD", "ETHUSD", "NASDAQ", "SPX500", "RELIANCE", "TCS"],
            "widget_visibility": vis,
            "widget_order": all_widgets
        }
    elif layout_name == "Analytics Focus":
        vis = {w: False for w in all_widgets}
        for w in ["analyticsOverview", "tradePerformance", "aiInsights", "voiceJournalSummary"]:
            vis[w] = True
        return {
            "selected_symbols": ["NIFTY", "BANKNIFTY", "RELIANCE"],
            "widget_visibility": vis,
            "widget_order": all_widgets
        }
    else:
        # Custom user layout fallback to standard defaults
        return {
            "selected_symbols": ["XAUUSD", "GBPUSD", "EURUSD", "NIFTY", "BANKNIFTY", "BTCUSD"],
            "widget_visibility": default_vis,
            "widget_order": all_widgets
        }

def seed_dashboard_preference(db: Session, user_id, layout_name: str) -> DashboardPreference:
    import uuid
    layout_data = get_default_layout_preference(layout_name)
    db_pref = DashboardPreference(
        id=uuid.uuid4(),
        user_id=user_id,
        layout_name=layout_name,
        selected_symbols=layout_data["selected_symbols"],
        widget_visibility=layout_data["widget_visibility"],
        widget_order=layout_data["widget_order"]
    )
    db.add(db_pref)
    db.commit()
    db.refresh(db_pref)
    return db_pref

@router.get("/dashboard-preferences", response_model=DashboardPreferenceResponse)
def get_dashboard_preferences(
    layout_name: str = "default",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    pref = db.query(DashboardPreference).filter(
        DashboardPreference.user_id == current_user.id,
        DashboardPreference.layout_name == layout_name
    ).first()
    
    if not pref:
        pref = seed_dashboard_preference(db, current_user.id, layout_name)
        
    return pref

@router.get("/dashboard-preferences/layouts", response_model=List[str])
def get_dashboard_layouts_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    default_layouts = ["default", "Scalping", "Swing Trading", "Analytics Focus"]
    
    saved_prefs = db.query(DashboardPreference.layout_name).filter(
        DashboardPreference.user_id == current_user.id
    ).all()
    
    saved_names = [p[0] for p in saved_prefs]
    
    all_layouts = list(default_layouts)
    for name in saved_names:
        if name not in all_layouts:
            all_layouts.append(name)
            
    return all_layouts

@router.post("/dashboard-preferences", response_model=DashboardPreferenceResponse)
def save_dashboard_preferences(
    pref_in: DashboardPreferenceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    layout_name = pref_in.layout_name or "default"
    
    pref = db.query(DashboardPreference).filter(
        DashboardPreference.user_id == current_user.id,
        DashboardPreference.layout_name == layout_name
    ).first()
    
    if not pref:
        import uuid
        # Fetch default seed data if it's one of default layouts
        layout_data = get_default_layout_preference(layout_name)
        pref = DashboardPreference(
            id=uuid.uuid4(),
            user_id=current_user.id,
            layout_name=layout_name,
            selected_symbols=layout_data["selected_symbols"],
            widget_visibility=layout_data["widget_visibility"],
            widget_order=layout_data["widget_order"]
        )
        db.add(pref)
        
    update_data = pref_in.model_dump(exclude_unset=True)
    if "selected_symbols" in update_data and update_data["selected_symbols"] is not None:
        pref.selected_symbols = update_data["selected_symbols"]
    if "widget_visibility" in update_data and update_data["widget_visibility"] is not None:
        pref.widget_visibility = update_data["widget_visibility"]
    if "widget_order" in update_data and update_data["widget_order"] is not None:
        pref.widget_order = update_data["widget_order"]
        
    db.commit()
    db.refresh(pref)
    return pref

@router.delete("/dashboard-preferences", status_code=status.HTTP_204_NO_CONTENT)
def delete_dashboard_preferences(
    layout_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    default_layouts = ["default", "Scalping", "Swing Trading", "Analytics Focus"]
    if layout_name in default_layouts:
        raise HTTPException(
            status_code=400,
            detail=f"Predefined default layout '{layout_name}' cannot be deleted."
        )
        
    pref = db.query(DashboardPreference).filter(
        DashboardPreference.user_id == current_user.id,
        DashboardPreference.layout_name == layout_name
    ).first()
    
    if not pref:
        raise HTTPException(
            status_code=404,
            detail=f"Layout preference '{layout_name}' not found."
        )
        
    db.delete(pref)
    db.commit()
    return None

@router.post("/dashboard-preferences/reset", response_model=DashboardPreferenceResponse)
def reset_dashboard_preferences(
    layout_name: str = "default",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    pref = db.query(DashboardPreference).filter(
        DashboardPreference.user_id == current_user.id,
        DashboardPreference.layout_name == layout_name
    ).first()
    
    layout_data = get_default_layout_preference(layout_name)
    
    if not pref:
        import uuid
        pref = DashboardPreference(
            id=uuid.uuid4(),
            user_id=current_user.id,
            layout_name=layout_name
        )
        db.add(pref)
        
    pref.selected_symbols = layout_data["selected_symbols"]
    pref.widget_visibility = layout_data["widget_visibility"]
    pref.widget_order = layout_data["widget_order"]
    
    db.commit()
    db.refresh(pref)
    return pref

@router.get("/calendar")
def get_economic_calendar():
    """
    Get the current week's high impact economic calendar events.
    """
    return reference_engine.public_service.get_economic_calendar()


from fastapi import WebSocket, WebSocketDisconnect
import json
import asyncio
from app.core.database import SessionLocal
from app.models.models import User, MarketData
from app.services.market_data import AliceBlueService, OandaService
from datetime import datetime, timezone

def get_live_price_tick_helper(db: Session, symbol: str, market: str, user: Optional[User]) -> dict:
    sym_upper = symbol.strip().upper()
    live_connected = False
    live_price = None
    
    # 1. Try to load dynamically from Alice Blue or Oanda if user is authenticated and has credentials
    if user:
        try:
            from app.models.models import UserMarketPreferences
            prefs = db.query(UserMarketPreferences).filter(UserMarketPreferences.user_id == user.id).first()
            if prefs and prefs.broker_credentials:
                pref_feed = prefs.broker_credentials.get("preferred_feed")
                if pref_feed == "alice_blue" and prefs.broker_credentials.get("alice_blue_api_key"):
                    alice_service = AliceBlueService()
                    alice_service.initialize(prefs.broker_credentials)
                    live_price = alice_service.get_live_price(sym_upper, market)
                    if live_price and live_price != 1.0:
                        live_connected = True
                elif pref_feed == "oanda" and prefs.broker_credentials.get("oanda_token"):
                    oanda_service = OandaService()
                    oanda_service.initialize(prefs.broker_credentials)
                    live_price = oanda_service.get_live_price(sym_upper, market)
                    if live_price and live_price != 1.0:
                        live_connected = True
        except Exception as e:
            print(f"Error checking credentials in WS tick helper: {e}")
            
    # 2. Try Swissquote public feed for Forex
    if live_price is None or live_price == 1.0:
        try:
            live_data = reference_engine.public_service.get_live_price_data(sym_upper, market)
            if live_data:
                mid_val = live_data["mid"]
                if mid_val and mid_val != 1.0:
                    live_price = mid_val
                    # Consider Forex/Gold BBO as live connected
                    if market.lower() == "forex" or sym_upper == "XAUUSD":
                        live_connected = True
        except Exception as e:
            print(f"Error getting Swissquote price in WS tick helper: {e}")
            
    # 3. Fallback to cached DB price
    if live_price is None or live_price == 1.0:
        try:
            db_item = db.query(MarketData).filter(
                MarketData.symbol == sym_upper,
                MarketData.market == market
            ).first()
            if db_item and db_item.live_price and float(db_item.live_price) != 1.0:
                live_price = float(db_item.live_price)
        except Exception as e:
            print(f"Error querying DB cache in WS tick helper: {e}")
            
    # 4. Fallback to last close from candles
    if live_price is None or live_price == 1.0:
        try:
            candles = reference_engine.public_service.get_historical_candles(sym_upper, market, timeframe="1d", period="5d")
            if candles:
                live_price = float(candles[-1]["close"])
        except Exception as e:
            print(f"Error getting last close in WS tick helper: {e}")
            
    # 5. Hardcoded baseline fallback
    if live_price is None or live_price == 1.0:
        base_prices = {
            "NIFTY": 23480.0,
            "BANKNIFTY": 49800.0,
            "FINNIFTY": 22400.0,
            "RELIANCE": 2930.0,
            "TCS": 3850.0,
            "INFY": 1500.0,
            "HDFCBANK": 1600.0,
            "SBIN": 830.0,
            "XAUUSD": 2315.0,
            "EURUSD": 1.0850,
            "GBPUSD": 1.2720,
            "BTCUSD": 67250.0
        }
        live_price = base_prices.get(sym_upper, 100.0)
        
    return {
        "price": live_price,
        "live_connected": live_connected
    }

@router.websocket("/ws")
async def market_websocket(websocket: WebSocket):
    # Accept WebSocket connection
    await websocket.accept()
    print("[WebSocket] Client connection established.")
    
    token = websocket.query_params.get("token")
    current_user = None
    if token:
        try:
            from jose import jwt
            from app.core.config import settings
            from uuid import UUID
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
            user_id: str = payload.get("sub")
            if user_id:
                db = SessionLocal()
                try:
                    current_user = db.query(User).filter(User.id == UUID(user_id)).first()
                finally:
                    db.close()
            print(f"[WebSocket] User authenticated: {current_user.email if current_user else 'Unknown'}")
        except Exception as auth_err:
            print(f"[WebSocket] Authentication failed: {auth_err}")
            
    active_subscription = None
    send_task = None
    
    async def send_ticks():
        nonlocal active_subscription, current_user
        last_base_price = None
        while True:
            if not active_subscription:
                await asyncio.sleep(1)
                continue
                
            symbol = active_subscription["symbol"]
            market = active_subscription["market"]
            
            db = SessionLocal()
            try:
                # 1. Fetch price tick
                tick_info = get_live_price_tick_helper(db, symbol, market, current_user)
                base_price = tick_info["price"]
                live_connected = tick_info["live_connected"]
                
                # Introduce slight simulation ticks fluctuations if not connected to a live exchange BBO feeds
                if not live_connected:
                    import random
                    # Walk of +/- 0.02%
                    fluctuation = base_price * random.uniform(-0.0002, 0.0002)
                    price = base_price + fluctuation
                else:
                    price = base_price
                
                # 2. Recalculate indicators dynamically
                db_item = db.query(MarketData).filter(
                    MarketData.symbol == symbol,
                    MarketData.market == market
                ).first()
                
                if db_item:
                    # Update database live_price cache
                    try:
                        db_item.live_price = price
                        db_item.last_updated = datetime.now()
                        db.commit()
                    except Exception as db_update_err:
                        db.rollback()
                        print(f"Error caching price in WS loop: {db_update_err}")
                        
                    curr_high = float(db_item.current_day_high) if db_item.current_day_high else price
                    curr_low = float(db_item.current_day_low) if db_item.current_day_low else price
                    curr_high = max(curr_high, price)
                    curr_low = min(curr_low, price)
                    
                    prev_high = float(db_item.previous_day_high) if db_item.previous_day_high else price
                    prev_low = float(db_item.previous_day_low) if db_item.previous_day_low else price
                    prev_close = float(db_item.previous_day_close) if db_item.previous_day_close else price
                    
                    daily_range = curr_high - curr_low
                    
                    # Recalculate CPR
                    cpr = calculate_cpr(prev_high, prev_low, prev_close)
                    std = calculate_standard_pivots(cpr["pivot"], prev_high, prev_low)
                    
                    # Recalculate Camarilla
                    cam = calculate_camarilla(prev_high, prev_low, prev_close)
                    
                    payload = {
                        "type": "tick",
                        "symbol": symbol,
                        "price": price,
                        "live_connected": live_connected,
                        "daily_range": daily_range,
                        "current_day_high": curr_high,
                        "current_day_low": curr_low,
                        "trueday_open": float(db_item.trueday_open) if db_item.trueday_open else price,
                        "previous_trueday_open": float(db_item.previous_trueday_open) if db_item.previous_trueday_open else price,
                        "indian_midnight_open": float(db_item.indian_midnight_open) if db_item.indian_midnight_open else price,
                        "previous_day_high": prev_high,
                        "previous_day_low": prev_low,
                        "previous_day_close": prev_close,
                        "cpr_levels": cpr_levels_rounded(cpr, std),
                        "camarilla_levels": camarilla_levels_rounded(cam),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    
                    await websocket.send_json(payload)
                    print(f"[WebSocket] Sent Tick: {symbol} = {price:.4f} (Live: {live_connected})")
            except Exception as loop_err:
                print(f"[WebSocket] Loop exception: {loop_err}")
            finally:
                db.close()
                
            await asyncio.sleep(1)
            
    try:
        send_task = asyncio.create_task(send_ticks())
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            action = message.get("action")
            
            if action == "subscribe":
                symbol = message.get("symbol")
                market = message.get("market")
                if symbol and market:
                    active_subscription = {"symbol": symbol.upper(), "market": market}
                    print(f"[WebSocket] Subscribed to {symbol} ({market})")
                    await websocket.send_json({
                        "type": "subscription_success",
                        "symbol": symbol.upper(),
                        "message": f"Subscribed successfully to {symbol}"
                    })
            elif action == "unsubscribe":
                active_subscription = None
                print("[WebSocket] Unsubscribed")
                await websocket.send_json({"type": "unsubscribed"})
            elif action == "ping":
                await websocket.send_json({"type": "pong"})
                
    except WebSocketDisconnect:
        print("[WebSocket] Connection closed by client.")
    except Exception as ws_err:
        print(f"[WebSocket] Connection error: {ws_err}")
    finally:
        if send_task:
            send_task.cancel()
