"""Polymarket price-history fetcher.

Uses the public CLOB endpoint to fetch historical prices for a market token.
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request

CLOB_BASE = "https://clob.polymarket.com"


def fetch_polymarket_price_history(
    token_id: str,
    interval: str = "1h",
    fidelity: int = 60,
    start_ts: int | None = None,
    end_ts: int | None = None,
    timeout_sec: float = 30.0,
) -> list[dict]:
    """Fetch price-history rows for a Polymarket token.

    Returns list[{"timestamp": unix_ms, "price": float}].

    The Polymarket CLOB exposes `/prices-history` with parameters:
      market: token_id
      fidelity: bucket size in minutes (60 = hourly)
      startTs / endTs: unix seconds (optional)
    """
    params = {"market": token_id, "fidelity": fidelity}
    if start_ts is not None:
        params["startTs"] = start_ts
    if end_ts is not None:
        params["endTs"] = end_ts

    url = f"{CLOB_BASE}/prices-history?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=timeout_sec) as r:
        data = json.loads(r.read())

    rows: list[dict] = []
    for entry in data.get("history", []):
        ts = int(entry.get("t") or entry.get("timestamp") or 0)
        # Polymarket returns timestamps in seconds; convert to ms for consistency with Binance
        if ts < 1e12:
            ts = ts * 1000
        rows.append({"timestamp": ts, "price": float(entry.get("p") or entry.get("price") or 0.0)})
    return rows
