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
