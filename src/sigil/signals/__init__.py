"""Composite signals — combinations of base indicators that emit a single score.

Three signals shipped in v0.1:
  - reversion_score(series): mean-reversion composite (RSI + BB position + ATR-relative deviation)
  - momentum_composite(series): trend-strength composite (RSI + MACD histogram + Supertrend direction)
  - polymarket_sentiment_divergence(asset_series, pm_prices): the unique signal — divergence
    between underlying-asset price action and Polymarket-resolved sentiment for a related contract.

Each returns a list[float | None] same-length-as-input, scored on a unified scale:
  -1.0 = strong bearish / strong reversion-from-overbought
   0.0 = neutral / no signal
  +1.0 = strong bullish / strong reversion-from-oversold
"""
from sigil.signals.reversion import reversion_score
from sigil.signals.momentum import momentum_composite
from sigil.signals.psd import polymarket_sentiment_divergence, PSDResult

__all__ = [
    "reversion_score",
    "momentum_composite",
    "polymarket_sentiment_divergence",
    "PSDResult",
]
