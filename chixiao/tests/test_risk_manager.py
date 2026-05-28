from datetime import datetime
from decimal import Decimal
from chixiao.core.models import Position, Portfolio, Signal, SignalDirection
from chixiao.portfolio.risk_manager import RiskManager


def _make_portfolio_with_positions(positions_data: list[tuple]) -> Portfolio:
    positions = []
    for sym, name, qty, cost, price in positions_data:
        positions.append(Position(symbol=sym, name=name, quantity=qty, avg_cost=Decimal(str(cost)), current_price=Decimal(str(price))))
    return Portfolio(positions=positions, cash=Decimal("50000"), timestamp=datetime.now())


class TestRiskManager:
    def test_check_position_limit_pass(self):
        mgr = RiskManager(max_position_pct=0.25)
        portfolio = _make_portfolio_with_positions([
            ("000001", "平安银行", 1000, 10.0, 11.0),
        ])
        signal = Signal(symbol="600036", direction=SignalDirection.BUY, strength=0.8,
                       timestamp=datetime.now())
        result = mgr.check_position_limit(signal, portfolio, Decimal("10000"))
        assert result.allowed is True

    def test_check_position_limit_fail(self):
        mgr = RiskManager(max_position_pct=0.10)
        portfolio = _make_portfolio_with_positions([
            ("000001", "平安银行", 1000, 10.0, 11.0),
        ])
        signal = Signal(symbol="600036", direction=SignalDirection.BUY, strength=0.8,
                       timestamp=datetime.now())
        result = mgr.check_position_limit(signal, portfolio, Decimal("15000"))
        assert result.allowed is False
        assert "仓位上限" in result.reason

    def test_check_drawdown(self):
        mgr = RiskManager(max_drawdown_pct=0.10)
        portfolio = _make_portfolio_with_positions([
            ("000001", "平安银行", 1000, 10.0, 2.0),
        ])
        result = mgr.check_drawdown(portfolio, Decimal("60000"))
        assert result.triggered is True

    def test_check_drawdown_safe(self):
        mgr = RiskManager(max_drawdown_pct=0.10)
        portfolio = _make_portfolio_with_positions([
            ("000001", "平安银行", 1000, 10.0, 10.5),
        ])
        result = mgr.check_drawdown(portfolio, Decimal("60000"))
        assert result.triggered is False
