import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.services.market_data import PublicMarketDataService
from app.services.indicators import (
    calculate_emas, calculate_cpr, calculate_camarilla,
    calculate_rsi, calculate_vwap, detect_engulfing,
)

class ScannerEngine:
    def __init__(self):
        self.public_service = PublicMarketDataService()

    def run_scans_for_symbol(self, symbol: str, market: str, enabled_scanners: List[str]) -> List[Dict[str, Any]]:
        candles = self.public_service.get_historical_candles(symbol, market, timeframe="1d", period="60d")
        if not candles or len(candles) < 20:
            return []
            
        df = pd.DataFrame(candles)
        df.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"}, inplace=True)
            
        closes = df["Close"].values
        highs = df["High"].values
        lows = df["Low"].values
        opens = df["Open"].values
        volumes = df["Volume"].values if "Volume" in df.columns else np.zeros(len(df))
        
        # Calculate EMA Indicators
        calculate_emas(df, close_col="Close", spans=(20, 50, 200))
        
        latest_open = float(opens[-1])
        latest_high = float(highs[-1])
        latest_low = float(lows[-1])
        latest_close = float(closes[-1])
        latest_volume = float(volumes[-1])
        
        prev_high = float(highs[-2])
        prev_low = float(lows[-2])
        prev_close = float(closes[-2])
        
        # CPR Calculations
        cpr = calculate_cpr(prev_high, prev_low, prev_close)
        pivot = cpr["pivot"]
        tc = cpr["tc"]
        bc = cpr["bc"]
        cpr_top = cpr["cpr_top"]
        cpr_bottom = cpr["cpr_bottom"]
        cpr_width_pct = cpr["width_pct"]
        cpr_range_type = cpr["range_type"]
        
        # CPR Bias Analysis
        if cpr_range_type == "Narrow":
            cpr_bias = "Trending"
        elif cpr_range_type == "Wide":
            cpr_bias = "Sideways/Rangebound"
        else:
            cpr_bias = "Neutral"
            
        cpr_top_label = "TC" if tc > bc else "BC"
        cpr_bottom_label = "BC" if bc < tc else "TC"
        
        # Camarilla Calculations
        cam = calculate_camarilla(prev_high, prev_low, prev_close)
        r3 = cam["h3"]
        r4 = cam["h4"]
        s3 = cam["l3"]
        s4 = cam["l4"]
        
        # Helper to describe Camarilla level relative to CPR
        def get_camarilla_relation(level_val):
            if level_val > cpr_top:
                return "above CPR"
            elif level_val < cpr_bottom:
                return "below CPR"
            else:
                return "inside CPR"
                
        def get_alignment_str(scanner_type, bias):
            if bias == "Trending" and scanner_type == "Breakout":
                return "aligns with Trending CPR bias"
            elif bias == "Sideways/Rangebound" and scanner_type == "Bounce":
                return "aligns with Sideways/Rangebound CPR bias"
            elif bias == "Neutral":
                return "neutral alignment with CPR bias"
            else:
                return f"runs counter to current {bias} CPR bias"
        
        # Average volume over last 20 candles (excluding today)
        avg_volume = float(volumes[-21:-1].mean()) if len(volumes) >= 21 else 1.0
        
        triggered_signals = []

        # ==========================================
        # FOREX & GENERIC SCANNERS
        # ==========================================
        
        # 1. CPR Breakout
        if "CPR Breakout" in enabled_scanners:
            if latest_close > cpr_top and closes[-2] <= cpr_top:
                reason = (
                    f"Close {latest_close:.4f} broke out above CPR Top ({cpr_top_label}: {cpr_top:.4f}). "
                    f"CPR is {cpr_range_type} ({cpr_width_pct:.3f}% width, Bias: {cpr_bias})."
                )
                triggered_signals.append({
                    "scanner_name": "CPR Breakout",
                    "signal_type": "BULLISH",
                    "price": latest_close,
                    "confidence_score": 82.0,
                    "details": {"reason": reason}
                })
            elif latest_close < cpr_bottom and closes[-2] >= cpr_bottom:
                reason = (
                    f"Close {latest_close:.4f} broke down below CPR Bottom ({cpr_bottom_label}: {cpr_bottom:.4f}). "
                    f"CPR is {cpr_range_type} ({cpr_width_pct:.3f}% width, Bias: {cpr_bias})."
                )
                triggered_signals.append({
                    "scanner_name": "CPR Breakout",
                    "signal_type": "BEARISH",
                    "price": latest_close,
                    "confidence_score": 80.0,
                    "details": {"reason": reason}
                })

        # 2. CPR Reversal
        if "CPR Reversal" in enabled_scanners:
            # Rejection from TC/BC with a pin bar style logic
            is_bullish_rejection = latest_low <= cpr_top and latest_close > cpr_top and latest_close > latest_open
            is_bearish_rejection = latest_high >= cpr_bottom and latest_close < cpr_bottom and latest_close < latest_open
            if is_bullish_rejection:
                diffs_low = {"TC": abs(latest_low - tc), "BC": abs(latest_low - bc), "Pivot": abs(latest_low - pivot)}
                tested_level = min(diffs_low, key=diffs_low.get)
                reason = (
                    f"Price rejected CPR Top ({cpr_top_label}: {cpr_top:.4f}) with low {latest_low:.4f} and closed above it. "
                    f"Test occurred closest to {tested_level} level. CPR is {cpr_range_type} ({cpr_width_pct:.3f}% width, Bias: {cpr_bias})."
                )
                triggered_signals.append({
                    "scanner_name": "CPR Reversal",
                    "signal_type": "BULLISH",
                    "price": latest_close,
                    "confidence_score": 75.0,
                    "details": {"reason": reason}
                })
            elif is_bearish_rejection:
                diffs_high = {"TC": abs(latest_high - tc), "BC": abs(latest_high - bc), "Pivot": abs(latest_high - pivot)}
                tested_level = min(diffs_high, key=diffs_high.get)
                reason = (
                    f"Price rejected CPR Bottom ({cpr_bottom_label}: {cpr_bottom:.4f}) with high {latest_high:.4f} and closed below it. "
                    f"Test occurred closest to {tested_level} level. CPR is {cpr_range_type} ({cpr_width_pct:.3f}% width, Bias: {cpr_bias})."
                )
                triggered_signals.append({
                    "scanner_name": "CPR Reversal",
                    "signal_type": "BEARISH",
                    "price": latest_close,
                    "confidence_score": 75.0,
                    "details": {"reason": reason}
                })

        # 3. Camarilla Bounce
        if "Camarilla Bounce" in enabled_scanners:
            if latest_low <= s3 and latest_close > s3:
                relation = get_camarilla_relation(s3)
                alignment = get_alignment_str("Bounce", cpr_bias)
                reason = (
                    f"Price bounced off Camarilla Support S3 ({s3:.4f}) which is {relation} (CPR TC: {tc:.4f}, BC: {bc:.4f}, Pivot: {pivot:.4f}). "
                    f"CPR is {cpr_range_type} ({alignment})."
                )
                triggered_signals.append({
                    "scanner_name": "Camarilla Bounce",
                    "signal_type": "BULLISH",
                    "price": latest_close,
                    "confidence_score": 78.0,
                    "details": {"reason": reason}
                })
            elif latest_high >= r3 and latest_close < r3:
                relation = get_camarilla_relation(r3)
                alignment = get_alignment_str("Bounce", cpr_bias)
                reason = (
                    f"Price rejected Camarilla Resistance R3 ({r3:.4f}) which is {relation} (CPR TC: {tc:.4f}, BC: {bc:.4f}, Pivot: {pivot:.4f}). "
                    f"CPR is {cpr_range_type} ({alignment})."
                )
                triggered_signals.append({
                    "scanner_name": "Camarilla Bounce",
                    "signal_type": "BEARISH",
                    "price": latest_close,
                    "confidence_score": 78.0,
                    "details": {"reason": reason}
                })

        # 4. Camarilla Breakout
        if "Camarilla Breakout" in enabled_scanners:
            if latest_close > r4 and closes[-2] <= r4:
                relation = get_camarilla_relation(r4)
                alignment = get_alignment_str("Breakout", cpr_bias)
                reason = (
                    f"Price broke out above Camarilla Resistance R4 ({r4:.4f}) which is {relation} (CPR TC: {tc:.4f}, BC: {bc:.4f}, Pivot: {pivot:.4f}). "
                    f"CPR is {cpr_range_type} ({alignment})."
                )
                triggered_signals.append({
                    "scanner_name": "Camarilla Breakout",
                    "signal_type": "BULLISH",
                    "price": latest_close,
                    "confidence_score": 85.0,
                    "details": {"reason": reason}
                })
            elif latest_close < s4 and closes[-2] >= s4:
                relation = get_camarilla_relation(s4)
                alignment = get_alignment_str("Breakout", cpr_bias)
                reason = (
                    f"Price broke down below Camarilla Support S4 ({s4:.4f}) which is {relation} (CPR TC: {tc:.4f}, BC: {bc:.4f}, Pivot: {pivot:.4f}). "
                    f"CPR is {cpr_range_type} ({alignment})."
                )
                triggered_signals.append({
                    "scanner_name": "Camarilla Breakout",
                    "signal_type": "BEARISH",
                    "price": latest_close,
                    "confidence_score": 85.0,
                    "details": {"reason": reason}
                })

        # 5. EMA Trend
        if "EMA Trend" in enabled_scanners:
            ema20 = float(df["EMA20"].iloc[-1])
            ema50 = float(df["EMA50"].iloc[-1])
            ema200 = float(df["EMA200"].iloc[-1])
            if latest_close > ema20 > ema50 > ema200:
                triggered_signals.append({
                    "scanner_name": "EMA Trend",
                    "signal_type": "BULLISH",
                    "price": latest_close,
                    "confidence_score": 80.0,
                    "details": {"reason": f"Strong bullish trend: Price > EMA20 > EMA50 > EMA200."}
                })
            elif latest_close < ema20 < ema50 < ema200:
                triggered_signals.append({
                    "scanner_name": "EMA Trend",
                    "signal_type": "BEARISH",
                    "price": latest_close,
                    "confidence_score": 80.0,
                    "details": {"reason": f"Strong bearish trend: Price < EMA20 < EMA50 < EMA200."}
                })

        # 6. Fibonacci Confluence
        if "Fibonacci Confluence" in enabled_scanners:
            # Find recent swing high/low in the last 20 candles
            recent_high = float(highs[-20:].max())
            recent_low = float(lows[-20:].min())
            fib_range = recent_high - recent_low
            fib_50 = recent_low + fib_range * 0.5
            fib_618 = recent_low + fib_range * 0.618
            
            # Check if close is near 50% or 61.8% retracement level (within 0.3%)
            if abs(latest_close - fib_618) / latest_close < 0.003:
                triggered_signals.append({
                    "scanner_name": "Fibonacci Confluence",
                    "signal_type": "BULLISH",
                    "price": latest_close,
                    "confidence_score": 76.0,
                    "details": {"reason": f"Price retraced near the Golden 61.8% Fibonacci zone {fib_618:.4f}."}
                })
            elif abs(latest_close - fib_50) / latest_close < 0.003:
                triggered_signals.append({
                    "scanner_name": "Fibonacci Confluence",
                    "signal_type": "BULLISH",
                    "price": latest_close,
                    "confidence_score": 70.0,
                    "details": {"reason": f"Price retraced near the 50.0% Fibonacci zone {fib_50:.4f}."}
                })

        # ==========================================
        # INDIAN MARKET SPECIFIC SCANNERS
        # ==========================================
        
        # 1. Gap Up
        if "Gap Up" in enabled_scanners:
            if latest_open > prev_high:
                triggered_signals.append({
                    "scanner_name": "Gap Up",
                    "signal_type": "BULLISH",
                    "price": latest_close,
                    "confidence_score": 75.0,
                    "details": {"reason": f"Asset opened with a Gap Up at {latest_open:.2f} above previous day's high {prev_high:.2f}."}
                })

        # 2. Gap Down
        if "Gap Down" in enabled_scanners:
            if latest_open < prev_low:
                triggered_signals.append({
                    "scanner_name": "Gap Down",
                    "signal_type": "BEARISH",
                    "price": latest_close,
                    "confidence_score": 75.0,
                    "details": {"reason": f"Asset opened with a Gap Down at {latest_open:.2f} below previous day's low {prev_low:.2f}."}
                })

        # 3. EMA Setup
        if "EMA Setup" in enabled_scanners:
            ema20_curr = float(df["EMA20"].iloc[-1])
            ema20_prev = float(df["EMA20"].iloc[-2])
            ema50_curr = float(df["EMA50"].iloc[-1])
            ema50_prev = float(df["EMA50"].iloc[-2])
            
            # Crossover check
            if ema20_curr > ema50_curr and ema20_prev <= ema50_prev:
                triggered_signals.append({
                    "scanner_name": "EMA Setup",
                    "signal_type": "BULLISH",
                    "price": latest_close,
                    "confidence_score": 81.0,
                    "details": {"reason": "EMA 20 crossed above EMA 50 (Golden Cross setup)."}
                })
            elif ema20_curr < ema50_curr and ema20_prev >= ema50_prev:
                triggered_signals.append({
                    "scanner_name": "EMA Setup",
                    "signal_type": "BEARISH",
                    "price": latest_close,
                    "confidence_score": 81.0,
                    "details": {"reason": "EMA 20 crossed below EMA 50 (Death Cross setup)."}
                })

        # 4. Volume Breakout
        if "Volume Breakout" in enabled_scanners:
            if latest_volume > 2.0 * avg_volume and latest_volume > 50000: # Ensure minimum activity
                sig_type = "BULLISH" if latest_close > latest_open else "BEARISH"
                triggered_signals.append({
                    "scanner_name": "Volume Breakout",
                    "signal_type": sig_type,
                    "price": latest_close,
                    "confidence_score": 83.0,
                    "details": {"reason": f"Extreme volume spike: {latest_volume:,.0f} is {(latest_volume/avg_volume):.1f}x the 20-day average volume."}
                })

        # 5. Momentum Stocks
        if "Momentum Stocks" in enabled_scanners:
            # 5-day Rate of Change (ROC)
            roc_5 = ((latest_close - closes[-5]) / closes[-5]) * 100 if len(closes) >= 5 else 0.0
            if roc_5 > 5.0: # 5% gain in 5 days
                triggered_signals.append({
                    "scanner_name": "Momentum Stocks",
                    "signal_type": "BULLISH",
                    "price": latest_close,
                    "confidence_score": 79.0,
                    "details": {"reason": f"Strong bullish momentum: 5-day Rate of Change is {roc_5:.1f}%."}
                })
            elif roc_5 < -5.0:
                triggered_signals.append({
                    "scanner_name": "Momentum Stocks",
                    "signal_type": "BEARISH",
                    "confidence_score": 79.0,
                    "details": {"reason": f"Strong bearish momentum: 5-day Rate of Change is {roc_5:.1f}%."}
                })

        latest_candle_time = candles[-1]["time"]
        for sig in triggered_signals:
            sig["trigger_time"] = latest_candle_time

        return triggered_signals

    def evaluate_custom_condition(self, symbol: str, market: str, conditions_tree: Any) -> Dict[str, Any]:
        """
        Evaluates a nested structure of logical conditions (AND, OR, NOT)
        for a given symbol.
        """
        
        # Clean symbol and market
        symbol_upper = symbol.strip().upper()
        
        # Fetch candles
        candles = self.public_service.get_historical_candles(symbol_upper, market, timeframe="1d", period="60d")
        if not candles or len(candles) < 20:
            return {"matched": False, "reason": "Insufficient market data (need at least 20 daily candles)", "price": 0.0}

        df = pd.DataFrame(candles)
        df.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"}, inplace=True)
            
        closes = df["Close"].values
        highs = df["High"].values
        lows = df["Low"].values
        opens = df["Open"].values
        volumes = df["Volume"].values if "Volume" in df.columns else np.zeros(len(df))
        
        latest_close = float(closes[-1])
        latest_open = float(opens[-1])
        latest_high = float(highs[-1])
        latest_low = float(lows[-1])
        latest_volume = float(volumes[-1])
        
        prev_close = float(closes[-2])
        prev_open = float(opens[-2])
        prev_high = float(highs[-2])
        prev_low = float(lows[-2])

        # Technical Indicators calculations (using shared module):
        
        # 1. EMA
        calculate_emas(df, close_col="Close", spans=(20, 50))
        ema20 = float(df["EMA20"].iloc[-1])
        ema50 = float(df["EMA50"].iloc[-1])
        
        # 2. RSI
        rsi = calculate_rsi(closes)

        # 3. CPR
        cpr = calculate_cpr(prev_high, prev_low, prev_close)
        pivot = cpr["pivot"]
        tc = cpr["tc"]
        bc = cpr["bc"]
        cpr_top = cpr["cpr_top"]
        cpr_bottom = cpr["cpr_bottom"]

        # 4. VWAP Proxy
        vwap = calculate_vwap(highs, lows, closes, volumes)

        # 5. Bullish/Bearish Engulfing
        engulf = detect_engulfing(latest_open, latest_close, prev_open, prev_close)
        bullish_engulfing = engulf["bullish"]
        bearish_engulfing = engulf["bearish"]

        def eval_node(node: Any) -> tuple:
            # Evaluates a single node. Can be operator node or leaf node.
            # Returns (matched_bool, description_str)
            if not isinstance(node, dict):
                return False, "Invalid rule node"
                
            if "operator" in node and node["operator"].upper() in ["AND", "OR", "NOT"]:
                op = node["operator"].upper()
                rules = node.get("rules", [])
                
                if op == "NOT":
                    if not rules:
                        return True, "NOT (Empty)"
                    matched, desc = eval_node(rules[0])
                    return not matched, f"NOT ({desc})"
                
                results = [eval_node(r) for r in rules]
                if not results:
                    return True, "Empty"
                
                matches = [r[0] for r in results]
                descs = [r[1] for r in results]
                
                if op == "AND":
                    matched = all(matches)
                    desc = " AND ".join(descs)
                    if len(rules) > 1:
                        desc = f"({desc})"
                    return matched, desc
                elif op == "OR":
                    matched = any(matches)
                    desc = " OR ".join(descs)
                    if len(rules) > 1:
                        desc = f"({desc})"
                    return matched, desc
                else:
                    return False, f"Unknown operator {op}"
            
            # Leaf node
            field = node.get("field", "")
            operator = node.get("operator", "")
            value = node.get("value")
            
            # Match condition
            if field == "RSI":
                try:
                    val_float = float(value)
                    if operator == ">":
                        return rsi > val_float, f"RSI({rsi:.1f}) > {val_float}"
                    elif operator == "<":
                        return rsi < val_float, f"RSI({rsi:.1f}) < {val_float}"
                    elif operator == ">=":
                        return rsi >= val_float, f"RSI({rsi:.1f}) >= {val_float}"
                    elif operator == "<=":
                        return rsi <= val_float, f"RSI({rsi:.1f}) <= {val_float}"
                except:
                    pass
                return False, f"Invalid RSI condition"
                
            elif field == "Price Above CPR" or field == "Price Above CPR":
                return latest_close > cpr_top, f"Price({latest_close:.4f}) Above CPR Top({cpr_top:.4f})"
                
            elif field == "Price Below CPR":
                return latest_close < cpr_bottom, f"Price({latest_close:.4f}) Below CPR Bottom({cpr_bottom:.4f})"
                
            elif field == "Close Above Pivot":
                return latest_close > pivot, f"Close({latest_close:.4f}) Above Pivot({pivot:.4f})"
                
            elif field == "Close Below Pivot":
                return latest_close < pivot, f"Close({latest_close:.4f}) Below Pivot({pivot:.4f})"
                
            elif field == "Bullish Engulfing":
                return bullish_engulfing, f"Bullish Engulfing is {bullish_engulfing}"
                
            elif field == "Bearish Engulfing":
                return bearish_engulfing, f"Bearish Engulfing is {bearish_engulfing}"
                
            elif field == "Price Above VWAP":
                return latest_close > vwap, f"Price({latest_close:.4f}) Above VWAP({vwap:.4f})"
                
            elif field == "Price Below VWAP":
                return latest_close < vwap, f"Price({latest_close:.4f}) Below VWAP({vwap:.4f})"
                
            elif field == "EMA20 > EMA50":
                return ema20 > ema50, f"EMA20({ema20:.4f}) > EMA50({ema50:.4f})"
                
            elif field == "EMA20 < EMA50":
                return ema20 < ema50, f"EMA20({ema20:.4f}) < EMA50({ema50:.4f})"
                
            elif field == "Volume > Previous Candle":
                return latest_volume > volumes[-2], f"Volume({latest_volume:,.0f}) > Prev Volume({volumes[-2]:,.0f})"
                
            return False, f"Unknown field {field}"

        # Normalize: if conditions_tree is a list, treat it as AND of all conditions
        if isinstance(conditions_tree, list):
            conditions_tree = {"operator": "AND", "rules": conditions_tree}
            
        matched, reason = eval_node(conditions_tree)
        return {
            "matched": matched,
            "reason": reason,
            "price": latest_close,
            "time": candles[-1]["time"],
            "rsi": rsi,
            "ema20": ema20,
            "ema50": ema50,
            "cpr": {"pivot": pivot, "tc": tc, "bc": bc},
            "vwap": vwap
        }
