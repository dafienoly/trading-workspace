from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal
from typing import Optional

from chixiao.core.models import Bar, Order, Position


class DataAdapter(ABC):
    @abstractmethod
    def get_bars(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        frequency: str = "daily",
    ) -> list[Bar]:
        ...

    @abstractmethod
    def get_latest_price(self, symbol: str) -> Optional[Decimal]:
        ...

    @abstractmethod
    def get_symbols(self) -> list[str]:
        ...


class Executor(ABC):
    @abstractmethod
    def submit_order(self, order: Order) -> str:
        ...

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        ...

    @abstractmethod
    def sync_positions(self) -> list[Position]:
        ...


class FactorProvider(ABC):
    @abstractmethod
    def compute_factors(self, symbol: str, bars: list[Bar]) -> dict[str, float]:
        ...
