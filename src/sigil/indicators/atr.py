"""Average True Range — Wilder volatility measure."""
from __future__ import annotations

from typing import Sequence

from sigil.core import OHLCVSeries, to_series


def atr(series, period: int = 14) -> list[float | None]:
    """Wilder ATR.

    True Range[i] = max(
        high[i] - low[i],
        |high[i] - close[i-1]|,
        |low[i] - close[i-1]|,
    )
    ATR[period] = SMA of TR[1..period]
    ATR[i]      = ((period-1) * ATR[i-1] + TR[i]) / period
    """
    if period < 1:
        raise ValueError("period must be >= 1")

    s = to_series(series)
    n = len(s)
    out: list[float | None] = [None] * n
    if n < period + 1:
        return out

    tr: list[float] = [0.0] * n  # tr[0] is undefined, leave 0
    for i in range(1, n):
        prev_close = s.bars[i - 1].close
        h = s.bars[i].high
        l = s.bars[i].low
        tr[i] = max(h - l, abs(h - prev_close), abs(l - prev_close))

    # First ATR = SMA of TR[1..period] inclusive
    first_atr = sum(tr[1: period + 1]) / period
    out[period] = first_atr
    prev_atr = first_atr
    for i in range(period + 1, n):
        prev_atr = ((period - 1) * prev_atr + tr[i]) / period
        out[i] = prev_atr
    return out
