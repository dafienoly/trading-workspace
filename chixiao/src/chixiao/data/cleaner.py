from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from decimal import Decimal

import numpy as np

from chixiao.core.models import Bar


@dataclass
class OutlierResult:
    outlier_indices: list[int] = field(default_factory=list)
    z_scores: list[float] = field(default_factory=list)


class DataCleaner:
    @staticmethod
    def remove_zero_volume(bars: list[Bar]) -> list[Bar]:
        return [b for b in bars if b.volume > 0]

    @staticmethod
    def fill_missing_dates(bars: list[Bar], frequency: str = "daily") -> list[Bar]:
        if not bars:
            return []

        sorted_bars = sorted(bars, key=lambda b: b.timestamp)
        filled = [sorted_bars[0]]

        for i in range(1, len(sorted_bars)):
            prev = filled[-1]
            curr = sorted_bars[i]
            expected_next = prev.timestamp + timedelta(days=1)

            while expected_next < curr.timestamp:
                if expected_next.weekday() < 5:
                    synthetic = Bar(
                        symbol=prev.symbol,
                        timestamp=expected_next,
                        open=prev.close,
                        high=prev.close,
                        low=prev.close,
                        close=prev.close,
                        volume=0,
                        amount=Decimal("0"),
                    )
                    filled.append(synthetic)
                expected_next += timedelta(days=1)

            filled.append(curr)

        return filled

    @staticmethod
    def detect_outliers(bars: list[Bar], z_threshold: float = 3.0) -> OutlierResult:
        if len(bars) < 3:
            return OutlierResult()

        closes = np.array([float(b.close) for b in bars])
        returns = np.diff(closes) / closes[:-1]
        returns = np.append([0.0], returns)

        mean = np.mean(returns)
        std = np.std(returns)
        if std == 0:
            return OutlierResult(z_scores=returns.tolist())

        z_scores = np.abs((returns - mean) / std)
        outlier_indices = [i for i, z in enumerate(z_scores) if z > z_threshold]

        return OutlierResult(
            outlier_indices=outlier_indices,
            z_scores=z_scores.tolist(),
        )

    @classmethod
    def clean(cls, bars: list[Bar]) -> list[Bar]:
        bars = cls.remove_zero_volume(bars)
        bars = cls.fill_missing_dates(bars)
        return bars
