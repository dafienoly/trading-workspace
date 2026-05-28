from datetime import datetime
from decimal import Decimal
from chixiao.core.models import Bar, Signal, SignalDirection
from chixiao.alpha.alpha_model import AlphaModel
from chixiao.alpha.factor_calculator import FactorCalculator


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


class TestAlphaModel:
    def test_generate_signal_up_trend(self):
        bars = _make_bars(30, trend="up")
        model = AlphaModel(FactorCalculator())
        signal = model.generate_signal("000001", bars)
        assert signal is not None
        assert signal.symbol == "000001"
        assert signal.direction in [SignalDirection.BUY, SignalDirection.HOLD, SignalDirection.SELL]

    def test_generate_signal_down_trend(self):
        bars = _make_bars(30, trend="down")
        model = AlphaModel(FactorCalculator())
        signal = model.generate_signal("000001", bars)
        assert signal is not None

    def test_generate_signal_empty_bars(self):
        model = AlphaModel(FactorCalculator())
        signal = model.generate_signal("000001", [])
        assert signal is None

    def test_signal_strength_range(self):
        bars = _make_bars(30, trend="up")
        model = AlphaModel(FactorCalculator())
        signal = model.generate_signal("000001", bars)
        assert 0.0 <= signal.strength <= 1.0

    def test_generate_signals_multiple(self):
        up_bars = _make_bars(30, trend="up")
        down_bars = _make_bars(30, trend="down")
        model = AlphaModel(FactorCalculator())
        signals = model.generate_signals({
            "000001": up_bars,
            "000002": down_bars,
        })
        assert len(signals) == 2
        assert all(isinstance(s, Signal) for s in signals)
