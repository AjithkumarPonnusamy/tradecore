"""
Unit tests for the shared indicators module.

Verifies all indicator calculations produce known-good results
with deterministic inputs.
"""

import numpy as np
import pandas as pd
import pytest

from app.services.indicators import (
    calculate_ema,
    calculate_emas,
    calculate_rsi,
    calculate_cpr,
    calculate_standard_pivots,
    calculate_camarilla,
    calculate_vwap,
    detect_engulfing,
    cpr_levels_rounded,
    camarilla_levels_rounded,
)


# ── EMA ───────────────────────────────────────────────────────────────────

class TestEMA:
    def test_ema_length_matches_input(self):
        s = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        result = calculate_ema(s, span=3)
        assert len(result) == len(s)

    def test_ema_first_value_equals_first_input(self):
        s = pd.Series([10.0, 20.0, 30.0])
        result = calculate_ema(s, span=3)
        assert result.iloc[0] == 10.0  # EMA starts at first value when adjust=False

    def test_calculate_emas_adds_columns(self):
        df = pd.DataFrame({"Close": [1.0, 2.0, 3.0, 4.0, 5.0]})
        calculate_emas(df, close_col="Close", spans=(3, 5))
        assert "EMA3" in df.columns
        assert "EMA5" in df.columns


# ── RSI ───────────────────────────────────────────────────────────────────

class TestRSI:
    def test_rsi_all_gains(self):
        closes = np.array([float(i) for i in range(1, 30)])  # monotonically increasing
        rsi = calculate_rsi(closes)
        assert rsi == 100.0  # all gains → RSI = 100

    def test_rsi_all_losses(self):
        closes = np.array([float(i) for i in range(30, 1, -1)])  # monotonically decreasing
        rsi = calculate_rsi(closes)
        assert rsi == 0.0  # all losses → RSI = 0

    def test_rsi_insufficient_data(self):
        closes = np.array([1.0, 2.0, 3.0])
        rsi = calculate_rsi(closes)
        assert rsi == 50.0  # fallback

    def test_rsi_mid_range(self):
        np.random.seed(42)
        closes = np.cumsum(np.random.randn(100)) + 100
        rsi = calculate_rsi(closes)
        assert 0.0 <= rsi <= 100.0


# ── CPR ───────────────────────────────────────────────────────────────────

class TestCPR:
    def test_cpr_basic_calculation(self):
        high, low, close = 110.0, 90.0, 100.0
        cpr = calculate_cpr(high, low, close)

        expected_pivot = (110 + 90 + 100) / 3  # 100.0
        expected_bc = (110 + 90) / 2  # 100.0
        expected_tc = (expected_pivot - expected_bc) + expected_pivot  # 100.0

        assert cpr["pivot"] == pytest.approx(expected_pivot)
        assert cpr["bc"] == pytest.approx(expected_bc)
        assert cpr["tc"] == pytest.approx(expected_tc)
        assert cpr["cpr_top"] >= cpr["cpr_bottom"]

    def test_cpr_range_type_narrow(self):
        # Construct values that give a very narrow CPR (< 0.15% width)
        high, low, close = 100.1, 99.9, 100.0
        cpr = calculate_cpr(high, low, close)
        assert cpr["range_type"] == "Narrow"

    def test_cpr_range_type_wide(self):
        # Asymmetric values produce a wide CPR (close far from midpoint of H-L)
        high, low, close = 110.0, 90.0, 108.0
        cpr = calculate_cpr(high, low, close)
        # pivot = (110+90+108)/3 = 102.667, bc = 100, tc = 105.333
        # width_pct ≈ 5.333 / 102.667 * 100 ≈ 5.19% → Wide
        assert cpr["range_type"] == "Wide"


# ── Standard Pivots ──────────────────────────────────────────────────────

class TestStandardPivots:
    def test_standard_pivots_symmetry(self):
        pivot, high, low = 100.0, 110.0, 90.0
        sp = calculate_standard_pivots(pivot, high, low)

        # r1 = 2*100 - 90 = 110, s1 = 2*100 - 110 = 90
        assert sp["r1"] == pytest.approx(110.0)
        assert sp["s1"] == pytest.approx(90.0)

        # r2 = 100 + 20 = 120, s2 = 100 - 20 = 80
        assert sp["r2"] == pytest.approx(120.0)
        assert sp["s2"] == pytest.approx(80.0)


# ── Camarilla ────────────────────────────────────────────────────────────

class TestCamarilla:
    def test_camarilla_has_all_levels(self):
        cam = calculate_camarilla(110.0, 90.0, 100.0)
        expected_keys = {"h1", "h2", "h3", "h4", "h5", "l1", "l2", "l3", "l4", "l5"}
        assert set(cam.keys()) == expected_keys

    def test_camarilla_ordering(self):
        cam = calculate_camarilla(110.0, 90.0, 100.0)
        # h levels should be ascending: h1 < h2 < h3 < h4 < h5
        assert cam["h1"] < cam["h2"] < cam["h3"] < cam["h4"] < cam["h5"]
        # l levels should be descending: l1 > l2 > l3 > l4 > l5
        assert cam["l1"] > cam["l2"] > cam["l3"] > cam["l4"] > cam["l5"]

    def test_camarilla_h3_formula(self):
        high, low, close = 110.0, 90.0, 100.0
        cam = calculate_camarilla(high, low, close)
        c_range = high - low
        expected_h3 = close + c_range * 1.1 / 4
        assert cam["h3"] == pytest.approx(expected_h3)


# ── VWAP ─────────────────────────────────────────────────────────────────

class TestVWAP:
    def test_vwap_uniform_volume(self):
        highs = np.array([12.0, 14.0, 16.0])
        lows = np.array([8.0, 10.0, 12.0])
        closes = np.array([10.0, 12.0, 14.0])
        volumes = np.array([100.0, 100.0, 100.0])

        vwap = calculate_vwap(highs, lows, closes, volumes)
        # Typical prices: 10, 12, 14 → mean = 12
        assert vwap == pytest.approx(12.0)

    def test_vwap_zero_volume_fallback(self):
        highs = np.array([12.0])
        lows = np.array([8.0])
        closes = np.array([10.0])
        volumes = np.array([0.0])

        vwap = calculate_vwap(highs, lows, closes, volumes)
        assert vwap == pytest.approx(10.0)  # fallback to last close


# ── Engulfing ────────────────────────────────────────────────────────────

class TestEngulfing:
    def test_bullish_engulfing(self):
        # prev: bearish candle (open=12, close=10), curr: bullish candle (open=9, close=13)
        result = detect_engulfing(
            latest_open=9.0, latest_close=13.0,
            prev_open=12.0, prev_close=10.0
        )
        assert result["bullish"] is True
        assert result["bearish"] is False

    def test_bearish_engulfing(self):
        # prev: bullish candle (open=10, close=12), curr: bearish candle (open=13, close=9)
        result = detect_engulfing(
            latest_open=13.0, latest_close=9.0,
            prev_open=10.0, prev_close=12.0
        )
        assert result["bullish"] is False
        assert result["bearish"] is True

    def test_no_engulfing(self):
        result = detect_engulfing(
            latest_open=10.0, latest_close=11.0,
            prev_open=10.0, prev_close=11.0
        )
        assert result["bullish"] is False
        assert result["bearish"] is False


# ── Convenience Rounders ─────────────────────────────────────────────────

class TestRoundingHelpers:
    def test_cpr_levels_rounded_keys(self):
        cpr = calculate_cpr(110.0, 90.0, 100.0)
        std = calculate_standard_pivots(cpr["pivot"], 110.0, 90.0)
        rounded = cpr_levels_rounded(cpr, std)
        expected_keys = {"pivot", "tc", "bc", "range", "range_type", "r1", "r2", "r5", "s1", "s2", "s5"}
        assert set(rounded.keys()) == expected_keys

    def test_camarilla_levels_rounded_precision(self):
        cam = calculate_camarilla(110.0, 90.0, 100.0)
        rounded = camarilla_levels_rounded(cam, precision=2)
        for v in rounded.values():
            # Check that it's rounded to 2 decimal places
            assert v == round(v, 2)
