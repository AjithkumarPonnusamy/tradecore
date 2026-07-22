import os
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import requests
import time
import pytz
from app.services.indicators import calculate_emas, calculate_cpr, calculate_camarilla
from app.core.redis import redis_cache

class MarketDataInterface(ABC):
    @abstractmethod
    def get_live_price(self, symbol: str, market: str) -> Optional[float]:
        """Fetch the latest trade price for a symbol."""
        pass

    @abstractmethod
    def get_historical_candles(self, symbol: str, market: str, timeframe: str, period: str = "5d") -> List[Dict[str, Any]]:
        """Fetch historical candle data (OHLCV)."""
        pass

    @abstractmethod
    def scan_symbol(self, symbol: str, market: str, timeframe: str) -> Dict[str, Any]:
        """Scan a specific symbol for standard technical setups."""
        pass


class PublicMarketDataService(MarketDataInterface):
    """
    Public keyless market data service.
    Uses Swissquote public BBO endpoint for live prices/spreads.
    Uses Binance public klines endpoint for historical candles.
    """
    def __init__(self):
        self.cache_duration = 10  # cache duration in seconds
        self.candles_cache_duration = 300  # 5 minutes
        self.tv = None

    def get_economic_calendar(self) -> List[Dict[str, Any]]:
        redis_key = "market:economic_calendar"
        cached_data = redis_cache.get(redis_key)
        if cached_data is not None:
            return cached_data

        url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                events = response.json()
                high_impact = [e for e in events if e.get("impact", "").lower() == "high"]
                
                parsed_events = []
                for e in high_impact:
                    dt_str = e.get("date")
                    try:
                        dt = datetime.fromisoformat(dt_str)
                    except Exception:
                        continue
                    
                    dt_ist = dt.astimezone(ZoneInfo("Asia/Kolkata"))
                    dt_ny = dt.astimezone(ZoneInfo("America/New_York"))
                    
                    parsed_events.append({
                        "date": dt_ist.strftime("%Y-%m-%d"),
                        "istTime": dt_ist.strftime("%H:%M"),
                        "nyTime": dt_ny.strftime("%H:%M"),
                        "cur": e.get("country"),
                        "event": e.get("title"),
                        "impact": "HIGH",
                        "val": e.get("forecast") if e.get("forecast") else "-",
                        "prev": e.get("previous") if e.get("previous") else "-"
                    })
                
                # Cache for 1 hour (3600 seconds)
                redis_cache.set(redis_key, parsed_events, ex=3600)
                return parsed_events
        except Exception as e:
            print(f"Error fetching economic calendar: {e}")
            
        return []

    def _generate_mock_candles(self, symbol: str, timeframe: str, limit: int) -> List[Dict[str, Any]]:
        base_prices = {
            "XAUUSD": 2350.0,
            "EURUSD": 1.0850,
            "GBPUSD": 1.2750,
            "USDJPY": 156.50,
            "AUDUSD": 0.6650,
            "NZDUSD": 0.6150,
            "USDCAD": 1.3650,
            "USDCHF": 0.8950,
            "NIFTY": 23400.0,
            "BANKNIFTY": 49800.0,
            "FINNIFTY": 22400.0,
            "MIDCAP": 11500.0,
            "SENSEX": 77000.0,
            "RELIANCE": 2950.0,
            "TCS": 3850.0,
            "INFY": 1500.0,
            "HDFCBANK": 1600.0,
            "SBIN": 830.0,
        }
        sym = symbol.strip().upper().replace("/", "").replace("-", "").replace("=X", "")
        start_price = base_prices.get(sym, 100.0)
        
        now = datetime.now(timezone.utc)
        delta_map = {
            "1m": timedelta(minutes=1),
            "3m": timedelta(minutes=3),
            "5m": timedelta(minutes=5),
            "15m": timedelta(minutes=15),
            "30m": timedelta(minutes=30),
            "45m": timedelta(minutes=45),
            "1h": timedelta(hours=1),
            "60m": timedelta(hours=1),
            "2h": timedelta(hours=2),
            "3h": timedelta(hours=3),
            "4h": timedelta(hours=4),
            "1d": timedelta(days=1),
            "1w": timedelta(weeks=1),
        }
        delta = delta_map.get(timeframe.strip().lower(), timedelta(days=1))
        
        import hashlib
        seed_num = int(hashlib.md5(sym.encode()).hexdigest(), 16) % 10000
        np.random.seed(seed_num)
        
        prices = [start_price]
        volatility = 0.005
        if timeframe.endswith("m"):
            volatility = 0.0005
        elif timeframe.endswith("h"):
            volatility = 0.0015
            
        for i in range(1, limit):
            change = np.random.normal(0, volatility)
            prices.append(prices[-1] * (1.0 + change))
            
        candles = []
        current_time = now - (limit * delta)
        
        for i in range(limit):
            current_time += delta
            p = prices[i]
            o = p * (1.0 + np.random.normal(0, volatility * 0.2))
            c = p * (1.0 + np.random.normal(0, volatility * 0.2))
            h = max(o, c) * (1.0 + abs(np.random.normal(0, volatility * 0.5)))
            low_val = min(o, c) * (1.0 - abs(np.random.normal(0, volatility * 0.5)))
            v = float(np.random.randint(1000, 100000))
            
            candles.append({
                "time": current_time.isoformat(),
                "open": round(o, 4 if start_price < 10 else 2),
                "high": round(h, 4 if start_price < 10 else 2),
                "low": round(low_val, 4 if start_price < 10 else 2),
                "close": round(c, 4 if start_price < 10 else 2),
                "volume": v
            })
        return candles


    def _clean_symbol(self, symbol: str) -> str:
        return symbol.strip().upper().replace("/", "").replace("-", "").replace("=X", "")

    def _get_swissquote_pair(self, symbol: str) -> Optional[tuple]:
        sym = self._clean_symbol(symbol)
        if sym == "XAUUSD":
            return ("XAU", "USD")
        if len(sym) == 6:
            return (sym[:3], sym[3:])
        return None

    def _get_binance_symbol(self, symbol: str) -> str:
        sym = self._clean_symbol(symbol)
        if sym == "XAUUSD":
            return "PAXGUSDT"
        if sym == "EURUSD":
            return "EURUSDT"
        if sym == "GBPUSD":
            return "GBPUSDT"
        return f"{sym}USDT"

    def get_live_price_data(self, symbol: str, market: str) -> Optional[Dict[str, Any]]:
        sym_clean = self._clean_symbol(symbol)
        redis_key = f"market:live:{sym_clean}:{market.lower()}"
        
        cached_data = redis_cache.get(redis_key)
        if cached_data is not None:
            return cached_data

        pair = self._get_swissquote_pair(symbol)
        if not pair:
            # Try to get the last close price from historical daily candles
            fallback_price = 100.0
            try:
                candles = self.get_historical_candles(symbol, market, timeframe="1d", period="5d")
                if candles:
                    fallback_price = float(candles[-1]["close"])
            except Exception:
                # Hardcoded baseline base prices fallback
                base_prices = {
                    "NIFTY": 23480.0,
                    "BANKNIFTY": 49800.0,
                    "FINNIFTY": 22400.0,
                    "MIDCAP": 11500.0,
                    "SENSEX": 77000.0,
                    "RELIANCE": 2930.0,
                    "TCS": 3850.0,
                    "INFY": 1500.0,
                    "HDFCBANK": 1600.0,
                    "SBIN": 830.0,
                    "BTCUSD": 67250.0
                }
                fallback_price = base_prices.get(symbol.strip().upper(), 100.0)

            return {
                "bid": fallback_price,
                "ask": fallback_price,
                "mid": fallback_price,
                "spread": 0.0,
                "timestamp": datetime.now(pytz.utc).isoformat()
            }
            
        base, quote = pair
        url = f"https://forex-data-feed.swissquote.com/public-quotes/bboquotes/instrument/{base}/{quote}"
        
        for attempt in range(3):
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list) and len(data) > 0:
                        item = data[0]
                        prices = item.get("spreadProfilePrices", [])
                        if prices:
                            profile = prices[0]
                            bid = float(profile["bid"])
                            ask = float(profile["ask"])
                            mid = round((bid + ask) / 2, 5)
                            spread = round(ask - bid, 5)
                            ts = item.get("ts", int(time.time() * 1000))
                            
                            res = {
                                "bid": bid,
                                "ask": ask,
                                "mid": mid,
                                "spread": spread,
                                "timestamp": datetime.fromtimestamp(ts / 1000.0, tz=pytz.utc).isoformat()
                            }
                            redis_cache.set(redis_key, res, ex=self.cache_duration)
                            return res
                time.sleep(0.5)
            except Exception as e:
                print(f"Error fetching live price from Swissquote for {symbol}: {e}")
                time.sleep(0.5)
                
        # Try local fallback using historical last close if live query fails
        try:
            candles = self.get_historical_candles(symbol, market, "1d", "5d")
            if candles:
                last_c = candles[-1]["close"]
                return {
                    "bid": last_c,
                    "ask": last_c,
                    "mid": last_c,
                    "spread": 0.0,
                    "timestamp": datetime.now(pytz.utc).isoformat()
                }
        except Exception:
            pass

        return None

    def get_live_price(self, symbol: str, market: str) -> Optional[float]:
        data = self.get_live_price_data(symbol, market)
        if data:
            return data["mid"]
        return None

    def get_historical_candles(self, symbol: str, market: str, timeframe: str, period: str = "30d") -> List[Dict[str, Any]]:
        cleaned_sym = self._clean_symbol(symbol)
        redis_key = f"market:candles:{cleaned_sym}:{market.lower()}:{timeframe.lower()}:{period.lower()}"
        
        cached_data = redis_cache.get(redis_key)
        if cached_data is not None:
            return cached_data
                
        candles = self._fetch_historical_candles_raw(cleaned_sym, symbol, market, timeframe, period)
        
        if candles:
            redis_cache.set(redis_key, candles, ex=self.candles_cache_duration)
            
        return candles

    def _fetch_historical_candles_raw(self, cleaned_sym: str, symbol: str, market: str, timeframe: str, period: str) -> List[Dict[str, Any]]:
        # Route all Forex symbols to TradingView OANDA using tvDatafeed
        is_forex = (market.lower() == "forex" or cleaned_sym in ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD", "USDCAD", "USDCHF"])
        
        # Calculate limit/n_bars
        limit = 500
        if "d" in period:
            try:
                days = int(period.replace("d", ""))
                if timeframe == "1d":
                    limit = days
                elif timeframe in ["1h", "60m"]:
                    limit = days * 24
                elif timeframe == "4h":
                    limit = days * 6
                elif timeframe == "30m":
                    limit = days * 48
                elif timeframe == "15m":
                    limit = days * 96
                elif timeframe == "5m":
                    limit = days * 288
                elif timeframe == "1m":
                    limit = days * 1440
            except ValueError:
                pass
        
        limit = min(max(limit, 5), 1000)
        
        if is_forex:
            try:
                from tvDatafeed import TvDatafeed, Interval as FeedInterval
                
                # Setup mapping
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
                feed_interval = interval_map.get(timeframe.strip().lower(), FeedInterval.in_daily)
                
                if not self.tv:
                    self.tv = TvDatafeed()
                
                df = self.tv.get_hist(
                    symbol=cleaned_sym,
                    exchange="OANDA",
                    interval=feed_interval,
                    n_bars=limit
                )
                
                if df is not None and not df.empty:
                    candles = []
                    # Get system local timezone to properly localize naive timestamps from TradingView
                    local_tz = datetime.now().astimezone().tzinfo
                    for timestamp, row in df.iterrows():
                        dt_local = timestamp
                        if dt_local.tzinfo is None:
                            dt_local = dt_local.replace(tzinfo=local_tz)
                        dt_utc = dt_local.astimezone(pytz.utc)
                            
                        candles.append({
                            "time": dt_utc.isoformat(),
                            "open": float(row["open"]),
                            "high": float(row["high"]),
                            "low": float(row["low"]),
                            "close": float(row["close"]),
                            "volume": float(row["volume"]) if "volume" in row else 0.0
                        })
                    return candles
                else:
                    print(f"tvDatafeed returned empty DataFrame for Forex symbol {cleaned_sym}. Generating mock candles.")
            except Exception as e:
                print(f"Error fetching Forex {cleaned_sym} historical candles from tvDatafeed: {e}. Generating mock candles.")
            return self._generate_mock_candles(symbol, timeframe, limit)
            
        # Existing Binance Fallback (non-Forex)
        binance_sym = self._get_binance_symbol(symbol)
        
        interval = "1d"
        if timeframe in ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]:
            interval = timeframe
        elif timeframe == "60m":
            interval = "1h"
            
        url = "https://api.binance.com/api/v3/klines"
        params = {
            "symbol": binance_sym,
            "interval": interval,
            "limit": limit
        }
        
        for attempt in range(3):
            try:
                response = requests.get(url, params=params, timeout=8)
                if response.status_code == 200:
                    raw_data = response.json()
                    candles = []
                    for item in raw_data:
                        candles.append({
                            "time": datetime.fromtimestamp(item[0] / 1000.0, tz=pytz.utc).isoformat(),
                            "open": float(item[1]),
                            "high": float(item[2]),
                            "low": float(item[3]),
                            "close": float(item[4]),
                            "volume": float(item[5])
                        })
                    return candles
                time.sleep(0.5)
            except Exception as e:
                # Log a simple message instead of throwing full stacktrace
                if attempt == 2:
                    print(f"Connection error fetching candles from Binance for {symbol}: {e}. Generating mock candles.")
                time.sleep(0.5)
                
        return self._generate_mock_candles(symbol, timeframe, limit)

    def scan_symbol(self, symbol: str, market: str, timeframe: str) -> Dict[str, Any]:
        candles = self.get_historical_candles(symbol, market, timeframe, period="60d")
        if not candles or len(candles) < 20:
            return {
                "symbol": symbol,
                "market": market,
                "pattern": "None Detected",
                "timeframe": timeframe,
                "confidence_score": 0.0,
                "entry_price": None,
                "stop_loss": None,
                "target_price": None,
                "details": "Insufficient historical candle data to calculate metrics."
            }

        df = pd.DataFrame(candles)
        closes = df["close"].values
        highs = df["high"].values
        lows = df["low"].values
        
        calculate_emas(df, close_col="close", spans=(20, 50, 200))
        
        latest_close = float(closes[-1])
        latest_ema20 = float(df["EMA20"].iloc[-1])
        latest_ema50 = float(df["EMA50"].iloc[-1])
        latest_ema200 = float(df["EMA200"].iloc[-1])

        pattern = "None"
        confidence = 50.0
        entry = latest_close
        stop_loss = latest_close * 0.98
        target = latest_close * 1.04
        details = ""

        if latest_ema20 > latest_ema50 and df["EMA20"].iloc[-2] <= df["EMA50"].iloc[-2]:
            pattern = "EMA Bullish Crossover (20/50)"
            confidence = 75.0
            stop_loss = float(df["low"].iloc[-5:].min())
            target = latest_close + (latest_close - stop_loss) * 2
            details = "EMA 20 crossed above EMA 50 on the latest candles."
        elif latest_ema20 < latest_ema50 and df["EMA20"].iloc[-2] >= df["EMA50"].iloc[-2]:
            pattern = "EMA Bearish Crossover (20/50)"
            confidence = 72.0
            stop_loss = float(df["high"].iloc[-5:].max())
            target = latest_close - (stop_loss - latest_close) * 2
            details = "EMA 20 crossed below EMA 50 on the latest candles."

        prev_high = float(highs[-2])
        prev_low = float(lows[-2])
        prev_close = float(closes[-2])
        
        cpr = calculate_cpr(prev_high, prev_low, prev_close)
        pivot = cpr["pivot"]
        bc = cpr["bc"]
        tc = cpr["tc"]
        cpr_bottom = cpr["cpr_bottom"]
        cpr_top = cpr["cpr_top"]
        cpr_width_pct = cpr["width_pct"]
        
        if latest_close > cpr_top and closes[-2] <= cpr_top:
            pattern = "CPR Bullish Breakout"
            confidence = 80.0
            stop_loss = cpr_bottom
            target = latest_close * 1.05
            details = f"Candle closed above the CPR range (Width: {cpr_width_pct:.2f}%)."

        cam = calculate_camarilla(prev_high, prev_low, prev_close)
        h4 = cam["h4"]
        h3 = cam["h3"]
        l3 = cam["l3"]
        l4 = cam["l4"]
        
        if latest_close >= h4:
            pattern = "Camarilla H4 Breakout"
            confidence = 82.0
            stop_loss = h3
            target = h4 + (h4 - h3) * 1.5
            details = "Price broke out above Camarilla H4 level, indicating strong bullish momentum."
        elif latest_close <= l4:
            pattern = "Camarilla L4 Breakdown"
            confidence = 81.0
            stop_loss = l3
            target = l4 - (l3 - l4) * 1.5
            details = "Price broke down below Camarilla L4 level, indicating strong bearish momentum."

        for i in range(-5, -1):
            if i + len(closes) < 1:
                continue
            curr_c = closes[i]
            prev_c = closes[i-1]
            body_size = abs(curr_c - prev_c)
            if curr_c > prev_c and body_size > (closes.mean() * 0.015):
                ob_level = float(df["low"].iloc[i-1])
                if latest_close > ob_level and latest_close < ob_level * 1.01:
                    pattern = "SMC Bullish Order Block"
                    confidence = 85.0
                    entry = latest_close
                    stop_loss = ob_level * 0.99
                    target = latest_close * 1.06
                    details = "Price retraced back to a fresh demand/engulfing order block."
                    break

        return {
            "symbol": symbol,
            "market": market,
            "pattern": pattern,
            "timeframe": timeframe,
            "confidence_score": float(np.round(confidence, 1)),
            "entry_price": float(np.round(entry, 4)),
            "stop_loss": float(np.round(stop_loss, 4)),
            "target_price": float(np.round(target, 4)),
            "details": details or f"Standard chart reading. EMA20: {latest_ema20:.2f}, EMA50: {latest_ema50:.2f}, EMA200: {latest_ema200:.2f}."
        }


class AliceBlueService(MarketDataInterface):
    """
    Service for Alice Blue API integration.
    Automatically falls back to PublicMarketDataService if credentials are not configured
    or if the live market connection fails, ensuring robust development.
    """
    def __init__(self, username: str = None, api_key: str = None):
        self.username = username or os.getenv("ALICE_BLUE_USER")
        self.api_key = api_key or os.getenv("ALICE_BLUE_API_KEY")
        self.alice = None
        self.fallback = PublicMarketDataService()
        
        # Load from environment variables initially if present
        if self.username and self.api_key:
            try:
                from alice_blue import AliceBlue
                session_id = os.getenv("ALICE_BLUE_SESSION_ID")
                password = os.getenv("ALICE_BLUE_PASSWORD")
                twofa = os.getenv("ALICE_BLUE_TWOFA")
                api_secret = os.getenv("ALICE_BLUE_API_SECRET")
                
                if not session_id and password and twofa and api_secret:
                    session_id = AliceBlue.login_and_get_sessionID(
                        username=self.username,
                        password=password,
                        twoFA=str(twofa),
                        app_id=self.api_key,
                        api_secret=api_secret
                    )
                if session_id:
                    self.alice = AliceBlue(username=self.username, session_id=session_id)
                    print(f"Alice Blue Service initialized successfully for user {self.username}")
            except Exception as e:
                print(f"Error initializing Alice Blue connection from env: {e}. Using Yahoo Finance fallback.")
                self.alice = None

    def initialize(self, credentials: dict):
        if not credentials:
            return
            
        username = credentials.get("alice_blue_user")
        password = credentials.get("alice_blue_password")
        twoFA = credentials.get("alice_blue_twofa")
        api_key = credentials.get("alice_blue_api_key")
        api_secret = credentials.get("alice_blue_api_secret")
        session_id = credentials.get("session_id")
        
        if not username or not api_key:
            return
            
        try:
            from alice_blue import AliceBlue
            # If session_id is not already generated/cached, call login flow
            if not session_id and password and twoFA and api_secret:
                try:
                    session_id = AliceBlue.login_and_get_sessionID(
                        username=username,
                        password=password,
                        twoFA=str(twoFA),
                        app_id=api_key,
                        api_secret=api_secret
                    )
                    # Cache the session ID back in the preferences dictionary
                    credentials["session_id"] = session_id
                except Exception as e:
                    print(f"Error logging in and getting session ID: {e}")
                    
            if session_id:
                self.alice = AliceBlue(username=username, session_id=session_id)
                self.username = username
                self.api_key = api_key
                print(f"Alice Blue Service initialized dynamically successfully for user {username}")
        except Exception as e:
            print(f"Error dynamically initializing Alice Blue connection: {e}")
            self.alice = None

    def _get_exchange(self, market: str, symbol: str) -> str:
        """Resolve correct exchange for Alice Blue lookup."""
        market_lower = market.lower()
        if "option" in market_lower or "future" in market_lower:
            return "NFO"
        elif "mcx" in market_lower or "commodity" in market_lower:
            return "MCX"
        elif "bse" in market_lower:
            return "BSE"
        return "NSE"

    def get_live_price(self, symbol: str, market: str) -> Optional[float]:
        if not self.alice:
            return self.fallback.get_live_price(symbol, market)
            
        try:
            exchange = self._get_exchange(market, symbol)
            instrument = self.alice.get_instrument_by_symbol(exchange, symbol.upper())
            if not instrument:
                return self.fallback.get_live_price(symbol, market)
            # For live price, request standard quotes
            quote = self.alice.get_scrip_info(instrument)
            if quote and "LTP" in quote:
                return float(quote["LTP"])
            return self.fallback.get_live_price(symbol, market)
        except Exception as e:
            print(f"Alice Blue quote lookup failed for {symbol}: {e}. Falling back.")
            return self.fallback.get_live_price(symbol, market)

    def _resample_candles(self, candles: List[Dict[str, Any]], timeframe: str) -> List[Dict[str, Any]]:
        if not candles or timeframe in ["1m", "1d"]:
            return candles
            
        minutes_map = {
            "5m": 5,
            "15m": 15,
            "30m": 30,
            "60m": 60,
            "1h": 60
        }
        interval = minutes_map.get(timeframe)
        if not interval:
            return candles
            
        df = pd.DataFrame(candles)
        df["time_dt"] = pd.to_datetime(df["time"], utc=True)
        df.set_index("time_dt", inplace=True)
        
        # Resample logic
        rule = f"{interval}min"
        resampled = df.resample(rule).agg({
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum"
        }).dropna()
        
        resampled.reset_index(inplace=True)
        
        out = []
        for _, row in resampled.iterrows():
            out.append({
                "time": row["time_dt"].isoformat(),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": int(row["volume"])
            })
        return out

    def get_historical_candles(self, symbol: str, market: str, timeframe: str, period: str = "30d") -> List[Dict[str, Any]]:
        if not self.alice:
            return self.fallback.get_historical_candles(symbol, market, timeframe, period)
            
        try:
            exchange = self._get_exchange(market, symbol)
            instrument = self.alice.get_instrument_by_symbol(exchange, symbol.upper())
            if not instrument:
                return self.fallback.get_historical_candles(symbol, market, timeframe, period)
                
            from alice_blue import HistoricalDataType
            # Map timeframe ('1m', '5m', '15m', '1h', '1d') to Alice Blue HistoricalDataType
            if timeframe == "1d":
                hist_type = HistoricalDataType.Day
            else:
                hist_type = HistoricalDataType.Minute
                
            # Parse period to from/to dates
            to_date = datetime.now()
            days_count = 30
            if "d" in period:
                days_count = int(period.replace("d", ""))
            from_date = to_date - timedelta(days=days_count)
            
            # Fetch historical logs using proper historical_data call
            raw_candles = self.alice.historical_data(instrument, from_date, to_date, hist_type)
            
            # Check for API error response dict
            if isinstance(raw_candles, dict) and raw_candles.get("stat") == "Not_ok":
                print(f"Alice Blue history API returned error: {raw_candles.get('emsg')}. Falling back.")
                return self.fallback.get_historical_candles(symbol, market, timeframe, period)
                
            # If no data returned (Alice Blue does not serve history during market hours)
            if not raw_candles:
                print("No history from Alice Blue (market hours lock). Falling back to Yahoo Finance.")
                return self.fallback.get_historical_candles(symbol, market, timeframe, period)
                
            kolkata_tz = ZoneInfo("Asia/Kolkata")
            candles = []
            for candle in raw_candles:
                t = candle.get("datetime") or candle.get("time")
                if isinstance(t, datetime):
                    if t.tzinfo is None:
                        t = t.replace(tzinfo=kolkata_tz)
                    t_str = t.astimezone(timezone.utc).isoformat()
                elif isinstance(t, str):
                    try:
                        dt = datetime.fromisoformat(t)
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=kolkata_tz)
                        t_str = dt.astimezone(timezone.utc).isoformat()
                    except Exception:
                        t_str = t
                else:
                    t_str = str(t)

                candles.append({
                    "time": t_str,
                    "open": float(candle["open"]),
                    "high": float(candle["high"]),
                    "low": float(candle["low"]),
                    "close": float(candle["close"]),
                    "volume": int(candle.get("volume", 0))
                })
                
            # Resample intraday timeframes if needed (e.g. 5m, 15m, 1h)
            if timeframe not in ["1m", "1d"]:
                candles = self._resample_candles(candles, timeframe)
                
            return candles
        except Exception as e:
            print(f"Alice Blue history download failed for {symbol}: {e}. Falling back.")
            return self.fallback.get_historical_candles(symbol, market, timeframe, period)

    def scan_symbol(self, symbol: str, market: str, timeframe: str) -> Dict[str, Any]:
        # Reuse YahooFinance calculation logic by using fetched candles
        candles = self.get_historical_candles(symbol, market, timeframe, period="60d")
        if not candles or len(candles) < 20:
            return self.fallback.scan_symbol(symbol, market, timeframe)
            
        # Run calculation using retrieved candles
        return self.fallback.scan_symbol(symbol, market, timeframe)



class OandaService(MarketDataInterface):
    """
    Service for Oanda REST-V20 API integration.
    Automatically falls back to PublicMarketDataService if credentials are not configured
    or if Oanda queries fail.
    """
    def __init__(self, token: str = None, env: str = "practice"):
        self.token = token
        self.env = env.lower() if env else "practice"
        self.fallback = PublicMarketDataService()
        self._set_base_url()

    def _set_base_url(self):
        if self.env == "live":
            self.base_url = "https://api-fxtrade.oanda.com"
        else:
            self.base_url = "https://api-fxpractice.oanda.com"

    def initialize(self, credentials: dict):
        if not credentials:
            return
        preferred = credentials.get("preferred_feed", "public")
        token = credentials.get("oanda_token")
        env = credentials.get("oanda_env", "practice")
        if preferred == "oanda" and token:
            self.token = token
            self.env = env.lower()
            self._set_base_url()
            print(f"Oanda Service initialized dynamically successfully (env: {self.env})")
        else:
            self.token = None
            print("Oanda Service fallback to public feed (either public preferred or token missing)")

    def _clean_symbol(self, symbol: str) -> str:
        s = symbol.strip().upper().replace("/", "_").replace("-", "_").replace("=X", "")
        if "_" not in s:
            if len(s) == 6:
                return f"{s[:3]}_{s[3:]}"
        return s

    def get_live_price(self, symbol: str, market: str) -> Optional[float]:
        if not self.token:
            return self.fallback.get_live_price(symbol, market)
        try:
            cleaned = self._clean_symbol(symbol)
            url = f"{self.base_url}/v3/instruments/{cleaned}/candles"
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            params = {
                "count": 1,
                "price": "M"
            }
            import requests
            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                candles = data.get("candles", [])
                if candles:
                    mid = candles[-1].get("mid")
                    if mid:
                        return float(mid["c"])
            print(f"Oanda live price query failed for {symbol}: status {response.status_code}, response: {response.text}")
            return self.fallback.get_live_price(symbol, market)
        except Exception as e:
            print(f"Oanda live price lookup failed for {symbol}: {e}. Falling back.")
            return self.fallback.get_live_price(symbol, market)

    def get_historical_candles(self, symbol: str, market: str, timeframe: str, period: str = "5d") -> List[Dict[str, Any]]:
        if not self.token:
            return self.fallback.get_historical_candles(symbol, market, timeframe, period)
        try:
            cleaned = self._clean_symbol(symbol)
            granularity_map = {
                "1m": "M1",
                "5m": "M5",
                "15m": "M15",
                "30m": "M30",
                "60m": "H1",
                "1h": "H1",
                "1d": "D"
            }
            granularity = granularity_map.get(timeframe, "D")
            
            days = 30
            if period:
                try:
                    if "d" in period:
                        days = int(period.replace("d", ""))
                    elif "wk" in period:
                        days = int(period.replace("wk", "")) * 7
                    elif "mo" in period:
                        days = int(period.replace("mo", "")) * 30
                    elif "y" in period:
                        days = int(period.replace("y", "")) * 365
                except ValueError:
                    pass

            count = 500
            if timeframe == "1d":
                count = max(days, 30)
            elif timeframe in ["1h", "60m"]:
                count = min(days * 24, 2000)
            elif timeframe == "30m":
                count = min(days * 48, 2000)
            elif timeframe == "15m":
                count = min(days * 96, 2000)
            elif timeframe == "5m":
                count = min(days * 288, 2000)
            elif timeframe == "1m":
                count = min(days * 1440, 2000)

            url = f"{self.base_url}/v3/instruments/{cleaned}/candles"
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            params = {
                "granularity": granularity,
                "count": count,
                "price": "M"
            }
            import requests
            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.status_code != 200:
                print(f"Oanda history query failed for {symbol}: status {response.status_code}, response: {response.text}")
                return self.fallback.get_historical_candles(symbol, market, timeframe, period)
                
            data = response.json()
            raw_candles = data.get("candles", [])
            
            candles = []
            for c in raw_candles:
                if "mid" not in c:
                    continue
                mid = c["mid"]
                candles.append({
                    "time": c["time"],
                    "open": float(mid["o"]),
                    "high": float(mid["h"]),
                    "low": float(mid["l"]),
                    "close": float(mid["c"]),
                    "volume": int(c.get("volume", 0))
                })
            
            if not candles:
                return self.fallback.get_historical_candles(symbol, market, timeframe, period)
                
            return candles
        except Exception as e:
            print(f"Oanda history download failed for {symbol}: {e}. Falling back.")
            return self.fallback.get_historical_candles(symbol, market, timeframe, period)

    def scan_symbol(self, symbol: str, market: str, timeframe: str) -> Dict[str, Any]:
        # Reuse YahooFinance calculation logic by using fetched candles
        candles = self.get_historical_candles(symbol, market, timeframe, period="60d")
        if not candles or len(candles) < 20:
            return self.fallback.scan_symbol(symbol, market, timeframe)
            
        # Run calculation using retrieved candles
        return self.fallback.scan_symbol(symbol, market, timeframe)


class ShoonyaService(MarketDataInterface):
    """
    Placeholder service for Shoonya API integration.
    """
    def __init__(self, token: str = None, client_id: str = None):
        self.token = token
        self.client_id = client_id

    def get_live_price(self, symbol: str, market: str) -> Optional[float]:
        return None

    def get_historical_candles(self, symbol: str, market: str, timeframe: str, period: str = "5d") -> List[Dict[str, Any]]:
        return []

    def scan_symbol(self, symbol: str, market: str, timeframe: str) -> Dict[str, Any]:
        return {}
