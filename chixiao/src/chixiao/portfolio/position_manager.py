from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from chixiao.core.models import Position, Portfolio


class PositionManager:
    def __init__(self):
        self._positions: dict[str, Position] = {}
        self._cash: Decimal = Decimal("0")

    def update_position(
        self, symbol: str, name: str, quantity: int, price: Decimal
    ) -> None:
        if symbol in self._positions:
            existing = self._positions[symbol]
            total_cost = existing.avg_cost * existing.quantity + price * quantity
            new_quantity = existing.quantity + quantity
            new_avg_cost = (total_cost / new_quantity).quantize(Decimal("0.01")) if new_quantity > 0 else Decimal("0")
            self._positions[symbol] = Position(
                symbol=symbol,
                name=name,
                quantity=new_quantity,
                avg_cost=new_avg_cost,
                current_price=price,
            )
        else:
            self._positions[symbol] = Position(
                symbol=symbol,
                name=name,
                quantity=quantity,
                avg_cost=price,
                current_price=price,
            )

    def reduce_position(self, symbol: str, quantity: int) -> None:
        if symbol not in self._positions:
            return
        existing = self._positions[symbol]
        new_quantity = existing.quantity - quantity
        if new_quantity <= 0:
            self.remove_position(symbol)
        else:
            self._positions[symbol] = Position(
                symbol=symbol,
                name=existing.name,
                quantity=new_quantity,
                avg_cost=existing.avg_cost,
                current_price=existing.current_price,
            )

    def remove_position(self, symbol: str) -> None:
        self._positions.pop(symbol, None)

    def get_position(self, symbol: str) -> Optional[Position]:
        return self._positions.get(symbol)

    def set_cash(self, amount: Decimal) -> None:
        self._cash = amount

    def get_portfolio(self) -> Portfolio:
        positions = list(self._positions.values())
        return Portfolio(
            positions=positions,
            cash=self._cash,
            timestamp=datetime.now(),
        )

    def get_position_weights(self) -> dict[str, float]:
        portfolio = self.get_portfolio()
        total = float(portfolio.total_value)
        if total == 0:
            return {}
        return {
            pos.symbol: float(pos.market_value) / total
            for pos in portfolio.positions
        }
