"""Sigil Streamlit dashboard.

Layout:
  - Sidebar: pick symbol, interval, indicator
  - Main: candlestick chart + indicator overlay + backtest stats

Run:
    sigil-dashboard
        or
    streamlit run src/sigil/dashboard/app.py
"""
from __future__ import annotations

import sys
import argparse

try:
    import streamlit as st
    import pandas as pd
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
except ImportError:
    print(
        "ERROR: dashboard requires streamlit, pandas, plotly. Install with:\n"
        "    pip install sigil[dashboard]",
        file=sys.stderr,
    )
    raise

from sigil import indicators, signals
from sigil.core import OHLCV, OHLCVSeries
from sigil.data import fetch_binance_ohlcv
from sigil.backtest import backtest_signal


SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "MATICUSDT", "AVAXUSDT", "BNBUSDT"]
INTERVALS = ["5m", "15m", "30m", "1h", "4h", "1d"]
INDICATORS = [
    "SMA", "EMA", "RSI", "MACD", "Bollinger Bands",
    "ATR", "Supertrend", "Stochastic",
    "ReversionScore", "MomentumComposite",
]


def render():
    st.set_page_config(page_title="Sigil — TA Runtime", layout="wide")
    st.title("Sigil — MCP-native Technical Analysis")

    with st.sidebar:
        st.header("Configuration")
        symbol = st.selectbox("Symbol", SYMBOLS, index=0)
        interval = st.selectbox("Interval", INTERVALS, index=3)
        limit = st.slider("Bars", 100, 1000, 500, 50)
        indicator_choice = st.selectbox("Indicator", INDICATORS, index=8)
        st.divider()
        st.caption("Run `sigil-mcp` to expose these as Claude/Cursor tools.")

    with st.spinner(f"Fetching {symbol} {interval} from Binance..."):
        try:
            series = fetch_binance_ohlcv(symbol, interval, limit)
        except Exception as e:
            st.error(f"Failed to fetch: {e}")
            return

    df = series.to_pandas()
    df["dt"] = pd.to_datetime(df["timestamp"], unit="ms")

    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3],
        vertical_spacing=0.04,
    )

    fig.add_trace(go.Candlestick(
        x=df["dt"], open=df["open"], high=df["high"],
        low=df["low"], close=df["close"], name="Price",
    ), row=1, col=1)

    closes = series.closes
    indicator_values: list[float | None] = []

    if indicator_choice == "SMA":
        period = st.sidebar.number_input("Period", 5, 200, 20, 1)
        indicator_values = indicators.sma(closes, period)
        fig.add_trace(go.Scatter(x=df["dt"], y=indicator_values, name=f"SMA({period})",
                                  line=dict(color="orange")), row=1, col=1)

    elif indicator_choice == "EMA":
        period = st.sidebar.number_input("Period", 5, 200, 20, 1)
        indicator_values = indicators.ema(closes, period)
        fig.add_trace(go.Scatter(x=df["dt"], y=indicator_values, name=f"EMA({period})",
                                  line=dict(color="purple")), row=1, col=1)

    elif indicator_choice == "RSI":
        period = st.sidebar.number_input("Period", 2, 50, 14, 1)
        rsi_vals = indicators.rsi(closes, period)
        fig.add_trace(go.Scatter(x=df["dt"], y=rsi_vals, name=f"RSI({period})",
                                  line=dict(color="cyan")), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
        indicator_values = rsi_vals

    elif indicator_choice == "MACD":
        m = indicators.macd(closes)
        fig.add_trace(go.Scatter(x=df["dt"], y=m.macd, name="MACD",
                                  line=dict(color="blue")), row=2, col=1)
        fig.add_trace(go.Scatter(x=df["dt"], y=m.signal, name="Signal",
                                  line=dict(color="red")), row=2, col=1)
        fig.add_trace(go.Bar(x=df["dt"], y=m.histogram, name="Histogram",
                             marker_color="grey"), row=2, col=1)

    elif indicator_choice == "Bollinger Bands":
        period = st.sidebar.number_input("Period", 5, 100, 20, 1)
        std_mult = st.sidebar.number_input("Std multiplier", 1.0, 4.0, 2.0, 0.1)
        bb = indicators.bollinger_bands(closes, period, std_mult)
        fig.add_trace(go.Scatter(x=df["dt"], y=bb.upper, name="Upper",
                                  line=dict(color="red", dash="dash")), row=1, col=1)
        fig.add_trace(go.Scatter(x=df["dt"], y=bb.middle, name="Middle",
                                  line=dict(color="orange")), row=1, col=1)
        fig.add_trace(go.Scatter(x=df["dt"], y=bb.lower, name="Lower",
                                  line=dict(color="green", dash="dash")), row=1, col=1)

    elif indicator_choice == "ATR":
        period = st.sidebar.number_input("Period", 2, 50, 14, 1)
        atr_vals = indicators.atr(series, period)
        fig.add_trace(go.Scatter(x=df["dt"], y=atr_vals, name=f"ATR({period})",
                                  line=dict(color="orange")), row=2, col=1)

    elif indicator_choice == "Supertrend":
        period = st.sidebar.number_input("Period", 2, 50, 10, 1)
        mult = st.sidebar.number_input("Multiplier", 1.0, 6.0, 3.0, 0.5)
        st_res = indicators.supertrend(series, period, mult)
        fig.add_trace(go.Scatter(x=df["dt"], y=st_res.line, name="Supertrend",
                                  line=dict(color="purple")), row=1, col=1)

    elif indicator_choice == "Stochastic":
        k = st.sidebar.number_input("K period", 2, 50, 14, 1)
        d = st.sidebar.number_input("D period", 1, 20, 3, 1)
        stoch = indicators.stochastic(series, k, d)
        fig.add_trace(go.Scatter(x=df["dt"], y=stoch.k, name="%K",
                                  line=dict(color="cyan")), row=2, col=1)
        fig.add_trace(go.Scatter(x=df["dt"], y=stoch.d, name="%D",
                                  line=dict(color="magenta")), row=2, col=1)
        fig.add_hline(y=80, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=20, line_dash="dash", line_color="green", row=2, col=1)

    elif indicator_choice == "ReversionScore":
        scores = signals.reversion_score(series)
        fig.add_trace(go.Scatter(x=df["dt"], y=scores, name="ReversionScore",
                                  line=dict(color="cyan")), row=2, col=1)
        fig.add_hline(y=0.5, line_dash="dash", line_color="green", row=2, col=1)
        fig.add_hline(y=-0.5, line_dash="dash", line_color="red", row=2, col=1)
        indicator_values = scores

    elif indicator_choice == "MomentumComposite":
        scores = signals.momentum_composite(series)
        fig.add_trace(go.Scatter(x=df["dt"], y=scores, name="MomentumComposite",
                                  line=dict(color="magenta")), row=2, col=1)
        fig.add_hline(y=0.5, line_dash="dash", line_color="green", row=2, col=1)
        fig.add_hline(y=-0.5, line_dash="dash", line_color="red", row=2, col=1)
        indicator_values = scores

    fig.update_layout(
        height=700, xaxis_rangeslider_visible=False,
        margin=dict(l=0, r=0, t=30, b=0),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Backtest section for signals on [-1, +1]
    if indicator_choice in ("ReversionScore", "MomentumComposite") and indicator_values:
        st.subheader("Backtest")
        col1, col2, col3, col4 = st.columns(4)
        entry = col1.number_input("Entry threshold", 0.1, 1.0, 0.5, 0.05)
        exit_thr = col2.number_input("Exit threshold", 0.0, 1.0, 0.0, 0.05)
        long_only = col3.checkbox("Long-only", value=False)
        col4.write(" ")

        result = backtest_signal(
            series, indicator_values,
            entry_threshold=entry, exit_threshold=exit_thr,
            long_only=long_only,
        )
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Trades", result.n_trades)
        c2.metric("Win rate", f"{result.win_rate*100:.1f}%")
        c3.metric("Total PnL %", f"{result.total_pnl_pct*100:+.2f}%")
        c4.metric("Avg bars held", f"{result.avg_bars_held:.1f}")


def cli_main():
    """Launcher: `sigil-dashboard` finds the right entrypoint and invokes streamlit."""
    parser = argparse.ArgumentParser(prog="sigil-dashboard")
    parser.add_argument("--port", type=int, default=8501)
    args = parser.parse_args()

    import streamlit.web.cli as stcli
    import os
    here = os.path.abspath(__file__)
    sys.argv = ["streamlit", "run", here, "--server.port", str(args.port)]
    sys.exit(stcli.main())


if __name__ == "__main__":
    render()
