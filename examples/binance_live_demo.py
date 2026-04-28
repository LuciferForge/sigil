#!/usr/bin/env python3
"""Pull live BTCUSDT data from Binance, compute signals, backtest.

Run:
    python examples/binance_live_demo.py

Requires network access. No API key needed — Binance public klines endpoint.
"""
from sigil import indicators, signals
from sigil.data import fetch_binance_ohlcv
from sigil.backtest import backtest_signal


def main():
    print("Fetching BTCUSDT 1h bars (last 500)...")
    series = fetch_binance_ohlcv("BTCUSDT", "1h", limit=500)
    print(f"Got {len(series)} bars; latest close = ${series[-1].close:,.2f}")
    print()

    closes = series.closes
    rsi_vals = indicators.rsi(closes)
    macd_res = indicators.macd(closes)
    bb = indicators.bollinger_bands(closes)

    print("== Live indicators ==")
    print(f"  RSI(14)         = {rsi_vals[-1]:.2f}")
    print(f"  MACD            = {macd_res.macd[-1]:.2f}")
    print(f"  MACD signal     = {macd_res.signal[-1]:.2f}")
    print(f"  BB upper        = ${bb.upper[-1]:,.2f}")
    print(f"  BB lower        = ${bb.lower[-1]:,.2f}")
    print()

    rev = signals.reversion_score(series)
    mom = signals.momentum_composite(series)
    print("== Composite signals ==")
    print(f"  ReversionScore    = {rev[-1]:+.3f}")
    print(f"  MomentumComposite = {mom[-1]:+.3f}")
    print()

    bt_mom = backtest_signal(series, mom, entry_threshold=0.4, exit_threshold=0.0,
                              fee_per_side_pct=0.001, long_only=True)
    bt_rev = backtest_signal(series, rev, entry_threshold=0.4, exit_threshold=0.0,
                              fee_per_side_pct=0.001, long_only=False)
    print("== Backtest (last 500 bars, 10bps/side fees) ==")
    print(f"  MomentumComposite (long-only):  {bt_mom.summary()}")
    print(f"  ReversionScore (long+short):    {bt_rev.summary()}")


if __name__ == "__main__":
    main()
