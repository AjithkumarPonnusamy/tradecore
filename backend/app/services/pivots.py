from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional
import pytz
from app.services.market_data import PublicMarketDataService
from app.services.indicators import calculate_cpr, calculate_standard_pivots, calculate_camarilla

def get_trading_session_date(candle_time_str: str, market: str) -> date:
    # Parse the ISO time string to UTC datetime
    dt_utc = datetime.fromisoformat(candle_time_str)
    
    # Convert to appropriate market timezone
    if market.lower() == "forex":
        tz = pytz.timezone("America/New_York")
    else:
        tz = pytz.timezone("Asia/Kolkata")
        
    dt_local = dt_utc.astimezone(tz)
    
    # If Forex and hour is 17:00 (5 PM NY) or later, it belongs to the next day's session
    if market.lower() == "forex" and dt_local.hour >= 17:
        return (dt_local + timedelta(days=1)).date()
    else:
        return dt_local.date()

def calculate_pivots_for_date(symbol: str, market: str, target_date_str: str) -> Optional[Dict[str, Any]]:
    """
    Downloads daily historical candles for the given symbol and market.
    Finds the daily candle immediately preceding the target_date_str.
    Calculates CPR levels (tc, pivot, bc, range, range_type) and Camarilla levels (h3, h4, h5, l3, l4, l5).
    """
    yf_service = PublicMarketDataService()
    # Fetch historical data (60 days is plenty to get recent daily candles)
    candles = yf_service.get_historical_candles(symbol, market, timeframe="1d", period="60d")
    if not candles:
        return None
        
    # Parse target date
    try:
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
    except ValueError:
        return None

    # Filter candles strictly before the target date
    valid_candles = []
    for candle in candles:
        try:
            session_date = get_trading_session_date(candle["time"], market)
        except ValueError:
            # Fallback for date strings if fromisoformat fails
            try:
                raw_date_str = candle["time"].split("T")[0]
                session_date = datetime.strptime(raw_date_str, "%Y-%m-%d").date()
            except ValueError:
                continue
        
        if session_date < target_date:
            valid_candles.append((session_date, candle))
            
    if not valid_candles:
        return None
        
    # Sort by date ascending to find the most recent candle before the target date
    valid_candles.sort(key=lambda x: x[0])
    prev_date, prev_candle = valid_candles[-1]
    
    high = prev_candle["high"]
    low = prev_candle["low"]
    close = prev_candle["close"]
    
    # CPR Calculations
    cpr = calculate_cpr(high, low, close)
    pivot = cpr["pivot"]
    cpr_top = cpr["cpr_top"]
    cpr_bottom = cpr["cpr_bottom"]
    cpr_range = cpr["range"]
    range_type = cpr["range_type"]
    
    # Camarilla Calculations
    cam = calculate_camarilla(high, low, close)
    h1, h2, h3, h4, h5 = cam["h1"], cam["h2"], cam["h3"], cam["h4"], cam["h5"]
    l1, l2, l3, l4, l5 = cam["l1"], cam["l2"], cam["l3"], cam["l4"], cam["l5"]
    
    # Standard pivot support/resistance
    std = calculate_standard_pivots(pivot, high, low)
    std_r1, std_s1 = std["r1"], std["s1"]
    std_r2, std_s2 = std["r2"], std["s2"]
    std_r5, std_s5 = std["r5"], std["s5"]
    
    return {
        "prev_candle_date": prev_date.isoformat(),
        "cpr": {
            "pivot": round(pivot, 4),
            "tc": round(cpr_top, 4),
            "bc": round(cpr_bottom, 4),
            "range": round(cpr_range, 4),
            "range_type": range_type,
            "r1": round(std_r1, 4),
            "r2": round(std_r2, 4),
            "r5": round(std_r5, 4),
            "s1": round(std_s1, 4),
            "s2": round(std_s2, 4),
            "s5": round(std_s5, 4)
        },
        "camarilla": {
            "h1": round(h1, 4),
            "h2": round(h2, 4),
            "h3": round(h3, 4),
            "h4": round(h4, 4),
            "h5": round(h5, 4),
            "l1": round(l1, 4),
            "l2": round(l2, 4),
            "l3": round(l3, 4),
            "l4": round(l4, 4),
            "l5": round(l5, 4)
        }
    }
