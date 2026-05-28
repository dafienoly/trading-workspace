from datetime import datetime
from decimal import Decimal
from chixiao.core.models import Bar
from chixiao.alpha.factor_calculator import FactorCalculator
from chixiao.core.interfaces import FactorProvider


def _make_bars(n: int, base_close: float = 10.0, trend: str = "up") -> list[Bar]:
    bars = []
    for i in range(n):
        if trend == "up":
            close = base_close + i * 0.1
        elif trend == "down":
            close = base_close - i * 0.1
        else:
            close = base_close
        bars.append(Bar(
            symbol="000001",
            timestamp=datetime(2024, 1, 2 + i),
            open=Decimal(str(round(close - 0.05, 2))),
            high=Decimal(str(round(close + 0.2, 2))),
            low=Decimal(str(round(close - 0.2, 2))),
            close=Decimal(str(round(close, 2))),
            volume=1000000 + i * 10000,
            amount=Decimal(str(round(close * 1000000, 2))),
        ))
    return bars


class TestFactorCalculator:
    def test_implements_factor_provider(self):
        assert issubclass(FactorCalculator, FactorProvider)

    def test_compute_factors_returns_dict(self):
        bars = _make_bars(30)
        calc = FactorCalculator()
        factors = calc.compute_factors("000001", bars)
        assert isinstance(factors, dict)
        assert "ma_5" in factors
        assert "ma_20" in factors
        assert "rsi_14" in factors
        assert "macd" in factors
        assert "bollinger_upper" in factors
        assert "bollinger_lower" in factors

    def test_ma_calculation(self):
        bars = _make_bars(30)
        calc = FactorCalculator()
        factors = calc.compute_factors("000001", bars)
        assert factors["ma_5"] > 0
        assert factors["ma_20"] > 0

    def test_rsi_range(self):
        bars = _make_bars(30)
        calc = FactorCalculator()
        factors = calc.compute_factors("000001", bars)
        assert 0 <= factors["rsi_14"] <= 100

    def test_empty_bars_returns_empty(self):
        calc = FactorCalculator()
        factors = calc.compute_factors("000001", [])
        assert factors == {}
