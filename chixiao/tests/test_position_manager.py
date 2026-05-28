from datetime import datetime
from decimal import Decimal
from chixiao.core.models import Position, Portfolio
from chixiao.portfolio.position_manager import PositionManager


class TestPositionManager:
    def test_update_position_new(self):
        mgr = PositionManager()
        mgr.update_position("000001", "平安银行", 1000, Decimal("10.50"))
        pos = mgr.get_position("000001")
        assert pos is not None
        assert pos.quantity == 1000
        assert pos.avg_cost == Decimal("10.50")

    def test_update_position_add(self):
        mgr = PositionManager()
        mgr.update_position("000001", "平安银行", 1000, Decimal("10.00"))
        mgr.update_position("000001", "平安银行", 500, Decimal("11.00"))
        pos = mgr.get_position("000001")
        assert pos.quantity == 1500
        assert pos.avg_cost == Decimal("10.33")

    def test_update_position_reduce(self):
        mgr = PositionManager()
        mgr.update_position("000001", "平安银行", 1000, Decimal("10.00"))
        mgr.reduce_position("000001", 300)
        pos = mgr.get_position("000001")
        assert pos.quantity == 700

    def test_remove_position(self):
        mgr = PositionManager()
        mgr.update_position("000001", "平安银行", 1000, Decimal("10.00"))
        mgr.remove_position("000001")
        assert mgr.get_position("000001") is None

    def test_get_portfolio(self):
        mgr = PositionManager()
        mgr.update_position("000001", "平安银行", 1000, Decimal("10.00"))
        mgr.update_position("600036", "招商银行", 500, Decimal("35.00"))
        mgr.set_cash(Decimal("50000"))
        portfolio = mgr.get_portfolio()
        assert len(portfolio.positions) == 2
        assert portfolio.cash == Decimal("50000")

    def test_position_weight(self):
        mgr = PositionManager()
        mgr.update_position("000001", "平安银行", 1000, Decimal("10.00"))
        mgr.update_position("600036", "招商银行", 500, Decimal("35.00"))
        mgr.set_cash(Decimal("0"))
        weights = mgr.get_position_weights()
        assert "000001" in weights
        assert "600036" in weights
        total = sum(weights.values())
        assert abs(total - 1.0) < 0.01
