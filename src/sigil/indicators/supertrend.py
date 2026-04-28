"""Supertrend — ATR-based trend follower."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from sigil.core import to_series
from sigil.indicators.atr import atr


@dataclass(frozen=True)
class SupertrendResult:
    line: list[float | None]
    direction: list[int | None]  # +1 = uptrend, -1 = downtrend


def supertrend(series, period: int = 10, multiplier: float = 3.0) -> SupertrendResult:
    s = to_series(series)
    n = len(s)
    line: list[float | None] = [None] * n
    direction: list[int | None] = [None] * n
    if n < period + 1:
        return SupertrendResult(line=line, direction=direction)

    atr_vals = atr(s, period)
    final_upper: list[float | None] = [None] * n
    final_lower: list[float | None] = [None] * n

    for i in range(n):
        a = atr_vals[i]
        if a is None:
            continue
        hl2 = (s.bars[i].high + s.bars[i].low) / 2
        bub = hl2 + multiplier * a
        blb = hl2 - multiplier * a

        if i == 0 or atr_vals[i - 1] is None:
            final_upper[i] = bub
            final_lower[i] = blb
            continue

        prev_close = s.bars[i - 1].close
        prev_upper = final_upper[i - 1] or bub
        prev_lower = final_lower[i - 1] or blb

        # Tighten bands per Supertrend rules
        final_upper[i] = bub if (bub < prev_upper or prev_close > prev_upper) else prev_upper
        final_lower[i] = blb if (blb > prev_lower or prev_close < prev_lower) else prev_lower

    # Direction & line
    for i in range(n):
        if final_upper[i] is None or final_lower[i] is None:
            continue
        prev_dir = direction[i - 1] if i > 0 else None
        prev_line = line[i - 1] if i > 0 else None
        close_i = s.bars[i].close

        if prev_line is None:
            # Initial direction: above middle band? uptrend, else downtrend
            mid = (final_upper[i] + final_lower[i]) / 2
            d = 1 if close_i >= mid else -1
        elif prev_dir == 1:
            d = -1 if close_i < final_lower[i] else 1
        else:  # prev_dir == -1
            d = 1 if close_i > final_upper[i] else -1

        direction[i] = d
        line[i] = final_lower[i] if d == 1 else final_upper[i]

    return SupertrendResult(line=line, direction=direction)
