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
