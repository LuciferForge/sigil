"""MomentumComposite — trend-strength signal on [-1, +1].

Components (equal-weighted):
  1. RSI - 50, scaled to [-1, +1]
  2. MACD histogram, normalized by recent volatility
  3. Supertrend direction (-1 / +1)
"""
from __future__ import annotations

from typing import Sequence

from sigil.core import to_series
from sigil.indicators.rsi import rsi
from sigil.indicators.macd import macd
from sigil.indicators.supertrend import supertrend


def _clip(x: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def momentum_composite(
    series,
    *,
    rsi_period: int = 14,
    macd_fast: int = 12,
    macd_slow: int = 26,
    macd_signal: int = 9,
    supertrend_period: int = 10,
    supertrend_mult: float = 3.0,
) -> list[float | None]:
    s = to_series(series)
    n = len(s)
    closes = s.closes

    rsi_vals = rsi(closes, rsi_period)
    macd_res = macd(closes, macd_fast, macd_slow, macd_signal)
    st = supertrend(s, supertrend_period, supertrend_mult)

    out: list[float | None] = [None] * n

    # Compute typical histogram magnitude for normalization
    valid_hist = [h for h in macd_res.histogram if h is not None]
    typical_hist = (sum(abs(h) for h in valid_hist) / len(valid_hist)) if valid_hist else 1.0

    for i in range(n):
        r = rsi_vals[i]
        h = macd_res.histogram[i]
        d = st.direction[i]
        if r is None or h is None or d is None:
            continue

        rsi_component = _clip((r - 50.0) / 50.0)
        macd_component = _clip(h / (typical_hist * 2.0)) if typical_hist > 0 else 0.0
        st_component = float(d)

        out[i] = (rsi_component + macd_component + st_component) / 3.0
    return out
