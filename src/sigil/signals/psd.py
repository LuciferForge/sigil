"""Polymarket Sentiment Divergence (PSD).

The unique signal — measures divergence between an underlying asset's
price action and the resolved sentiment of a related Polymarket prediction
market.

EXAMPLE:
  Asset: BTC (close prices, hourly)
  Polymarket: "Will BTC be above $X by date Y?" — yields a probability time series

  PSD scores when:
    - Asset price is RISING (positive return) but PM probability is FALLING (sentiment cooling) → bearish divergence (-)
    - Asset price is FALLING (negative return) but PM probability is RISING (sentiment heating) → bullish divergence (+)
    - Both move together: 0 (no divergence)

INPUTS:
  asset_returns: list[float] — log-returns of the asset (length N)
  pm_returns: list[float]    — same-length log-returns (or first-difference) of PM probability

OUTPUT: list[float | None] same length, scored on [-1, +1].

The signal is only meaningful when BOTH series are non-trivially moving;
when |asset_returns| or |pm_returns| is below a noise floor, PSD = 0.

WHY THIS IS UNCOPYABLE:
  Pure-TA tools have no access to prediction-market sentiment. By integrating
  Polymarket as a second-channel sentiment input, PSD captures information
  that a chart-only signal cannot see. The crash bot's edge comes from this
  same intuition: when the market consensus and the price action disagree,
  one of them is wrong.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class PSDResult:
    score: list[float | None]            # [-1, +1] per bar
    asset_log_return: list[float | None]
    pm_log_change: list[float | None]


def _safe_log_return(prev: float, curr: float) -> float | None:
    if prev <= 0 or curr <= 0:
        return None
    return math.log(curr / prev)


def _safe_diff(prev: float, curr: float) -> float:
    return curr - prev


def polymarket_sentiment_divergence(
    asset_closes: Sequence[float],
    pm_probabilities: Sequence[float],
    *,
    smoothing_window: int = 5,
    noise_floor_asset: float = 0.001,   # 0.1% per-bar return below = noise
    noise_floor_pm: float = 0.005,      # 0.5% probability change below = noise
) -> PSDResult:
    """Compute PSD over aligned asset & PM series.

    Both series must be the same length; pre-align by timestamp before passing
    in. The first bar of each series gets None (no prior reference).
    """
    n = len(asset_closes)
    if len(pm_probabilities) != n:
        raise ValueError(
            f"asset_closes (len {n}) and pm_probabilities (len {len(pm_probabilities)}) "
            "must be the same length"
        )

    asset_ret: list[float | None] = [None] * n
    pm_change: list[float | None] = [None] * n

    for i in range(1, n):
        asset_ret[i] = _safe_log_return(asset_closes[i - 1], asset_closes[i])
        pm_change[i] = _safe_diff(pm_probabilities[i - 1], pm_probabilities[i])

    # Smooth each series using a simple rolling mean to reduce tick noise
    def _smooth(seq: Sequence[float | None], window: int) -> list[float | None]:
        out: list[float | None] = [None] * n
        for i in range(window - 1, n):
            chunk = [v for v in seq[i - window + 1: i + 1] if v is not None]
            if len(chunk) == window:
                out[i] = sum(chunk) / window
        return out

    asset_sm = _smooth(asset_ret, smoothing_window)
    pm_sm = _smooth(pm_change, smoothing_window)

    score: list[float | None] = [None] * n
    for i in range(n):
        a = asset_sm[i]
        p = pm_sm[i]
        if a is None or p is None:
            continue
        if abs(a) < noise_floor_asset and abs(p) < noise_floor_pm:
            score[i] = 0.0
            continue

        # Normalize each into [-1, +1]
        # Use a soft scaling — divide by 5x the noise floor to get to ±1 magnitude
        a_n = max(-1.0, min(1.0, a / (noise_floor_asset * 5)))
        p_n = max(-1.0, min(1.0, p / (noise_floor_pm * 5)))

        # Divergence score: +1 when asset_ret negative AND pm_change positive (bullish setup)
        # -1 when asset_ret positive AND pm_change negative (bearish)
        # When they agree (same sign), score is small (no divergence)
        # We compute: (p_n - a_n) / 2 — when they disagree, magnitude is large
        score[i] = max(-1.0, min(1.0, (p_n - a_n) / 2.0))

    return PSDResult(score=score, asset_log_return=asset_ret, pm_log_change=pm_change)
