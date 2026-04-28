# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-04-28

### Added
- Initial public release.
- 8 core indicators (pure stdlib, no numpy required):
  - `sma`, `ema`, `rsi`, `macd`, `bollinger_bands`, `atr`, `supertrend`, `stochastic`
- 2 composite signals (`-1, +1` scale):
  - `reversion_score` — RSI deviation + BB position + ATR-normalized deviation
  - `momentum_composite` — RSI + MACD histogram + Supertrend direction
- 1 unique signal:
  - `polymarket_sentiment_divergence` (PSD) — divergence between asset price action and Polymarket prediction-market sentiment
- Backtest harness with realistic fees (10 bps/side default), no look-ahead, FOK-style fills at next bar's open.
- Live data fetchers:
  - `fetch_binance_ohlcv(symbol, interval, limit)` — Binance public klines
  - `fetch_polymarket_price_history(token_id, ...)` — Polymarket CLOB
- 14 MCP tools via FastMCP (optional `pip install sigil-ta[mcp]`).
- Streamlit dashboard (optional `pip install sigil-ta[dashboard]`).
- `sigil` CLI with `list` and `demo` subcommands.
- 47 tests including end-to-end pipeline + RSI constant-input bug fix (returns 50, not 100).
- Pure stdlib core, zero runtime dependencies.
- MIT license.

### Note
- PyPI distribution name is `sigil-ta` because the bare `sigil` name was already taken by an unrelated package. The Python module, CLI commands, and GitHub repo all stay `sigil`.

[0.1.0]: https://github.com/LuciferForge/sigil/releases/tag/v0.1.0
