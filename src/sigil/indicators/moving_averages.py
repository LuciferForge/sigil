"""SMA and EMA — pure-Python implementations."""
from __future__ import annotations

from typing import Sequence


def sma(closes: Sequence[float], period: int) -> list[float | None]:
    """Simple Moving Average.

    Returns a list same length as `closes`. The first `period - 1` entries are
    None (warm-up). Each subsequent entry is the mean of the previous `period`
    closes (inclusive of current bar).
    """
    if period < 1:
        raise ValueError("period must be >= 1")

    out: list[float | None] = []
    n = len(closes)
    if n == 0:
        return []

    rolling_sum = 0.0
    for i, c in enumerate(closes):
        rolling_sum += c
        if i >= period:
            rolling_sum -= closes[i - period]
        if i >= period - 1:
            out.append(rolling_sum / period)
        else:
            out.append(None)
    return out


def ema(closes: Sequence[float], period: int) -> list[float | None]:
    """Exponential Moving Average.

    Uses the standard 2/(period+1) smoothing factor. Seed value is the SMA of
    the first `period` bars (Wilder convention varies — we use SMA seed for
    determinism). Bars before the warm-up return None.
    """
    if period < 1:
        raise ValueError("period must be >= 1")

    n = len(closes)
    out: list[float | None] = [None] * n
    if n < period:
        return out

    alpha = 2.0 / (period + 1)
    # Seed with SMA of first `period` closes
    seed = sum(closes[:period]) / period
    out[period - 1] = seed
    prev = seed
    for i in range(period, n):
        prev = alpha * closes[i] + (1 - alpha) * prev
        out[i] = prev
    return out
