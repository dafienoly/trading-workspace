from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import akshare as ak


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
