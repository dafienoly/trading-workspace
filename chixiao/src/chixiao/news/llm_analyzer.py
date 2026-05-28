from __future__ import annotations

import json
from dataclasses import dataclass

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
