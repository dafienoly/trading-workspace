# 赤霄量化交易系统 — 第三阶段(半自动执行与交易复盘)实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现策略与交易执行的半自动连接(easytrader方案)，引入AI交易复盘点评功能，实现跨券商账户聚合管理。

**Architecture:** ModeBExecutor通过easytrader库对接券商客户端，实现一键下单。交易复盘模块读取历史交易记录，调用LLM生成操作评价和改进建议。AccountManager维护统一的账户和持仓视图，支持跨券商数据聚合。

**Tech Stack:** Python 3.11+, easytrader (模拟操作券商客户端), 新增于前两阶段基础之上

---

## 文件结构增量

```
chixiao/
├── src/chixiao/
│   ├── execution/
│   │   └── mode_b.py            # easytrader执行器 (新增)
│   ├── account/
│   │   ├── __init__.py
│   │   └── account_manager.py   # 账户聚合管理 (新增)
│   ├── review/
│   │   ├── __init__.py
│   │   ├── trade_review.py      # 交易复盘分析 (新增)
│   │   └── llm_reviewer.py      # LLM交易点评 (新增)
│   └── api/
│       └── main.py              # 扩展API端点
├── dashboard/
│   └── app.py                   # 升级仪表盘
└── tests/
    ├── test_mode_b.py
    ├── test_account_manager.py
    ├── test_trade_review.py
    └── test_llm_reviewer.py
```

---

### Task 1: easytrader执行器 (Mode B)

**Files:**
- Create: `chixiao/src/chixiao/execution/mode_b.py`
- Create: `chixiao/tests/test_mode_b.py`

- [ ] **Step 1: 编写Mode B执行器测试**

```python
from datetime import datetime
from decimal import Decimal
from unittest.mock import patch, MagicMock
from chixiao.execution.mode_b import ModeBExecutor
from chixiao.core.models import Order, OrderSide, Position
from chixiao.core.interfaces import Executor


class TestModeBExecutor:
    def test_implements_executor(self):
        assert issubclass(ModeBExecutor, Executor)

    @patch("chixiao.execution.mode_b.easytrader")
    def test_connect(self, mock_easytrader):
        mock_trader = MagicMock()
        mock_easytrader.use.return_value = mock_trader
        executor = ModeBExecutor(broker="yh", exe_path="/path/to/client")
        assert executor.is_connected()

    @patch("chixiao.execution.mode_b.easytrader")
    def test_submit_order_buy(self, mock_easytrader):
        mock_trader = MagicMock()
        mock_easytrader.use.return_value = mock_trader
        mock_trader.buy.return_value = {"entrust_no": "12345"}

        executor = ModeBExecutor(broker="yh", exe_path="/path/to/client")
        order = Order(
            symbol="000001",
            side=OrderSide.BUY,
            quantity=500,
            price=Decimal("10.50"),
            timestamp=datetime.now(),
        )
        order_id = executor.submit_order(order)
        assert order_id.startswith("MODEB-")
        mock_trader.buy.assert_called_once()

    @patch("chixiao.execution.mode_b.easytrader")
    def test_submit_order_sell(self, mock_easytrader):
        mock_trader = MagicMock()
        mock_easytrader.use.return_value = mock_trader
        mock_trader.sell.return_value = {"entrust_no": "67890"}

        executor = ModeBExecutor(broker="yh", exe_path="/path/to/client")
        order = Order(
            symbol="000001",
            side=OrderSide.SELL,
            quantity=500,
            price=Decimal("10.50"),
            timestamp=datetime.now(),
        )
        order_id = executor.submit_order(order)
        assert order_id.startswith("MODEB-")
        mock_trader.sell.assert_called_once()

    @patch("chixiao.execution.mode_b.easytrader")
    def test_cancel_order(self, mock_easytrader):
        mock_trader = MagicMock()
        mock_easytrader.use.return_value = mock_trader
        mock_trader.cancel_entrust.return_value = {"message": "success"}

        executor = ModeBExecutor(broker="yh", exe_path="/path/to/client")
        result = executor.cancel_order("ENTRUST-12345")
        assert result is True

    @patch("chixiao.execution.mode_b.easytrader")
    def test_sync_positions(self, mock_easytrader):
        mock_trader = MagicMock()
        mock_easytrader.use.return_value = mock_trader
        mock_trader.position.return_value = [
            {"证券代码": "000001", "证券名称": "平安银行", "股票余额": 1000, "成本价": 10.50, "当前价": 11.00},
            {"证券代码": "600036", "证券名称": "招商银行", "股票余额": 500, "成本价": 35.00, "当前价": 36.00},
        ]

        executor = ModeBExecutor(broker="yh", exe_path="/path/to/client")
        positions = executor.sync_positions()
        assert len(positions) == 2
        assert positions[0].symbol == "000001"

    @patch("chixiao.execution.mode_b.easytrader")
    def test_not_connected_fallback(self, mock_easytrader):
        mock_easytrader.use.side_effect = Exception("连接失败")
        executor = ModeBExecutor(broker="yh", exe_path="/path/to/client")
        assert not executor.is_connected()
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd /workspace/chixiao && pytest tests/test_mode_b.py -v`
Expected: FAIL

- [ ] **Step 3: 实现Mode B执行器**

```python
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

import easytrader

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
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd /workspace/chixiao && pytest tests/test_mode_b.py -v`
Expected: 全部 PASS

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: add Mode B executor with easytrader integration"
```

---

### Task 2: 账户聚合管理

**Files:**
- Create: `chixiao/src/chixiao/account/__init__.py`
- Create: `chixiao/src/chixiao/account/account_manager.py`
- Create: `chixiao/tests/test_account_manager.py`

- [ ] **Step 1: 编写账户管理器测试**

```python
from datetime import datetime, date
from decimal import Decimal
from chixiao.account.account_manager import AccountManager, AccountInfo
from chixiao.core.models import Position, Portfolio, AccountSnapshot


class TestAccountManager:
    def test_register_account(self):
        mgr = AccountManager()
        mgr.register_account("manual_001", "手动同步", "mode_a")
        accounts = mgr.list_accounts()
        assert len(accounts) == 1
        assert accounts[0].account_id == "manual_001"

    def test_register_multiple_accounts(self):
        mgr = AccountManager()
        mgr.register_account("manual_001", "手动同步", "mode_a")
        mgr.register_account("broker_001", "国泰海通", "mode_b")
        accounts = mgr.list_accounts()
        assert len(accounts) == 2

    def test_get_aggregated_portfolio(self):
        mgr = AccountManager()
        mgr.register_account("acc_1", "券商A", "mode_a")
        mgr.register_account("acc_2", "券商B", "mode_a")

        snapshot_1 = AccountSnapshot(
            account_id="acc_1",
            broker="券商A",
            portfolio=Portfolio(
                positions=[Position("000001", "平安银行", 1000, Decimal("10.00"), Decimal("11.00"))],
                cash=Decimal("50000"),
                timestamp=datetime.now(),
            ),
            date=date.today(),
        )
        snapshot_2 = AccountSnapshot(
            account_id="acc_2",
            broker="券商B",
            portfolio=Portfolio(
                positions=[Position("000001", "平安银行", 500, Decimal("10.50"), Decimal("11.00"))],
                cash=Decimal("30000"),
                timestamp=datetime.now(),
            ),
            date=date.today(),
        )

        mgr.update_snapshot("acc_1", snapshot_1)
        mgr.update_snapshot("acc_2", snapshot_2)

        agg = mgr.get_aggregated_portfolio()
        assert agg is not None
        assert agg.cash == Decimal("80000")
        pos_000001 = next(p for p in agg.positions if p.symbol == "000001")
        assert pos_000001.quantity == 1500

    def test_get_account_snapshot(self):
        mgr = AccountManager()
        mgr.register_account("acc_1", "券商A", "mode_a")
        snapshot = AccountSnapshot(
            account_id="acc_1",
            broker="券商A",
            portfolio=Portfolio(
                positions=[], cash=Decimal("100000"), timestamp=datetime.now()
            ),
            date=date.today(),
        )
        mgr.update_snapshot("acc_1", snapshot)
        result = mgr.get_snapshot("acc_1")
        assert result is not None
        assert result.total_assets == Decimal("100000")

    def test_get_nonexistent_snapshot(self):
        mgr = AccountManager()
        result = mgr.get_snapshot("nonexistent")
        assert result is None
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd /workspace/chixiao && pytest tests/test_account_manager.py -v`
Expected: FAIL

- [ ] **Step 3: 实现账户管理器**

```python
from __future__ import annotations

from dataclasses import dataclass, field
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
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd /workspace/chixiao && pytest tests/test_account_manager.py -v`
Expected: 全部 PASS

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: add account manager with cross-broker aggregation"
```

---

### Task 3: 交易复盘分析

**Files:**
- Create: `chixiao/src/chixiao/review/__init__.py`
- Create: `chixiao/src/chixiao/review/trade_review.py`
- Create: `chixiao/tests/test_trade_review.py`

- [ ] **Step 1: 编写交易复盘测试**

```python
from datetime import datetime
from decimal import Decimal
from chixiao.review.trade_review import TradeReviewAnalyzer, TradeRecord, ReviewResult


class TestTradeReviewAnalyzer:
    def test_analyze_profitable_trades(self):
        analyzer = TradeReviewAnalyzer()
        trades = [
            TradeRecord("000001", "平安银行", "BUY", 1000, Decimal("10.00"), datetime(2024, 1, 2)),
            TradeRecord("000001", "平安银行", "SELL", 1000, Decimal("11.00"), datetime(2024, 1, 10)),
        ]
        result = analyzer.analyze(trades)
        assert isinstance(result, ReviewResult)
        assert result.total_trades == 2
        assert result.win_rate >= 0
        assert result.total_pnl == Decimal("1000.00")

    def test_analyze_losing_trades(self):
        analyzer = TradeReviewAnalyzer()
        trades = [
            TradeRecord("000001", "平安银行", "BUY", 1000, Decimal("10.00"), datetime(2024, 1, 2)),
            TradeRecord("000001", "平安银行", "SELL", 1000, Decimal("9.00"), datetime(2024, 1, 10)),
        ]
        result = analyzer.analyze(trades)
        assert result.total_pnl == Decimal("-1000.00")

    def test_analyze_empty(self):
        analyzer = TradeReviewAnalyzer()
        result = analyzer.analyze([])
        assert result.total_trades == 0
        assert result.win_rate == 0.0

    def test_holding_period(self):
        analyzer = TradeReviewAnalyzer()
        trades = [
            TradeRecord("000001", "平安银行", "BUY", 1000, Decimal("10.00"), datetime(2024, 1, 2)),
            TradeRecord("000001", "平安银行", "SELL", 1000, Decimal("11.00"), datetime(2024, 1, 12)),
        ]
        result = analyzer.analyze(trades)
        assert result.avg_holding_days > 0

    def test_max_drawdown(self):
        analyzer = TradeReviewAnalyzer()
        trades = [
            TradeRecord("000001", "平安银行", "BUY", 1000, Decimal("10.00"), datetime(2024, 1, 2)),
            TradeRecord("000001", "平安银行", "SELL", 1000, Decimal("9.00"), datetime(2024, 1, 5)),
            TradeRecord("000002", "万科A", "BUY", 500, Decimal("8.00"), datetime(2024, 1, 6)),
            TradeRecord("000002", "万科A", "SELL", 500, Decimal("9.00"), datetime(2024, 1, 10)),
        ]
        result = analyzer.analyze(trades)
        assert result.max_drawdown <= 0
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd /workspace/chixiao && pytest tests/test_trade_review.py -v`
Expected: FAIL

- [ ] **Step 3: 实现交易复盘分析器**

```python
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional


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
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd /workspace/chixiao && pytest tests/test_trade_review.py -v`
Expected: 全部 PASS

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: add trade review analyzer with PnL, win rate, drawdown metrics"
```

---

### Task 4: LLM交易点评

**Files:**
- Create: `chixiao/src/chixiao/review/llm_reviewer.py`
- Create: `chixiao/tests/test_llm_reviewer.py`

- [ ] **Step 1: 编写LLM点评测试**

```python
from unittest.mock import patch
from datetime import datetime
from decimal import Decimal
from chixiao.review.llm_reviewer import LLMReviewer, ReviewComment
from chixiao.review.trade_review import ReviewResult, ClosedTrade


class TestLLMReviewer:
    def test_review_with_result(self):
        reviewer = LLMReviewer(api_key="test-key", model="deepseek-chat")
        result = ReviewResult(
            total_trades=4,
            closed_trades=2,
            win_count=1,
            loss_count=1,
            win_rate=0.5,
            total_pnl=Decimal("500"),
            avg_holding_days=5.0,
            max_drawdown=Decimal("-1000"),
            profit_factor=1.5,
            details=[
                ClosedTrade("000001", "平安银行", Decimal("10"), Decimal("11"), 1000,
                           datetime(2024, 1, 2), datetime(2024, 1, 7), Decimal("1000"), Decimal("10"), 5),
                ClosedTrade("000002", "万科A", Decimal("8"), Decimal("7.5"), 500,
                           datetime(2024, 1, 3), datetime(2024, 1, 8), Decimal("-250"), Decimal("-6.25"), 5),
            ],
        )

        with patch.object(reviewer, "_call_llm") as mock_llm:
            mock_llm.return_value = '{"score": 6, "strengths": ["盈利交易占比合理"], "weaknesses": ["止损不够果断"], "suggestions": ["建议设置更严格的止损线"]}'
            comment = reviewer.review(result)
            assert isinstance(comment, ReviewComment)
            assert 1 <= comment.score <= 10
            assert len(comment.strengths) > 0
            assert len(comment.suggestions) > 0

    def test_review_empty_result(self):
        reviewer = LLMReviewer(api_key="test-key", model="deepseek-chat")
        result = ReviewResult()
        comment = reviewer.review(result)
        assert comment.score == 0
        assert "暂无交易数据" in comment.summary
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd /workspace/chixiao && pytest tests/test_llm_reviewer.py -v`
Expected: FAIL

- [ ] **Step 3: 实现LLM点评器**

```python
from __future__ import annotations

import json
from dataclasses import dataclass, field

from chixiao.review.trade_review import ReviewResult


@dataclass
class ReviewComment:
    score: int
    summary: str = ""
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)


class LLMReviewer:
    def __init__(
        self,
        api_key: str = "",
        model: str = "deepseek-chat",
        base_url: str = "https://api.deepseek.com/v1",
    ):
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")

    def review(self, result: ReviewResult) -> ReviewComment:
        if result.total_trades == 0:
            return ReviewComment(score=0, summary="暂无交易数据，无法进行点评")

        prompt = self._build_prompt(result)
        response_text = self._call_llm(prompt)
        return self._parse_response(response_text)

    def _build_prompt(self, result: ReviewResult) -> str:
        details_str = ""
        for d in result.details[:10]:
            details_str += f"- {d.name}({d.symbol}): 买入{d.buy_price}→卖出{d.sell_price}, 盈亏{d.pnl_pct}%, 持有{d.holding_days}天\n"

        return f"""你是一名专业的A股交易复盘分析师。请根据以下交易统计数据进行点评。

交易统计:
- 总交易次数: {result.total_trades}
- 已平仓交易: {result.closed_trades}
- 盈利次数: {result.win_count}, 亏损次数: {result.loss_count}
- 胜率: {result.win_rate:.1%}
- 总盈亏: {result.total_pnl}
- 平均持仓天数: {result.avg_holding_days:.1f}
- 最大回撤: {result.max_drawdown}
- 盈亏比: {result.profit_factor:.2f}

交易明细:
{details_str}

请以JSON格式返回点评结果:
- score: 综合评分 (1-10分)
- summary: 一句话总结
- strengths: 做得好的地方 (数组)
- weaknesses: 需要改进的地方 (数组)
- suggestions: 具体改进建议 (数组)

仅返回JSON。"""

    def _call_llm(self, prompt: str) -> str:
        if not self._api_key:
            return '{"score": 5, "summary": "未配置API Key", "strengths": [], "weaknesses": [], "suggestions": ["请配置LLM API Key以获取详细点评"]}'

        try:
            import httpx
            response = httpx.post(
                f"{self._base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "model": self._model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 1000,
                },
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            return f'{{"score": 5, "summary": "API调用失败", "strengths": [], "weaknesses": [], "suggestions": ["修复API连接: {str(e)}"]}}'

    def _parse_response(self, text: str) -> ReviewComment:
        try:
            json_str = text.strip()
            if json_str.startswith("```"):
                lines = json_str.split("\n")
                json_str = "\n".join(lines[1:-1])
            data = json.loads(json_str)
            return ReviewComment(
                score=int(data.get("score", 5)),
                summary=data.get("summary", ""),
                strengths=data.get("strengths", []),
                weaknesses=data.get("weaknesses", []),
                suggestions=data.get("suggestions", []),
            )
        except (json.JSONDecodeError, ValueError):
            return ReviewComment(
                score=5,
                summary="点评解析失败",
                strengths=[],
                weaknesses=[],
                suggestions=["请检查LLM输出格式"],
            )
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd /workspace/chixiao && pytest tests/test_llm_reviewer.py -v`
Expected: 全部 PASS

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: add LLM trade reviewer with scoring and suggestions"
```

---

### Task 5: API端点扩展与仪表盘升级

**Files:**
- Modify: `chixiao/src/chixiao/api/main.py`
- Modify: `chixiao/dashboard/app.py`

- [ ] **Step 1: 在FastAPI中添加复盘和账户端点**

在 `api/main.py` 中新增：

```python
@app.get("/api/accounts")
def get_accounts():
    from chixiao.account.account_manager import AccountManager
    mgr = AccountManager()
    accounts = mgr.list_accounts()
    return {
        "accounts": [
            {"account_id": a.account_id, "broker": a.broker, "mode": a.mode, "last_sync": a.last_sync}
            for a in accounts
        ]
    }


@app.post("/api/trade-review")
def trade_review(trades: list[dict]):
    from chixiao.review.trade_review import TradeReviewAnalyzer, TradeRecord
    from chixiao.review.llm_reviewer import LLMReviewer
    from decimal import Decimal as D

    records = []
    for t in trades:
        records.append(TradeRecord(
            symbol=t["symbol"],
            name=t.get("name", ""),
            side=t["side"],
            quantity=t["quantity"],
            price=D(t["price"]),
            timestamp=datetime.fromisoformat(t["timestamp"]),
        ))

    analyzer = TradeReviewAnalyzer()
    result = analyzer.analyze(records)

    reviewer = LLMReviewer(api_key=_config.llm_api_key, model=_config.llm_model)
    comment = reviewer.review(result)

    return {
        "statistics": {
            "total_trades": result.total_trades,
            "win_rate": result.win_rate,
            "total_pnl": str(result.total_pnl),
            "profit_factor": result.profit_factor,
            "avg_holding_days": result.avg_holding_days,
        },
        "review": {
            "score": comment.score,
            "summary": comment.summary,
            "strengths": comment.strengths,
            "weaknesses": comment.weaknesses,
            "suggestions": comment.suggestions,
        },
    }
```

- [ ] **Step 2: 在Streamlit仪表盘中添加交易复盘tab**

在 `dashboard/app.py` 中新增tab：

```python
tab_review = st.tabs(["📝 交易复盘"])

with tab_review:
    st.header("交易复盘点评")
    st.info("请上传交易记录CSV文件（格式: symbol, name, side, quantity, price, timestamp）")
    review_file = st.file_uploader("上传交易记录", type=["csv"], key="review_csv")
    if review_file and st.button("开始复盘"):
        import csv, io
        from chixiao.review.trade_review import TradeReviewAnalyzer, TradeRecord
        from chixiao.review.llm_reviewer import LLMReviewer

        content = review_file.read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(content))
        records = []
        for row in reader:
            records.append(TradeRecord(
                symbol=row["symbol"],
                name=row.get("name", ""),
                side=row["side"],
                quantity=int(row["quantity"]),
                price=Decimal(row["price"]),
                timestamp=datetime.fromisoformat(row["timestamp"]),
            ))

        analyzer = TradeReviewAnalyzer()
        result = analyzer.analyze(records)

        col1, col2, col3 = st.columns(3)
        col1.metric("胜率", f"{result.win_rate:.1%}")
        col2.metric("总盈亏", f"¥{float(result.total_pnl):,.2f}")
        col3.metric("盈亏比", f"{result.profit_factor:.2f}")

        if result.details:
            st.subheader("交易明细")
            for d in result.details:
                emoji = "🟢" if d.pnl > 0 else "🔴"
                st.write(f"{emoji} {d.name}({d.symbol}): {d.pnl_pct}% | 持有{d.holding_days}天")

        reviewer = LLMReviewer(api_key=config.llm_api_key, model=config.llm_model)
        comment = reviewer.review(result)
        st.subheader(f"AI点评 (评分: {comment.score}/10)")
        st.write(comment.summary)
        if comment.strengths:
            st.write("**优点:**")
            for s in comment.strengths:
                st.write(f"  ✅ {s}")
        if comment.weaknesses:
            st.write("**不足:**")
            for w in comment.weaknesses:
                st.write(f"  ⚠️ {w}")
        if comment.suggestions:
            st.write("**建议:**")
            for s in comment.suggestions:
                st.write(f"  💡 {s}")
```

- [ ] **Step 3: 运行全量测试**

Run: `cd /workspace/chixiao && pytest tests/ -v`
Expected: 全部 PASS

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "feat: add trade review and account endpoints, upgrade dashboard"
```

---

## 自审清单

### 1. 规格覆盖

| 需求项 | 对应Task |
|:---|:---|
| easytrader半自动执行 | Task 1 |
| 账户聚合管理 | Task 2 |
| 交易复盘分析 | Task 3 |
| LLM交易点评 | Task 4 |
| API端点扩展 | Task 5 |
| 仪表盘升级 | Task 5 |

### 2. 占位符扫描

无 TBD/TODO 等占位符。

### 3. 类型一致性

- `TradeRecord` 在 trade_review 和 llm_reviewer 中使用一致
- `ReviewResult` 在 trade_review 和 llm_reviewer 中传递一致
- `AccountSnapshot` 在 account_manager 中使用与 core/models.py 定义一致
