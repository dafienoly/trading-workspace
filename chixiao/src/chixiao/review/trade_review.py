from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal


@dataclass
class TradeRecord:
    symbol: str
    name: str
    side: str
    quantity: int
    price: Decimal
    timestamp: datetime


@dataclass
class ClosedTrade:
    symbol: str
    name: str
    buy_price: Decimal
    sell_price: Decimal
    quantity: int
    buy_time: datetime
    sell_time: datetime
    pnl: Decimal
    pnl_pct: Decimal
    holding_days: int


@dataclass
class ReviewResult:
    total_trades: int = 0
    closed_trades: int = 0
    win_count: int = 0
    loss_count: int = 0
    win_rate: float = 0.0
    total_pnl: Decimal = Decimal("0")
    avg_holding_days: float = 0.0
    max_drawdown: Decimal = Decimal("0")
    profit_factor: float = 0.0
    details: list[ClosedTrade] = field(default_factory=list)


class TradeReviewAnalyzer:
    def analyze(self, trades: list[TradeRecord]) -> ReviewResult:
        if not trades:
            return ReviewResult()

        closed = self._match_trades(trades)
        if not closed:
            return ReviewResult(total_trades=len(trades))

        win_count = sum(1 for t in closed if t.pnl > 0)
        loss_count = sum(1 for t in closed if t.pnl < 0)
        total_pnl = sum(t.pnl for t in closed)
        avg_days = sum(t.holding_days for t in closed) / len(closed)

        cumulative = Decimal("0")
        peak = Decimal("0")
        max_dd = Decimal("0")
        for t in closed:
            cumulative += t.pnl
            if cumulative > peak:
                peak = cumulative
            dd = cumulative - peak
            if dd < max_dd:
                max_dd = dd

        gross_profit = sum(t.pnl for t in closed if t.pnl > 0) or Decimal("0")
        gross_loss = abs(sum(t.pnl for t in closed if t.pnl < 0)) or Decimal("1")
        pf = float(gross_profit / gross_loss)

        return ReviewResult(
            total_trades=len(trades),
            closed_trades=len(closed),
            win_count=win_count,
            loss_count=loss_count,
            win_rate=win_count / len(closed) if closed else 0.0,
            total_pnl=total_pnl,
            avg_holding_days=avg_days,
            max_drawdown=max_dd,
            profit_factor=pf,
            details=closed,
        )

    def _match_trades(self, trades: list[TradeRecord]) -> list[ClosedTrade]:
        open_positions: dict[str, list[TradeRecord]] = {}
        closed: list[ClosedTrade] = []

        sorted_trades = sorted(trades, key=lambda t: t.timestamp)

        for trade in sorted_trades:
            if trade.side.upper() == "BUY":
                if trade.symbol not in open_positions:
                    open_positions[trade.symbol] = []
                open_positions[trade.symbol].append(trade)
            elif trade.side.upper() == "SELL":
                if trade.symbol in open_positions and open_positions[trade.symbol]:
                    buy_trade = open_positions[trade.symbol].pop(0)
                    pnl = (trade.price - buy_trade.price) * trade.quantity
                    pnl_pct = ((trade.price - buy_trade.price) / buy_trade.price * 100).quantize(Decimal("0.01"))
                    holding_days = (trade.timestamp - buy_trade.timestamp).days

                    closed.append(ClosedTrade(
                        symbol=trade.symbol,
                        name=trade.name,
                        buy_price=buy_trade.price,
                        sell_price=trade.price,
                        quantity=trade.quantity,
                        buy_time=buy_trade.timestamp,
                        sell_time=trade.timestamp,
                        pnl=pnl,
                        pnl_pct=pnl_pct,
                        holding_days=holding_days,
                    ))

        return closed
