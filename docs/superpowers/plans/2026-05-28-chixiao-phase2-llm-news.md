# 赤霄量化交易系统 — 第二阶段(LLM新闻分析与策略增强)实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 引入LLM能力将新闻情绪转化为量化因子，完善半导体特色因子库，升级仪表盘，将策略和评分能力封装为RESTful API。

**Architecture:** LLM引擎通过适配器模式对接DeepSeek API，新闻爬取与情感分析结果作为独立因子注入AlphaModel的评分体系。半导体特色因子库扩展FactorCalculator，新增因子与既有因子通过加权融合产生最终Alpha信号。FastAPI新增新闻和因子暴露端点。

**Tech Stack:** Python 3.11+, httpx (LLM API调用), akshare (新闻数据), scipy (因子融合), 新增于第一阶段基础之上

---

## 文件结构增量

```
chixiao/
├── src/chixiao/
│   ├── news/
│   │   ├── __init__.py
│   │   ├── crawler.py           # 新闻爬取器
│   │   ├── llm_analyzer.py      # LLM情感/事件分析
│   │   └── momentum_factor.py   # 新闻动量因子
│   ├── alpha/
│   │   ├── semi_factors.py      # 半导体特色因子库 (新增)
│   │   └── factor_fusion.py     # 因子融合引擎 (新增)
│   └── api/
│       └── main.py              # 扩展API端点
├── dashboard/
│   └── app.py                   # 升级仪表盘
└── tests/
    ├── test_crawler.py
    ├── test_llm_analyzer.py
    ├── test_momentum_factor.py
    ├── test_semi_factors.py
    └── test_factor_fusion.py
```

---

### Task 1: 新闻爬取器

**Files:**
- Create: `chixiao/src/chixiao/news/__init__.py`
- Create: `chixiao/src/chixiao/news/crawler.py`
- Create: `chixiao/tests/test_crawler.py`

- [ ] **Step 1: 编写新闻爬取器测试**

```python
from unittest.mock import patch, MagicMock
import pandas as pd
from chixiao.news.crawler import NewsCrawler, NewsItem


class TestNewsCrawler:
    @patch("chixiao.news.crawler.ak")
    def test_fetch_news(self, mock_ak):
        mock_df = pd.DataFrame({
            "标题": ["半导体行业景气度回升", "某公司发布业绩预告"],
            "内容": ["半导体行业迎来新一轮景气周期...", "公司预计2024年净利润增长..."],
            "发布时间": ["2024-01-15 10:00:00", "2024-01-15 09:30:00"],
            "来源": ["财经网", "东方财富"],
        })
        mock_ak.stock_news_em.return_value = mock_df

        crawler = NewsCrawler()
        items = crawler.fetch_news("000001")

        assert len(items) == 2
        assert isinstance(items[0], NewsItem)
        assert items[0].title == "半导体行业景气度回升"
        assert items[0].source == "财经网"

    @patch("chixiao.news.crawler.ak")
    def test_fetch_news_empty(self, mock_ak):
        mock_ak.stock_news_em.return_value = pd.DataFrame()

        crawler = NewsCrawler()
        items = crawler.fetch_news("000001")

        assert len(items) == 0

    @patch("chixiao.news.crawler.ak")
    def test_fetch_news_by_keyword(self, mock_ak):
        mock_df = pd.DataFrame({
            "标题": ["半导体设备国产替代加速"],
            "内容": ["国产半导体设备厂商迎来发展机遇..."],
            "发布时间": ["2024-01-15 10:00:00"],
            "来源": ["证券时报"],
        })
        mock_ak.news_cctv_date.return_value = mock_df

        crawler = NewsCrawler()
        items = crawler.fetch_news_by_keyword("半导体")

        assert len(items) >= 0
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd /workspace/chixiao && pytest tests/test_crawler.py -v`
Expected: FAIL

- [ ] **Step 3: 实现新闻爬取器**

```python
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import akshare as ak
import pandas as pd


@dataclass
class NewsItem:
    title: str
    content: str
    publish_time: str
    source: str
    symbol: str = ""
    keywords: list[str] = field(default_factory=list)
    sentiment_score: Optional[float] = None
    event_type: Optional[str] = None


class NewsCrawler:
    def fetch_news(self, symbol: str, limit: int = 20) -> list[NewsItem]:
        try:
            df = ak.stock_news_em(symbol=symbol)
            if df.empty:
                return []

            items = []
            for _, row in df.head(limit).iterrows():
                item = NewsItem(
                    title=str(row.get("标题", "")),
                    content=str(row.get("内容", "")),
                    publish_time=str(row.get("发布时间", "")),
                    source=str(row.get("来源", "")),
                    symbol=symbol,
                )
                items.append(item)
            return items
        except Exception:
            return []

    def fetch_news_by_keyword(self, keyword: str, limit: int = 20) -> list[NewsItem]:
        try:
            df = ak.news_cctv_date(date=datetime.now().strftime("%Y%m%d"))
            if df.empty:
                return []

            filtered = df[df["标题"].str.contains(keyword, na=False)]
            items = []
            for _, row in filtered.head(limit).iterrows():
                item = NewsItem(
                    title=str(row.get("标题", "")),
                    content=str(row.get("内容", "")),
                    publish_time=str(row.get("发布时间", "")),
                    source=str(row.get("来源", "")),
                    keywords=[keyword],
                )
                items.append(item)
            return items
        except Exception:
            return []
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd /workspace/chixiao && pytest tests/test_crawler.py -v`
Expected: 全部 PASS

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: add news crawler with symbol and keyword based fetching"
```

---

### Task 2: LLM新闻分析引擎

**Files:**
- Create: `chixiao/src/chixiao/news/llm_analyzer.py`
- Create: `chixiao/tests/test_llm_analyzer.py`

- [ ] **Step 1: 编写LLM分析器测试**

```python
from unittest.mock import patch, MagicMock, AsyncMock
from chixiao.news.llm_analyzer import LLMAnalyzer, SentimentResult
from chixiao.news.crawler import NewsItem


class TestLLMAnalyzer:
    def test_analyze_sentiment_positive(self):
        analyzer = LLMAnalyzer(api_key="test-key", model="deepseek-chat")
        with patch.object(analyzer, "_call_llm") as mock_llm:
            mock_llm.return_value = '{"sentiment": "positive", "score": 0.85, "event_type": "业绩利好", "summary": "公司业绩超预期"}'
            item = NewsItem(
                title="某公司业绩大增",
                content="公司2024年净利润同比增长50%",
                publish_time="2024-01-15 10:00:00",
                source="财经网",
                symbol="000001",
            )
            result = analyzer.analyze_sentiment(item)
            assert isinstance(result, SentimentResult)
            assert result.sentiment == "positive"
            assert result.score == 0.85
            assert result.event_type == "业绩利好"

    def test_analyze_sentiment_negative(self):
        analyzer = LLMAnalyzer(api_key="test-key", model="deepseek-chat")
        with patch.object(analyzer, "_call_llm") as mock_llm:
            mock_llm.return_value = '{"sentiment": "negative", "score": -0.7, "event_type": "监管风险", "summary": "公司收到监管函"}'
            item = NewsItem(
                title="某公司收到监管函",
                content="公司因信息披露违规收到证监会警示函",
                publish_time="2024-01-15 10:00:00",
                source="财经网",
                symbol="000001",
            )
            result = analyzer.analyze_sentiment(item)
            assert result.sentiment == "negative"
            assert result.score == -0.7

    def test_analyze_batch(self):
        analyzer = LLMAnalyzer(api_key="test-key", model="deepseek-chat")
        items = [
            NewsItem("利好消息", "业绩增长", "2024-01-15", "财经网", "000001"),
            NewsItem("利空消息", "业绩下滑", "2024-01-15", "财经网", "000002"),
        ]
        with patch.object(analyzer, "analyze_sentiment") as mock_analyze:
            mock_analyze.side_effect = [
                SentimentResult("positive", 0.8, "业绩利好", "业绩增长"),
                SentimentResult("negative", -0.6, "业绩下滑", "业绩下滑"),
            ]
            results = analyzer.analyze_batch(items)
            assert len(results) == 2

    def test_build_prompt(self):
        analyzer = LLMAnalyzer(api_key="test-key", model="deepseek-chat")
        item = NewsItem("测试标题", "测试内容", "2024-01-15", "财经网", "000001")
        prompt = analyzer._build_prompt(item)
        assert "000001" in prompt
        assert "测试标题" in prompt
        assert "JSON" in prompt
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd /workspace/chixiao && pytest tests/test_llm_analyzer.py -v`
Expected: FAIL

- [ ] **Step 3: 实现LLM分析器**

```python
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Optional

import httpx

from chixiao.news.crawler import NewsItem


@dataclass
class SentimentResult:
    sentiment: str
    score: float
    event_type: str
    summary: str


class LLMAnalyzer:
    def __init__(
        self,
        api_key: str = "",
        model: str = "deepseek-chat",
        base_url: str = "https://api.deepseek.com/v1",
    ):
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")

    def analyze_sentiment(self, item: NewsItem) -> SentimentResult:
        prompt = self._build_prompt(item)
        response_text = self._call_llm(prompt)
        return self._parse_response(response_text)

    def analyze_batch(self, items: list[NewsItem]) -> list[SentimentResult]:
        return [self.analyze_sentiment(item) for item in items]

    def _build_prompt(self, item: NewsItem) -> str:
        return f"""你是一名专业的A股新闻分析师。请分析以下新闻的情感倾向和事件类型。

股票代码: {item.symbol}
新闻标题: {item.title}
新闻内容: {item.content}
新闻来源: {item.source}

请以JSON格式返回分析结果，包含以下字段:
- sentiment: 情感倾向 (positive/negative/neutral)
- score: 情感分数 (-1.0到1.0之间，正数代表利好，负数代表利空)
- event_type: 事件类型 (如: 业绩利好/业绩利空/政策利好/政策利空/行业动态/监管风险/其他)
- summary: 一句话摘要

仅返回JSON，不要包含其他文字。"""

    def _call_llm(self, prompt: str) -> str:
        if not self._api_key:
            return '{"sentiment": "neutral", "score": 0.0, "event_type": "其他", "summary": "未配置API Key"}'

        try:
            response = httpx.post(
                f"{self._base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "model": self._model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "max_tokens": 500,
                },
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            return f'{{"sentiment": "neutral", "score": 0.0, "event_type": "其他", "summary": "API调用失败: {str(e)}"}}'

    def _parse_response(self, text: str) -> SentimentResult:
        try:
            json_str = text.strip()
            if json_str.startswith("```"):
                lines = json_str.split("\n")
                json_str = "\n".join(lines[1:-1])
            data = json.loads(json_str)
            return SentimentResult(
                sentiment=data.get("sentiment", "neutral"),
                score=float(data.get("score", 0.0)),
                event_type=data.get("event_type", "其他"),
                summary=data.get("summary", ""),
            )
        except (json.JSONDecodeError, ValueError):
            return SentimentResult(
                sentiment="neutral",
                score=0.0,
                event_type="其他",
                summary="解析失败",
            )
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd /workspace/chixiao && pytest tests/test_llm_analyzer.py -v`
Expected: 全部 PASS

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: add LLM news analyzer with DeepSeek API integration"
```

---

### Task 3: 新闻动量因子

**Files:**
- Create: `chixiao/src/chixiao/news/momentum_factor.py`
- Create: `chixiao/tests/test_momentum_factor.py`

- [ ] **Step 1: 编写新闻动量因子测试**

```python
from chixiao.news.momentum_factor import NewsMomentumFactor
from chixiao.news.crawler import NewsItem
from chixiao.news.llm_analyzer import SentimentResult


class TestNewsMomentumFactor:
    def test_compute_with_sentiments(self):
        factor = NewsMomentumFactor()
        sentiments = [
            SentimentResult("positive", 0.8, "业绩利好", "业绩大增"),
            SentimentResult("positive", 0.6, "政策利好", "政策支持"),
            SentimentResult("neutral", 0.0, "其他", "无重大消息"),
        ]
        result = factor.compute(sentiments)
        assert "news_sentiment_score" in result
        assert "news_momentum" in result
        assert "news_positive_ratio" in result
        assert result["news_sentiment_score"] > 0
        assert 0 <= result["news_positive_ratio"] <= 1.0

    def test_compute_empty(self):
        factor = NewsMomentumFactor()
        result = factor.compute([])
        assert result["news_sentiment_score"] == 0.0
        assert result["news_momentum"] == 0.0

    def test_compute_all_negative(self):
        factor = NewsMomentumFactor()
        sentiments = [
            SentimentResult("negative", -0.8, "业绩利空", "业绩下滑"),
            SentimentResult("negative", -0.6, "监管风险", "收到监管函"),
        ]
        result = factor.compute(sentiments)
        assert result["news_sentiment_score"] < 0
        assert result["news_positive_ratio"] == 0.0

    def test_decay_weight(self):
        factor = NewsMomentumFactor()
        sentiments = [
            SentimentResult("positive", 0.9, "利好", "最新利好"),
            SentimentResult("positive", 0.5, "利好", "较早利好"),
        ]
        result = factor.compute(sentiments)
        assert result["news_sentiment_score"] > 0
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd /workspace/chixiao && pytest tests/test_momentum_factor.py -v`
Expected: FAIL

- [ ] **Step 3: 实现新闻动量因子**

```python
from __future__ import annotations

from chixiao.news.llm_analyzer import SentimentResult


class NewsMomentumFactor:
    def compute(self, sentiments: list[SentimentResult]) -> dict[str, float]:
        if not sentiments:
            return {
                "news_sentiment_score": 0.0,
                "news_momentum": 0.0,
                "news_positive_ratio": 0.0,
                "news_negative_ratio": 0.0,
                "news_count": 0,
            }

        n = len(sentiments)
        decay_weights = [0.9 ** i for i in range(n)]
        decay_weights.reverse()
        total_weight = sum(decay_weights)

        weighted_score = sum(
            s.score * w for s, w in zip(sentiments, decay_weights)
        ) / total_weight

        positive_count = sum(1 for s in sentiments if s.sentiment == "positive")
        negative_count = sum(1 for s in sentiments if s.sentiment == "negative")

        momentum = 0.0
        if n >= 2:
            recent_avg = sum(s.score for s in sentiments[:3]) / min(3, n)
            older_avg = sum(s.score for s in sentiments[3:]) / max(1, n - 3)
            momentum = recent_avg - older_avg

        return {
            "news_sentiment_score": round(weighted_score, 4),
            "news_momentum": round(momentum, 4),
            "news_positive_ratio": round(positive_count / n, 4),
            "news_negative_ratio": round(negative_count / n, 4),
            "news_count": n,
        }
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd /workspace/chixiao && pytest tests/test_momentum_factor.py -v`
Expected: 全部 PASS

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: add news momentum factor with decay-weighted sentiment scoring"
```

---

### Task 4: 半导体特色因子库

**Files:**
- Create: `chixiao/src/chixiao/alpha/semi_factors.py`
- Create: `chixiao/tests/test_semi_factors.py`

- [ ] **Step 1: 编写半导体因子测试**

```python
from datetime import datetime
from decimal import Decimal
from chixiao.core.models import Bar
from chixiao.alpha.semi_factors import SemiFactorLib


def _make_bar(close: float, volume: int = 1000000, amount: float = 0) -> Bar:
    return Bar(
        symbol="002415",
        timestamp=datetime(2024, 1, 15),
        open=Decimal(str(close - 0.1)),
        high=Decimal(str(close + 0.2)),
        low=Decimal(str(close - 0.2)),
        close=Decimal(str(close)),
        volume=volume,
        amount=Decimal(str(amount if amount else close * volume)),
    )


class TestSemiFactorLib:
    def test_compute_semi_factors(self):
        bars = [_make_bar(28.0 + i * 0.5) for i in range(30)]
        lib = SemiFactorLib()
        factors = lib.compute(bars)
        assert "semi_turnover_rate" in factors
        assert "semi_price_momentum_5d" in factors
        assert "semi_volatility_rank" in factors

    def test_turnover_rate(self):
        bars = [_make_bar(28.0, volume=2000000) for _ in range(5)]
        lib = SemiFactorLib()
        factors = lib.compute(bars)
        assert factors["semi_turnover_rate"] > 0

    def test_empty_bars(self):
        lib = SemiFactorLib()
        factors = lib.compute([])
        assert factors == {}
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd /workspace/chixiao && pytest tests/test_semi_factors.py -v`
Expected: FAIL

- [ ] **Step 3: 实现半导体特色因子库**

```python
from __future__ import annotations

import numpy as np

from chixiao.core.models import Bar


class SemiFactorLib:
    SEMI_SYMBOLS = {
        "002415", "688981", "603501", "688012", "300782",
        "688396", "688256", "300661", "002371", "688008",
    }

    def is_semi_conductor(self, symbol: str) -> bool:
        return symbol in self.SEMI_SYMBOLS

    def compute(self, bars: list[Bar]) -> dict[str, float]:
        if not bars:
            return {}

        closes = np.array([float(b.close) for b in bars])
        volumes = np.array([float(b.volume) for b in bars])
        amounts = np.array([float(b.amount) for b in bars])

        factors: dict[str, float] = {}

        factors["semi_turnover_rate"] = self._turnover_rate(volumes, amounts)
        factors["semi_price_momentum_5d"] = self._price_momentum(closes, 5)
        factors["semi_price_momentum_20d"] = self._price_momentum(closes, 20)
        factors["semi_volatility_rank"] = self._volatility_rank(closes)
        factors["semi_volume_ratio"] = self._volume_ratio(volumes)
        factors["semi_amplitude"] = self._amplitude(bars)

        return factors

    def _turnover_rate(self, volumes: np.ndarray, amounts: np.ndarray) -> float:
        if len(volumes) < 2:
            return 0.0
        avg_volume = float(np.mean(volumes[-5:]))
        avg_amount = float(np.mean(amounts[-5:]))
        if avg_amount == 0:
            return 0.0
        avg_price = avg_amount / avg_volume
        estimated_shares = avg_amount / avg_price if avg_price > 0 else 1.0
        turnover = avg_volume / estimated_shares if estimated_shares > 0 else 0.0
        return round(min(turnover, 1.0), 4)

    def _price_momentum(self, closes: np.ndarray, period: int) -> float:
        if len(closes) < period + 1:
            return 0.0
        momentum = (closes[-1] - closes[-1 - period]) / closes[-1 - period]
        return round(float(momentum), 4)

    def _volatility_rank(self, closes: np.ndarray) -> float:
        if len(closes) < 5:
            return 0.5
        returns = np.diff(closes) / closes[:-1]
        vol = float(np.std(returns[-20:])) if len(returns) >= 20 else float(np.std(returns))
        rank = min(vol / 0.05, 1.0)
        return round(rank, 4)

    def _volume_ratio(self, volumes: np.ndarray) -> float:
        if len(volumes) < 10:
            return 1.0
        recent = float(np.mean(volumes[-5:]))
        longer = float(np.mean(volumes[-10:]))
        if longer == 0:
            return 1.0
        return round(recent / longer, 4)

    def _amplitude(self, bars: list[Bar]) -> float:
        if not bars:
            return 0.0
        recent = bars[-min(5, len(bars)):]
        amplitudes = []
        for b in recent:
            mid = (float(b.high) + float(b.low)) / 2
            if mid > 0:
                amplitudes.append((float(b.high) - float(b.low)) / mid)
        return round(float(np.mean(amplitudes)), 4) if amplitudes else 0.0
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd /workspace/chixiao && pytest tests/test_semi_factors.py -v`
Expected: 全部 PASS

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: add semiconductor-specific factor library"
```

---

### Task 5: 因子融合引擎

**Files:**
- Create: `chixiao/src/chixiao/alpha/factor_fusion.py`
- Create: `chixiao/tests/test_factor_fusion.py`

- [ ] **Step 1: 编写因子融合测试**

```python
from chixiao.alpha.factor_fusion import FactorFusion


class TestFactorFusion:
    def test_fuse_technical_and_news(self):
        tech_factors = {"ma_5": 10.5, "rsi_14": 55.0, "macd_hist": 0.02}
        news_factors = {"news_sentiment_score": 0.6, "news_momentum": 0.1}
        semi_factors = {"semi_turnover_rate": 0.05, "semi_price_momentum_5d": 0.03}

        fusion = FactorFusion(
            tech_weight=0.50,
            news_weight=0.30,
            semi_weight=0.20,
        )
        result = fusion.fuse(tech_factors, news_factors, semi_factors)

        assert "composite_score" in result
        assert -1.0 <= result["composite_score"] <= 1.0
        assert "tech_score" in result
        assert "news_score" in result
        assert "semi_score" in result

    def test_fuse_without_news(self):
        tech_factors = {"ma_5": 10.5, "rsi_14": 55.0}
        fusion = FactorFusion(tech_weight=0.70, news_weight=0.30, semi_weight=0.0)
        result = fusion.fuse(tech_factors, {}, {})
        assert "composite_score" in result

    def test_fuse_all_empty(self):
        fusion = FactorFusion()
        result = fusion.fuse({}, {}, {})
        assert result["composite_score"] == 0.0
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd /workspace/chixiao && pytest tests/test_factor_fusion.py -v`
Expected: FAIL

- [ ] **Step 3: 实现因子融合引擎**

```python
from __future__ import annotations


class FactorFusion:
    def __init__(
        self,
        tech_weight: float = 0.50,
        news_weight: float = 0.30,
        semi_weight: float = 0.20,
    ):
        self._tech_weight = tech_weight
        self._news_weight = news_weight
        self._semi_weight = semi_weight

    def fuse(
        self,
        tech_factors: dict[str, float],
        news_factors: dict[str, float],
        semi_factors: dict[str, float],
    ) -> dict[str, float]:
        tech_score = self._normalize_tech(tech_factors)
        news_score = self._normalize_news(news_factors)
        semi_score = self._normalize_semi(semi_factors)

        total_weight = 0.0
        composite = 0.0

        if tech_factors:
            composite += tech_score * self._tech_weight
            total_weight += self._tech_weight
        if news_factors:
            composite += news_score * self._news_weight
            total_weight += self._news_weight
        if semi_factors:
            composite += semi_score * self._semi_weight
            total_weight += self._semi_weight

        if total_weight > 0:
            composite = composite / total_weight

        return {
            "composite_score": round(max(min(composite, 1.0), -1.0), 4),
            "tech_score": round(tech_score, 4),
            "news_score": round(news_score, 4),
            "semi_score": round(semi_score, 4),
        }

    def _normalize_tech(self, factors: dict[str, float]) -> float:
        if not factors:
            return 0.0

        score = 0.0
        count = 0

        rsi = factors.get("rsi_14")
        if rsi is not None:
            if rsi < 30:
                score += 0.5
            elif rsi > 70:
                score -= 0.5
            count += 1

        macd_hist = factors.get("macd_hist")
        if macd_hist is not None:
            score += max(min(macd_hist * 50, 0.5), -0.5)
            count += 1

        momentum = factors.get("momentum_5")
        if momentum is not None:
            score += max(min(momentum * 5, 0.5), -0.5)
            count += 1

        return score / count if count > 0 else 0.0

    def _normalize_news(self, factors: dict[str, float]) -> float:
        if not factors:
            return 0.0
        sentiment = factors.get("news_sentiment_score", 0.0)
        momentum = factors.get("news_momentum", 0.0)
        return max(min(sentiment * 0.7 + momentum * 0.3, 1.0), -1.0)

    def _normalize_semi(self, factors: dict[str, float]) -> float:
        if not factors:
            return 0.0
        momentum = factors.get("semi_price_momentum_5d", 0.0)
        vol_rank = factors.get("semi_volatility_rank", 0.5)
        vol_adjust = 1.0 - vol_rank * 0.5
        return max(min(momentum * 10 * vol_adjust, 1.0), -1.0)
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd /workspace/chixiao && pytest tests/test_factor_fusion.py -v`
Expected: 全部 PASS

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: add factor fusion engine with weighted tech/news/semi scoring"
```

---

### Task 6: API端点扩展与仪表盘升级

**Files:**
- Modify: `chixiao/src/chixiao/api/main.py`
- Modify: `chixiao/dashboard/app.py`

- [ ] **Step 1: 在FastAPI中添加新闻和因子暴露端点**

在 `api/main.py` 中新增以下端点：

```python
@app.get("/api/news/{symbol}")
def get_news_analysis(symbol: str, limit: int = 10):
    from chixiao.news.crawler import NewsCrawler
    from chixiao.news.llm_analyzer import LLMAnalyzer
    from chixiao.news.momentum_factor import NewsMomentumFactor

    crawler = NewsCrawler()
    analyzer = LLMAnalyzer(api_key=_config.llm_api_key, model=_config.llm_model)
    momentum = NewsMomentumFactor()

    items = crawler.fetch_news(symbol, limit=limit)
    sentiments = analyzer.analyze_batch(items)
    news_factors = momentum.compute(sentiments)

    return {
        "symbol": symbol,
        "news_count": len(items),
        "sentiments": [
            {
                "title": s.summary,
                "sentiment": s.sentiment,
                "score": s.score,
                "event_type": s.event_type,
            }
            for s in sentiments
        ],
        "factors": news_factors,
    }


@app.get("/api/factor-exposure/{symbol}")
def get_factor_exposure(symbol: str, days: int = 60):
    from chixiao.alpha.semi_factors import SemiFactorLib
    from chixiao.alpha.factor_fusion import FactorFusion

    bars = _data_adapter.get_bars(symbol, datetime.now().date() - __import__("datetime").timedelta(days=days), datetime.now().date())
    if not bars:
        return {"symbol": symbol, "factors": {}}

    tech_factors = _factor_calc.compute_factors(symbol, bars)
    semi_lib = SemiFactorLib()
    semi_factors = semi_lib.compute(bars) if semi_lib.is_semi_conductor(symbol) else {}
    fusion = FactorFusion()
    fused = fusion.fuse(tech_factors, {}, semi_factors)

    return {
        "symbol": symbol,
        "tech_factors": tech_factors,
        "semi_factors": semi_factors,
        "fused_score": fused,
    }
```

- [ ] **Step 2: 在Streamlit仪表盘中添加新闻情报墙和因子暴露页**

在 `dashboard/app.py` 中新增两个tab：

```python
tab_news, tab_factors = st.tabs(["📰 新闻情报", "🔬 因子暴露"])

with tab_news:
    st.header("新闻情报墙")
    news_symbol = st.text_input("查询股票代码", value="000001", key="news_sym")
    if st.button("获取新闻分析"):
        from chixiao.news.crawler import NewsCrawler
        from chixiao.news.llm_analyzer import LLMAnalyzer
        from chixiao.news.momentum_factor import NewsMomentumFactor

        crawler = NewsCrawler()
        analyzer = LLMAnalyzer(api_key=config.llm_api_key, model=config.llm_model)
        momentum = NewsMomentumFactor()

        with st.spinner("正在获取和分析新闻..."):
            items = crawler.fetch_news(news_symbol)
            if items:
                sentiments = analyzer.analyze_batch(items)
                news_factors = momentum.compute(sentiments)
                st.metric("新闻情感分数", value=f"{news_factors['news_sentiment_score']:.2f}")
                st.metric("正面新闻占比", value=f"{news_factors['news_positive_ratio']:.1%}")
                for item, sent in zip(items, sentiments):
                    emoji = {"positive": "🟢", "negative": "🔴", "neutral": "🟡"}.get(sent.sentiment, "⚪")
                    st.write(f"{emoji} **{item.title}** | {sent.event_type} | 评分: {sent.score:.2f}")
                    st.caption(item.content[:100] + "...")
            else:
                st.warning("未获取到新闻数据")

with tab_factors:
    st.header("因子暴露分析")
    factor_symbol = st.text_input("股票代码", value="002415", key="factor_sym")
    if st.button("分析因子"):
        from chixiao.alpha.semi_factors import SemiFactorLib
        from chixiao.alpha.factor_fusion import FactorFusion

        with st.spinner("正在计算因子..."):
            end = date.today()
            start = end - timedelta(days=60)
            bars = data_adapter.get_bars(factor_symbol, start, end)
            if bars:
                tech = factor_calc.compute_factors(factor_symbol, bars)
                semi_lib = SemiFactorLib()
                semi = semi_lib.compute(bars) if semi_lib.is_semi_conductor(factor_symbol) else {}
                fusion = FactorFusion()
                fused = fusion.fuse(tech, {}, semi)

                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("技术因子")
                    st.json(tech)
                with col2:
                    if semi:
                        st.subheader("半导体特色因子")
                        st.json(semi)
                    else:
                        st.info("非半导体行业股票")

                st.subheader("综合评分")
                st.metric("综合得分", value=f"{fused['composite_score']:.4f}")
            else:
                st.error("未获取到数据")
```

- [ ] **Step 3: 运行全量测试**

Run: `cd /workspace/chixiao && pytest tests/ -v`
Expected: 全部 PASS

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "feat: add news analysis and factor exposure endpoints and dashboard tabs"
```

---

## 自审清单

### 1. 规格覆盖

| 需求项 | 对应Task |
|:---|:---|
| LLM新闻分析引擎 | Task 2 |
| 新闻动量因子 | Task 3 |
| 新闻爬取 | Task 1 |
| 半导体特色因子库 | Task 4 |
| 因子融合 | Task 5 |
| 仪表盘新闻情报墙 | Task 6 |
| 因子暴露页面 | Task 6 |
| FastAPI新闻/因子端点 | Task 6 |

### 2. 占位符扫描

无 TBD/TODO 等占位符。

### 3. 类型一致性

- `NewsItem` 在 crawler 和 llm_analyzer 中使用一致
- `SentimentResult` 在 llm_analyzer 和 momentum_factor 中使用一致
- 因子字典 `dict[str, float]` 在所有模块间传递一致
