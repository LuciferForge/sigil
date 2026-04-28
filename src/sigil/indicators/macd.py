"""MACD — Moving Average Convergence Divergence."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from sigil.indicators.moving_averages import ema


@dataclass(frozen=True)
class MACDResult:
    macd: list[float | None]    # fast EMA - slow EMA
    signal: list[float | None]  # EMA of macd line
    histogram: list[float | None]  # macd - signal


def macd(
    closes: Sequence[float],
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> MACDResult:
    if fast >= slow:
        raise ValueError("fast period must be less than slow period")

    fast_ema = ema(closes, fast)
    slow_ema = ema(closes, slow)
    n = len(closes)

    macd_line: list[float | None] = []
    for f, s in zip(fast_ema, slow_ema):
        if f is None or s is None:
            macd_line.append(None)
        else:
            macd_line.append(f - s)

    # Signal line = EMA of MACD line, but EMA can't handle Nones — drop them, then re-align.
    valid_indices = [i for i, v in enumerate(macd_line) if v is not None]
    valid_values = [macd_line[i] for i in valid_indices]
    sig_partial = ema(valid_values, signal) if valid_values else []
    sig_line: list[float | None] = [None] * n
    for j, idx in enumerate(valid_indices):
        sig_line[idx] = sig_partial[j] if j < len(sig_partial) else None

    histogram: list[float | None] = []
    for m, s in zip(macd_line, sig_line):
        if m is None or s is None:
            histogram.append(None)
        else:
            histogram.append(m - s)

    return MACDResult(macd=macd_line, signal=sig_line, histogram=histogram)
