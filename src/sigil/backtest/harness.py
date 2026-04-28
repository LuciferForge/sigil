"""Backtest harness — single-asset, single-position, threshold-based."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from sigil.core import to_series, OHLCVSeries


@dataclass
class Trade:
    entry_index: int
    entry_timestamp: int
    entry_price: float
    side: str  # "LONG" or "SHORT"
    exit_index: int | None = None
    exit_timestamp: int | None = None
    exit_price: float | None = None
    pnl: float | None = None
    pnl_pct: float | None = None
    bars_held: int | None = None


@dataclass
class BacktestResult:
    trades: list[Trade]
    total_pnl: float
    total_pnl_pct: float
    n_trades: int
    n_wins: int
    win_rate: float
    avg_pnl_per_trade: float
    avg_bars_held: float

    def summary(self) -> str:
        return (
            f"Backtest: {self.n_trades} trades, "
            f"WR {self.win_rate*100:.1f}% ({self.n_wins}/{self.n_trades}), "
            f"total_pnl_pct {self.total_pnl_pct*100:+.2f}%, "
            f"avg_per_trade {self.avg_pnl_per_trade*100:+.2f}%, "
            f"avg_bars_held {self.avg_bars_held:.1f}"
        )


def backtest_signal(
    series,
    signal: Sequence[float | None],
    *,
    entry_threshold: float = 0.5,
    exit_threshold: float = 0.0,
    position_size: float = 1.0,
    fee_per_side_pct: float = 0.001,  # 10 bps each side; for crypto realistic
    long_only: bool = False,
) -> BacktestResult:
    """Run a backtest where positions enter when |signal| >= entry_threshold and
    exit when |signal| crosses exit_threshold (or signal flips sign).

    Trades execute at the next bar's open (no look-ahead).

    Args:
      series: OHLCV input.
      signal: same length as series, values in [-1, +1] or None.
      entry_threshold: open a position when signal >= +threshold (long) or <= -threshold (short).
      exit_threshold: close when |signal| < this AND has the wrong sign.
      position_size: notional units (default 1.0 — P&L is fraction of position size).
      fee_per_side_pct: round-trip fee = 2 × this (default 0.1% each side = 20 bps round-trip).
      long_only: if True, ignore short signals.
    """
    s = to_series(series)
    n = len(s)
    if len(signal) != n:
        raise ValueError(f"signal length {len(signal)} != series length {n}")

    trades: list[Trade] = []
    open_trade: Trade | None = None

    for i in range(n - 1):  # last bar can't open a new trade (no next bar to fill)
        sig = signal[i]
        next_bar = s.bars[i + 1]

        if open_trade is None:
            if sig is None:
                continue
            if sig >= entry_threshold:
                open_trade = Trade(
                    entry_index=i + 1,
                    entry_timestamp=next_bar.timestamp,
                    entry_price=next_bar.open,
                    side="LONG",
                )
            elif (not long_only) and sig <= -entry_threshold:
                open_trade = Trade(
                    entry_index=i + 1,
                    entry_timestamp=next_bar.timestamp,
                    entry_price=next_bar.open,
                    side="SHORT",
                )
        else:
            # Decide whether to close
            should_close = False
            if sig is None:
                pass
            elif open_trade.side == "LONG":
                if sig <= exit_threshold:
                    should_close = True
            else:  # SHORT
                if sig >= -exit_threshold:
                    should_close = True

            if should_close:
                exit_price = next_bar.open
                if open_trade.side == "LONG":
                    raw_pnl_pct = (exit_price - open_trade.entry_price) / open_trade.entry_price
                else:
                    raw_pnl_pct = (open_trade.entry_price - exit_price) / open_trade.entry_price
                # Apply fees
                pnl_pct = raw_pnl_pct - 2 * fee_per_side_pct
                open_trade.exit_index = i + 1
                open_trade.exit_timestamp = next_bar.timestamp
                open_trade.exit_price = exit_price
                open_trade.pnl_pct = pnl_pct
                open_trade.pnl = pnl_pct * position_size
                open_trade.bars_held = open_trade.exit_index - open_trade.entry_index
                trades.append(open_trade)
                open_trade = None

    # Close any open position at the last bar
    if open_trade is not None:
        last = s.bars[-1]
        if open_trade.side == "LONG":
            raw = (last.close - open_trade.entry_price) / open_trade.entry_price
        else:
            raw = (open_trade.entry_price - last.close) / open_trade.entry_price
        pnl_pct = raw - 2 * fee_per_side_pct
        open_trade.exit_index = n - 1
        open_trade.exit_timestamp = last.timestamp
        open_trade.exit_price = last.close
        open_trade.pnl_pct = pnl_pct
        open_trade.pnl = pnl_pct * position_size
        open_trade.bars_held = open_trade.exit_index - open_trade.entry_index
        trades.append(open_trade)

    n_trades = len(trades)
    if n_trades == 0:
        return BacktestResult(
            trades=[], total_pnl=0.0, total_pnl_pct=0.0, n_trades=0,
            n_wins=0, win_rate=0.0, avg_pnl_per_trade=0.0, avg_bars_held=0.0,
        )

    n_wins = sum(1 for t in trades if (t.pnl or 0) > 0)
    total_pnl = sum(t.pnl or 0 for t in trades)
    total_pct = sum(t.pnl_pct or 0 for t in trades)
    avg_bars = sum(t.bars_held or 0 for t in trades) / n_trades

    return BacktestResult(
        trades=trades,
        total_pnl=total_pnl,
        total_pnl_pct=total_pct,
        n_trades=n_trades,
        n_wins=n_wins,
        win_rate=n_wins / n_trades,
        avg_pnl_per_trade=total_pnl / n_trades,
        avg_bars_held=avg_bars,
    )
