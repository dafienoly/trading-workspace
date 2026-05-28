from __future__ import annotations

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, computed_field


class SignalDirection(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class Bar(BaseModel):
    symbol: str
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    amount: Decimal

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "open": str(self.open),
            "high": str(self.high),
            "low": str(self.low),
            "close": str(self.close),
            "volume": self.volume,
            "amount": str(self.amount),
        }


class Signal(BaseModel):
    symbol: str
    direction: SignalDirection
    strength: float
    timestamp: datetime
    factors: dict[str, float] = {}


class Position(BaseModel):
    symbol: str
    name: str = ""
    quantity: int
    avg_cost: Decimal
    current_price: Decimal

    @computed_field
    @property
    def market_value(self) -> Decimal:
        return self.current_price * self.quantity

    @computed_field
    @property
    def unrealized_pnl(self) -> Decimal:
        return (self.current_price - self.avg_cost) * self.quantity

    @computed_field
    @property
    def unrealized_pnl_pct(self) -> Decimal:
        if self.avg_cost == 0:
            return Decimal("0")
        return ((self.current_price - self.avg_cost) / self.avg_cost * 100).quantize(
            Decimal("0.01")
        )


class Order(BaseModel):
    symbol: str
    side: OrderSide
    quantity: int
    price: Decimal
    timestamp: datetime
    filled_quantity: int = 0
    filled_price: Optional[Decimal] = None

    @computed_field
    @property
    def total_amount(self) -> Decimal:
        return self.price * self.quantity


class Portfolio(BaseModel):
    positions: list[Position]
    cash: Decimal
    timestamp: datetime

    @computed_field
    @property
    def total_value(self) -> Decimal:
        positions_value = sum(p.market_value for p in self.positions)
        return self.cash + positions_value


class AccountSnapshot(BaseModel):
    account_id: str
    broker: str
    portfolio: Portfolio
    date: date

    @computed_field
    @property
    def total_assets(self) -> Decimal:
        return self.portfolio.total_value
