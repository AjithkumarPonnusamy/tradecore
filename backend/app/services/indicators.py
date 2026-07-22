"""
Shared Technical Indicator Calculations.

All indicator math lives here. No side effects, no DB access.
Every consumer in the codebase should import from this module instead
of re-implementing the formulas inline.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any


# ---------------------------------------------------------------------------
# EMA
# ---------------------------------------------------------------------------

def calculate_ema(series: pd.Series, span: int) -> pd.Series:
    """Calculate Exponential Moving Average for a pandas Series."""
    return series.ewm(span=span, adjust=False).mean()


def calculate_emas(df: pd.DataFrame, close_col: str = "Close", spans: tuple = (20, 50, 200)) -> pd.DataFrame:
    """
    Add EMA columns to a DataFrame in-place and return it.
    Column names follow the pattern EMA{span}, e.g. EMA20, EMA50, EMA200.
    """
    for span in spans:
        df[f"EMA{span}"] = calculate_ema(df[close_col], span)
    return df


# ---------------------------------------------------------------------------
# RSI
# ---------------------------------------------------------------------------

def calculate_rsi(closes: np.ndarray, period: int = 14) -> float:
    """
    Compute 14-period (default) Wilder-smoothed RSI from a numpy array of
    closing prices.  Returns 50.0 as a neutral fallback when data is
    insufficient.
    """
    deltas = np.diff(closes)
    if len(deltas) < period:
        return 50.0

    seed = deltas[:period]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period

    for i in range(period, len(deltas)):
        d = deltas[i]
        upval = d if d > 0 else 0.0
        downval = -d if d < 0 else 0.0
        up = (up * (period - 1) + upval) / period
        down = (down * (period - 1) + downval) / period

    rs = up / down if down != 0 else np.inf
    return 100.0 - 100.0 / (1.0 + rs)


# ---------------------------------------------------------------------------
# CPR  (Central Pivot Range)
# ---------------------------------------------------------------------------

def calculate_cpr(high: float, low: float, close: float) -> Dict[str, Any]:
    """
    Calculate Central Pivot Range from the *previous* candle's high, low, close.

    Returns dict with keys:
        pivot, tc, bc, cpr_top, cpr_bottom, range, width_pct, range_type
    """
    pivot = (high + low + close) / 3
    bc = (high + low) / 2
    tc = (pivot - bc) + pivot

    cpr_top = max(bc, tc)
    cpr_bottom = min(bc, tc)
    cpr_range = abs(tc - bc)
    width_pct = (cpr_range / pivot) * 100 if pivot > 0 else 0.0

    if width_pct < 0.15:
        range_type = "Narrow"
    elif width_pct <= 0.5:
        range_type = "Medium"
    else:
        range_type = "Wide"

    return {
        "pivot": pivot,
        "tc": tc,
        "bc": bc,
        "cpr_top": cpr_top,
        "cpr_bottom": cpr_bottom,
        "range": cpr_range,
        "width_pct": width_pct,
        "range_type": range_type,
    }


# ---------------------------------------------------------------------------
# Standard (Classic Floor) Pivot Support / Resistance
# ---------------------------------------------------------------------------

def calculate_standard_pivots(pivot: float, high: float, low: float) -> Dict[str, float]:
    """
    Classic floor-trader support/resistance levels.

    Returns dict with keys: r1, r2, r5, s1, s2, s5
    """
    return {
        "r1": 2 * pivot - low,
        "s1": 2 * pivot - high,
        "r2": pivot + (high - low),
        "s2": pivot - (high - low),
        "r5": pivot + 4 * (high - low),
        "s5": pivot - 4 * (high - low),
    }


# ---------------------------------------------------------------------------
# Camarilla Levels
# ---------------------------------------------------------------------------

def calculate_camarilla(high: float, low: float, close: float) -> Dict[str, float]:
    """
    Full Camarilla pivot levels (h1–h5, l1–l5).

    Parameters are the *previous* candle's high, low, close.
    """
    c_range = high - low

    h1 = close + c_range * 1.1 / 12
    h2 = close + c_range * 1.1 / 6
    h3 = close + c_range * 1.1 / 4
    h4 = close + c_range * 1.1 / 2
    h5 = h4 + 1.168 * (h4 - h3)

    l1 = close - c_range * 1.1 / 12
    l2 = close - c_range * 1.1 / 6
    l3 = close - c_range * 1.1 / 4
    l4 = close - c_range * 1.1 / 2
    l5 = l4 - 1.168 * (l3 - l4)

    return {
        "h1": h1, "h2": h2, "h3": h3, "h4": h4, "h5": h5,
        "l1": l1, "l2": l2, "l3": l3, "l4": l4, "l5": l5,
    }


# ---------------------------------------------------------------------------
# VWAP (Typical-Price Proxy)
# ---------------------------------------------------------------------------

def calculate_vwap(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray,
                   volumes: np.ndarray) -> float:
    """
    Session VWAP proxy: cumulative typical-price × volume / cumulative volume.
    Falls back to the last close when total volume is zero.
    """
    typical_prices = (highs + lows + closes) / 3
    total_volume = np.sum(volumes)
    if total_volume > 0:
        return float(np.sum(typical_prices * volumes) / total_volume)
    return float(closes[-1])


# ---------------------------------------------------------------------------
# Candlestick Pattern Helpers
# ---------------------------------------------------------------------------

def detect_engulfing(latest_open: float, latest_close: float,
                     prev_open: float, prev_close: float) -> Dict[str, bool]:
    """
    Detect bullish and bearish engulfing candle patterns.

    Returns dict with keys: bullish, bearish
    """
    bullish = (
        latest_close > latest_open
        and prev_close < prev_open
        and latest_close >= prev_open
        and latest_open <= prev_close
    )
    bearish = (
        latest_close < latest_open
        and prev_close > prev_open
        and latest_close <= prev_open
        and latest_open >= prev_close
    )
    return {"bullish": bullish, "bearish": bearish}


# ---------------------------------------------------------------------------
# Convenience: rounded dict for API/WebSocket responses
# ---------------------------------------------------------------------------

def cpr_levels_rounded(cpr: Dict, std_pivots: Dict, precision: int = 4) -> Dict[str, Any]:
    """Build a rounded CPR + standard pivots dict ready for JSON serialisation."""
    return {
        "pivot": round(cpr["pivot"], precision),
        "tc": round(cpr["cpr_top"], precision),
        "bc": round(cpr["cpr_bottom"], precision),
        "range": round(cpr["range"], precision),
        "range_type": cpr["range_type"],
        "r1": round(std_pivots["r1"], precision),
        "r2": round(std_pivots["r2"], precision),
        "r5": round(std_pivots["r5"], precision),
        "s1": round(std_pivots["s1"], precision),
        "s2": round(std_pivots["s2"], precision),
        "s5": round(std_pivots["s5"], precision),
    }


def camarilla_levels_rounded(cam: Dict, precision: int = 4) -> Dict[str, float]:
    """Build a rounded Camarilla dict ready for JSON serialisation."""
    return {k: round(v, precision) for k, v in cam.items()}
