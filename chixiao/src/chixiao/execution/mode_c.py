from __future__ import annotations

import uuid
from decimal import Decimal

from chixiao.core.interfaces import Executor
from chixiao.core.models import Order, OrderSide, Position


class ModeCExecutor(Executor):
    def __init__(self, path: str = "", session_id: int = 123456, account_id: str = ""):
        self._path = path
        self._session_id = session_id
        self._account_id = account_id
        self._trader = None
        self._account = None
        self._connected = False
        self._order_map: dict[str, int] = {}

        try:
            from xtquant.xttrader import XtQuantTrader
            from xtquant.xttype import StockAccount

            self._trader = XtQuantTrader(path, session_id)
            self._account = StockAccount(account_id) if account_id else None
            self._trader.start()
            self._connected = True
        except ImportError:
            self._connected = False
        except Exception:
            self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def submit_order(self, order: Order) -> str:
        if not self._connected or not self._trader or not self._account:
            return f"MODEC-ERROR-{uuid.uuid4().hex[:8]}"

        order_id = f"MODEC-{uuid.uuid4().hex[:8].upper()}"

        try:
            from xtquant.xttype import StockOrder

            xt_order = StockOrder()
            xt_order.account = self._account
            xt_order.stock_code = order.symbol
            xt_order.price = float(order.price)
            xt_order.volume = order.quantity

            if order.side == OrderSide.BUY:
                xt_order.order_type = 11
            else:
                xt_order.order_type = 12

            result = self._trader.order_stock(self._account, xt_order)
            if hasattr(result, "order_id"):
                self._order_map[order_id] = result.order_id
        except Exception:
            pass

        return order_id

    def cancel_order(self, order_id: str) -> bool:
        if not self._connected or not self._trader or not self._account:
            return False

        xt_order_id = self._order_map.get(order_id)
        if xt_order_id is None:
            return False

        try:
            self._trader.cancel_order_stock(self._account, xt_order_id)
            self._order_map.pop(order_id, None)
            return True
        except Exception:
            return False

    def sync_positions(self) -> list[Position]:
        if not self._connected or not self._trader or not self._account:
            return []

        try:
            raw_positions = self._trader.query_stock_positions(self._account)
            positions = []
            for item in raw_positions:
                pos = Position(
                    symbol=getattr(item, "stock_code", ""),
                    name="",
                    quantity=getattr(item, "volume", 0),
                    avg_cost=Decimal(str(round(getattr(item, "avg_price", 0), 2))),
                    current_price=Decimal(str(round(
                        getattr(item, "market_value", 0) / max(getattr(item, "volume", 1), 1), 2
                    ))),
                )
                positions.append(pos)
            return positions
        except Exception:
            return []
