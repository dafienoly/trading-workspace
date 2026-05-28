from datetime import datetime
from decimal import Decimal
from chixiao.execution.mode_a import ModeAExecutor
from chixiao.core.models import Order, OrderSide, Position
from chixiao.core.interfaces import Executor


class TestModeAExecutor:
    def test_implements_executor(self):
        assert issubclass(ModeAExecutor, Executor)

    def test_sync_positions_from_csv(self, tmp_path):
        csv_content = "symbol,name,quantity,avg_cost,current_price\n000001,平安银行,1000,10.50,11.00\n600036,招商银行,500,35.00,36.00\n"
        csv_file = tmp_path / "positions.csv"
        csv_file.write_text(csv_content, encoding="utf-8")

        executor = ModeAExecutor(csv_dir=str(tmp_path))
        positions = executor.sync_positions()

        assert len(positions) == 2
        assert positions[0].symbol == "000001"
        assert positions[0].quantity == 1000
        assert positions[0].avg_cost == Decimal("10.50")
        assert positions[1].symbol == "600036"

    def test_sync_positions_empty_csv(self, tmp_path):
        csv_content = "symbol,name,quantity,avg_cost,current_price\n"
        csv_file = tmp_path / "positions.csv"
        csv_file.write_text(csv_content, encoding="utf-8")

        executor = ModeAExecutor(csv_dir=str(tmp_path))
        positions = executor.sync_positions()

        assert len(positions) == 0

    def test_sync_positions_no_file(self, tmp_path):
        executor = ModeAExecutor(csv_dir=str(tmp_path))
        positions = executor.sync_positions()

        assert len(positions) == 0

    def test_submit_order_creates_record(self, tmp_path):
        executor = ModeAExecutor(csv_dir=str(tmp_path))
        order = Order(
            symbol="000001",
            side=OrderSide.BUY,
            quantity=500,
            price=Decimal("10.50"),
            timestamp=datetime.now(),
        )
        order_id = executor.submit_order(order)
        assert order_id.startswith("MODEA-")
        pending = executor.get_pending_orders()
        assert len(pending) == 1

    def test_cancel_order(self, tmp_path):
        executor = ModeAExecutor(csv_dir=str(tmp_path))
        order = Order(
            symbol="000001",
            side=OrderSide.BUY,
            quantity=500,
            price=Decimal("10.50"),
            timestamp=datetime.now(),
        )
        order_id = executor.submit_order(order)
        result = executor.cancel_order(order_id)
        assert result is True
        pending = executor.get_pending_orders()
        assert len(pending) == 0

    def test_cancel_nonexistent_order(self, tmp_path):
        executor = ModeAExecutor(csv_dir=str(tmp_path))
        result = executor.cancel_order("MODEA-999")
        assert result is False

    def test_export_orders_to_csv(self, tmp_path):
        executor = ModeAExecutor(csv_dir=str(tmp_path))
        order = Order(
            symbol="000001",
            side=OrderSide.BUY,
            quantity=500,
            price=Decimal("10.50"),
            timestamp=datetime(2024, 1, 2, 9, 30),
        )
        executor.submit_order(order)
        executor.export_orders()

        orders_file = tmp_path / "pending_orders.csv"
        assert orders_file.exists()
