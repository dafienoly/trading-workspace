from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from chixiao.core.models import Portfolio, Signal


@dataclass
class RiskCheckResult:
    allowed: bool
    reason: str = ""


@dataclass
class DrawdownCheckResult:
    triggered: bool
    drawdown_pct: float = 0.0
    reason: str = ""


class RiskManager:
    def __init__(
        self,
        max_position_pct: float = 0.25,
        max_single_loss_pct: float = 0.02,
        max_drawdown_pct: float = 0.10,
    ):
        self._max_position_pct = max_position_pct
        self._max_single_loss_pct = max_single_loss_pct
        self._max_drawdown_pct = max_drawdown_pct

    def check_position_limit(
        self, signal: Signal, portfolio: Portfolio, order_amount: Decimal
    ) -> RiskCheckResult:
        total_value = portfolio.total_value
        if total_value == 0:
            return RiskCheckResult(allowed=True)

        position_pct = float(order_amount) / float(total_value)
        if position_pct > self._max_position_pct:
            return RiskCheckResult(
                allowed=False,
                reason=f"仓位上限: 单笔仓位占比 {position_pct:.1%} 超过限制 {self._max_position_pct:.1%}",
            )

        return RiskCheckResult(allowed=True)

    def check_drawdown(
        self, portfolio: Portfolio, peak_value: Decimal
    ) -> DrawdownCheckResult:
        if peak_value == 0:
            return DrawdownCheckResult(triggered=False)

        current_value = portfolio.total_value
        drawdown_pct = float(peak_value - current_value) / float(peak_value)

        if drawdown_pct > self._max_drawdown_pct:
            return DrawdownCheckResult(
                triggered=True,
                drawdown_pct=drawdown_pct,
                reason=f"回撤 {drawdown_pct:.1%} 超过限制 {self._max_drawdown_pct:.1%}",
            )

        return DrawdownCheckResult(triggered=False, drawdown_pct=drawdown_pct)
