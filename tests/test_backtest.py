"""Backtest harness tests."""
from sigil.core import OHLCV, OHLCVSeries
from sigil.backtest import backtest_signal


def _series(closes):
    return OHLCVSeries([
        OHLCV(timestamp=i * 60_000, open=c, high=c, low=c, close=c, volume=1.0)
        for i, c in enumerate(closes)
    ])


def test_no_trades_on_neutral_signal():
    closes = list(range(100, 120))
    s = _series(closes)
    sig = [0.0] * 20  # all neutral
    res = backtest_signal(s, sig, entry_threshold=0.5)
    assert res.n_trades == 0


def test_simple_long_trade():
    """Signal goes from +1 (entry) to 0 (exit). Verify long P&L."""
    closes = [100, 100, 100, 105, 110, 115, 110, 110]
    s = _series(closes)
    # entry on bar 2 (signal[2]=+1 → enter at next bar's open = bar 3 open = 105)
    # exit on bar 5 (signal[5]=0 → exit at bar 6 open = 110)
    sig = [None, None, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0]
    res = backtest_signal(s, sig, entry_threshold=0.5, exit_threshold=0.0,
                          fee_per_side_pct=0.0)
    assert res.n_trades == 1
    t = res.trades[0]
    assert t.side == "LONG"
    assert t.entry_price == 105
    assert t.exit_price == 110
    expected_pnl_pct = (110 - 105) / 105
    assert abs(t.pnl_pct - expected_pnl_pct) < 1e-9


def test_short_trade_when_long_only_disabled():
    closes = [100, 100, 100, 95, 90, 85, 90]
    s = _series(closes)
    # signal[2] = -1 → SHORT at bar 3 open = 95
    # signal[5] = 0 → close at bar 6 open = 90
    sig = [None, None, -1.0, -1.0, -1.0, 0.0, 0.0]
    res = backtest_signal(s, sig, entry_threshold=0.5, fee_per_side_pct=0.0,
                          long_only=False)
    assert res.n_trades == 1
    assert res.trades[0].side == "SHORT"
    expected = (95 - 90) / 95  # short profit when price drops
    assert abs(res.trades[0].pnl_pct - expected) < 1e-9


def test_long_only_ignores_short_signals():
    closes = [100, 100, 100, 95, 90, 85, 90]
    s = _series(closes)
    sig = [None, None, -1.0, -1.0, -1.0, 0.0, 0.0]
    res = backtest_signal(s, sig, entry_threshold=0.5, fee_per_side_pct=0.0,
                          long_only=True)
    assert res.n_trades == 0


def test_open_position_closed_at_end():
    """If signal stays high to the end, position closes at last close."""
    closes = [100, 105, 110, 115, 120]
    s = _series(closes)
    sig = [1.0, 1.0, 1.0, 1.0, 1.0]
    res = backtest_signal(s, sig, entry_threshold=0.5, fee_per_side_pct=0.0)
    # Entry at bar 1 open=105; exit at last close=120
    assert res.n_trades == 1
    t = res.trades[0]
    assert t.entry_price == 105
    assert t.exit_price == 120


def test_fees_reduce_pnl():
    closes = [100, 100, 100, 110, 110]
    s = _series(closes)
    sig = [None, None, 1.0, 1.0, 0.0]
    no_fee = backtest_signal(s, sig, entry_threshold=0.5, fee_per_side_pct=0.0)
    with_fee = backtest_signal(s, sig, entry_threshold=0.5, fee_per_side_pct=0.005)
    # 0.5% per side → 1% round trip lost
    assert abs((no_fee.trades[0].pnl_pct - with_fee.trades[0].pnl_pct) - 0.01) < 1e-9


def test_summary_string():
    closes = [100, 100, 100, 105, 100]
    s = _series(closes)
    sig = [None, None, 1.0, 1.0, 0.0]
    res = backtest_signal(s, sig, entry_threshold=0.5, fee_per_side_pct=0.0)
    summary = res.summary()
    assert "trades" in summary
    assert "WR" in summary
