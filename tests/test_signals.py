"""Composite signal tests."""
import math

from sigil import signals
from sigil.core import OHLCV, OHLCVSeries


def _series_from_closes(closes):
    return OHLCVSeries([
        OHLCV(timestamp=i * 60_000, open=c, high=c * 1.005,
              low=c * 0.995, close=c, volume=1.0)
        for i, c in enumerate(closes)
    ])


# ── ReversionScore ─────────────────────────────────────────────────


def test_reversion_score_in_range():
    closes = [100 + math.sin(i / 5) * 5 + i * 0.05 for i in range(100)]
    s = _series_from_closes(closes)
    out = signals.reversion_score(s)
    valid = [v for v in out if v is not None]
    assert all(-1.0 <= v <= 1.0 for v in valid)
    assert len(valid) > 50  # should produce values for most bars


def test_reversion_score_constant_input_near_zero():
    """Constant series → no extension from mean → score near 0."""
    closes = [100.0] * 60
    s = _series_from_closes(closes)
    out = signals.reversion_score(s)
    valid = [v for v in out if v is not None]
    assert all(abs(v) < 1e-6 for v in valid)


# ── MomentumComposite ─────────────────────────────────────────────


def test_momentum_uptrend_positive():
    closes = [100 + i * 0.3 for i in range(100)]
    s = _series_from_closes(closes)
    out = signals.momentum_composite(s)
    # Last value should be clearly positive (strong uptrend)
    assert out[-1] is not None
    assert out[-1] > 0.3


def test_momentum_downtrend_negative():
    closes = [100 - i * 0.3 for i in range(100)]
    s = _series_from_closes(closes)
    out = signals.momentum_composite(s)
    assert out[-1] is not None
    assert out[-1] < -0.3


# ── PSD ────────────────────────────────────────────────────────────


def test_psd_aligned_lengths():
    asset = [100 + i for i in range(20)]
    pm = [0.5 + i * 0.01 for i in range(20)]
    res = signals.polymarket_sentiment_divergence(asset, pm)
    assert len(res.score) == 20
    assert len(res.asset_log_return) == 20
    assert len(res.pm_log_change) == 20


def test_psd_length_mismatch_raises():
    import pytest
    with pytest.raises(ValueError):
        signals.polymarket_sentiment_divergence([1, 2, 3], [0.5, 0.6])


def test_psd_perfect_disagreement_high_score():
    """Asset rising while PM probability falling → bearish divergence (score < 0)."""
    n = 30
    asset = [100 + i * 1.0 for i in range(n)]      # +1% per step
    pm = [0.6 - i * 0.01 for i in range(n)]         # PM falling
    res = signals.polymarket_sentiment_divergence(asset, pm, smoothing_window=3)
    valid = [v for v in res.score if v is not None]
    # Most scores should be negative (bearish divergence: price up, sentiment down)
    assert sum(1 for v in valid if v < 0) > sum(1 for v in valid if v > 0)


def test_psd_perfect_agreement_near_zero():
    """Both rising together → minimal divergence."""
    n = 30
    asset = [100 + i * 1.0 for i in range(n)]
    pm = [0.5 + i * 0.01 for i in range(n)]
    res = signals.polymarket_sentiment_divergence(asset, pm, smoothing_window=3)
    valid = [v for v in res.score if v is not None]
    # Score magnitude should be small when both move together
    assert max(abs(v) for v in valid) < 0.5


def test_psd_score_in_range():
    n = 30
    asset = [100 + math.sin(i / 3) * 5 for i in range(n)]
    pm = [0.5 + math.cos(i / 3) * 0.05 for i in range(n)]
    res = signals.polymarket_sentiment_divergence(asset, pm)
    valid = [v for v in res.score if v is not None]
    assert all(-1.0 <= v <= 1.0 for v in valid)
