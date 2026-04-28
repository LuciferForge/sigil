"""sigil — MCP-native technical analysis runtime.

Public API:
    from sigil import OHLCV, indicators, signals
    from sigil.backtest import backtest

8 core indicators (SMA, EMA, RSI, MACD, Bollinger Bands, ATR, Supertrend, Stochastic),
2 composite signals (ReversionScore, MomentumComposite), and the unique
PolymarketSentimentDivergence (PSD).

Differentiators vs other TA libraries:
  1. MCP-native — exposes every indicator as a Claude-callable tool.
  2. PSD — uses Polymarket prediction-market data nobody else integrates.
  3. Public ground truth — every signal we publish is verifiable via the
     bundled backtest harness.
"""
from sigil.core import OHLCV, OHLCVSeries
from sigil import indicators, signals

__version__ = "0.1.0"
__all__ = ["OHLCV", "OHLCVSeries", "indicators", "signals", "__version__"]
