"""Backtest harness — turn a signal series into trades + P&L.

Usage:
    from sigil.backtest import backtest_signal

    result = backtest_signal(
        series=ohlcv_series,
        signal=signal_values,         # list[float | None] in [-1, +1]
        entry_threshold=0.5,          # |signal| >= this opens a position
        exit_threshold=0.0,           # |signal| <= this closes
        position_size=1.0,
    )
    print(result.summary())
"""
from sigil.backtest.harness import backtest_signal, BacktestResult, Trade

__all__ = ["backtest_signal", "BacktestResult", "Trade"]
