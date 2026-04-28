"""Stochastic Oscillator — %K and %D."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from sigil.core import to_series
from sigil.indicators.moving_averages import sma


@dataclass(frozen=True)
class StochasticResult:
    k: list[float | None]
    d: list[float | None]


def stochastic(series, k_period: int = 14, d_period: int = 3) -> StochasticResult:
    s = to_series(series)
    n = len(s)
    k_vals: list[float | None] = [None] * n
    d_vals: list[float | None] = [None] * n
    if n < k_period:
        return StochasticResult(k=k_vals, d=d_vals)

    for i in range(k_period - 1, n):
        window_highs = [s.bars[j].high for j in range(i - k_period + 1, i + 1)]
        window_lows = [s.bars[j].low for j in range(i - k_period + 1, i + 1)]
        hh = max(window_highs)
        ll = min(window_lows)
        denom = hh - ll
        if denom == 0:
            k_vals[i] = 50.0  # convention: flat range → midpoint
        else:
            k_vals[i] = (s.bars[i].close - ll) / denom * 100.0

    # %D = SMA of %K over d_period
    valid_k = [(i, v) for i, v in enumerate(k_vals) if v is not None]
    if len(valid_k) >= d_period:
        idx_list, val_list = zip(*valid_k)
        d_partial = sma(list(val_list), d_period)
        for j, idx in enumerate(idx_list):
            d_vals[idx] = d_partial[j] if d_partial[j] is not None else None

    return StochasticResult(k=k_vals, d=d_vals)
