"""ReversionScore — composite mean-reversion signal.

Scores each bar on [-1, +1]:
  +1: strongly oversold (likely reversion up)
  -1: strongly overbought (likely reversion down)
   0: neutral

Components (equal-weighted):
  1. RSI deviation from 50 → mapped to [-1, +1] with sign flipped
     (RSI=70 → -0.4; RSI=30 → +0.4)
  2. Position within Bollinger Bands → close above upper = -1, below lower = +1
  3. ATR-normalized close vs 20-bar SMA → mean-reversion magnitude
"""
from __future__ import annotations

from typing import Sequence

from sigil.core import to_series
from sigil.indicators.rsi import rsi
from sigil.indicators.bollinger import bollinger_bands
from sigil.indicators.atr import atr
from sigil.indicators.moving_averages import sma


def _clip(x: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def reversion_score(
    series,
    *,
    rsi_period: int = 14,
    bb_period: int = 20,
    bb_std: float = 2.0,
    atr_period: int = 14,
) -> list[float | None]:
    s = to_series(series)
    n = len(s)
    closes = s.closes

    rsi_vals = rsi(closes, rsi_period)
    bb = bollinger_bands(closes, bb_period, bb_std)
    atr_vals = atr(s, atr_period)
    sma_vals = sma(closes, bb_period)

    out: list[float | None] = [None] * n
    for i in range(n):
        if rsi_vals[i] is None or bb.upper[i] is None or atr_vals[i] is None or sma_vals[i] is None:
            continue

        # Component 1: RSI deviation
        # RSI=50 → 0; RSI=70 → -0.4; RSI=80 → -0.6; RSI=30 → +0.4
        rsi_component = -((rsi_vals[i] - 50.0) / 50.0)

        # Component 2: BB position (-1 if above upper, +1 if below lower)
        c = closes[i]
        upper, mid, lower = bb.upper[i], bb.middle[i], bb.lower[i]
        band_width = upper - lower
        if band_width <= 0:
            bb_component = 0.0
        else:
            # Normalize: (c - mid) / (band_width / 2), then clip and flip sign
            normalized = (c - mid) / (band_width / 2.0)
            bb_component = _clip(-normalized)

        # Component 3: ATR-normalized deviation from SMA
        a = atr_vals[i]
        if a <= 0:
            atr_component = 0.0
        else:
            dev = (c - sma_vals[i]) / a
            # 2 ATRs above mean → -0.5; 2 below → +0.5
            atr_component = _clip(-dev / 4.0)

        out[i] = (rsi_component + bb_component + atr_component) / 3.0
    return out
