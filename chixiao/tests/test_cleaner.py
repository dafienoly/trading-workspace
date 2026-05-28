from datetime import datetime
from decimal import Decimal
from chixiao.core.models import Bar
from chixiao.data.cleaner import DataCleaner


def _make_bar(symbol: str, ts: datetime, close: str, volume: int = 1000) -> Bar:
    return Bar(
        symbol=symbol,
        timestamp=ts,
        open=Decimal(close),
        high=Decimal(close),
        low=Decimal(close),
        close=Decimal(close),
        volume=volume,
        amount=Decimal(close) * volume,
    )


class TestDataCleaner:
    def test_remove_zero_volume_bars(self):
        bars = [
            _make_bar("000001", datetime(2024, 1, 2), "10.0", 1000),
            _make_bar("000001", datetime(2024, 1, 3), "10.5", 0),
            _make_bar("000001", datetime(2024, 1, 4), "10.8", 2000),
        ]
        result = DataCleaner.remove_zero_volume(bars)
        assert len(result) == 2
        assert result[0].volume == 1000
        assert result[1].volume == 2000

    def test_fill_missing_dates(self):
        bars = [
            _make_bar("000001", datetime(2024, 1, 2), "10.0"),
            _make_bar("000001", datetime(2024, 1, 4), "10.8"),
        ]
        result = DataCleaner.fill_missing_dates(bars, "daily")
        assert len(result) == 3
        assert result[1].close == Decimal("10.0")
        assert result[1].volume == 0

    def test_detect_outliers(self):
        bars = [
            _make_bar("000001", datetime(2024, 1, 2 + i), "10.0")
            for i in range(10)
        ]
        bars.append(_make_bar("000001", datetime(2024, 1, 12), "100.0"))
        result = DataCleaner.detect_outliers(bars, z_threshold=3.0)
        assert len(result.outlier_indices) == 1
        assert 10 in result.outlier_indices

    def test_clean_pipeline(self):
        bars = [
            _make_bar("000001", datetime(2024, 1, 2), "10.0", 0),
            _make_bar("000001", datetime(2024, 1, 3), "10.5", 1000),
            _make_bar("000001", datetime(2024, 1, 5), "10.8", 2000),
        ]
        result = DataCleaner.clean(bars)
        assert len(result) >= 2
        original_bars = [b for b in result if b.volume > 0]
        assert len(original_bars) >= 2
