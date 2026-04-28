"""Data fetchers — Binance OHLCV + Polymarket prices.

Both modules use only stdlib HTTP for zero-dependency core. Adapters are
optional — if you already have your own data source, skip these and feed
your data into OHLCVSeries directly.
"""
from sigil.data.binance import fetch_binance_ohlcv
from sigil.data.polymarket import fetch_polymarket_price_history

__all__ = ["fetch_binance_ohlcv", "fetch_polymarket_price_history"]
