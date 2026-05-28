from __future__ import annotations

import csv
import uuid
from decimal import Decimal
from pathlib import Path

from chixiao.core.interfaces import Executor
from chixiao.core.models import Order, Position


class ModeAExecutor(Executor):
    def __init__(self, csv_dir: str = "data/positions"):
        self._csv_dir = Path(csv_dir)
        self._pending_orders: dict[str, Order] = {}

    def sync_positions(self) -> list[Position]:
        positions_file = self._csv_dir / "positions.csv"
        if not positions_file.exists():
            return []

        positions = []
        with open(positions_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    pos = Position(
                        symbol=row["symbol"],
                        name=row.get("name", ""),
                        quantity=int(row["quantity"]),
                        avg_cost=Decimal(row["avg_cost"]),
                        current_price=Decimal(row["current_price"]),
                    )
                    positions.append(pos)
                except (KeyError, ValueError):
                    continue

        return positions

    def submit_order(self, order: Order) -> str:
        order_id = f"MODEA-{uuid.uuid4().hex[:8].upper()}"
        self._pending_orders[order_id] = order
        return order_id

    def cancel_order(self, order_id: str) -> bool:
        if order_id in self._pending_orders:
            del self._pending_orders[order_id]
            return True
        return False

    def get_pending_orders(self) -> dict[str, Order]:
        return dict(self._pending_orders)

    def export_orders(self) -> None:
        self._csv_dir.mkdir(parents=True, exist_ok=True)
        orders_file = self._csv_dir / "pending_orders.csv"

        with open(orders_file, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["order_id", "symbol", "side", "quantity", "price", "timestamp"])
            for order_id, order in self._pending_orders.items():
                writer.writerow([
                    order_id,
                    order.symbol,
                    order.side.value,
                    order.quantity,
                    str(order.price),
                    order.timestamp.isoformat(),
                ])
