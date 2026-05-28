# 赤霄量化交易系统 — 第一阶段(MVP)实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 搭建最小可行性产品，实现从免费数据源获取行情数据、生成策略信号、通过CSV手动同步持仓、在仪表盘上查看分析结果。

**Architecture:** 采用分层架构与依赖倒置原则。核心领域模型和接口定义在 `core/` 层，不依赖任何外部库；数据适配器、执行适配器分别实现 `core/interfaces.py` 中定义的抽象接口；Streamlit仪表盘通过调用领域服务展示数据。CQRS模式将"查询数据"与"执行交易"职责分离。

**Tech Stack:** Python 3.11+, pandas, numpy, akshare, streamlit, fastapi, uvicorn, pydantic, pytest

---

## 文件结构总览

```
chixiao/
├── pyproject.toml
├── requirements.txt
├── config.yaml
├── src/
│   └── chixiao/
│       ├── __init__.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── models.py            # 领域模型: Bar, Signal, Position, Order, Portfolio
│       │   ├── interfaces.py        # 抽象接口: DataAdapter, Executor, FactorProvider
│       │   └── config.py            # 配置管理: Settings, load_config
│       ├── data/
│       │   ├── __init__.py
│       │   ├── akshare_adapter.py   # AKShare数据源适配器
│       │   └── cleaner.py           # 数据清洗与对齐
│       ├── alpha/
│       │   ├── __init__.py
│       │   ├── factor_calculator.py # 技术因子计算
│       │   └── alpha_model.py       # Alpha信号生成
│       ├── execution/
│       │   ├── __init__.py
│       │   └── mode_a.py            # 手动CSV执行器
│       ├── portfolio/
│       │   ├── __init__.py
│       │   ├── position_manager.py  # 持仓管理
│       │   └── risk_manager.py      # 风控规则
│       └── api/
│           ├── __init__.py
│           └── main.py              # FastAPI应用入口
├── dashboard/
│   └── app.py                       # Streamlit仪表盘
├── data/
│   └── positions_sample.csv         # 示例持仓CSV
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_models.py
│   ├── test_interfaces.py
│   ├── test_config.py
│   ├── test_akshare_adapter.py
│   ├── test_cleaner.py
│   ├── test_factor_calculator.py
│   ├── test_alpha_model.py
│   ├── test_mode_a.py
│   ├── test_position_manager.py
│   └── test_risk_manager.py
└── docs/
    └── superpowers/
        └── plans/
```

---

### Task 1: 项目脚手架与依赖管理

**Files:**
- Create: `chixiao/pyproject.toml`
- Create: `chixiao/requirements.txt`
- Create: `chixiao/src/chixiao/__init__.py`
- Create: `chixiao/src/chixiao/core/__init__.py`
- Create: `chixiao/src/chixiao/data/__init__.py`
- Create: `chixiao/src/chixiao/alpha/__init__.py`
- Create: `chixiao/src/chixiao/execution/__init__.py`
- Create: `chixiao/src/chixiao/portfolio/__init__.py`
- Create: `chixiao/src/chixiao/api/__init__.py`
- Create: `chixiao/tests/__init__.py`
- Create: `chixiao/tests/conftest.py`

- [ ] **Step 1: 创建 pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "chixiao"
version = "0.1.0"
description = "赤霄量化交易决策辅助系统"
requires-python = ">=3.11"
dependencies = [
    "pandas>=2.1",
    "numpy>=1.25",
    "akshare>=1.12",
    "streamlit>=1.30",
    "fastapi>=0.109",
    "uvicorn>=0.27",
    "pydantic>=2.5",
    "pydantic-settings>=2.1",
    "pyyaml>=6.0",
    "scipy>=1.12",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4",
    "pytest-cov>=4.1",
    "pytest-asyncio>=0.23",
    "httpx>=0.26",
    "ruff>=0.2",
]

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]

[tool.ruff]
line-length = 120
target-version = "py311"
```

- [ ] **Step 2: 创建 requirements.txt**

```
pandas>=2.1
numpy>=1.25
akshare>=1.12
streamlit>=1.30
fastapi>=0.109
uvicorn>=0.27
pydantic>=2.5
pydantic-settings>=2.1
pyyaml>=6.0
scipy>=1.12
pytest>=7.4
pytest-cov>=4.1
pytest-asyncio>=0.23
httpx>=0.26
ruff>=0.2
```

- [ ] **Step 3: 创建所有 `__init__.py` 文件**

每个 `__init__.py` 内容为空文件，仅用于包标识。

- [ ] **Step 4: 创建 tests/conftest.py**

```python
import pytest
from pathlib import Path


@pytest.fixture
def project_root() -> Path:
    return Path(__file__).parent.parent


@pytest.fixture
def sample_csv_path(project_root) -> Path:
    return project_root / "data" / "positions_sample.csv"
```

- [ ] **Step 5: 安装依赖并验证**

Run: `cd /workspace/chixiao && pip install -e ".[dev]"`
Expected: 安装成功，无报错

- [ ] **Step 6: 验证 pytest 可运行**

Run: `cd /workspace/chixiao && pytest --co`
Expected: 显示空测试列表，无报错

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "feat: scaffold project structure with dependencies"
```

---

### Task 2: 核心领域模型

**Files:**
- Create: `chixiao/src/chixiao/core/models.py`
- Create: `chixiao/tests/test_models.py`

- [ ] **Step 1: 编写领域模型的测试**

```python
from datetime import datetime, date
from decimal import Decimal
from chixiao.core.models import (
    Bar, Signal, SignalDirection, Position, Order, OrderSide,
    Portfolio, AccountSnapshot
)


class TestBar:
    def test_create_bar(self):
        bar = Bar(
            symbol="000001",
            timestamp=datetime(2024, 1, 2, 9, 30),
            open=Decimal("10.00"),
            high=Decimal("10.50"),
            low=Decimal("9.80"),
            close=Decimal("10.20"),
            volume=1000000,
            amount=Decimal("10200000"),
        )
        assert bar.symbol == "000001"
        assert bar.close == Decimal("10.20")
        assert bar.volume == 1000000

    def test_bar_to_dict(self):
        bar = Bar(
            symbol="000001",
            timestamp=datetime(2024, 1, 2, 9, 30),
            open=Decimal("10.00"),
            high=Decimal("10.50"),
            low=Decimal("9.80"),
            close=Decimal("10.20"),
            volume=1000000,
            amount=Decimal("10200000"),
        )
        d = bar.to_dict()
        assert d["symbol"] == "000001"
        assert d["close"] == "10.20"


class TestSignal:
    def test_buy_signal(self):
        signal = Signal(
            symbol="000001",
            direction=SignalDirection.BUY,
            strength=0.85,
            timestamp=datetime(2024, 1, 2, 15, 0),
            factors={"momentum": 0.9, "value": 0.8},
        )
        assert signal.direction == SignalDirection.BUY
        assert signal.strength == 0.85

    def test_sell_signal(self):
        signal = Signal(
            symbol="000001",
            direction=SignalDirection.SELL,
            strength=0.6,
            timestamp=datetime(2024, 1, 2, 15, 0),
            factors={"momentum": 0.3},
        )
        assert signal.direction == SignalDirection.SELL


class TestPosition:
    def test_create_position(self):
        pos = Position(
            symbol="000001",
            name="平安银行",
            quantity=1000,
            avg_cost=Decimal("10.50"),
            current_price=Decimal("11.00"),
        )
        assert pos.symbol == "000001"
        assert pos.market_value == Decimal("11000.00")
        assert pos.unrealized_pnl == Decimal("500.00")
        assert pos.unrealized_pnl_pct == Decimal("4.76")

    def test_position_zero_cost(self):
        pos = Position(
            symbol="000001",
            name="平安银行",
            quantity=1000,
            avg_cost=Decimal("0"),
            current_price=Decimal("11.00"),
        )
        assert pos.unrealized_pnl_pct == Decimal("0")


class TestOrder:
    def test_buy_order(self):
        order = Order(
            symbol="000001",
            side=OrderSide.BUY,
            quantity=500,
            price=Decimal("10.50"),
            timestamp=datetime(2024, 1, 2, 9, 30),
        )
        assert order.side == OrderSide.BUY
        assert order.total_amount == Decimal("5250.00")


class TestPortfolio:
    def test_portfolio_total_value(self):
        positions = [
            Position("000001", "平安银行", 1000, Decimal("10.50"), Decimal("11.00")),
            Position("600036", "招商银行", 500, Decimal("35.00"), Decimal("36.00")),
        ]
        portfolio = Portfolio(
            positions=positions,
            cash=Decimal("50000"),
            timestamp=datetime(2024, 1, 2, 15, 0),
        )
        assert portfolio.total_value == Decimal("93000.00")
        assert len(portfolio.positions) == 2

    def test_portfolio_empty(self):
        portfolio = Portfolio(
            positions=[],
            cash=Decimal("100000"),
            timestamp=datetime(2024, 1, 2, 15, 0),
        )
        assert portfolio.total_value == Decimal("100000")


class TestAccountSnapshot:
    def test_snapshot(self):
        positions = [
            Position("000001", "平安银行", 1000, Decimal("10.50"), Decimal("11.00")),
        ]
        portfolio = Portfolio(
            positions=positions,
            cash=Decimal("50000"),
            timestamp=datetime(2024, 1, 2, 15, 0),
        )
        snapshot = AccountSnapshot(
            account_id="manual_001",
            broker="手动同步",
            portfolio=portfolio,
            date=date(2024, 1, 2),
        )
        assert snapshot.account_id == "manual_001"
        assert snapshot.total_assets == Decimal("61000.00")
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd /workspace/chixiao && pytest tests/test_models.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'chixiao'`

- [ ] **Step 3: 实现领域模型**

```python
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
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd /workspace/chixiao && pytest tests/test_models.py -v`
Expected: 全部 PASS

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: add core domain models (Bar, Signal, Position, Order, Portfolio)"
```

---

### Task 3: 抽象接口定义

**Files:**
- Create: `chixiao/src/chixiao/core/interfaces.py`
- Create: `chixiao/tests/test_interfaces.py`

- [ ] **Step 1: 编写接口测试**

```python
from abc import ABC
from chixiao.core.interfaces import DataAdapter, Executor, FactorProvider
from chixiao.core.models import Signal, SignalDirection


class TestInterfaces:
    def test_data_adapter_is_abstract(self):
        assert issubclass(DataAdapter, ABC)
        assert hasattr(DataAdapter, "get_bars")
        assert hasattr(DataAdapter, "get_latest_price")

    def test_executor_is_abstract(self):
        assert issubclass(Executor, ABC)
        assert hasattr(Executor, "submit_order")
        assert hasattr(Executor, "cancel_order")
        assert hasattr(Executor, "sync_positions")

    def test_factor_provider_is_abstract(self):
        assert issubclass(FactorProvider, ABC)
        assert hasattr(FactorProvider, "compute_factors")
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd /workspace/chixiao && pytest tests/test_interfaces.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: 实现抽象接口**

```python
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from chixiao.core.models import Bar, Order, Position, Signal


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
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd /workspace/chixiao && pytest tests/test_interfaces.py -v`
Expected: 全部 PASS

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: add abstract interfaces (DataAdapter, Executor, FactorProvider)"
```

---

### Task 4: 配置管理

**Files:**
- Create: `chixiao/src/chixiao/core/config.py`
- Create: `chixiao/config.yaml`
- Create: `chixiao/tests/test_config.py`

- [ ] **Step 1: 编写配置管理测试**

```python
from chixiao.core.config import Settings, load_config


class TestConfig:
    def test_default_settings(self):
        settings = Settings()
        assert settings.data_source == "akshare"
        assert settings.execution_mode == "mode_a"
        assert settings.risk_max_position_pct == 0.25

    def test_load_config_from_yaml(self, tmp_path):
        yaml_content = """
data_source: akshare
execution_mode: mode_a
risk_max_position_pct: 0.3
"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml_content)
        settings = load_config(config_file)
        assert settings.risk_max_position_pct == 0.3

    def test_load_config_missing_file_uses_defaults(self):
        settings = load_config("/nonexistent/config.yaml")
        assert settings.data_source == "akshare"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd /workspace/chixiao && pytest tests/test_config.py -v`
Expected: FAIL

- [ ] **Step 3: 实现配置管理**

```python
from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class DataConfig(BaseModel):
    source: str = "akshare"
    cache_dir: str = "data/cache"
    cache_expiry_hours: int = 4


class RiskConfig(BaseModel):
    max_position_pct: float = 0.25
    max_single_loss_pct: float = 0.02
    max_portfolio_drawdown_pct: float = 0.10


class ExecutionConfig(BaseModel):
    mode: str = "mode_a"
    csv_dir: str = "data/positions"
    easytrader_broker: str = ""


class LLMConfig(BaseModel):
    provider: str = "deepseek"
    api_key: str = ""
    model: str = "deepseek-chat"


class Settings(BaseSettings):
    data_source: str = "akshare"
    execution_mode: str = "mode_a"
    risk_max_position_pct: float = 0.25
    risk_max_single_loss_pct: float = 0.02
    risk_max_portfolio_drawdown_pct: float = 0.10
    data_cache_dir: str = "data/cache"
    data_cache_expiry_hours: int = 4
    csv_dir: str = "data/positions"
    llm_provider: str = "deepseek"
    llm_api_key: str = ""
    llm_model: str = "deepseek-chat"

    model_config = {"env_prefix": "CHIXIAO_"}


def load_config(config_path: str | Path | None = None) -> Settings:
    if config_path is None:
        return Settings()

    path = Path(config_path)
    if not path.exists():
        return Settings()

    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    return Settings(**raw)
```

- [ ] **Step 4: 创建默认 config.yaml**

```yaml
data_source: akshare
execution_mode: mode_a
risk_max_position_pct: 0.25
risk_max_single_loss_pct: 0.02
risk_max_portfolio_drawdown_pct: 0.10
data_cache_dir: data/cache
data_cache_expiry_hours: 4
csv_dir: data/positions
llm_provider: deepseek
llm_api_key: ""
llm_model: deepseek-chat
```

- [ ] **Step 5: 运行测试确认通过**

Run: `cd /workspace/chixiao && pytest tests/test_config.py -v`
Expected: 全部 PASS

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat: add configuration management with YAML and env support"
```

---

### Task 5: AKShare数据适配器

**Files:**
- Create: `chixiao/src/chixiao/data/akshare_adapter.py`
- Create: `chixiao/tests/test_akshare_adapter.py`

- [ ] **Step 1: 编写AKShare适配器测试**

```python
from datetime import date
from decimal import Decimal
from unittest.mock import patch, MagicMock
import pandas as pd
from chixiao.data.akshare_adapter import AKShareAdapter
from chixiao.core.interfaces import DataAdapter


class TestAKShareAdapter:
    def test_implements_data_adapter(self):
        assert issubclass(AKShareAdapter, DataAdapter)

    @patch("chixiao.data.akshare_adapter.ak")
    def test_get_bars_daily(self, mock_ak):
        mock_df = pd.DataFrame({
            "日期": pd.to_datetime(["2024-01-02", "2024-01-03"]),
            "开盘": [10.0, 10.5],
            "最高": [10.5, 11.0],
            "最低": [9.8, 10.2],
            "收盘": [10.2, 10.8],
            "成交量": [1000000, 1200000],
            "成交额": [10200000.0, 12960000.0],
        })
        mock_ak.stock_zh_a_hist.return_value = mock_df

        adapter = AKShareAdapter()
        bars = adapter.get_bars("000001", date(2024, 1, 2), date(2024, 1, 3))

        assert len(bars) == 2
        assert bars[0].symbol == "000001"
        assert bars[0].close == Decimal("10.2")
        assert bars[1].volume == 1200000

    @patch("chixiao.data.akshare_adapter.ak")
    def test_get_bars_empty_result(self, mock_ak):
        mock_ak.stock_zh_a_hist.return_value = pd.DataFrame()

        adapter = AKShareAdapter()
        bars = adapter.get_bars("999999", date(2024, 1, 2), date(2024, 1, 3))

        assert len(bars) == 0

    @patch("chixiao.data.akshare_adapter.ak")
    def test_get_latest_price(self, mock_ak):
        mock_df = pd.DataFrame({
            "收盘": [10.5],
        })
        mock_ak.stock_zh_a_spot_em.return_value = mock_df[mock_df.columns]

        adapter = AKShareAdapter()
        price = adapter.get_latest_price("000001")

        assert price is not None

    @patch("chixiao.data.akshare_adapter.ak")
    def test_get_latest_price_not_found(self, mock_ak):
        mock_ak.stock_zh_a_spot_em.return_value = pd.DataFrame()

        adapter = AKShareAdapter()
        price = adapter.get_latest_price("999999")

        assert price is None

    @patch("chixiao.data.akshare_adapter.ak")
    def test_get_symbols(self, mock_ak):
        mock_df = pd.DataFrame({
            "代码": ["000001", "000002", "600036"],
            "名称": ["平安银行", "万科A", "招商银行"],
        })
        mock_ak.stock_zh_a_spot_em.return_value = mock_df

        adapter = AKShareAdapter()
        symbols = adapter.get_symbols()

        assert "000001" in symbols
        assert "600036" in symbols
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd /workspace/chixiao && pytest tests/test_akshare_adapter.py -v`
Expected: FAIL

- [ ] **Step 3: 实现AKShare适配器**

```python
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

import akshare as ak
import pandas as pd

from chixiao.core.interfaces import DataAdapter
from chixiao.core.models import Bar


class AKShareAdapter(DataAdapter):
    def get_bars(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        frequency: str = "daily",
    ) -> list[Bar]:
        freq_map = {"daily": "daily", "weekly": "weekly", "monthly": "monthly"}
        ak_freq = freq_map.get(frequency, "daily")

        try:
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period=ak_freq,
                start_date=start_date.strftime("%Y%m%d"),
                end_date=end_date.strftime("%Y%m%d"),
                adjust="qfq",
            )
        except Exception:
            return []

        if df.empty:
            return []

        bars = []
        for _, row in df.iterrows():
            bar = Bar(
                symbol=symbol,
                timestamp=pd.to_datetime(row["日期"]).to_pydatetime(),
                open=Decimal(str(round(row["开盘"], 2))),
                high=Decimal(str(round(row["最高"], 2))),
                low=Decimal(str(round(row["最低"], 2))),
                close=Decimal(str(round(row["收盘"], 2))),
                volume=int(row["成交量"]),
                amount=Decimal(str(round(row["成交额"], 2))),
            )
            bars.append(bar)

        return bars

    def get_latest_price(self, symbol: str) -> Optional[Decimal]:
        try:
            df = ak.stock_zh_a_spot_em()
            match = df[df["代码"] == symbol]
            if match.empty:
                return None
            return Decimal(str(round(float(match.iloc[0]["最新价"]), 2)))
        except Exception:
            return None

    def get_symbols(self) -> list[str]:
        try:
            df = ak.stock_zh_a_spot_em()
            return df["代码"].tolist()
        except Exception:
            return []
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd /workspace/chixiao && pytest tests/test_akshare_adapter.py -v`
Expected: 全部 PASS

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: add AKShare data adapter with bar/price/symbol queries"
```

---

### Task 6: 数据清洗与对齐

**Files:**
- Create: `chixiao/src/chixiao/data/cleaner.py`
- Create: `chixiao/tests/test_cleaner.py`

- [ ] **Step 1: 编写数据清洗测试**

```python
from datetime import datetime
from decimal import Decimal
from chixiao.core.models import Bar
from chixiao.data.cleaner import DataCleaner


def _make_bar(symbol: str, ts: datetime, close: str, volume: int = 1000) -> Bar:
    return Bar(
        symbol=symbol,
        timestamp=ts,
        open=Decimal(close),
        high=Decimal(close),
        low=Decimal(close),
        close=Decimal(close),
        volume=volume,
        amount=Decimal(close) * volume,
    )


class TestDataCleaner:
    def test_remove_zero_volume_bars(self):
        bars = [
            _make_bar("000001", datetime(2024, 1, 2), "10.0", 1000),
            _make_bar("000001", datetime(2024, 1, 3), "10.5", 0),
            _make_bar("000001", datetime(2024, 1, 4), "10.8", 2000),
        ]
        result = DataCleaner.remove_zero_volume(bars)
        assert len(result) == 2
        assert result[0].volume == 1000
        assert result[1].volume == 2000

    def test_fill_missing_dates(self):
        bars = [
            _make_bar("000001", datetime(2024, 1, 2), "10.0"),
            _make_bar("000001", datetime(2024, 1, 4), "10.8"),
        ]
        result = DataCleaner.fill_missing_dates(bars, "daily")
        assert len(result) == 3
        assert result[1].close == Decimal("10.0")
        assert result[1].volume == 0

    def test_detect_outliers(self):
        bars = [
            _make_bar("000001", datetime(2024, 1, 2 + i), "10.0")
            for i in range(10)
        ]
        bars.append(_make_bar("000001", datetime(2024, 1, 12), "100.0"))
        result = DataCleaner.detect_outliers(bars, z_threshold=3.0)
        assert len(result.outlier_indices) == 1
        assert 10 in result.outlier_indices

    def test_clean_pipeline(self):
        bars = [
            _make_bar("000001", datetime(2024, 1, 2), "10.0", 0),
            _make_bar("000001", datetime(2024, 1, 3), "10.5", 1000),
            _make_bar("000001", datetime(2024, 1, 5), "10.8", 2000),
        ]
        result = DataCleaner.clean(bars)
        assert len(result) >= 2
        assert all(b.volume > 0 for b in result)
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd /workspace/chixiao && pytest tests/test_cleaner.py -v`
Expected: FAIL

- [ ] **Step 3: 实现数据清洗器**

```python
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal

import numpy as np

from chixiao.core.models import Bar


@dataclass
class OutlierResult:
    outlier_indices: list[int] = field(default_factory=list)
    z_scores: list[float] = field(default_factory=list)


class DataCleaner:
    @staticmethod
    def remove_zero_volume(bars: list[Bar]) -> list[Bar]:
        return [b for b in bars if b.volume > 0]

    @staticmethod
    def fill_missing_dates(bars: list[Bar], frequency: str = "daily") -> list[Bar]:
        if not bars:
            return []

        sorted_bars = sorted(bars, key=lambda b: b.timestamp)
        filled = [sorted_bars[0]]

        for i in range(1, len(sorted_bars)):
            prev = filled[-1]
            curr = sorted_bars[i]
            expected_next = prev.timestamp + timedelta(days=1)

            while expected_next < curr.timestamp:
                if expected_next.weekday() < 5:
                    synthetic = Bar(
                        symbol=prev.symbol,
                        timestamp=expected_next,
                        open=prev.close,
                        high=prev.close,
                        low=prev.close,
                        close=prev.close,
                        volume=0,
                        amount=Decimal("0"),
                    )
                    filled.append(synthetic)
                expected_next += timedelta(days=1)

            filled.append(curr)

        return filled

    @staticmethod
    def detect_outliers(bars: list[Bar], z_threshold: float = 3.0) -> OutlierResult:
        if len(bars) < 3:
            return OutlierResult()

        closes = np.array([float(b.close) for b in bars])
        returns = np.diff(closes) / closes[:-1]
        returns = np.append([0.0], returns)

        mean = np.mean(returns)
        std = np.std(returns)
        if std == 0:
            return OutlierResult(z_scores=returns.tolist())

        z_scores = np.abs((returns - mean) / std)
        outlier_indices = [i for i, z in enumerate(z_scores) if z > z_threshold]

        return OutlierResult(
            outlier_indices=outlier_indices,
            z_scores=z_scores.tolist(),
        )

    @classmethod
    def clean(cls, bars: list[Bar]) -> list[Bar]:
        bars = cls.remove_zero_volume(bars)
        bars = cls.fill_missing_dates(bars)
        return bars
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd /workspace/chixiao && pytest tests/test_cleaner.py -v`
Expected: 全部 PASS

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: add data cleaner with zero-volume removal, date fill, outlier detection"
```

---

### Task 7: 技术因子计算器

**Files:**
- Create: `chixiao/src/chixiao/alpha/factor_calculator.py`
- Create: `chixiao/tests/test_factor_calculator.py`

- [ ] **Step 1: 编写因子计算器测试**

```python
from datetime import datetime
from decimal import Decimal
from chixiao.core.models import Bar
from chixiao.alpha.factor_calculator import FactorCalculator
from chixiao.core.interfaces import FactorProvider


def _make_bars(n: int, base_close: float = 10.0, trend: str = "up") -> list[Bar]:
    bars = []
    for i in range(n):
        if trend == "up":
            close = base_close + i * 0.1
        elif trend == "down":
            close = base_close - i * 0.1
        else:
            close = base_close
        bars.append(Bar(
            symbol="000001",
            timestamp=datetime(2024, 1, 2 + i),
            open=Decimal(str(round(close - 0.05, 2))),
            high=Decimal(str(round(close + 0.2, 2))),
            low=Decimal(str(round(close - 0.2, 2))),
            close=Decimal(str(round(close, 2))),
            volume=1000000 + i * 10000,
            amount=Decimal(str(round(close * 1000000, 2))),
        ))
    return bars


class TestFactorCalculator:
    def test_implements_factor_provider(self):
        assert issubclass(FactorCalculator, FactorProvider)

    def test_compute_factors_returns_dict(self):
        bars = _make_bars(30)
        calc = FactorCalculator()
        factors = calc.compute_factors("000001", bars)
        assert isinstance(factors, dict)
        assert "ma_5" in factors
        assert "ma_20" in factors
        assert "rsi_14" in factors
        assert "macd" in factors
        assert "bollinger_upper" in factors
        assert "bollinger_lower" in factors

    def test_ma_calculation(self):
        bars = _make_bars(30)
        calc = FactorCalculator()
        factors = calc.compute_factors("000001", bars)
        assert factors["ma_5"] > 0
        assert factors["ma_20"] > 0

    def test_rsi_range(self):
        bars = _make_bars(30)
        calc = FactorCalculator()
        factors = calc.compute_factors("000001", bars)
        assert 0 <= factors["rsi_14"] <= 100

    def test_insufficient_data_returns_partial(self):
        bars = _make_bars(5)
        calc = FactorCalculator()
        factors = calc.compute_factors("000001", bars)
        assert "ma_5" in factors
        assert factors.get("ma_20") is None or isinstance(factors.get("ma_20"), float)

    def test_empty_bars_returns_empty(self):
        calc = FactorCalculator()
        factors = calc.compute_factors("000001", [])
        assert factors == {}
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd /workspace/chixiao && pytest tests/test_factor_calculator.py -v`
Expected: FAIL

- [ ] **Step 3: 实现因子计算器**

```python
from __future__ import annotations

from decimal import Decimal

import numpy as np
import pandas as pd

from chixiao.core.interfaces import FactorProvider
from chixiao.core.models import Bar


class FactorCalculator(FactorProvider):
    def compute_factors(self, symbol: str, bars: list[Bar]) -> dict[str, float]:
        if not bars:
            return {}

        closes = np.array([float(b.close) for b in bars])
        volumes = np.array([float(b.volume) for b in bars])
        highs = np.array([float(b.high) for b in bars])
        lows = np.array([float(b.low) for b in bars])

        factors: dict[str, float] = {}

        factors.update(self._moving_averages(closes))
        factors.update(self._rsi(closes))
        factors.update(self._macd(closes))
        factors.update(self._bollinger(closes))
        factors.update(self._volume_factors(volumes))
        factors.update(self._price_factors(closes, highs, lows))

        return factors

    def _moving_averages(self, closes: np.ndarray) -> dict[str, float]:
        result: dict[str, float] = {}
        for period in [5, 10, 20, 60]:
            if len(closes) >= period:
                result[f"ma_{period}"] = float(np.mean(closes[-period:]))
            else:
                result[f"ma_{period}"] = float(np.mean(closes))
        return result

    def _rsi(self, closes: np.ndarray, period: int = 14) -> dict[str, float]:
        if len(closes) < period + 1:
            return {"rsi_14": 50.0}

        deltas = np.diff(closes)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = float(np.mean(gains[-period:]))
        avg_loss = float(np.mean(losses[-period:]))

        if avg_loss == 0:
            return {"rsi_14": 100.0}

        rs = avg_gain / avg_loss
        rsi = 100.0 - (100.0 / (1.0 + rs))
        return {"rsi_14": rsi}

    def _macd(self, closes: np.ndarray) -> dict[str, float]:
        if len(closes) < 26:
            return {"macd": 0.0, "macd_signal": 0.0, "macd_hist": 0.0}

        ema_12 = pd.Series(closes).ewm(span=12, adjust=False).mean()
        ema_26 = pd.Series(closes).ewm(span=26, adjust=False).mean()
        macd_line = ema_12 - ema_26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        hist = macd_line - signal_line

        return {
            "macd": float(macd_line.iloc[-1]),
            "macd_signal": float(signal_line.iloc[-1]),
            "macd_hist": float(hist.iloc[-1]),
        }

    def _bollinger(self, closes: np.ndarray, period: int = 20) -> dict[str, float]:
        if len(closes) < period:
            period = len(closes)
        if period == 0:
            return {"bollinger_upper": 0.0, "bollinger_lower": 0.0, "bollinger_width": 0.0}

        sma = float(np.mean(closes[-period:]))
        std = float(np.std(closes[-period:]))

        upper = sma + 2 * std
        lower = sma - 2 * std
        width = (upper - lower) / sma if sma != 0 else 0.0

        return {
            "bollinger_upper": upper,
            "bollinger_lower": lower,
            "bollinger_width": width,
        }

    def _volume_factors(self, volumes: np.ndarray) -> dict[str, float]:
        if len(volumes) < 5:
            return {"volume_ratio": 1.0}

        avg_vol = float(np.mean(volumes[-5:]))
        current_vol = float(volumes[-1])
        ratio = current_vol / avg_vol if avg_vol > 0 else 1.0

        return {"volume_ratio": ratio}

    def _price_factors(
        self, closes: np.ndarray, highs: np.ndarray, lows: np.ndarray
    ) -> dict[str, float]:
        if len(closes) < 2:
            return {"momentum_5": 0.0, "volatility": 0.0}

        n = min(5, len(closes) - 1)
        momentum = (float(closes[-1]) - float(closes[-1 - n])) / float(closes[-1 - n]) if float(closes[-1 - n]) != 0 else 0.0

        returns = np.diff(closes) / closes[:-1]
        volatility = float(np.std(returns[-20:])) if len(returns) >= 20 else float(np.std(returns))

        return {"momentum_5": momentum, "volatility": volatility}
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd /workspace/chixiao && pytest tests/test_factor_calculator.py -v`
Expected: 全部 PASS

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: add factor calculator with MA, RSI, MACD, Bollinger, volume, momentum"
```

---

### Task 8: Alpha信号生成模型

**Files:**
- Create: `chixiao/src/chixiao/alpha/alpha_model.py`
- Create: `chixiao/tests/test_alpha_model.py`

- [ ] **Step 1: 编写Alpha模型测试**

```python
from datetime import datetime
from decimal import Decimal
from chixiao.core.models import Bar, Signal, SignalDirection
from chixiao.alpha.alpha_model import AlphaModel
from chixiao.alpha.factor_calculator import FactorCalculator


def _make_bars(n: int, base_close: float = 10.0, trend: str = "up") -> list[Bar]:
    bars = []
    for i in range(n):
        if trend == "up":
            close = base_close + i * 0.1
        elif trend == "down":
            close = base_close - i * 0.1
        else:
            close = base_close
        bars.append(Bar(
            symbol="000001",
            timestamp=datetime(2024, 1, 2 + i),
            open=Decimal(str(round(close - 0.05, 2))),
            high=Decimal(str(round(close + 0.2, 2))),
            low=Decimal(str(round(close - 0.2, 2))),
            close=Decimal(str(round(close, 2))),
            volume=1000000 + i * 10000,
            amount=Decimal(str(round(close * 1000000, 2))),
        ))
    return bars


class TestAlphaModel:
    def test_generate_signal_up_trend(self):
        bars = _make_bars(30, trend="up")
        model = AlphaModel(FactorCalculator())
        signal = model.generate_signal("000001", bars)
        assert signal is not None
        assert signal.symbol == "000001"
        assert signal.direction in [SignalDirection.BUY, SignalDirection.HOLD, SignalDirection.SELL]

    def test_generate_signal_down_trend(self):
        bars = _make_bars(30, trend="down")
        model = AlphaModel(FactorCalculator())
        signal = model.generate_signal("000001", bars)
        assert signal is not None

    def test_generate_signal_empty_bars(self):
        model = AlphaModel(FactorCalculator())
        signal = model.generate_signal("000001", [])
        assert signal is None

    def test_signal_strength_range(self):
        bars = _make_bars(30, trend="up")
        model = AlphaModel(FactorCalculator())
        signal = model.generate_signal("000001", bars)
        assert 0.0 <= signal.strength <= 1.0

    def test_generate_signals_multiple(self):
        up_bars = _make_bars(30, trend="up")
        down_bars = _make_bars(30, trend="down")
        model = AlphaModel(FactorCalculator())
        signals = model.generate_signals({
            "000001": up_bars,
            "000002": down_bars,
        })
        assert len(signals) == 2
        assert all(isinstance(s, Signal) for s in signals)
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd /workspace/chixiao && pytest tests/test_alpha_model.py -v`
Expected: FAIL

- [ ] **Step 3: 实现Alpha模型**

```python
from __future__ import annotations

from datetime import datetime
from typing import Optional

from chixiao.core.interfaces import FactorProvider
from chixiao.core.models import Bar, Signal, SignalDirection


class AlphaModel:
    def __init__(self, factor_provider: FactorProvider):
        self._factor_provider = factor_provider

    def generate_signal(self, symbol: str, bars: list[Bar]) -> Optional[Signal]:
        if not bars:
            return None

        factors = self._factor_provider.compute_factors(symbol, bars)
        if not factors:
            return None

        score = self._compute_score(factors)
        direction = self._score_to_direction(score)

        return Signal(
            symbol=symbol,
            direction=direction,
            strength=min(abs(score), 1.0),
            timestamp=bars[-1].timestamp,
            factors=factors,
        )

    def generate_signals(
        self, bars_map: dict[str, list[Bar]]
    ) -> list[Signal]:
        signals = []
        for symbol, bars in bars_map.items():
            signal = self.generate_signal(symbol, bars)
            if signal is not None:
                signals.append(signal)
        return signals

    def _compute_score(self, factors: dict[str, float]) -> float:
        score = 0.0
        weight_sum = 0.0

        ma_score = self._ma_score(factors)
        if ma_score is not None:
            score += ma_score * 0.25
            weight_sum += 0.25

        rsi_score = self._rsi_score(factors)
        if rsi_score is not None:
            score += rsi_score * 0.20
            weight_sum += 0.20

        macd_score = self._macd_score(factors)
        if macd_score is not None:
            score += macd_score * 0.25
            weight_sum += 0.25

        momentum_score = self._momentum_score(factors)
        if momentum_score is not None:
            score += momentum_score * 0.20
            weight_sum += 0.20

        volume_score = self._volume_score(factors)
        if volume_score is not None:
            score += volume_score * 0.10
            weight_sum += 0.10

        if weight_sum == 0:
            return 0.0

        return score / weight_sum

    def _ma_score(self, factors: dict[str, float]) -> Optional[float]:
        ma_5 = factors.get("ma_5")
        ma_20 = factors.get("ma_20")
        if ma_5 is None or ma_20 is None:
            return None
        if ma_5 > ma_20:
            return 0.5 + min((ma_5 - ma_20) / ma_20 * 10, 0.5)
        else:
            return -0.5 - min((ma_20 - ma_5) / ma_20 * 10, 0.5)

    def _rsi_score(self, factors: dict[str, float]) -> Optional[float]:
        rsi = factors.get("rsi_14")
        if rsi is None:
            return None
        if rsi < 30:
            return 0.8
        elif rsi < 40:
            return 0.4
        elif rsi > 70:
            return -0.8
        elif rsi > 60:
            return -0.4
        return 0.0

    def _macd_score(self, factors: dict[str, float]) -> Optional[float]:
        hist = factors.get("macd_hist")
        if hist is None:
            return None
        if hist > 0:
            return min(hist * 100, 1.0)
        else:
            return max(hist * 100, -1.0)

    def _momentum_score(self, factors: dict[str, float]) -> Optional[float]:
        momentum = factors.get("momentum_5")
        if momentum is None:
            return None
        return max(min(momentum * 5, 1.0), -1.0)

    def _volume_score(self, factors: dict[str, float]) -> Optional[float]:
        ratio = factors.get("volume_ratio")
        if ratio is None:
            return None
        if ratio > 1.5:
            return 0.3
        elif ratio < 0.5:
            return -0.3
        return 0.0

    def _score_to_direction(self, score: float) -> SignalDirection:
        if score > 0.3:
            return SignalDirection.BUY
        elif score < -0.3:
            return SignalDirection.SELL
        return SignalDirection.HOLD
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd /workspace/chixiao && pytest tests/test_alpha_model.py -v`
Expected: 全部 PASS

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: add alpha model with multi-factor scoring signal generation"
```

---

### Task 9: CSV持仓同步与Mode A执行器

**Files:**
- Create: `chixiao/src/chixiao/execution/mode_a.py`
- Create: `chixiao/data/positions_sample.csv`
- Create: `chixiao/tests/test_mode_a.py`

- [ ] **Step 1: 编写Mode A执行器测试**

```python
from datetime import date
from decimal import Decimal
from pathlib import Path
import csv
from chixiao.execution.mode_a import ModeAExecutor
from chixiao.core.models import Order, OrderSide, Position
from chixiao.core.interfaces import Executor


class TestModeAExecutor:
    def test_implements_executor(self):
        assert issubclass(ModeAExecutor, Executor)

    def test_sync_positions_from_csv(self, tmp_path):
        csv_content = "symbol,name,quantity,avg_cost,current_price\n000001,平安银行,1000,10.50,11.00\n600036,招商银行,500,35.00,36.00\n"
        csv_file = tmp_path / "positions.csv"
        csv_file.write_text(csv_content, encoding="utf-8")

        executor = ModeAExecutor(csv_dir=str(tmp_path))
        positions = executor.sync_positions()

        assert len(positions) == 2
        assert positions[0].symbol == "000001"
        assert positions[0].quantity == 1000
        assert positions[0].avg_cost == Decimal("10.50")
        assert positions[1].symbol == "600036"

    def test_sync_positions_empty_csv(self, tmp_path):
        csv_content = "symbol,name,quantity,avg_cost,current_price\n"
        csv_file = tmp_path / "positions.csv"
        csv_file.write_text(csv_content, encoding="utf-8")

        executor = ModeAExecutor(csv_dir=str(tmp_path))
        positions = executor.sync_positions()

        assert len(positions) == 0

    def test_sync_positions_no_file(self, tmp_path):
        executor = ModeAExecutor(csv_dir=str(tmp_path))
        positions = executor.sync_positions()

        assert len(positions) == 0

    def test_submit_order_creates_record(self, tmp_path):
        executor = ModeAExecutor(csv_dir=str(tmp_path))
        order = Order(
            symbol="000001",
            side=OrderSide.BUY,
            quantity=500,
            price=Decimal("10.50"),
            timestamp=__import__("datetime").datetime.now(),
        )
        order_id = executor.submit_order(order)
        assert order_id.startswith("MODEA-")
        pending = executor.get_pending_orders()
        assert len(pending) == 1

    def test_cancel_order(self, tmp_path):
        executor = ModeAExecutor(csv_dir=str(tmp_path))
        order = Order(
            symbol="000001",
            side=OrderSide.BUY,
            quantity=500,
            price=Decimal("10.50"),
            timestamp=__import__("datetime").datetime.now(),
        )
        order_id = executor.submit_order(order)
        result = executor.cancel_order(order_id)
        assert result is True
        pending = executor.get_pending_orders()
        assert len(pending) == 0

    def test_cancel_nonexistent_order(self, tmp_path):
        executor = ModeAExecutor(csv_dir=str(tmp_path))
        result = executor.cancel_order("MODEA-999")
        assert result is False

    def test_export_orders_to_csv(self, tmp_path):
        executor = ModeAExecutor(csv_dir=str(tmp_path))
        order = Order(
            symbol="000001",
            side=OrderSide.BUY,
            quantity=500,
            price=Decimal("10.50"),
            timestamp=__import__("datetime").datetime(2024, 1, 2, 9, 30),
        )
        executor.submit_order(order)
        executor.export_orders()

        orders_file = tmp_path / "pending_orders.csv"
        assert orders_file.exists()
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd /workspace/chixiao && pytest tests/test_mode_a.py -v`
Expected: FAIL

- [ ] **Step 3: 实现Mode A执行器**

```python
from __future__ import annotations

import csv
import uuid
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional

from chixiao.core.interfaces import Executor
from chixiao.core.models import Order, Position


class ModeAExecutor(Executor):
    def __init__(self, csv_dir: str = "data/positions"):
        self._csv_dir = Path(csv_dir)
        self._pending_orders: dict[str, Order] = {}

    def sync_positions(self) -> list[Position]:
        positions_file = self._csv_dir / "positions.csv"
        if not positions_file.exists():
            return []

        positions = []
        with open(positions_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    pos = Position(
                        symbol=row["symbol"],
                        name=row.get("name", ""),
                        quantity=int(row["quantity"]),
                        avg_cost=Decimal(row["avg_cost"]),
                        current_price=Decimal(row["current_price"]),
                    )
                    positions.append(pos)
                except (KeyError, ValueError):
                    continue

        return positions

    def submit_order(self, order: Order) -> str:
        order_id = f"MODEA-{uuid.uuid4().hex[:8].upper()}"
        self._pending_orders[order_id] = order
        return order_id

    def cancel_order(self, order_id: str) -> bool:
        if order_id in self._pending_orders:
            del self._pending_orders[order_id]
            return True
        return False

    def get_pending_orders(self) -> dict[str, Order]:
        return dict(self._pending_orders)

    def export_orders(self) -> None:
        self._csv_dir.mkdir(parents=True, exist_ok=True)
        orders_file = self._csv_dir / "pending_orders.csv"

        with open(orders_file, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["order_id", "symbol", "side", "quantity", "price", "timestamp"])
            for order_id, order in self._pending_orders.items():
                writer.writerow([
                    order_id,
                    order.symbol,
                    order.side.value,
                    order.quantity,
                    str(order.price),
                    order.timestamp.isoformat(),
                ])
```

- [ ] **Step 4: 创建示例持仓CSV**

```csv
symbol,name,quantity,avg_cost,current_price
000001,平安银行,1000,10.50,11.00
600036,招商银行,500,35.00,36.00
002415,海康威视,800,28.50,29.20
```

- [ ] **Step 5: 运行测试确认通过**

Run: `cd /workspace/chixiao && pytest tests/test_mode_a.py -v`
Expected: 全部 PASS

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat: add Mode A executor with CSV sync and order management"
```

---

### Task 10: 持仓管理器

**Files:**
- Create: `chixiao/src/chixiao/portfolio/position_manager.py`
- Create: `chixiao/tests/test_position_manager.py`

- [ ] **Step 1: 编写持仓管理器测试**

```python
from datetime import datetime
from decimal import Decimal
from chixiao.core.models import Position, Portfolio
from chixiao.portfolio.position_manager import PositionManager


class TestPositionManager:
    def test_update_position_new(self):
        mgr = PositionManager()
        mgr.update_position("000001", "平安银行", 1000, Decimal("10.50"))
        pos = mgr.get_position("000001")
        assert pos is not None
        assert pos.quantity == 1000
        assert pos.avg_cost == Decimal("10.50")

    def test_update_position_add(self):
        mgr = PositionManager()
        mgr.update_position("000001", "平安银行", 1000, Decimal("10.00"))
        mgr.update_position("000001", "平安银行", 500, Decimal("11.00"))
        pos = mgr.get_position("000001")
        assert pos.quantity == 1500
        assert pos.avg_cost == Decimal("10.33")

    def test_update_position_reduce(self):
        mgr = PositionManager()
        mgr.update_position("000001", "平安银行", 1000, Decimal("10.00"))
        mgr.reduce_position("000001", 300)
        pos = mgr.get_position("000001")
        assert pos.quantity == 700

    def test_remove_position(self):
        mgr = PositionManager()
        mgr.update_position("000001", "平安银行", 1000, Decimal("10.00"))
        mgr.remove_position("000001")
        assert mgr.get_position("000001") is None

    def test_get_portfolio(self):
        mgr = PositionManager()
        mgr.update_position("000001", "平安银行", 1000, Decimal("10.00"))
        mgr.update_position("600036", "招商银行", 500, Decimal("35.00"))
        mgr.set_cash(Decimal("50000"))
        portfolio = mgr.get_portfolio()
        assert len(portfolio.positions) == 2
        assert portfolio.cash == Decimal("50000")

    def test_position_weight(self):
        mgr = PositionManager()
        mgr.update_position("000001", "平安银行", 1000, Decimal("10.00"))
        mgr.update_position("600036", "招商银行", 500, Decimal("35.00"))
        mgr.set_cash(Decimal("50000"))
        weights = mgr.get_position_weights()
        assert "000001" in weights
        assert "600036" in weights
        total = sum(weights.values())
        assert abs(total - 1.0) < 0.01
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd /workspace/chixiao && pytest tests/test_position_manager.py -v`
Expected: FAIL

- [ ] **Step 3: 实现持仓管理器**

```python
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
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd /workspace/chixiao && pytest tests/test_position_manager.py -v`
Expected: 全部 PASS

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: add position manager with CRUD and portfolio aggregation"
```

---

### Task 11: 风控管理器

**Files:**
- Create: `chixiao/src/chixiao/portfolio/risk_manager.py`
- Create: `chixiao/tests/test_risk_manager.py`

- [ ] **Step 1: 编写风控管理器测试**

```python
from datetime import datetime
from decimal import Decimal
from chixiao.core.models import Position, Portfolio, Signal, SignalDirection
from chixiao.portfolio.risk_manager import RiskManager


def _make_portfolio_with_positions(positions_data: list[tuple]) -> Portfolio:
    positions = []
    for sym, name, qty, cost, price in positions_data:
        positions.append(Position(sym, name, qty, Decimal(str(cost)), Decimal(str(price))))
    return Portfolio(positions=positions, cash=Decimal("50000"), timestamp=datetime.now())


class TestRiskManager:
    def test_check_position_limit_pass(self):
        mgr = RiskManager(max_position_pct=0.25)
        portfolio = _make_portfolio_with_positions([
            ("000001", "平安银行", 1000, 10.0, 11.0),
        ])
        signal = Signal(symbol="600036", direction=SignalDirection.BUY, strength=0.8,
                       timestamp=datetime.now())
        result = mgr.check_position_limit(signal, portfolio, Decimal("10000"))
        assert result.allowed is True

    def test_check_position_limit_fail(self):
        mgr = RiskManager(max_position_pct=0.10)
        portfolio = _make_portfolio_with_positions([
            ("000001", "平安银行", 1000, 10.0, 11.0),
        ])
        signal = Signal(symbol="600036", direction=SignalDirection.BUY, strength=0.8,
                       timestamp=datetime.now())
        result = mgr.check_position_limit(signal, portfolio, Decimal("15000"))
        assert result.allowed is False
        assert "仓位上限" in result.reason

    def test_check_drawdown(self):
        mgr = RiskManager(max_drawdown_pct=0.10)
        portfolio = _make_portfolio_with_positions([
            ("000001", "平安银行", 1000, 10.0, 9.0),
        ])
        result = mgr.check_drawdown(portfolio, Decimal("60000"))
        assert result.triggered is True

    def test_check_drawdown_safe(self):
        mgr = RiskManager(max_drawdown_pct=0.10)
        portfolio = _make_portfolio_with_positions([
            ("000001", "平安银行", 1000, 10.0, 10.5),
        ])
        result = mgr.check_drawdown(portfolio, Decimal("60000"))
        assert result.triggered is False
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd /workspace/chixiao && pytest tests/test_risk_manager.py -v`
Expected: FAIL

- [ ] **Step 3: 实现风控管理器**

```python
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
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd /workspace/chixiao && pytest tests/test_risk_manager.py -v`
Expected: 全部 PASS

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: add risk manager with position limit and drawdown checks"
```

---

### Task 12: FastAPI后端服务

**Files:**
- Create: `chixiao/src/chixiao/api/main.py`
- Create: `chixiao/tests/test_api.py`

- [ ] **Step 1: 编写API测试**

```python
from fastapi.testclient import TestClient
from chixiao.api.main import app


class TestAPI:
    def test_health_check(self):
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "0.1.0"

    def test_get_signals(self):
        client = TestClient(app)
        response = client.get("/api/signals", params={"symbols": "000001"})
        assert response.status_code == 200

    def test_get_positions(self):
        client = TestClient(app)
        response = client.get("/api/positions")
        assert response.status_code == 200

    def test_submit_order(self):
        client = TestClient(app)
        order_data = {
            "symbol": "000001",
            "side": "BUY",
            "quantity": 500,
            "price": "10.50",
        }
        response = client.post("/api/orders", json=order_data)
        assert response.status_code == 200
        data = response.json()
        assert "order_id" in data

    def test_get_portfolio(self):
        client = TestClient(app)
        response = client.get("/api/portfolio")
        assert response.status_code == 200
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd /workspace/chixiao && pytest tests/test_api.py -v`
Expected: FAIL

- [ ] **Step 3: 实现FastAPI应用**

```python
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import FastAPI, Query
from pydantic import BaseModel

from chixiao.alpha.alpha_model import AlphaModel
from chixiao.alpha.factor_calculator import FactorCalculator
from chixiao.core.config import load_config
from chixiao.data.akshare_adapter import AKShareAdapter
from chixiao.execution.mode_a import ModeAExecutor
from chixiao.portfolio.position_manager import PositionManager

app = FastAPI(title="赤霄量化交易系统", version="0.1.0")

_config = load_config()
_data_adapter = AKShareAdapter()
_factor_calc = FactorCalculator()
_alpha_model = AlphaModel(_factor_calc)
_executor = ModeAExecutor(csv_dir=_config.csv_dir)
_position_mgr = PositionManager()


class OrderRequest(BaseModel):
    symbol: str
    side: str
    quantity: int
    price: str


@app.get("/health")
def health_check():
    return {"status": "ok", "version": "0.1.0"}


@app.get("/api/signals")
def get_signals(symbols: str = Query(..., description="逗号分隔的股票代码")):
    from chixiao.core.models import OrderSide
    symbol_list = [s.strip() for s in symbols.split(",")]
    results = []
    for sym in symbol_list:
        try:
            bars = _data_adapter.get_bars(sym, datetime.now().date(), datetime.now().date())
            if bars:
                signal = _alpha_model.generate_signal(sym, bars)
                if signal:
                    results.append({
                        "symbol": signal.symbol,
                        "direction": signal.direction.value,
                        "strength": signal.strength,
                        "factors": signal.factors,
                    })
        except Exception:
            continue
    return {"signals": results}


@app.get("/api/positions")
def get_positions():
    positions = _executor.sync_positions()
    return {
        "positions": [
            {
                "symbol": p.symbol,
                "name": p.name,
                "quantity": p.quantity,
                "avg_cost": str(p.avg_cost),
                "current_price": str(p.current_price),
                "market_value": str(p.market_value),
                "unrealized_pnl": str(p.unrealized_pnl),
                "unrealized_pnl_pct": str(p.unrealized_pnl_pct) + "%",
            }
            for p in positions
        ]
    }


@app.post("/api/orders")
def submit_order(order: OrderRequest):
    from chixiao.core.models import Order, OrderSide
    side = OrderSide.BUY if order.side.upper() == "BUY" else OrderSide.SELL
    new_order = Order(
        symbol=order.symbol,
        side=side,
        quantity=order.quantity,
        price=Decimal(order.price),
        timestamp=datetime.now(),
    )
    order_id = _executor.submit_order(new_order)
    return {"order_id": order_id, "status": "pending"}


@app.get("/api/portfolio")
def get_portfolio():
    positions = _executor.sync_positions()
    for pos in positions:
        _position_mgr.update_position(pos.symbol, pos.name, pos.quantity, pos.current_price)
    portfolio = _position_mgr.get_portfolio()
    return {
        "total_value": str(portfolio.total_value),
        "cash": str(portfolio.cash),
        "positions_count": len(portfolio.positions),
    }
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd /workspace/chixiao && pytest tests/test_api.py -v`
Expected: 全部 PASS

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: add FastAPI backend with signals, positions, orders, portfolio endpoints"
```

---

### Task 13: Streamlit仪表盘

**Files:**
- Create: `chixiao/dashboard/app.py`

- [ ] **Step 1: 实现Streamlit仪表盘**

```python
import streamlit as st
from datetime import date, timedelta
from decimal import Decimal

from chixiao.core.config import load_config
from chixiao.data.akshare_adapter import AKShareAdapter
from chixiao.data.cleaner import DataCleaner
from chixiao.alpha.factor_calculator import FactorCalculator
from chixiao.alpha.alpha_model import AlphaModel
from chixiao.execution.mode_a import ModeAExecutor
from chixiao.portfolio.position_manager import PositionManager
from chixiao.portfolio.risk_manager import RiskManager

st.set_page_config(page_title="赤霄量化交易系统", layout="wide")
st.title("🔥 赤霄量化交易决策辅助系统")

config = load_config()
data_adapter = AKShareAdapter()
factor_calc = FactorCalculator()
alpha_model = AlphaModel(factor_calc)
executor = ModeAExecutor(csv_dir=config.csv_dir)
position_mgr = PositionManager()
risk_mgr = RiskManager(
    max_position_pct=config.risk_max_position_pct,
    max_drawdown_pct=config.risk_max_portfolio_drawdown_pct,
)

tab_signals, tab_positions, tab_risk, tab_orders = st.tabs(
    ["📊 策略信号", "💼 持仓管理", "🛡️ 风控监控", "📋 订单管理"]
)

with tab_signals:
    st.header("策略信号分析")
    col1, col2 = st.columns([1, 3])
    with col1:
        symbol_input = st.text_input("股票代码", value="000001")
        days = st.slider("回溯天数", min_value=30, max_value=120, value=60)
        analyze_btn = st.button("分析信号", type="primary")

    with col2:
        if analyze_btn:
            with st.spinner("正在获取数据并计算因子..."):
                end = date.today()
                start = end - timedelta(days=days)
                bars = data_adapter.get_bars(symbol_input, start, end)
                if bars:
                    bars = DataCleaner.clean(bars)
                    signal = alpha_model.generate_signal(symbol_input, bars)
                    if signal:
                        direction_emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}
                        st.metric(
                            label=f"{symbol_input} 信号方向",
                            value=f"{direction_emoji.get(signal.direction.value, '')} {signal.direction.value}",
                            delta=f"强度: {signal.strength:.2f}",
                        )
                        st.subheader("因子详情")
                        factors_df = {
                            "因子名称": list(signal.factors.keys()),
                            "因子值": [round(v, 4) if v else "N/A" for v in signal.factors.values()],
                        }
                        st.dataframe(factors_df, use_container_width=True)

                        import pandas as pd
                        chart_data = pd.DataFrame({
                            "日期": [b.timestamp for b in bars],
                            "收盘价": [float(b.close) for b in bars],
                        })
                        st.line_chart(chart_data, x="日期", y="收盘价")
                    else:
                        st.warning("无法生成信号，数据不足")
                else:
                    st.error("未获取到数据，请检查股票代码")

with tab_positions:
    st.header("持仓管理")
    col_sync, col_upload = st.columns(2)
    with col_sync:
        if st.button("从CSV同步持仓"):
            positions = executor.sync_positions()
            if positions:
                st.success(f"成功同步 {len(positions)} 个持仓")
                for pos in positions:
                    position_mgr.update_position(pos.symbol, pos.name, pos.quantity, pos.current_price)
            else:
                st.warning("未找到持仓数据，请先上传CSV文件")

    with col_upload:
        uploaded = st.file_uploader("上传持仓CSV", type=["csv"])
        if uploaded:
            import csv
            import io
            content = uploaded.read().decode("utf-8")
            reader = csv.DictReader(io.StringIO(content))
            count = 0
            for row in reader:
                try:
                    position_mgr.update_position(
                        row["symbol"],
                        row.get("name", ""),
                        int(row["quantity"]),
                        Decimal(row["current_price"]),
                    )
                    count += 1
                except (KeyError, ValueError):
                    continue
            st.success(f"成功导入 {count} 个持仓")

    portfolio = position_mgr.get_portfolio()
    if portfolio.positions:
        st.subheader("当前持仓")
        pos_data = []
        for p in portfolio.positions:
            pos_data.append({
                "代码": p.symbol,
                "名称": p.name,
                "数量": p.quantity,
                "成本价": float(p.avg_cost),
                "现价": float(p.current_price),
                "市值": float(p.market_value),
                "浮盈": float(p.unrealized_pnl),
                "浮盈%": f"{float(p.unrealized_pnl_pct)}%",
            })
        st.dataframe(pos_data, use_container_width=True)
        st.metric("总资产", value=f"¥{float(portfolio.total_value):,.2f}")
    else:
        st.info("暂无持仓数据")

with tab_risk:
    st.header("风控监控")
    portfolio = position_mgr.get_portfolio()
    if portfolio.positions:
        weights = position_mgr.get_position_weights()
        st.subheader("仓位分布")
        import pandas as pd
        weight_df = pd.DataFrame({
            "股票代码": list(weights.keys()),
            "仓位占比": [f"{w:.1%}" for w in weights.values()],
        })
        st.dataframe(weight_df, use_container_width=True)

        peak = st.number_input("历史最高资产", value=float(portfolio.total_value) * 1.05)
        dd_result = risk_mgr.check_drawdown(portfolio, Decimal(str(peak)))
        if dd_result.triggered:
            st.error(f"⚠️ 回撤预警: {dd_result.reason}")
        else:
            st.success(f"✅ 当前回撤: {dd_result.drawdown_pct:.1%}，在安全范围内")
    else:
        st.info("暂无持仓数据，无法进行风控分析")

with tab_orders:
    st.header("订单管理")
    col_buy, col_sell = st.columns(2)
    with col_buy:
        st.subheader("买入下单")
        buy_symbol = st.text_input("买入代码", key="buy_symbol")
        buy_qty = st.number_input("买入数量", min_value=100, step=100, key="buy_qty")
        buy_price = st.text_input("买入价格", key="buy_price")
        if st.button("提交买入", type="primary"):
            if buy_symbol and buy_price:
                from chixiao.core.models import Order, OrderSide
                order = Order(
                    symbol=buy_symbol,
                    side=OrderSide.BUY,
                    quantity=buy_qty,
                    price=Decimal(buy_price),
                    timestamp=__import__("datetime").datetime.now(),
                )
                order_id = executor.submit_order(order)
                st.success(f"买入订单已提交: {order_id}")

    with col_sell:
        st.subheader("卖出下单")
        sell_symbol = st.text_input("卖出代码", key="sell_symbol")
        sell_qty = st.number_input("卖出数量", min_value=100, step=100, key="sell_qty")
        sell_price = st.text_input("卖出价格", key="sell_price")
        if st.button("提交卖出"):
            if sell_symbol and sell_price:
                from chixiao.core.models import Order, OrderSide
                order = Order(
                    symbol=sell_symbol,
                    side=OrderSide.SELL,
                    quantity=sell_qty,
                    price=Decimal(sell_price),
                    timestamp=__import__("datetime").datetime.now(),
                )
                order_id = executor.submit_order(order)
                st.success(f"卖出订单已提交: {order_id}")

    st.subheader("待执行订单")
    pending = executor.get_pending_orders()
    if pending:
        for oid, order in pending.items():
            st.write(f"**{oid}** | {order.symbol} | {order.side.value} | {order.quantity}@{order.price}")
        if st.button("导出订单到CSV"):
            executor.export_orders()
            st.success("订单已导出到CSV文件")
    else:
        st.info("暂无待执行订单")
```

- [ ] **Step 2: 验证仪表盘可启动**

Run: `cd /workspace/chixiao && python -c "import dashboard.app"`
Expected: 无导入错误

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "feat: add Streamlit dashboard with signals, positions, risk, orders tabs"
```

---

### Task 14: 集成测试与全量验证

**Files:**
- Modify: `chixiao/tests/conftest.py`

- [ ] **Step 1: 运行全量单元测试**

Run: `cd /workspace/chixiao && pytest tests/ -v --tb=short`
Expected: 全部 PASS

- [ ] **Step 2: 运行 ruff 检查代码质量**

Run: `cd /workspace/chixiao && ruff check src/ dashboard/`
Expected: 无错误（或仅有可忽略的警告）

- [ ] **Step 3: 运行测试覆盖率检查**

Run: `cd /workspace/chixiao && pytest tests/ --cov=chixiao --cov-report=term-missing`
Expected: 核心模块覆盖率 > 70%

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "chore: integration test pass, code quality verified"
```

---

## 自审清单

### 1. 规格覆盖检查

| 需求项 | 对应Task |
|:---|:---|
| 数据采集(AKShare) | Task 5 |
| 数据清洗对齐 | Task 6 |
| 技术因子计算 | Task 7 |
| Alpha信号生成 | Task 8 |
| CSV手动同步 | Task 9 |
| 持仓管理 | Task 10 |
| 风控规则 | Task 11 |
| FastAPI后端 | Task 12 |
| Streamlit仪表盘 | Task 13 |
| 配置管理 | Task 4 |
| 核心领域模型 | Task 2 |
| 抽象接口 | Task 3 |
| 项目脚手架 | Task 1 |

### 2. 占位符扫描

无 TBD/TODO/实现后补充等占位符。所有步骤均包含完整代码。

### 3. 类型一致性检查

- `DataAdapter.get_bars()` → 返回 `list[Bar]`，AKShareAdapter实现一致
- `Executor.submit_order()` → 接受 `Order` 返回 `str`，ModeAExecutor实现一致
- `FactorProvider.compute_factors()` → 接受 `symbol, bars` 返回 `dict[str, float]`，FactorCalculator实现一致
- `Position` 的 `avg_cost`, `current_price` 均为 `Decimal` 类型，所有引用处一致
- `SignalDirection` 和 `OrderSide` 枚举值在所有模块中引用一致
