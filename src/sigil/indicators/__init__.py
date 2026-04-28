"""Indicator catalog.

All indicators take a closes (list[float]) or OHLCVSeries and return a
list[float | None] same-length-as-input. None at indices where the
indicator's lookback hasn't been reached yet (warm-up period).

Functions are pure — no side effects, deterministic.

Available:
  - sma(closes, period) — Simple Moving Average
  - ema(closes, period) — Exponential Moving Average
  - rsi(closes, period=14) — Relative Strength Index
  - macd(closes, fast=12, slow=26, signal=9) — Moving Average Convergence Divergence
  - bollinger_bands(closes, period=20, std_mult=2.0) — Bollinger Bands
  - atr(series, period=14) — Average True Range (needs OHLC)
  - supertrend(series, period=10, multiplier=3.0) — Supertrend (needs OHLC)
  - stochastic(series, k_period=14, d_period=3) — Stochastic Oscillator (needs OHLC)
"""
from sigil.indicators.moving_averages import sma, ema
from sigil.indicators.rsi import rsi
from sigil.indicators.macd import macd, MACDResult
from sigil.indicators.bollinger import bollinger_bands, BollingerBands
from sigil.indicators.atr import atr
from sigil.indicators.supertrend import supertrend, SupertrendResult
from sigil.indicators.stochastic import stochastic, StochasticResult

__all__ = [
    "sma", "ema",
    "rsi",
    "macd", "MACDResult",
    "bollinger_bands", "BollingerBands",
    "atr",
    "supertrend", "SupertrendResult",
    "stochastic", "StochasticResult",
]


CATALOG = {
    "sma": {
        "name": "Simple Moving Average",
        "description": "Arithmetic mean of close prices over `period` bars.",
        "params": {"period": "int, required, lookback length in bars"},
        "needs_ohlc": False,
    },
    "ema": {
        "name": "Exponential Moving Average",
        "description": "Recursive weighted average favoring recent bars (smoothing factor 2/(period+1)).",
        "params": {"period": "int, required"},
        "needs_ohlc": False,
    },
    "rsi": {
        "name": "Relative Strength Index",
        "description": "Wilder-smoothed momentum oscillator on close-to-close changes; 0-100.",
        "params": {"period": "int, default 14"},
        "needs_ohlc": False,
    },
    "macd": {
        "name": "Moving Average Convergence Divergence",
        "description": "EMA(fast) - EMA(slow), with EMA(signal) of the MACD line.",
        "params": {"fast": "int, default 12", "slow": "int, default 26", "signal": "int, default 9"},
        "needs_ohlc": False,
    },
    "bollinger_bands": {
        "name": "Bollinger Bands",
        "description": "SMA ± std_mult × rolling stdev. Returns (upper, middle, lower).",
        "params": {"period": "int, default 20", "std_mult": "float, default 2.0"},
        "needs_ohlc": False,
    },
    "atr": {
        "name": "Average True Range",
        "description": "Wilder-smoothed average of True Range. Volatility measure.",
        "params": {"period": "int, default 14"},
        "needs_ohlc": True,
    },
    "supertrend": {
        "name": "Supertrend",
        "description": "Trend-following band using ATR. Returns (line, direction).",
        "params": {"period": "int, default 10", "multiplier": "float, default 3.0"},
        "needs_ohlc": True,
    },
    "stochastic": {
        "name": "Stochastic Oscillator",
        "description": "%K and %D oscillator, 0-100.",
        "params": {"k_period": "int, default 14", "d_period": "int, default 3"},
        "needs_ohlc": True,
    },
}
