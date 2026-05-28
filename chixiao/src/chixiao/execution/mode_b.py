from __future__ import annotations

import uuid
from decimal import Decimal

from chixiao.core.interfaces import Executor
from chixiao.core.models import Order, OrderSide, Position


class ModeBExecutor(Executor):
    def __init__(self, broker: str = "yh", exe_path: str = ""):
        self._broker = broker
        self._exe_path = exe_path
        self._trader = None
        self._connected = False
        self._entrust_map: dict[str, str] = {}

        try:
            import easytrader
            self._trader = easytrader.use(broker)
            if exe_path:
                self._trader.prepare(exe_path=exe_path)
            self._connected = True
        except Exception:
            self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def submit_order(self, order: Order) -> str:
        if not self._connected or not self._trader:
            return f"MODEB-ERROR-{uuid.uuid4().hex[:8]}"

        order_id = f"MODEB-{uuid.uuid4().hex[:8].upper()}"

        try:
            if order.side == OrderSide.BUY:
                result = self._trader.buy(
                    security=order.symbol,
                    price=float(order.price),
                    amount=order.quantity,
                )
            else:
                result = self._trader.sell(
                    security=order.symbol,
                    price=float(order.price),
                    amount=order.quantity,
                )

            entrust_no = result.get("entrust_no", "")
            if entrust_no:
                self._entrust_map[order_id] = str(entrust_no)
        except Exception:
            pass

        return order_id

    def cancel_order(self, order_id: str) -> bool:
        if not self._connected or not self._trader:
            return False

        entrust_no = self._entrust_map.get(order_id, order_id.replace("ENTRUST-", ""))

        try:
            self._trader.cancel_entrust(entrust_no)
            self._entrust_map.pop(order_id, None)
            return True
        except Exception:
            return False

    def sync_positions(self) -> list[Position]:
        if not self._connected or not self._trader:
            return []

        try:
            raw_positions = self._trader.position
            positions = []
            for item in raw_positions:
                pos = Position(
                    symbol=str(item.get("证券代码", "")),
                    name=str(item.get("证券名称", "")),
                    quantity=int(item.get("股票余额", 0)),
                    avg_cost=Decimal(str(item.get("成本价", 0))),
                    current_price=Decimal(str(item.get("当前价", 0))),
                )
                positions.append(pos)
            return positions
        except Exception:
            return []
