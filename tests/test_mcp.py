"""MCP server tests — only run if `mcp` is installed."""
import pytest

mcp_pkg = pytest.importorskip("mcp", reason="mcp not installed")


def test_mcp_server_imports():
    import sigil.mcp.server  # noqa: F401


def test_all_expected_tools_registered():
    import sigil.mcp.server as srv

    expected = {
        "list_indicators",
        "compute_sma", "compute_ema", "compute_rsi",
        "compute_macd", "compute_bollinger_bands",
        "compute_atr", "compute_supertrend", "compute_stochastic",
        "compute_reversion_score", "compute_momentum_composite",
        "compute_psd",
        "fetch_binance_ohlcv",
        "backtest_signal_tool",
    }
    actual = {name for name in dir(srv) if not name.startswith("_")}
    missing = expected - actual
    assert not missing, f"Missing tools: {missing}"


def test_compute_sma_via_mcp_tool():
    """The MCP-decorated functions should still be callable directly in Python."""
    import sigil.mcp.server as srv

    result = srv.compute_sma([1, 2, 3, 4, 5], 3)
    assert result == [None, None, 2.0, 3.0, 4.0]


def test_compute_rsi_via_mcp_tool():
    import sigil.mcp.server as srv

    result = srv.compute_rsi(list(range(1, 31)), 14)
    # No losses → RSI = 100 at first non-None index
    valid = [v for v in result if v is not None]
    assert valid[0] == 100.0


def test_list_indicators_returns_catalog():
    import sigil.mcp.server as srv

    cat = srv.list_indicators()
    assert "rsi" in cat
    assert "supertrend" in cat
    assert cat["rsi"]["needs_ohlc"] is False
    assert cat["supertrend"]["needs_ohlc"] is True
