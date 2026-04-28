# Sigil

[![PyPI](https://img.shields.io/pypi/v/sigil-ta.svg)](https://pypi.org/project/sigil-ta/)
[![Python](https://img.shields.io/pypi/pyversions/sigil-ta.svg)](https://pypi.org/project/sigil-ta/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**MCP-native technical analysis runtime — 8 core indicators, 2 composite signals, and the unique Polymarket Sentiment Divergence (PSD).**

```bash
pip install sigil-ta
sigil demo rsi
```

Sigil is a TA library that's also a Claude / Cursor / Cline tool server. Every indicator is exposed via the Model Context Protocol — point your AI agent at `sigil-mcp`, ask "what's the RSI of BTC right now?", and it answers with live data.

## Why this exists

I built this because I needed three things in one toolkit:
1. **Indicators that aren't a pile of opinionated TA-Lib glue.** Pure Python core, zero runtime deps, deterministic outputs.
2. **A way to compose signals our way, not LuxAlgo's way.** Two of our composite signals (`ReversionScore`, `MomentumComposite`) and one unique signal (`PolymarketSentimentDivergence`) you won't find anywhere else.
3. **MCP-native runtime so any AI agent can query live signals.** No glue code. No subprocess wrappers. Install, configure once, ask in natural language.

## What's in v0.1

### 8 core indicators (pure stdlib)

| Indicator | Description |
|-----------|-------------|
| `sma(closes, period)` | Simple Moving Average |
| `ema(closes, period)` | Exponential Moving Average |
| `rsi(closes, period=14)` | Wilder's Relative Strength Index |
| `macd(closes, 12, 26, 9)` | MACD with signal & histogram |
| `bollinger_bands(closes, 20, 2.0)` | BB upper/middle/lower |
| `atr(series, 14)` | Wilder's Average True Range |
| `supertrend(series, 10, 3.0)` | Supertrend with line + direction |
| `stochastic(series, 14, 3)` | %K and %D |

### 2 composite signals (our naming, our weighting)

| Signal | Components | Use case |
|--------|------------|----------|
| `reversion_score` | RSI deviation + BB position + ATR-normalized deviation | Mean-reversion entries |
| `momentum_composite` | RSI + MACD histogram + Supertrend direction | Trend-following |

Both score on `[-1, +1]` — directly usable as a backtest signal.

### 1 unique signal: `polymarket_sentiment_divergence` (PSD)

Measures divergence between an underlying asset's price action and the resolved sentiment from a related Polymarket prediction market. When the chart says "going up" but the market consensus says "probably won't happen", one of them is wrong — that's signal, and that's what PSD captures.

**Why PSD is uncopyable:** Pure-TA libraries (LuxAlgo, ta, pandas-ta, ta-lib) do not have access to prediction-market sentiment. Sigil integrates Polymarket via `sigil.data.polymarket` so the sentiment channel is built in.

### Data fetchers (zero deps, stdlib only)

- `fetch_binance_ohlcv(symbol, interval, limit)` → live OHLCV
- `fetch_polymarket_price_history(token_id, ...)` → PM probability time series

### Backtest harness

```python
from sigil.backtest import backtest_signal

result = backtest_signal(
    series=ohlcv_series,
    signal=reversion_scores,
    entry_threshold=0.5,
    exit_threshold=0.0,
    fee_per_side_pct=0.001,  # 10 bps each side
)
print(result.summary())
# Backtest: 24 trades, WR 66.7% (16/24), total_pnl_pct -2.84%, avg_per_trade -0.12%, avg_bars_held 14.0
```

### MCP server

```bash
pip install sigil-ta[mcp]
sigil-mcp                # stdio (Claude Desktop / Cursor / Cline)
sigil-mcp --transport http --port 8765   # HTTP transport
```

14 tools exposed. Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "sigil": {
      "command": "sigil-mcp"
    }
  }
}
```

Then ask Claude things like:
- *"Fetch the last 200 hours of BTCUSDT and compute the RSI."*
- *"Run a Supertrend backtest on ETHUSDT with default params."*
- *"What's the Bollinger Bands upper band for SOLUSDT right now?"*

### Streamlit dashboard

```bash
pip install sigil-ta[dashboard]
sigil-dashboard
```

Pick a symbol, an interval, an indicator. See the candles + indicator + (for composite signals) a backtest panel underneath. Designed for `signals.protodex.io` deployment but runs locally too.

## Install options

```bash
# Core (pure stdlib, no deps)
pip install sigil-ta

# With MCP server
pip install sigil-ta[mcp]

# With Streamlit dashboard
pip install sigil-ta[dashboard]

# Everything
pip install sigil-ta[all]
```

## CLI quickstart

```bash
$ sigil list                  # list indicators
$ sigil demo rsi              # synthetic-data smoke test
RSI(14) last 5: [89.96, 91.16, 92.12, 92.89, 93.5]

$ sigil demo reversion
ReversionScore last 5: [-0.933, -0.941, -0.947, -0.953, -0.952]
```

## Python API

```python
from sigil import indicators, signals
from sigil.core import OHLCVSeries
from sigil.data import fetch_binance_ohlcv

# Fetch live data
series = fetch_binance_ohlcv("BTCUSDT", "1h", limit=500)
closes = series.closes

# Indicators
rsi = indicators.rsi(closes, 14)
macd = indicators.macd(closes)
bb = indicators.bollinger_bands(closes)
print(f"RSI = {rsi[-1]:.2f}, BB middle = ${bb.middle[-1]:,.2f}")

# Composite signals
rev = signals.reversion_score(series)
mom = signals.momentum_composite(series)
print(f"ReversionScore = {rev[-1]:+.3f}, MomentumComposite = {mom[-1]:+.3f}")
```

## PSD example

```python
from sigil import signals
from sigil.data import fetch_binance_ohlcv, fetch_polymarket_price_history

# 1. Fetch BTC 1h closes
series = fetch_binance_ohlcv("BTCUSDT", "1h", limit=500)
asset_closes = series.closes

# 2. Fetch Polymarket "Will BTC be above $X by Y" probability history (same length, aligned)
pm_rows = fetch_polymarket_price_history(token_id="...", fidelity=60)
pm_probs = [r["price"] for r in pm_rows[-500:]]

# 3. Compute PSD
result = signals.polymarket_sentiment_divergence(
    asset_closes, pm_probs, smoothing_window=5,
)
print(f"Latest PSD score: {result.score[-1]:+.3f}")
# Score > 0 = bullish divergence (price down, sentiment up)
# Score < 0 = bearish divergence (price up, sentiment down)
```

## Design choices

**Pure stdlib core.** No numpy, pandas, scipy required. Every indicator is plain Python doing arithmetic. This makes the package install in milliseconds, run on cold-start serverless, and never break from a third-party version bump. (pandas/streamlit/plotly/mcp are optional extras.)

**Indicators return `list[float | None]` same length as input.** None during warm-up. No magic resampling. No silent NaN propagation. What you put in, you get back, aligned.

**Composite signals score on `[-1, +1]`.** Clip-and-combine math, no exotic weights. If you don't like the weights, there are 100 lines of code to read in `signals/reversion.py` — fork it.

**Backtest is FOK-style.** Decisions on bar `i`, trade fills at bar `i+1` open. No look-ahead. Realistic-by-default fees (10 bps per side).

**Test coverage is the contract.** Every indicator has property tests (constant input behaves correctly, monotone-up RSI = 100, etc.). 47 tests at v0.1.

## Tested

47 tests. Run them:

```bash
git clone https://github.com/LuciferForge/sigil
cd sigil
pip install -e ".[dev,mcp]"
pytest -v
```

Sample output:
```
tests/test_backtest.py .......                                           [ 14%]
tests/test_core.py .....                                                 [ 25%]
tests/test_indicators.py .....................                           [ 70%]
tests/test_mcp.py .....                                                  [ 80%]
tests/test_signals.py .........                                          [100%]
============================== 47 passed in 3.18s ==============================
```

## What's coming (roadmap)

- v0.2 — More indicators: ADX, Ichimoku, OBV, VWAP, Heikin-Ashi
- v0.3 — Walk-forward backtest with parameter sweeps
- v0.4 — Multi-timeframe signal fusion (15m + 1h + 4h alignment)
- v0.5 — Live signal alerting (Discord/Telegram/Slack)
- v0.6 — Public ground-truth ledger at signals.protodex.io

## License

MIT.

## About the author

Built by [LuciferForge](https://github.com/LuciferForge), running a [public-audited Polymarket trading bot](https://github.com/LuciferForge/polymarket-crash-bot) (302 closed trades, 79.8% WR). I needed an MCP-native TA stack for my own bot work and built one from scratch rather than wrapping an existing library. Other projects:
- [polymarket-mcp](https://github.com/LuciferForge/polymarket-mcp) — Polymarket data as MCP tools
- [pnl-truthteller](https://github.com/LuciferForge/pnl-truthteller) — slippage audit for any Polymarket bot
- [cross-signal-data](https://github.com/LuciferForge/cross-signal-data) — labeled crash-recovery dataset
- [quant-rollout](https://github.com/LuciferForge/quant-rollout) — staged-deployment toolkit
- [polymarket-v2-migration](https://github.com/LuciferForge/polymarket-v2-migration) — V1→V2 cookbook
