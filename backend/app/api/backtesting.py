from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pytz
import uuid
import time
import pandas as pd

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.models import User, MarketCandle
from app.services.market_data import PublicMarketDataService
from app.services.indicators import calculate_emas, calculate_cpr, calculate_camarilla

router = APIRouter(prefix="/market", tags=["Market Sync & Backtesting"])

public_service = PublicMarketDataService()

# Global state for tracking background sync progress
# key: task_id (UUID string) -> dict: status, progress, total, error
SYNC_TASKS = {}

class SyncRequest(BaseModel):
    symbol: str
    timeframe: str
    start_date: str  # YYYY-MM-DD
    end_date: Optional[str] = None  # YYYY-MM-DD

class BacktestRequest(BaseModel):
    symbol: str
    timeframe: str
    strategy: str  # ema_cross, cpr_breakout, camarilla_breakout
    initial_capital: float
    risk_per_trade_pct: float
    reward_ratio: float
    start_date: Optional[str] = None
    end_date: Optional[str] = None

def run_candle_sync_task(task_id: str, symbol: str, timeframe: str, start_dt: datetime, end_dt: datetime, user_id: Any):
    db = None
    try:
        from app.core.database import SessionLocal
        db = SessionLocal()
        
        symbol_upper = symbol.strip().upper()
        timeframe_lower = timeframe.strip().lower()
        
        SYNC_TASKS[task_id] = {
            "symbol": symbol_upper,
            "timeframe": timeframe_lower,
            "status": "PROCESSING",
            "progress": 0,
            "message": "Initializing sync..."
        }
        
        # Check user preferences for preferred feed
        from app.models.models import UserMarketPreferences
        prefs = db.query(UserMarketPreferences).filter(UserMarketPreferences.user_id == user_id).first()
        broker_creds = prefs.broker_credentials if prefs else {}
        preferred = broker_creds.get("preferred_feed", "public")
        oanda_token = broker_creds.get("oanda_token")
        oanda_env = broker_creds.get("oanda_env", "practice")
        
        total_inserted = 0
        
        use_binance_fallback = False
        
        if preferred == "oanda" and oanda_token:
            # OANDA SYNC LOOP
            base_url = "https://api-fxtrade.oanda.com" if oanda_env == "live" else "https://api-fxpractice.oanda.com"
            cleaned_sym = symbol_upper.replace("/", "_").replace("-", "_").replace("=X", "")
            if "_" not in cleaned_sym and len(cleaned_sym) == 6:
                cleaned_sym = f"{cleaned_sym[:3]}_{cleaned_sym[3:]}"
                
            granularity_map = {
                "1m": "M1",
                "5m": "M5",
                "15m": "M15",
                "30m": "M30",
                "60m": "H1",
                "1h": "H1",
                "1d": "D"
            }
            granularity = granularity_map.get(timeframe_lower, "D")
            
            current_dt = start_dt
            
            while current_dt < end_dt:
                from_str = current_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
                to_str = end_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
                url = f"{base_url}/v3/instruments/{cleaned_sym}/candles"
                headers = {
                    "Authorization": f"Bearer {oanda_token}",
                    "Content-Type": "application/json"
                }
                params = {
                    "granularity": granularity,
                    "from": from_str,
                    "to": to_str,
                    "price": "M",
                    "count": 1000
                }
                
                response = None
                for attempt in range(3):
                    try:
                        import requests
                        res = requests.get(url, headers=headers, params=params, timeout=10)
                        if res.status_code == 200:
                            response = res.json()
                            break
                    except Exception as e:
                        print(f"Oanda Sync error (attempt {attempt+1}): {e}")
                    time.sleep(0.5)
                    
                if not response:
                    break
                    
                raw_candles = response.get("candles", [])
                if not raw_candles:
                    break
                    
                batch_candles = []
                for item in raw_candles:
                    if "mid" not in item:
                        continue
                    mid = item["mid"]
                    time_str = item["time"]
                    
                    # Parse Oanda time
                    cleaned_time = time_str.replace("Z", "+00:00")
                    if "." in cleaned_time:
                        parts = cleaned_time.split(".")
                        frac = parts[1][:6]
                        tz = ""
                        if "+" in parts[1]:
                            tz = "+" + parts[1].split("+")[1]
                        cleaned_time = parts[0] + "." + frac + tz
                    
                    dt_utc = datetime.fromisoformat(cleaned_time)
                    current_dt = dt_utc + timedelta(seconds=1)
                    
                    if dt_utc >= end_dt:
                        continue
                        
                    candle_data = {
                        "symbol": symbol_upper,
                        "timeframe": timeframe_lower,
                        "datetime": dt_utc,
                        "open": float(mid["o"]),
                        "high": float(mid["h"]),
                        "low": float(mid["l"]),
                        "close": float(mid["c"]),
                        "volume": float(item.get("volume", 0)),
                        "source": "oanda_credentials"
                    }
                    batch_candles.append(candle_data)
                    
                if not batch_candles:
                    break
                    
                # Upsert into database
                for c in batch_candles:
                    existing = db.query(MarketCandle).filter(
                        MarketCandle.symbol == c["symbol"],
                        MarketCandle.timeframe == c["timeframe"],
                        MarketCandle.datetime == c["datetime"]
                    ).first()
                    
                    if existing:
                        existing.open = c["open"]
                        existing.high = c["high"]
                        existing.low = c["low"]
                        existing.close = c["close"]
                        existing.volume = c["volume"]
                        existing.updated_at = datetime.now()
                    else:
                        db_candle = MarketCandle(**c)
                        db.add(db_candle)
                
                try:
                    db.commit()
                    total_inserted += len(batch_candles)
                    SYNC_TASKS[task_id]["progress"] = total_inserted
                    SYNC_TASKS[task_id]["message"] = f"Downloaded and synchronized {total_inserted} candles from Oanda..."
                except Exception as e:
                    db.rollback()
                    print(f"DB Oanda insertion error: {e}")
                    break
                    
                time.sleep(0.1)
                
            SYNC_TASKS[task_id]["status"] = "COMPLETED"
            SYNC_TASKS[task_id]["message"] = f"Successfully synchronized {total_inserted} Oanda historical candles!"
            
        elif symbol_upper == "XAUUSD":
            # TRADINGVIEW TVDATAFEED SYNC FOR XAUUSD
            try:
                from tvDatafeed import TvDatafeed, Interval as FeedInterval
                tv = TvDatafeed()
                
                interval_map = {
                    "1m": FeedInterval.in_1_minute,
                    "3m": FeedInterval.in_3_minute,
                    "5m": FeedInterval.in_5_minute,
                    "15m": FeedInterval.in_15_minute,
                    "30m": FeedInterval.in_30_minute,
                    "45m": FeedInterval.in_45_minute,
                    "1h": FeedInterval.in_1_hour,
                    "60m": FeedInterval.in_1_hour,
                    "2h": FeedInterval.in_2_hour,
                    "3h": FeedInterval.in_3_hour,
                    "4h": FeedInterval.in_4_hour,
                    "1d": FeedInterval.in_daily,
                    "1w": FeedInterval.in_weekly,
                    "1M": FeedInterval.in_monthly
                }
                feed_interval = interval_map.get(timeframe_lower, FeedInterval.in_1_hour)
                
                delta = end_dt - start_dt
                if timeframe_lower == "1d":
                    n_bars = max(delta.days, 100)
                elif timeframe_lower in ["1h", "60m"]:
                    n_bars = max(int(delta.total_seconds() / 3600), 500)
                elif timeframe_lower == "30m":
                    n_bars = max(int(delta.total_seconds() / 1800), 1000)
                elif timeframe_lower == "15m":
                    n_bars = max(int(delta.total_seconds() / 900), 2000)
                elif timeframe_lower == "5m":
                    n_bars = max(int(delta.total_seconds() / 300), 3000)
                else: # 1m
                    n_bars = max(int(delta.total_seconds() / 60), 5000)
                    
                n_bars = min(n_bars, 5000)
                
                SYNC_TASKS[task_id]["message"] = f"Fetching {n_bars} bars of XAUUSD from TradingView OANDA chart..."
                df = tv.get_hist(
                    symbol="XAUUSD",
                    exchange="OANDA",
                    interval=feed_interval,
                    n_bars=n_bars
                )
                
                if df is not None and not df.empty:
                    batch_candles = []
                    for timestamp, row in df.iterrows():
                        dt_utc = timestamp
                        if dt_utc.tzinfo is None:
                            dt_utc = dt_utc.replace(tzinfo=pytz.utc)
                        else:
                            dt_utc = dt_utc.astimezone(pytz.utc)
                            
                        if dt_utc < start_dt or dt_utc >= end_dt:
                            continue
                            
                        candle_data = {
                            "symbol": symbol_upper,
                            "timeframe": timeframe_lower,
                            "datetime": dt_utc,
                            "open": float(row["open"]),
                            "high": float(row["high"]),
                            "low": float(row["low"]),
                            "close": float(row["close"]),
                            "volume": float(row["volume"]) if "volume" in row else 0.0,
                            "source": "tradingview_oanda"
                        }
                        batch_candles.append(candle_data)
                        
                    for c in batch_candles:
                        existing = db.query(MarketCandle).filter(
                            MarketCandle.symbol == c["symbol"],
                            MarketCandle.timeframe == c["timeframe"],
                            MarketCandle.datetime == c["datetime"]
                        ).first()
                        
                        if existing:
                            existing.open = c["open"]
                            existing.high = c["high"]
                            existing.low = c["low"]
                            existing.close = c["close"]
                            existing.volume = c["volume"]
                            existing.updated_at = datetime.now()
                        else:
                            db_candle = MarketCandle(**c)
                            db.add(db_candle)
                            
                    db.commit()
                    total_inserted += len(batch_candles)
                    SYNC_TASKS[task_id]["status"] = "COMPLETED"
                    SYNC_TASKS[task_id]["message"] = f"Successfully synchronized {total_inserted} TradingView OANDA Gold candles!"
                else:
                    raise Exception("No data returned from TradingView tvDatafeed")
            except Exception as e:
                print(f"TradingView tvDatafeed sync failed: {e}. Falling back to Binance public sync...")
                use_binance_fallback = True
        else:
            use_binance_fallback = True
            
        if use_binance_fallback:
            # BINANCE PUBLIC SYNC LOOP
            current_start_ms = int(start_dt.timestamp() * 1000)
            end_ms = int(end_dt.timestamp() * 1000)
            
            binance_sym = symbol_upper
            if symbol_upper == "XAUUSD":
                binance_sym = "PAXGUSDT"
            elif symbol_upper == "EURUSD":
                binance_sym = "EURUSDT"
            elif symbol_upper == "GBPUSD":
                binance_sym = "GBPUSDT"
            else:
                binance_sym = f"{symbol_upper}USDT"
                
            interval = timeframe_lower
            if interval == "60m":
                interval = "1h"
                
            url = "https://api.binance.com/api/v3/klines"
            
            while current_start_ms < end_ms:
                params = {
                    "symbol": binance_sym,
                    "interval": interval,
                    "startTime": current_start_ms,
                    "endTime": end_ms,
                    "limit": 1000
                }
                
                response = None
                for attempt in range(3):
                    try:
                        import requests
                        res = requests.get(url, params=params, timeout=10)
                        if res.status_code == 200:
                            response = res.json()
                            break
                    except Exception as e:
                        print(f"Sync error (attempt {attempt+1}): {e}")
                    time.sleep(0.5)
                    
                if not response:
                    break
                    
                batch_candles = []
                for item in response:
                    open_time_ms = item[0]
                    current_start_ms = open_time_ms + 1
                    
                    dt_utc = datetime.fromtimestamp(open_time_ms / 1000.0, tz=pytz.utc)
                    if dt_utc >= end_dt:
                        continue
                        
                    candle_data = {
                        "symbol": symbol_upper,
                        "timeframe": timeframe_lower,
                        "datetime": dt_utc,
                        "open": float(item[1]),
                        "high": float(item[2]),
                        "low": float(item[3]),
                        "close": float(item[4]),
                        "volume": float(item[5]),
                        "source": "binance_public"
                    }
                    batch_candles.append(candle_data)
                    
                if not batch_candles:
                    break
                    
                for c in batch_candles:
                    existing = db.query(MarketCandle).filter(
                        MarketCandle.symbol == c["symbol"],
                        MarketCandle.timeframe == c["timeframe"],
                        MarketCandle.datetime == c["datetime"]
                    ).first()
                    
                    if existing:
                        existing.open = c["open"]
                        existing.high = c["high"]
                        existing.low = c["low"]
                        existing.close = c["close"]
                        existing.volume = c["volume"]
                        existing.updated_at = datetime.now()
                    else:
                        db_candle = MarketCandle(**c)
                        db.add(db_candle)
                
                try:
                    db.commit()
                    total_inserted += len(batch_candles)
                    SYNC_TASKS[task_id]["progress"] = total_inserted
                    SYNC_TASKS[task_id]["message"] = f"Downloaded and synchronized {total_inserted} candles..."
                except Exception as e:
                    db.rollback()
                    print(f"DB insertion error: {e}")
                    break
                    
                time.sleep(0.1)
                
            SYNC_TASKS[task_id]["status"] = "COMPLETED"
            SYNC_TASKS[task_id]["message"] = f"Successfully synchronized {total_inserted} historical candles!"
        
    except Exception as e:
        print(f"Background task failed: {e}")
        SYNC_TASKS[task_id]["status"] = "FAILED"
        SYNC_TASKS[task_id]["message"] = f"Sync failed: {str(e)}"
    finally:
        if db:
            db.close()

@router.post("/sync")
def trigger_historical_sync(
    req: SyncRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    try:
        start_dt = datetime.strptime(req.start_date, "%Y-%m-%d")
        start_dt = start_dt.replace(tzinfo=pytz.utc)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD")
        
    if req.end_date:
        try:
            end_dt = datetime.strptime(req.end_date, "%Y-%m-%d")
            end_dt = end_dt.replace(tzinfo=pytz.utc)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD")
    else:
        end_dt = datetime.now(pytz.utc)
        
    task_id = str(uuid.uuid4())
    SYNC_TASKS[task_id] = {
        "symbol": req.symbol.upper(),
        "timeframe": req.timeframe.lower(),
        "status": "QUEUED",
        "progress": 0,
        "message": "Task queued..."
    }
    
    background_tasks.add_task(
        run_candle_sync_task,
        task_id,
        req.symbol,
        req.timeframe,
        start_dt,
        end_dt,
        current_user.id
    )
    
    return {"task_id": task_id, "status": "QUEUED", "message": "Historical synchronization started in the background."}

@router.get("/sync/status/{task_id}")
def get_sync_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    if task_id not in SYNC_TASKS:
        raise HTTPException(status_code=404, detail="Sync task not found.")
    return SYNC_TASKS[task_id]

@router.get("/candles")
def get_candles(
    symbol: str,
    timeframe: str,
    limit: int = 500,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(MarketCandle).filter(
        MarketCandle.symbol == symbol.upper(),
        MarketCandle.timeframe == timeframe.lower()
    )
    
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(MarketCandle.datetime >= start_dt)
        except ValueError:
            pass
            
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            query = query.filter(MarketCandle.datetime <= end_dt)
        except ValueError:
            pass
            
    query = query.order_by(MarketCandle.datetime.asc())
    candles = query.limit(limit).all()
    
    return [
        {
            "time": c.datetime.isoformat(),
            "open": float(c.open),
            "high": float(c.high),
            "low": float(c.low),
            "close": float(c.close),
            "volume": float(c.volume)
        }
        for c in candles
    ]

@router.post("/backtest/run")
def run_backtest(
    req: BacktestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Retrieve stored candles
    query = db.query(MarketCandle).filter(
        MarketCandle.symbol == req.symbol.upper(),
        MarketCandle.timeframe == req.timeframe.lower()
    )
    
    if req.start_date:
        try:
            start_dt = datetime.strptime(req.start_date, "%Y-%m-%d")
            query = query.filter(MarketCandle.datetime >= start_dt)
        except ValueError:
            pass
            
    if req.end_date:
        try:
            end_dt = datetime.strptime(req.end_date, "%Y-%m-%d")
            query = query.filter(MarketCandle.datetime <= end_dt)
        except ValueError:
            pass
            
    candles = query.order_by(MarketCandle.datetime.asc()).all()
    if not candles or len(candles) < 50:
        raise HTTPException(
            status_code=400,
            detail="Insufficient candle data in database to run backtest. Please run historical sync first."
        )
        
    # Standard backtest simulation variables
    capital = req.initial_capital
    risk_pct = req.risk_per_trade_pct / 100.0
    reward_ratio = req.reward_ratio
    
    trades = []
    equity_curve = [{"time": candles[0].datetime.isoformat(), "equity": capital}]
    active_position = None  # Dict: direction, entry_price, stop_loss, target_price, size, time
    
    # Pre-calculate Indicators for the candles list to avoid re-runs
    closes = [float(c.close) for c in candles]
    highs = [float(c.high) for c in candles]
    lows = [float(c.low) for c in candles]
    times = [c.datetime.isoformat() for c in candles]
    
    # Calculate EMA indicators
    df = pd.DataFrame({"close": closes})
    calculate_emas(df, close_col="close", spans=(20, 50))
    ema20 = df["EMA20"].values
    ema50 = df["EMA50"].values
    
    # Candle-by-candle replay loop
    for i in range(20, len(candles)):
        c = candles[i]
        curr_time = times[i]
        curr_open = float(c.open)
        curr_high = float(c.high)
        curr_low = float(c.low)
        curr_close = float(c.close)
        
        # 1. Manage active position if any
        if active_position:
            is_closed = False
            p = active_position
            
            # Long position checks
            if p["direction"] == "BUY":
                if curr_low <= p["stop_loss"]:
                    # Hit Stop Loss
                    is_closed = True
                    exit_price = p["stop_loss"]
                    profit = (exit_price - p["entry_price"]) * p["size"]
                    status_str = "LOSS"
                elif curr_high >= p["target_price"]:
                    # Hit Target
                    is_closed = True
                    exit_price = p["target_price"]
                    profit = (exit_price - p["entry_price"]) * p["size"]
                    status_str = "WIN"
            # Short position checks
            elif p["direction"] == "SELL":
                if curr_high <= p["stop_loss"]: # wait, for Sell, low price hit means WIN, high price hit means Loss
                    pass # let's check correctly
                if curr_high >= p["stop_loss"]:
                    # Hit Stop Loss
                    is_closed = True
                    exit_price = p["stop_loss"]
                    profit = (p["entry_price"] - exit_price) * p["size"]
                    status_str = "LOSS"
                elif curr_low <= p["target_price"]:
                    # Hit Target
                    is_closed = True
                    exit_price = p["target_price"]
                    profit = (p["entry_price"] - exit_price) * p["size"]
                    status_str = "WIN"
                    
            if is_closed:
                capital += profit
                trades.append({
                    "entry_time": p["entry_time"],
                    "exit_time": curr_time,
                    "direction": p["direction"],
                    "entry_price": p["entry_price"],
                    "exit_price": exit_price,
                    "stop_loss": p["stop_loss"],
                    "target_price": p["target_price"],
                    "profit": round(profit, 2),
                    "status": status_str,
                    "net_equity": round(capital, 2)
                })
                active_position = None
                equity_curve.append({"time": curr_time, "equity": round(capital, 2)})
                
        # 2. Check for strategy setups to enter new positions (only if no active position)
        if not active_position:
            # A. EMA Cross strategy
            if req.strategy == "ema_cross":
                # BUY: EMA20 crosses above EMA50
                if ema20[i] > ema50[i] and ema20[i-1] <= ema50[i-1]:
                    direction = "BUY"
                    entry_price = curr_close
                    sl = curr_low * 0.99  # 1% below current low
                    tp = entry_price + (entry_price - sl) * reward_ratio
                    
                    # Risk management: size = (capital * risk) / (entry - sl)
                    risk_amount = capital * risk_pct
                    risk_per_unit = entry_price - sl
                    if risk_per_unit > 0:
                        size = risk_amount / risk_per_unit
                        active_position = {
                            "direction": direction,
                            "entry_price": entry_price,
                            "stop_loss": sl,
                            "target_price": tp,
                            "size": size,
                            "entry_time": curr_time
                        }
                # SELL: EMA20 crosses below EMA50
                elif ema20[i] < ema50[i] and ema20[i-1] >= ema50[i-1]:
                    direction = "SELL"
                    entry_price = curr_close
                    sl = curr_high * 1.01  # 1% above current high
                    tp = entry_price - (sl - entry_price) * reward_ratio
                    
                    risk_amount = capital * risk_pct
                    risk_per_unit = sl - entry_price
                    if risk_per_unit > 0:
                        size = risk_amount / risk_per_unit
                        active_position = {
                            "direction": direction,
                            "entry_price": entry_price,
                            "stop_loss": sl,
                            "target_price": tp,
                            "size": size,
                            "entry_time": curr_time
                        }
                        
            # B. CPR Breakout strategy
            elif req.strategy == "cpr_breakout":
                # Compute CPR for yesterday
                prev_high = highs[i-1]
                prev_low = lows[i-1]
                prev_close = closes[i-1]
                cpr = calculate_cpr(prev_high, prev_low, prev_close)
                cpr_top = cpr["cpr_top"]
                cpr_bottom = cpr["cpr_bottom"]
                
                # BUY: Close crosses above yesterday's CPR Top
                if curr_close > cpr_top and closes[i-1] <= cpr_top:
                    direction = "BUY"
                    entry_price = curr_close
                    sl = cpr_bottom
                    tp = entry_price + (entry_price - sl) * reward_ratio
                    
                    risk_amount = capital * risk_pct
                    risk_per_unit = entry_price - sl
                    if risk_per_unit > 0:
                        size = risk_amount / risk_per_unit
                        active_position = {
                            "direction": direction,
                            "entry_price": entry_price,
                            "stop_loss": sl,
                            "target_price": tp,
                            "size": size,
                            "entry_time": curr_time
                        }
                        
            # C. Camarilla Breakout strategy
            elif req.strategy == "camarilla_breakout":
                prev_high = highs[i-1]
                prev_low = lows[i-1]
                prev_close = closes[i-1]
                cam = calculate_camarilla(prev_high, prev_low, prev_close)
                h4 = cam["h4"]
                h3 = cam["h3"]
                l3 = cam["l3"]
                l4 = cam["l4"]
                
                # BUY: Close crosses above H4
                if curr_close > h4 and closes[i-1] <= h4:
                    direction = "BUY"
                    entry_price = curr_close
                    sl = h3
                    tp = entry_price + (entry_price - sl) * reward_ratio
                    
                    risk_amount = capital * risk_pct
                    risk_per_unit = entry_price - sl
                    if risk_per_unit > 0:
                        size = risk_amount / risk_per_unit
                        active_position = {
                            "direction": direction,
                            "entry_price": entry_price,
                            "stop_loss": sl,
                            "target_price": tp,
                            "size": size,
                            "entry_time": curr_time
                        }
                        
    # End of simulation
    # Calculate performance metrics
    total_trades = len(trades)
    if total_trades > 0:
        wins = [t for t in trades if t["status"] == "WIN"]
        losses = [t for t in trades if t["status"] == "LOSS"]
        win_rate = (len(wins) / total_trades) * 100.0
        
        total_profit = sum(t["profit"] for t in wins)
        total_loss = abs(sum(t["profit"] for t in losses))
        profit_factor = total_profit / total_loss if total_loss > 0 else total_profit
    else:
        win_rate = 0.0
        profit_factor = 0.0
        
    # Calculate drawdown
    peak = req.initial_capital
    max_dd = 0.0
    for e in equity_curve:
        if e["equity"] > peak:
            peak = e["equity"]
        dd = (peak - e["equity"]) / peak * 100.0
        if dd > max_dd:
            max_dd = dd
            
    return {
        "summary": {
            "initial_capital": req.initial_capital,
            "final_capital": round(capital, 2),
            "net_profit": round(capital - req.initial_capital, 2),
            "percentage_gain": round((capital - req.initial_capital) / req.initial_capital * 100.0, 2),
            "total_trades": total_trades,
            "win_rate": round(win_rate, 2),
            "profit_factor": round(profit_factor, 2),
            "max_drawdown": round(max_dd, 2)
        },
        "trades": trades,
        "equity_curve": equity_curve
    }
