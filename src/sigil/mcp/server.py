"""Sigil MCP server — every indicator is a Claude-callable tool.

Run:
    sigil-mcp                 # stdio transport (Claude Desktop / Cursor)
    sigil-mcp --http           # HTTP transport on 127.0.0.1:8765

Tools exposed:
    list_indicators
    compute_sma, compute_ema, compute_rsi, compute_macd
    compute_bollinger_bands, compute_atr, compute_supertrend, compute_stochastic
    compute_reversion_score, compute_momentum_composite
    compute_psd
    fetch_binance_ohlcv
    backtest_signal
"""
from __future__ import annotations

import argparse
import sys
from typing import Any

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print(
        "ERROR: MCP support requires the 'mcp' package. Install with:\n"
        "    pip install sigil[mcp]",
        file=sys.stderr,
    )
    raise

from sigil import indicators, signals
from sigil.core import OHLCV, OHLCVSeries
from sigil.indicators import CATALOG
from sigil.backtest import backtest_signal as _backtest

mcp = FastMCP("sigil")


def _bars_from_dicts(rows: list[dict[str, Any]]) -> OHLCVSeries:
    return OHLCVSeries.from_dicts(rows)


@mcp.tool()
def list_indicators() -> dict[str, Any]:
    """List all available Sigil indicators with their parameters and descriptions."""
    return CATALOG


@mcp.tool()
def compute_sma(closes: list[float], period: int) -> list[float | None]:
    """Simple Moving Average. Pass list of close prices."""
    return indicators.sma(closes, period)


@mcp.tool()
def compute_ema(closes: list[float], period: int) -> list[float | None]:
    """Exponential Moving Average."""
    return indicators.ema(closes, period)


@mcp.tool()
def compute_rsi(closes: list[float], period: int = 14) -> list[float | None]:
    """Wilder's RSI on close prices. Default period 14."""
    return indicators.rsi(closes, period)


@mcp.tool()
def compute_macd(
    closes: list[float],
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> dict[str, list[float | None]]:
    """MACD (default 12/26/9). Returns {macd, signal, histogram}."""
    res = indicators.macd(closes, fast, slow, signal)
    return {"macd": res.macd, "signal": res.signal, "histogram": res.histogram}


@mcp.tool()
def compute_bollinger_bands(
    closes: list[float],
    period: int = 20,
    std_mult: float = 2.0,
) -> dict[str, list[float | None]]:
    """Bollinger Bands (default 20, 2σ). Returns {upper, middle, lower}."""
    res = indicators.bollinger_bands(closes, period, std_mult)
    return {"upper": res.upper, "middle": res.middle, "lower": res.lower}


@mcp.tool()
def compute_atr(ohlcv_rows: list[dict[str, Any]], period: int = 14) -> list[float | None]:
    """ATR. Input rows must have keys timestamp, open, high, low, close (volume optional)."""
    series = _bars_from_dicts(ohlcv_rows)
    return indicators.atr(series, period)


@mcp.tool()
def compute_supertrend(
    ohlcv_rows: list[dict[str, Any]],
    period: int = 10,
    multiplier: float = 3.0,
) -> dict[str, Any]:
    """Supertrend. Returns {line, direction (-1=down, +1=up)}."""
    series = _bars_from_dicts(ohlcv_rows)
    res = indicators.supertrend(series, period, multiplier)
    return {"line": res.line, "direction": res.direction}


@mcp.tool()
def compute_stochastic(
    ohlcv_rows: list[dict[str, Any]],
    k_period: int = 14,
    d_period: int = 3,
) -> dict[str, list[float | None]]:
    """Stochastic Oscillator. Returns {k, d}."""
    series = _bars_from_dicts(ohlcv_rows)
    res = indicators.stochastic(series, k_period, d_period)
    return {"k": res.k, "d": res.d}


@mcp.tool()
def compute_reversion_score(ohlcv_rows: list[dict[str, Any]]) -> list[float | None]:
    """ReversionScore composite signal in [-1, +1]."""
    series = _bars_from_dicts(ohlcv_rows)
    return signals.reversion_score(series)


@mcp.tool()
def compute_momentum_composite(ohlcv_rows: list[dict[str, Any]]) -> list[float | None]:
    """MomentumComposite signal in [-1, +1]."""
    series = _bars_from_dicts(ohlcv_rows)
    return signals.momentum_composite(series)


@mcp.tool()
def compute_psd(
    asset_closes: list[float],
    pm_probabilities: list[float],
    smoothing_window: int = 5,
) -> dict[str, list[float | None]]:
    """Polymarket Sentiment Divergence — divergence between asset price action
    and Polymarket prediction-market sentiment.

    Both inputs MUST be the same length and pre-aligned by timestamp.
    Returns {score, asset_log_return, pm_log_change}.
    """
    res = signals.polymarket_sentiment_divergence(
        asset_closes, pm_probabilities, smoothing_window=smoothing_window
    )
    return {
        "score": res.score,
        "asset_log_return": res.asset_log_return,
        "pm_log_change": res.pm_log_change,
    }


@mcp.tool()
def fetch_binance_ohlcv(
    symbol: str,
    interval: str = "1h",
    limit: int = 500,
) -> list[dict[str, Any]]:
    """Fetch OHLCV from Binance public API. Returns list of dicts ready to feed back in."""
    from sigil.data import fetch_binance_ohlcv as _fetch

    series = _fetch(symbol, interval, limit)
    return [
        {
            "timestamp": b.timestamp,
            "open": b.open,
            "high": b.high,
            "low": b.low,
            "close": b.close,
            "volume": b.volume,
        }
        for b in series
    ]


@mcp.tool()
def backtest_signal_tool(
    ohlcv_rows: list[dict[str, Any]],
    signal_values: list[float | None],
    entry_threshold: float = 0.5,
    exit_threshold: float = 0.0,
    long_only: bool = False,
) -> dict[str, Any]:
    """Backtest a signal against OHLCV. Returns aggregate stats."""
    series = _bars_from_dicts(ohlcv_rows)
    res = _backtest(
        series, signal_values,
        entry_threshold=entry_threshold,
        exit_threshold=exit_threshold,
        long_only=long_only,
    )
    return {
        "n_trades": res.n_trades,
        "n_wins": res.n_wins,
        "win_rate": res.win_rate,
        "total_pnl_pct": res.total_pnl_pct,
        "avg_pnl_per_trade": res.avg_pnl_per_trade,
        "avg_bars_held": res.avg_bars_held,
        "summary": res.summary(),
    }


def main():
    parser = argparse.ArgumentParser(prog="sigil-mcp", description="Sigil MCP server")
    parser.add_argument("--transport", choices=["stdio", "http", "sse"], default="stdio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--list-tools", action="store_true",
                        help="Print registered tool names and exit")
    args = parser.parse_args()

    if args.list_tools:
        for name in sorted([t for t in dir(sys.modules[__name__]) if not t.startswith("_")]):
            obj = getattr(sys.modules[__name__], name)
            if callable(obj) and getattr(obj, "__module__", None) == __name__:
                print(name)
        return 0

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    elif args.transport == "http":
        mcp.run(transport="streamable-http", host=args.host, port=args.port)
    elif args.transport == "sse":
        mcp.run(transport="sse", host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
