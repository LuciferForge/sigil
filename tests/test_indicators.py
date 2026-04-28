"""Indicator unit tests — verify against known-good values."""
import math
import pytest

from sigil import indicators
from sigil.core import OHLCV, OHLCVSeries


# ── SMA ──────────────────────────────────────────────────────────────


def test_sma_basic():
    closes = [1, 2, 3, 4, 5]
    out = indicators.sma(closes, 3)
    assert out == [None, None, 2.0, 3.0, 4.0]


def test_sma_short_input_returns_all_none():
    out = indicators.sma([1, 2], 5)
    assert out == [None, None]


def test_sma_period_one_returns_input():
    out = indicators.sma([1, 2, 3], 1)
    assert out == [1.0, 2.0, 3.0]


def test_sma_invalid_period():
    with pytest.raises(ValueError):
        indicators.sma([1, 2, 3], 0)


# ── EMA ──────────────────────────────────────────────────────────────


def test_ema_seed_is_sma():
    closes = [1, 2, 3, 4, 5]
    out = indicators.ema(closes, 3)
    # First three are None, None, SMA of [1,2,3] = 2.0
    assert out[0] is None
    assert out[1] is None
    assert out[2] == 2.0


def test_ema_constant_input_stays_constant():
    closes = [10.0] * 20
    out = indicators.ema(closes, 5)
    # After warm-up, EMA of constant series = constant
    assert all(abs(v - 10.0) < 1e-9 for v in out[4:])


# ── RSI ──────────────────────────────────────────────────────────────


def test_rsi_short_input_all_none():
    out = indicators.rsi([1, 2, 3], 14)
    assert all(v is None for v in out)


def test_rsi_all_increasing_is_high():
    closes = list(range(1, 31))  # 1, 2, ..., 30
    out = indicators.rsi(closes, 14)
    # No losses → RSI = 100
    assert out[14] == 100.0


def test_rsi_all_decreasing_is_low():
    closes = list(range(30, 0, -1))  # 30, 29, ..., 1
    out = indicators.rsi(closes, 14)
    # No gains → RSI = 0
    assert out[14] == 0.0


def test_rsi_in_range():
    """Mixed gains/losses → RSI between 0 and 100."""
    closes = [10, 11, 10, 11, 12, 11, 12, 13, 12, 13, 14, 13, 14, 15, 14, 15]
    out = indicators.rsi(closes, 14)
    val = out[14]
    assert val is not None
    assert 0 <= val <= 100


# ── MACD ─────────────────────────────────────────────────────────────


def test_macd_lengths_match_input():
    closes = [float(i) + math.sin(i / 5) * 0.5 for i in range(60)]
    out = indicators.macd(closes)
    assert len(out.macd) == 60
    assert len(out.signal) == 60
    assert len(out.histogram) == 60


def test_macd_invalid_periods():
    with pytest.raises(ValueError):
        indicators.macd([1, 2, 3], fast=20, slow=10)


# ── Bollinger Bands ─────────────────────────────────────────────────


def test_bollinger_constant_input_zero_band_width():
    closes = [10.0] * 30
    bb = indicators.bollinger_bands(closes, period=20, std_mult=2.0)
    # On constant input, std=0 → upper = middle = lower
    assert bb.upper[19] == bb.middle[19] == bb.lower[19] == 10.0


def test_bollinger_widens_with_volatility():
    """Volatile series should produce wider bands than calm series at same period."""
    calm = [10 + 0.01 * i for i in range(40)]
    volatile = [10 + (i % 3) * 5 for i in range(40)]
    bb_calm = indicators.bollinger_bands(calm, 20, 2.0)
    bb_vol = indicators.bollinger_bands(volatile, 20, 2.0)
    width_calm = bb_calm.upper[-1] - bb_calm.lower[-1]
    width_vol = bb_vol.upper[-1] - bb_vol.lower[-1]
    assert width_vol > width_calm


# ── ATR ──────────────────────────────────────────────────────────────


def _make_series(highs, lows, closes, opens=None):
    if opens is None:
        opens = closes
    return OHLCVSeries([
        OHLCV(timestamp=i * 60_000, open=opens[i], high=highs[i],
              low=lows[i], close=closes[i], volume=1.0)
        for i in range(len(closes))
    ])


def test_atr_constant_range():
    """If high-low is always 1, ATR converges to 1."""
    n = 40
    s = _make_series([10] * n, [9] * n, [9.5] * n)
    out = indicators.atr(s, 14)
    assert out[14] is not None
    assert abs(out[14] - 1.0) < 1e-9
    assert abs(out[-1] - 1.0) < 1e-9


def test_atr_short_returns_none():
    n = 5
    s = _make_series([10] * n, [9] * n, [9.5] * n)
    out = indicators.atr(s, 14)
    assert all(v is None for v in out)


# ── Supertrend ──────────────────────────────────────────────────────


def test_supertrend_uptrend_direction_positive():
    """A monotonically rising series should end in direction +1."""
    n = 60
    closes = [100 + i * 0.5 for i in range(n)]
    highs = [c + 0.5 for c in closes]
    lows = [c - 0.5 for c in closes]
    s = _make_series(highs, lows, closes)
    res = indicators.supertrend(s, 10, 3.0)
    assert res.direction[-1] == 1


def test_supertrend_downtrend_direction_negative():
    n = 60
    closes = [100 - i * 0.5 for i in range(n)]
    highs = [c + 0.5 for c in closes]
    lows = [c - 0.5 for c in closes]
    s = _make_series(highs, lows, closes)
    res = indicators.supertrend(s, 10, 3.0)
    assert res.direction[-1] == -1


# ── Stochastic ──────────────────────────────────────────────────────


def test_stochastic_at_top_of_range():
    """When close == period high, %K should be 100."""
    n = 20
    highs = [10 + i * 0.1 for i in range(n)]
    lows = [9.0 + i * 0.05 for i in range(n)]
    closes = list(highs)  # close at the high
    s = _make_series(highs, lows, closes)
    res = indicators.stochastic(s, 14, 3)
    assert abs(res.k[-1] - 100.0) < 1e-6


def test_stochastic_at_bottom_of_range():
    """When close equals period-low, %K should be 0."""
    n = 20
    # Constant range so the period-low equals the last-bar low
    highs = [11.0] * n
    lows = [9.0] * n
    closes = [9.0] * n  # close at bottom of range
    s = _make_series(highs, lows, closes)
    res = indicators.stochastic(s, 14, 3)
    assert abs(res.k[-1] - 0.0) < 1e-6


def test_stochastic_flat_range_midpoint():
    """If hh == ll, our convention returns 50."""
    n = 20
    s = _make_series([10] * n, [10] * n, [10] * n)
    res = indicators.stochastic(s, 14, 3)
    assert res.k[-1] == 50.0
