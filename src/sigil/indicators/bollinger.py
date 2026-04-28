"""Bollinger Bands."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class BollingerBands:
    upper: list[float | None]
    middle: list[float | None]   # SMA
    lower: list[float | None]


def bollinger_bands(
    closes: Sequence[float],
    period: int = 20,
    std_mult: float = 2.0,
) -> BollingerBands:
    if period < 2:
        raise ValueError("period must be >= 2")

    n = len(closes)
    upper: list[float | None] = [None] * n
    middle: list[float | None] = [None] * n
    lower: list[float | None] = [None] * n
    if n < period:
        return BollingerBands(upper=upper, middle=middle, lower=lower)

    for i in range(period - 1, n):
        window = closes[i - period + 1: i + 1]
        m = sum(window) / period
        # Population stdev (ddof=0) — matches most TA implementations
        variance = sum((x - m) ** 2 for x in window) / period
        std = math.sqrt(variance)
        middle[i] = m
        upper[i] = m + std_mult * std
        lower[i] = m - std_mult * std
    return BollingerBands(upper=upper, middle=middle, lower=lower)
