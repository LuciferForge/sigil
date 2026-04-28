"""Relative Strength Index — Wilder-smoothed momentum oscillator."""
from __future__ import annotations

from typing import Sequence


def rsi(closes: Sequence[float], period: int = 14) -> list[float | None]:
    """Wilder's RSI.

    Standard formula:
      U = max(close[i] - close[i-1], 0)
      D = max(close[i-1] - close[i], 0)
      avg_U[period] = SMA of U over first `period` bars
      avg_D[period] = SMA of D over first `period` bars
      avg_U[i]   = ((period-1) * avg_U[i-1] + U[i]) / period   (Wilder)
      avg_D[i]   = ((period-1) * avg_D[i-1] + D[i]) / period
      rs = avg_U / avg_D
      RSI = 100 - 100 / (1 + rs)
    """
    if period < 2:
        raise ValueError("period must be >= 2")

    n = len(closes)
    out: list[float | None] = [None] * n
    if n < period + 1:
        return out

    gains: list[float] = []
    losses: list[float] = []
    for i in range(1, n):
        diff = closes[i] - closes[i - 1]
        gains.append(max(diff, 0.0))
        losses.append(max(-diff, 0.0))

    # First averages = SMA of the initial `period` gains/losses
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    if avg_gain == 0 and avg_loss == 0:
        out[period] = 50.0   # constant series → neutral
    elif avg_loss == 0:
        out[period] = 100.0
    else:
        rs = avg_gain / avg_loss
        out[period] = 100.0 - 100.0 / (1.0 + rs)

    for i in range(period + 1, n):
        g = gains[i - 1]
        l = losses[i - 1]
        avg_gain = ((period - 1) * avg_gain + g) / period
        avg_loss = ((period - 1) * avg_loss + l) / period
        if avg_gain == 0 and avg_loss == 0:
            out[i] = 50.0
        elif avg_loss == 0:
            out[i] = 100.0
        else:
            rs = avg_gain / avg_loss
            out[i] = 100.0 - 100.0 / (1.0 + rs)
    return out
