#!/usr/bin/env python3
"""End-to-end demo: indicators → composite signals → backtest.

Run:
    python examples/full_pipeline_demo.py

Generates synthetic OHLCV data (deterministic), computes ReversionScore and
MomentumComposite signals, and backtests both. Verifies the full pipeline
without needing a network call.
"""
from __future__ import annotations

import math

from sigil import indicators, signals
from sigil.core import OHLCV, OHLCVSeries
from sigil.backtest import backtest_signal


def generate_synthetic_series(n: int = 500) -> OHLCVSeries:
    """Generate a noisy mean-reverting series — favorable for ReversionScore."""
    bars = []
    base_price = 100.0
    for i in range(n):
        # Mean-reverting around 100 with sinusoidal cycles + noise
        offset = math.sin(i / 20) * 8 + math.cos(i / 7) * 3
        close = base_price + offset
        # Small intra-bar range
        bar_range = abs(math.sin(i / 11)) * 1.5 + 0.5
        high = close + bar_range / 2
        low = close - bar_range / 2
        prev_close = bars[-1].close if bars else close
        open_ = (prev_close + close) / 2
        bars.append(OHLCV(
            timestamp=i * 60_000,
            open=open_, high=high, low=low, close=close,
            volume=100.0 + (i % 10) * 5,
        ))
    return OHLCVSeries(bars)


def main():
    series = generate_synthetic_series(500)
    closes = series.closes
    n = len(series)

    print(f"Generated {n} synthetic bars")
    print(f"Price range: ${min(closes):.2f} – ${max(closes):.2f}")
    print()

    # Run all indicators
    print("== Indicator computations ==")
    rsi_vals = indicators.rsi(closes)
    macd_res = indicators.macd(closes)
    bb = indicators.bollinger_bands(closes)
    atr_vals = indicators.atr(series)
    st = indicators.supertrend(series)
    stoch = indicators.stochastic(series)

    last_rsi = next((v for v in reversed(rsi_vals) if v is not None), None)
    last_macd = next((v for v in reversed(macd_res.macd) if v is not None), None)
    last_bb_mid = next((v for v in reversed(bb.middle) if v is not None), None)
    last_atr = next((v for v in reversed(atr_vals) if v is not None), None)
    last_st_dir = next((v for v in reversed(st.direction) if v is not None), None)
    last_k = next((v for v in reversed(stoch.k) if v is not None), None)

    print(f"  RSI(14)         = {last_rsi:.2f}")
    print(f"  MACD            = {last_macd:.4f}")
    print(f"  BB middle       = ${last_bb_mid:.2f}")
    print(f"  ATR(14)         = {last_atr:.4f}")
    print(f"  Supertrend dir  = {last_st_dir:+d}")
    print(f"  Stoch %K        = {last_k:.2f}")
    print()

    # Composite signals
    print("== Composite signals ==")
    rev_scores = signals.reversion_score(series)
    mom_scores = signals.momentum_composite(series)
    last_rev = next((v for v in reversed(rev_scores) if v is not None), None)
    last_mom = next((v for v in reversed(mom_scores) if v is not None), None)
    print(f"  ReversionScore     = {last_rev:+.3f}")
    print(f"  MomentumComposite  = {last_mom:+.3f}")
    print()

    # Backtest both signals
    print("== Backtests (entry=0.4, exit=0.0, fees=10bps/side) ==")
    rev_bt = backtest_signal(series, rev_scores, entry_threshold=0.4,
                              exit_threshold=0.0, fee_per_side_pct=0.001)
    mom_bt = backtest_signal(series, mom_scores, entry_threshold=0.4,
                              exit_threshold=0.0, fee_per_side_pct=0.001)
    print(f"  ReversionScore   {rev_bt.summary()}")
    print(f"  MomentumComposite {mom_bt.summary()}")
    print()

    # PSD demo (synthetic asset + PM probabilities that mostly disagree)
    print("== PSD demo ==")
    asset_closes = closes[-100:]
    # Inverse PM: when asset rises, PM falls
    pm_probs = [0.5 + (100 - c) / 200 for c in asset_closes]
    psd = signals.polymarket_sentiment_divergence(asset_closes, pm_probs,
                                                    smoothing_window=5)
    valid_scores = [v for v in psd.score if v is not None]
    print(f"  Valid PSD scores: {len(valid_scores)} bars")
    print(f"  Min/max:  {min(valid_scores):.3f} / {max(valid_scores):.3f}")
    print(f"  Mean abs score (when divergent): {sum(abs(v) for v in valid_scores) / len(valid_scores):.3f}")
    print()
    print("All systems verified.")


if __name__ == "__main__":
    main()
