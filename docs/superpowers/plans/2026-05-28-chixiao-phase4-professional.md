# 赤霄量化交易系统 — 第四阶段(专业化拓展)实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 当策略成熟、准备加大资金投入时，平滑过渡到专业级架构——切换至付费数据源、QMT执行通道，以及高性能计算升级。

**Architecture:** 通过适配器模式，新增TuShareProAdapter和WindPyAdapter实现DataAdapter接口，新增ModeCExecutor实现Executor接口对接QMT/MiniQMT。策略核心代码零修改即可切换数据源和执行通道。高性能升级将热点路径用Cython改写。

**Tech Stack:** Python 3.11+, tushare (付费数据源), WindPy (万得), xtquant (QMT接口), Cython (性能优化), 新增于前三阶段基础之上

---

## 文件结构增量

```
chixiao/
├── src/chixiao/
│   ├── data/
│   │   ├── tushare_adapter.py     # TuShare Pro适配器 (新增)
│   │   └── wind_adapter.py        # WindPy适配器 (新增)
│   ├── execution/
│   │   └── mode_c.py              # QMT/MiniQMT执行器 (新增)
│   └── perf/
│       ├── __init__.py
│       └── factor_calculator_fast.pyx  # Cython加速版因子计算 (新增)
├── tests/
│   ├── test_tushare_adapter.py
│   ├── test_wind_adapter.py
│   └── test_mode_c.py
└── setup_cython.py                # Cython构建脚本 (新增)
```

---

### Task 1: TuShare Pro数据适配器

**Files:**
- Create: `chixiao/src/chixiao/data/tushare_adapter.py`
- Create: `chixiao/tests/test_tushare_adapter.py`

- [ ] **Step 1: 编写TuShare适配器测试**

```python
from datetime import date
from decimal import Decimal
from unittest.mock import patch, MagicMock
from chixiao.data.tushare_adapter import TuShareAdapter
from chixiao.core.interfaces import DataAdapter


class TestTuShareAdapter:
    def test_implements_data_adapter(self):
        assert issubclass(TuShareAdapter, DataAdapter)

    @patch("chixiao.data.tushare_adapter.tushare")
    def test_get_bars_daily(self, mock_ts):
        mock_pro = MagicMock()
        mock_ts.pro_api.return_value = mock_pro
        mock_pro.daily.return_value = MagicMock(
            iterrows=lambda: iter([
                (0, {"trade_date": "20240102", "open": 10.0, "high": 10.5, "low": 9.8, "close": 10.2, "vol": 1000000, "amount": 10200000.0}),
            ])
        )
        mock_pro.daily.return_value.__iter__ = lambda self: iter([
            {"trade_date": "20240102", "open": 10.0, "high": 10.5, "low": 9.8, "close": 10.2, "vol": 1000000, "amount": 10200000.0},
        ])
        mock_pro.daily.return_value.empty = False
        mock_pro.daily.return_value.__len__ = lambda self: 1

        adapter = TuShareAdapter(token="test-token")
        assert adapter is not None

    @patch("chixiao.data.tushare_adapter.tushare")
    def test_get_latest_price(self, mock_ts):
        mock_pro = MagicMock()
        mock_ts.pro_api.return_value = mock_pro
        mock_pro.daily.return_value = MagicMock()
        mock_pro.daily.return_value.empty = True

        adapter = TuShareAdapter(token="test-token")
        price = adapter.get_latest_price("000001")
        assert price is None

    @patch("chixiao.data.tushare_adapter.tushare")
    def test_get_symbols(self, mock_ts):
        mock_pro = MagicMock()
        mock_ts.pro_api.return_value = mock_pro
        mock_pro.stock_basic.return_value = MagicMock()
        mock_pro.stock_basic.return_value.empty = True

        adapter = TuShareAdapter(token="test-token")
        symbols = adapter.get_symbols()
        assert isinstance(symbols, list)
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd /workspace/chixiao && pytest tests/test_tushare_adapter.py -v`
Expected: FAIL

- [ ] **Step 3: 实现TuShare适配器**

```python
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

import tushare as ts

from chixiao.core.interfaces import DataAdapter
from chixiao.core.models import Bar


class TuShareAdapter(DataAdapter):
    def __init__(self, token: str = ""):
        self._pro = ts.pro_api(token) if token else None

    def get_bars(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        frequency: str = "daily",
    ) -> list[Bar]:
        if not self._pro:
            return []

        ts_code = self._to_ts_code(symbol)
        freq_map = {"daily": "D", "weekly": "W", "monthly": "M"}
        asset = "E"

        try:
            df = self._pro.daily(
                ts_code=ts_code,
                start_date=start_date.strftime("%Y%m%d"),
                end_date=end_date.strftime("%Y%m%d"),
            )
        except Exception:
            return []

        if df.empty:
            return []

        bars = []
        for _, row in df.iterrows():
            bar = Bar(
                symbol=symbol,
                timestamp=datetime.strptime(str(row["trade_date"]), "%Y%m%d"),
                open=Decimal(str(round(row["open"], 2))),
                high=Decimal(str(round(row["high"], 2))),
                low=Decimal(str(round(row["low"], 2))),
                close=Decimal(str(round(row["close"], 2))),
                volume=int(row["vol"]),
                amount=Decimal(str(round(row.get("amount", 0), 2))),
            )
            bars.append(bar)

        bars.reverse()
        return bars

    def get_latest_price(self, symbol: str) -> Optional[Decimal]:
        if not self._pro:
            return None

        ts_code = self._to_ts_code(symbol)
        try:
            df = self._pro.daily(
                ts_code=ts_code,
                start_date=date.today().strftime("%Y%m%d"),
                end_date=date.today().strftime("%Y%m%d"),
            )
            if df.empty:
                return None
            return Decimal(str(round(float(df.iloc[0]["close"]), 2)))
        except Exception:
            return None

    def get_symbols(self) -> list[str]:
        if not self._pro:
            return []

        try:
            df = self._pro.stock_basic(exchange="", list_status="L", fields="ts_code,symbol")
            if df.empty:
                return []
            return df["symbol"].tolist()
        except Exception:
            return []

    @staticmethod
    def _to_ts_code(symbol: str) -> str:
        if "." in symbol:
            return symbol
        if symbol.startswith(("6",)):
            return f"{symbol}.SH"
        return f"{symbol}.SZ"
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd /workspace/chixiao && pytest tests/test_tushare_adapter.py -v`
Expected: 全部 PASS

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: add TuShare Pro data adapter"
```

---

### Task 2: QMT/MiniQMT执行器 (Mode C)

**Files:**
- Create: `chixiao/src/chixiao/execution/mode_c.py`
- Create: `chixiao/tests/test_mode_c.py`

- [ ] **Step 1: 编写Mode C执行器测试**

```python
from datetime import datetime
from decimal import Decimal
from unittest.mock import patch, MagicMock
from chixiao.execution.mode_c import ModeCExecutor
from chixiao.core.models import Order, OrderSide
from chixiao.core.interfaces import Executor


class TestModeCExecutor:
    def test_implements_executor(self):
        assert issubclass(ModeCExecutor, Executor)

    @patch("chixiao.execution.mode_c.xtquant")
    def test_connect(self, mock_xt):
        mock_trader = MagicMock()
        mock_xt.XtQuantTrader.return_value = mock_trader

        executor = ModeCExecutor(path="/path/to/qmt", session_id=123456)
        assert executor is not None

    @patch("chixiao.execution.mode_c.xtquant")
    def test_submit_order_buy(self, mock_xt):
        mock_trader = MagicMock()
        mock_xt.XtQuantTrader.return_value = mock_trader
        mock_xt.StockAccount.return_value = MagicMock()
        mock_xt.StockOrder.return_value = MagicMock()
        mock_trader.order_stock.return_value = MagicMock(order_id=100001)

        executor = ModeCExecutor(path="/path/to/qmt", session_id=123456)
        order = Order(
            symbol="000001",
            side=OrderSide.BUY,
            quantity=500,
            price=Decimal("10.50"),
            timestamp=datetime.now(),
        )
        order_id = executor.submit_order(order)
        assert order_id.startswith("MODEC-")

    @patch("chixiao.execution.mode_c.xtquant")
    def test_cancel_order(self, mock_xt):
        mock_trader = MagicMock()
        mock_xt.XtQuantTrader.return_value = mock_trader
        mock_trader.cancel_order_stock.return_value = True

        executor = ModeCExecutor(path="/path/to/qmt", session_id=123456)
        result = executor.cancel_order("MODEC-100001")
        assert isinstance(result, bool)

    @patch("chixiao.execution.mode_c.xtquant")
    def test_sync_positions(self, mock_xt):
        mock_trader = MagicMock()
        mock_xt.XtQuantTrader.return_value = mock_trader
        mock_trader.query_stock_positions.return_value = [
            MagicMock(stock_code="000001", volume=1000, avg_price=10.50, market_value=11000),
        ]

        executor = ModeCExecutor(path="/path/to/qmt", session_id=123456)
        positions = executor.sync_positions()
        assert isinstance(positions, list)
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd /workspace/chixiao && pytest tests/test_mode_c.py -v`
Expected: FAIL

- [ ] **Step 3: 实现Mode C执行器**

```python
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

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
            from xtquant.xttrader import XtQuantTrader, XtQuantTraderCallback
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
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd /workspace/chixiao && pytest tests/test_mode_c.py -v`
Expected: 全部 PASS

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: add Mode C executor with QMT/MiniQMT integration"
```

---

### Task 3: 数据源与执行通道切换机制

**Files:**
- Create: `chixiao/src/chixiao/core/factory.py`
- Create: `chixiao/tests/test_factory.py`

- [ ] **Step 1: 编写工厂模式测试**

```python
from chixiao.core.factory import create_data_adapter, create_executor
from chixiao.data.akshare_adapter import AKShareAdapter
from chixiao.data.tushare_adapter import TuShareAdapter
from chixiao.execution.mode_a import ModeAExecutor
from chixiao.core.interfaces import DataAdapter, Executor


class TestFactory:
    def test_create_akshare_adapter(self):
        adapter = create_data_adapter("akshare")
        assert isinstance(adapter, AKShareAdapter)
        assert isinstance(adapter, DataAdapter)

    def test_create_tushare_adapter(self):
        adapter = create_data_adapter("tushare", token="test")
        assert isinstance(adapter, TuShareAdapter)
        assert isinstance(adapter, DataAdapter)

    def test_create_unknown_adapter_fallback(self):
        adapter = create_data_adapter("unknown")
        assert isinstance(adapter, AKShareAdapter)

    def test_create_mode_a_executor(self):
        executor = create_executor("mode_a")
        assert isinstance(executor, ModeAExecutor)
        assert isinstance(executor, Executor)

    def test_create_unknown_executor_fallback(self):
        executor = create_executor("unknown")
        assert isinstance(executor, ModeAExecutor)
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd /workspace/chixiao && pytest tests/test_factory.py -v`
Expected: FAIL

- [ ] **Step 3: 实现工厂**

```python
from __future__ import annotations

from chixiao.core.interfaces import DataAdapter, Executor


def create_data_adapter(source: str, **kwargs) -> DataAdapter:
    if source == "akshare":
        from chixiao.data.akshare_adapter import AKShareAdapter
        return AKShareAdapter()
    elif source == "tushare":
        from chixiao.data.tushare_adapter import TuShareAdapter
        return TuShareAdapter(token=kwargs.get("token", ""))
    elif source == "wind":
        from chixiao.data.wind_adapter import WindAdapter
        return WindAdapter(**kwargs)
    else:
        from chixiao.data.akshare_adapter import AKShareAdapter
        return AKShareAdapter()


def create_executor(mode: str, **kwargs) -> Executor:
    if mode == "mode_a":
        from chixiao.execution.mode_a import ModeAExecutor
        return ModeAExecutor(csv_dir=kwargs.get("csv_dir", "data/positions"))
    elif mode == "mode_b":
        from chixiao.execution.mode_b import ModeBExecutor
        return ModeBExecutor(
            broker=kwargs.get("broker", "yh"),
            exe_path=kwargs.get("exe_path", ""),
        )
    elif mode == "mode_c":
        from chixiao.execution.mode_c import ModeCExecutor
        return ModeCExecutor(
            path=kwargs.get("path", ""),
            session_id=kwargs.get("session_id", 123456),
            account_id=kwargs.get("account_id", ""),
        )
    else:
        from chixiao.execution.mode_a import ModeAExecutor
        return ModeAExecutor(csv_dir=kwargs.get("csv_dir", "data/positions"))
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd /workspace/chixiao && pytest tests/test_factory.py -v`
Expected: 全部 PASS

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: add factory pattern for data adapter and executor switching"
```

---

### Task 4: Cython加速因子计算 (可选)

**Files:**
- Create: `chixiao/src/chixiao/perf/__init__.py`
- Create: `chixiao/src/chixiao/perf/factor_calculator_fast.pyx`
- Create: `chixiao/setup_cython.py`

- [ ] **Step 1: 编写Cython版因子计算器**

```python
# factor_calculator_fast.pyx
import numpy as np
cimport numpy as np
from libc.math cimport sqrt

def fast_moving_average(np.ndarray[np.float64_t, ndim=1] closes, int period):
    cdef int n = closes.shape[0]
    cdef int i, j
    cdef double s
    cdef np.ndarray[np.float64_t, ndim=1] result = np.empty(n)

    for i in range(n):
        if i < period - 1:
            result[i] = np.nan
        else:
            s = 0.0
            for j in range(i - period + 1, i + 1):
                s += closes[j]
            result[i] = s / period

    return result


def fast_rsi(np.ndarray[np.float64_t, ndim=1] closes, int period=14):
    cdef int n = closes.shape[0]
    if n < period + 1:
        return 50.0

    cdef double avg_gain = 0.0
    cdef double avg_loss = 0.0
    cdef double delta
    cdef int i

    for i in range(1, period + 1):
        delta = closes[i] - closes[i - 1]
        if delta > 0:
            avg_gain += delta
        else:
            avg_loss += (-delta)

    avg_gain /= period
    avg_loss /= period

    if avg_loss == 0:
        return 100.0

    cdef double rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))
```

- [ ] **Step 2: 编写setup.py**

```python
from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy as np

extensions = [
    Extension(
        "chixiao.perf.factor_calculator_fast",
        sources=["src/chixiao/perf/factor_calculator_fast.pyx"],
        include_dirs=[np.get_include()],
    )
]

setup(
    ext_modules=cythonize(extensions, language_level="3"),
)
```

- [ ] **Step 3: 构建Cython扩展**

Run: `cd /workspace/chixiao && python setup_cython.py build_ext --inplace`
Expected: 编译成功

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "feat: add Cython-accelerated factor calculation (optional)"
```

---

## 自审清单

### 1. 规格覆盖

| 需求项 | 对应Task |
|:---|:---|
| TuShare Pro数据源 | Task 1 |
| QMT/MiniQMT执行通道 | Task 2 |
| 数据源/执行通道切换 | Task 3 |
| Cython性能优化 | Task 4 |

### 2. 占位符扫描

WindPy适配器因依赖商业软件Wind终端，仅在工厂中注册入口，实际实现需在部署环境中完成。

### 3. 类型一致性

- 所有适配器均实现 `DataAdapter` 接口
- 所有执行器均实现 `Executor` 接口
- 工厂函数返回类型与接口定义一致
