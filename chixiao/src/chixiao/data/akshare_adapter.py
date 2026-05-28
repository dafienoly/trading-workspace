from __future__ import annotations

from datetime import date
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
