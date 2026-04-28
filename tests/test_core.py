"""Core type tests."""
from sigil.core import OHLCV, OHLCVSeries, to_series


def test_ohlcv_construction():
    b = OHLCV(timestamp=1, open=10.0, high=11.0, low=9.5, close=10.5, volume=100.0)
    assert b.timestamp == 1
    assert b.close == 10.5


def test_series_views():
    s = OHLCVSeries([
        OHLCV(timestamp=i, open=i, high=i + 1, low=i - 1, close=i + 0.5, volume=1.0)
        for i in range(5)
    ])
    assert s.closes == [0.5, 1.5, 2.5, 3.5, 4.5]
    assert s.opens == [0, 1, 2, 3, 4]
    assert s.highs == [1, 2, 3, 4, 5]
    assert len(s) == 5
    assert s[0].close == 0.5
    assert s[-1].close == 4.5


def test_from_dicts():
    rows = [
        {"timestamp": 1, "open": 10, "high": 11, "low": 9.5, "close": 10.5, "volume": 100},
        {"timestamp": 2, "open": 10.5, "high": 11.5, "low": 10, "close": 11, "volume": 90},
    ]
    s = OHLCVSeries.from_dicts(rows)
    assert len(s) == 2
    assert s[0].timestamp == 1
    assert s[1].close == 11.0


def test_to_series_passes_through_OHLCVSeries():
    s = OHLCVSeries([])
    assert to_series(s) is s


def test_to_series_from_dict_list():
    rows = [
        {"timestamp": 1, "open": 10, "high": 11, "low": 9.5, "close": 10.5, "volume": 100},
    ]
    s = to_series(rows)
    assert isinstance(s, OHLCVSeries)
    assert len(s) == 1
