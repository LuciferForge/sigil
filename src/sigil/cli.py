"""CLI for sigil — basic info + smoke tests."""
from __future__ import annotations

import argparse
import json
import sys

from sigil import indicators, signals
from sigil.indicators import CATALOG
from sigil.core import OHLCV, OHLCVSeries


def cmd_list(args):
    """List all indicators with descriptions."""
    for key, meta in CATALOG.items():
        print(f"{key:25s}  {meta['name']}")
        print(f"{'':25s}  {meta['description']}")
        print(f"{'':25s}  params: {meta['params']}")
        print()
    print("Composite signals:")
    print(f"  reversion_score          ReversionScore composite [-1, +1]")
    print(f"  momentum_composite       MomentumComposite [-1, +1]")
    print(f"  polymarket_sentiment_divergence   PSD signal")


def cmd_demo(args):
    """Run an indicator on synthetic data and print the last few values."""
    # Make a noisy uptrend
    import math
    n = 100
    closes = [100.0 + i * 0.5 + math.sin(i / 5) * 5 for i in range(n)]
    bars = [OHLCV(timestamp=i * 60_000, open=c, high=c * 1.005, low=c * 0.995,
                  close=c, volume=1.0) for i, c in enumerate(closes)]
    series = OHLCVSeries(bars)

    name = args.indicator
    if name == "rsi":
        result = indicators.rsi(closes)
        print(f"RSI(14) last 5: {[round(v, 2) if v else None for v in result[-5:]]}")
    elif name == "macd":
        result = indicators.macd(closes)
        print(f"MACD last 3: {[round(v, 4) if v else None for v in result.macd[-3:]]}")
        print(f"Signal last 3: {[round(v, 4) if v else None for v in result.signal[-3:]]}")
    elif name == "bb":
        result = indicators.bollinger_bands(closes)
        print(f"BB upper last 3: {[round(v, 2) if v else None for v in result.upper[-3:]]}")
        print(f"BB middle last 3: {[round(v, 2) if v else None for v in result.middle[-3:]]}")
        print(f"BB lower last 3: {[round(v, 2) if v else None for v in result.lower[-3:]]}")
    elif name == "atr":
        result = indicators.atr(series)
        print(f"ATR(14) last 5: {[round(v, 4) if v else None for v in result[-5:]]}")
    elif name == "supertrend":
        result = indicators.supertrend(series)
        print(f"Supertrend line last 5: {[round(v, 2) if v else None for v in result.line[-5:]]}")
        print(f"Direction last 5: {result.direction[-5:]}")
    elif name == "stoch":
        result = indicators.stochastic(series)
        print(f"%K last 5: {[round(v, 2) if v else None for v in result.k[-5:]]}")
        print(f"%D last 5: {[round(v, 2) if v else None for v in result.d[-5:]]}")
    elif name == "reversion":
        result = signals.reversion_score(series)
        print(f"ReversionScore last 5: {[round(v, 3) if v else None for v in result[-5:]]}")
    elif name == "momentum":
        result = signals.momentum_composite(series)
        print(f"MomentumComposite last 5: {[round(v, 3) if v else None for v in result[-5:]]}")
    else:
        print(f"Unknown indicator: {name}", file=sys.stderr)
        return 1
    return 0


def main():
    p = argparse.ArgumentParser(prog="sigil")
    sub = p.add_subparsers(dest="cmd")

    p_list = sub.add_parser("list", help="List all indicators")
    p_list.set_defaults(func=cmd_list)

    p_demo = sub.add_parser("demo", help="Run an indicator on synthetic data")
    p_demo.add_argument("indicator", choices=[
        "rsi", "macd", "bb", "atr", "supertrend", "stoch",
        "reversion", "momentum",
    ])
    p_demo.set_defaults(func=cmd_demo)

    args = p.parse_args()
    if not getattr(args, "func", None):
        p.print_help()
        return 0
    return args.func(args) or 0


if __name__ == "__main__":
    raise SystemExit(main())
