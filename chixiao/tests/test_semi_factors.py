from datetime import datetime
from decimal import Decimal
from chixiao.core.models import Bar
from chixiao.alpha.semi_factors import SemiFactorLib


def _make_bar(close: float, volume: int = 1000000, amount: float = 0) -> Bar:
    return Bar(
        symbol="002415",
        timestamp=datetime(2024, 1, 15),
        open=Decimal(str(close - 0.1)),
        high=Decimal(str(close + 0.2)),
        low=Decimal(str(close - 0.2)),
        close=Decimal(str(close)),
        volume=volume,
        amount=Decimal(str(amount if amount else close * volume)),
    )


class TestSemiFactorLib:
    def test_compute_semi_factors(self):
        bars = [_make_bar(28.0 + i * 0.5) for i in range(30)]
        lib = SemiFactorLib()
        factors = lib.compute(bars)
        assert "semi_turnover_rate" in factors
        assert "semi_price_momentum_5d" in factors
        assert "semi_volatility_rank" in factors

    def test_turnover_rate(self):
        bars = [_make_bar(28.0, volume=2000000) for _ in range(5)]
        lib = SemiFactorLib()
        factors = lib.compute(bars)
        assert factors["semi_turnover_rate"] > 0

    def test_empty_bars(self):
        lib = SemiFactorLib()
        factors = lib.compute([])
        assert factors == {}

    def test_is_semi_conductor(self):
        lib = SemiFactorLib()
        assert lib.is_semi_conductor("002415") is True
        assert lib.is_semi_conductor("000001") is False
