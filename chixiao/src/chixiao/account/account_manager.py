from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from chixiao.core.models import AccountSnapshot, Portfolio, Position


@dataclass
class AccountInfo:
    account_id: str
    broker: str
    mode: str
    last_sync: Optional[str] = None


class AccountManager:
    def __init__(self):
        self._accounts: dict[str, AccountInfo] = {}
        self._snapshots: dict[str, AccountSnapshot] = {}

    def register_account(self, account_id: str, broker: str, mode: str) -> None:
        self._accounts[account_id] = AccountInfo(
            account_id=account_id,
            broker=broker,
            mode=mode,
        )

    def list_accounts(self) -> list[AccountInfo]:
        return list(self._accounts.values())

    def update_snapshot(self, account_id: str, snapshot: AccountSnapshot) -> None:
        self._snapshots[account_id] = snapshot
        if account_id in self._accounts:
            self._accounts[account_id].last_sync = snapshot.date.isoformat()

    def get_snapshot(self, account_id: str) -> Optional[AccountSnapshot]:
        return self._snapshots.get(account_id)

    def get_aggregated_portfolio(self) -> Optional[Portfolio]:
        if not self._snapshots:
            return None

        all_positions: dict[str, Position] = {}
        total_cash = Decimal("0")

        for snapshot in self._snapshots.values():
            total_cash += snapshot.portfolio.cash
            for pos in snapshot.portfolio.positions:
                if pos.symbol in all_positions:
                    existing = all_positions[pos.symbol]
                    total_cost = existing.avg_cost * existing.quantity + pos.avg_cost * pos.quantity
                    new_qty = existing.quantity + pos.quantity
                    new_avg = (total_cost / new_qty).quantize(Decimal("0.01")) if new_qty > 0 else Decimal("0")
                    all_positions[pos.symbol] = Position(
                        symbol=pos.symbol,
                        name=pos.name or existing.name,
                        quantity=new_qty,
                        avg_cost=new_avg,
                        current_price=pos.current_price,
                    )
                else:
                    all_positions[pos.symbol] = pos

        return Portfolio(
            positions=list(all_positions.values()),
            cash=total_cash,
            timestamp=datetime.now(),
        )
