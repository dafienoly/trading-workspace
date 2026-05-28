from datetime import datetime, date
from decimal import Decimal
from chixiao.core.models import (
    Bar, Signal, SignalDirection, Position, Order, OrderSide,
    Portfolio, AccountSnapshot
)


class TestBar:
    def test_create_bar(self):
        bar = Bar(
            symbol="000001",
            timestamp=datetime(2024, 1, 2, 9, 30),
            open=Decimal("10.00"),
            high=Decimal("10.50"),
            low=Decimal("9.80"),
            close=Decimal("10.20"),
            volume=1000000,
            amount=Decimal("10200000"),
        )
        assert bar.symbol == "000001"
        assert bar.close == Decimal("10.20")
        assert bar.volume == 1000000

    def test_bar_to_dict(self):
        bar = Bar(
            symbol="000001",
            timestamp=datetime(2024, 1, 2, 9, 30),
            open=Decimal("10.00"),
            high=Decimal("10.50"),
            low=Decimal("9.80"),
            close=Decimal("10.20"),
            volume=1000000,
            amount=Decimal("10200000"),
        )
        d = bar.to_dict()
        assert d["symbol"] == "000001"
        assert d["close"] == "10.20"


class TestSignal:
    def test_buy_signal(self):
        signal = Signal(
            symbol="000001",
            direction=SignalDirection.BUY,
            strength=0.85,
            timestamp=datetime(2024, 1, 2, 15, 0),
            factors={"momentum": 0.9, "value": 0.8},
        )
        assert signal.direction == SignalDirection.BUY
        assert signal.strength == 0.85

    def test_sell_signal(self):
        signal = Signal(
            symbol="000001",
            direction=SignalDirection.SELL,
            strength=0.6,
            timestamp=datetime(2024, 1, 2, 15, 0),
            factors={"momentum": 0.3},
        )
        assert signal.direction == SignalDirection.SELL


class TestPosition:
    def test_create_position(self):
        pos = Position(
            symbol="000001",
            name="平安银行",
            quantity=1000,
            avg_cost=Decimal("10.50"),
            current_price=Decimal("11.00"),
        )
        assert pos.symbol == "000001"
        assert pos.market_value == Decimal("11000.00")
        assert pos.unrealized_pnl == Decimal("500.00")
        assert pos.unrealized_pnl_pct == Decimal("4.76")

    def test_position_zero_cost(self):
        pos = Position(
            symbol="000001",
            name="平安银行",
            quantity=1000,
            avg_cost=Decimal("0"),
            current_price=Decimal("11.00"),
        )
        assert pos.unrealized_pnl_pct == Decimal("0")


class TestOrder:
    def test_buy_order(self):
        order = Order(
            symbol="000001",
            side=OrderSide.BUY,
            quantity=500,
            price=Decimal("10.50"),
            timestamp=datetime(2024, 1, 2, 9, 30),
        )
        assert order.side == OrderSide.BUY
        assert order.total_amount == Decimal("5250.00")


class TestPortfolio:
    def test_portfolio_total_value(self):
        positions = [
            Position(symbol="000001", name="平安银行", quantity=1000, avg_cost=Decimal("10.50"), current_price=Decimal("11.00")),
            Position(symbol="600036", name="招商银行", quantity=500, avg_cost=Decimal("35.00"), current_price=Decimal("36.00")),
        ]
        portfolio = Portfolio(
            positions=positions,
            cash=Decimal("50000"),
            timestamp=datetime(2024, 1, 2, 15, 0),
        )
        assert portfolio.total_value == Decimal("79000.00")
        assert len(portfolio.positions) == 2

    def test_portfolio_empty(self):
        portfolio = Portfolio(
            positions=[],
            cash=Decimal("100000"),
            timestamp=datetime(2024, 1, 2, 15, 0),
        )
        assert portfolio.total_value == Decimal("100000")


class TestAccountSnapshot:
    def test_snapshot(self):
        positions = [
            Position(symbol="000001", name="平安银行", quantity=1000, avg_cost=Decimal("10.50"), current_price=Decimal("11.00")),
        ]
        portfolio = Portfolio(
            positions=positions,
            cash=Decimal("50000"),
            timestamp=datetime(2024, 1, 2, 15, 0),
        )
        snapshot = AccountSnapshot(
            account_id="manual_001",
            broker="手动同步",
            portfolio=portfolio,
            date=date(2024, 1, 2),
        )
        assert snapshot.account_id == "manual_001"
        assert snapshot.total_assets == Decimal("61000.00")
