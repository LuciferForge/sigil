"""Core types: OHLCV bar and OHLCVSeries.

OHLCV is the canonical input shape for every indicator. All indicators
accept either a list[OHLCV], an OHLCVSeries (lightweight wrapper), or
a pandas DataFrame with columns [open, high, low, close, volume, timestamp].
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence


@dataclass(frozen=True)
class OHLCV:
    timestamp: int       # unix ms
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    metadata: dict = field(default_factory=dict)


class OHLCVSeries:
    """Lightweight wrapper around a list of OHLCV bars.

    Provides:
      - Indexed access (s[0], s[-1])
      - Iteration
      - Per-field views (s.close → list[float])
      - Length
    """

    def __init__(self, bars: Sequence[OHLCV]):
        self.bars: list[OHLCV] = list(bars)

    def __len__(self) -> int:
        return len(self.bars)

    def __iter__(self):
        return iter(self.bars)

    def __getitem__(self, idx):
        return self.bars[idx]

    @property
    def opens(self) -> list[float]:
        return [b.open for b in self.bars]

    @property
    def highs(self) -> list[float]:
        return [b.high for b in self.bars]

    @property
    def lows(self) -> list[float]:
        return [b.low for b in self.bars]

    @property
    def closes(self) -> list[float]:
        return [b.close for b in self.bars]

    @property
    def volumes(self) -> list[float]:
        return [b.volume for b in self.bars]

    @property
    def timestamps(self) -> list[int]:
        return [b.timestamp for b in self.bars]

    @classmethod
    def from_dicts(cls, rows: Iterable[dict[str, Any]]) -> "OHLCVSeries":
        return cls([
            OHLCV(
                timestamp=int(r["timestamp"]),
                open=float(r["open"]),
                high=float(r["high"]),
                low=float(r["low"]),
                close=float(r["close"]),
                volume=float(r.get("volume", 0.0)),
            )
            for r in rows
        ])

    @classmethod
    def from_pandas(cls, df) -> "OHLCVSeries":
        """Build from a pandas DataFrame with [timestamp, open, high, low, close, volume] cols."""
        return cls([
            OHLCV(
                timestamp=int(row["timestamp"]),
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=float(row.get("volume", 0.0)),
            )
            for _, row in df.iterrows()
        ])

    def to_pandas(self):
        """Return as pandas DataFrame. Requires pandas."""
        import pandas as pd

        return pd.DataFrame(
            [
                {
                    "timestamp": b.timestamp,
                    "open": b.open,
                    "high": b.high,
                    "low": b.low,
                    "close": b.close,
                    "volume": b.volume,
                }
                for b in self.bars
            ]
        )


def to_series(data) -> OHLCVSeries:
    """Coerce input to OHLCVSeries."""
    if isinstance(data, OHLCVSeries):
        return data
    if isinstance(data, list) and data and isinstance(data[0], OHLCV):
        return OHLCVSeries(data)
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return OHLCVSeries.from_dicts(data)
    # Try pandas DataFrame
    try:
        import pandas as pd
        if isinstance(data, pd.DataFrame):
            return OHLCVSeries.from_pandas(data)
    except ImportError:
        pass
    raise TypeError(f"Cannot coerce {type(data)} to OHLCVSeries")
