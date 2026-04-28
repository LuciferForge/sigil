"""Binance public API klines fetcher — pure stdlib."""
from __future__ import annotations

import json
import urllib.parse
import urllib.request

from sigil.core import OHLCV, OHLCVSeries

BINANCE_API = "https://api.binance.com/api/v3/klines"

VALID_INTERVALS = {
    "1m", "3m", "5m", "15m", "30m",
    "1h", "2h", "4h", "6h", "8h", "12h",
    "1d", "3d", "1w", "1M",
}


def fetch_binance_ohlcv(
    symbol: str,
    interval: str = "1h",
    limit: int = 500,
    start_time_ms: int | None = None,
    end_time_ms: int | None = None,
    timeout_sec: float = 30.0,
) -> OHLCVSeries:
    """Fetch klines from Binance public API.

    Args:
      symbol: e.g. "BTCUSDT"
      interval: one of VALID_INTERVALS (default "1h")
      limit: max 1000 per Binance
      start_time_ms / end_time_ms: optional unix ms range

    Returns OHLCVSeries.
    """
    if interval not in VALID_INTERVALS:
        raise ValueError(f"interval must be one of {sorted(VALID_INTERVALS)}")

    params = {"symbol": symbol.upper(), "interval": interval, "limit": min(limit, 1000)}
    if start_time_ms is not None:
        params["startTime"] = start_time_ms
    if end_time_ms is not None:
        params["endTime"] = end_time_ms

    url = f"{BINANCE_API}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=timeout_sec) as r:
        rows = json.loads(r.read())

    bars: list[OHLCV] = []
    for row in rows:
        # Binance kline format: [open_time, open, high, low, close, volume, close_time, ...]
        bars.append(
            OHLCV(
                timestamp=int(row[0]),
                open=float(row[1]),
                high=float(row[2]),
                low=float(row[3]),
                close=float(row[4]),
                volume=float(row[5]),
            )
        )
    return OHLCVSeries(bars)
