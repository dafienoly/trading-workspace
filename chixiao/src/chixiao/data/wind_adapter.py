from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional

from chixiao.core.interfaces import DataAdapter
from chixiao.core.models import Bar


class WindAdapter(DataAdapter):
    def __init__(self, **kwargs):
        self._w = None
        try:
            from WindPy import w

            w.start()
            self._w = w
        except ImportError:
            self._w = None

    def get_bars(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        frequency: str = "daily",
    ) -> list[Bar]:
        if self._w is None:
            return []

        try:
            wind_code = self._to_wind_code(symbol)
            freq_map = {"daily": "D", "weekly": "W", "monthly": "M"}
            freq = freq_map.get(frequency, "D")

            data = self._w.wsd(
                wind_code,
                "open,high,low,close,volume,amt",
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d"),
                f"Period={freq}",
            )

            if data.ErrorCode != 0 or not data.Data:
                return []

            from datetime import datetime

            bars = []
            for i in range(len(data.Times)):
                bar = Bar(
                    symbol=symbol,
                    timestamp=data.Times[i] if isinstance(data.Times[i], datetime) else datetime.combine(data.Times[i], datetime.min.time()),
                    open=Decimal(str(round(data.Data[0][i], 2))) if data.Data[0][i] else Decimal("0"),
                    high=Decimal(str(round(data.Data[1][i], 2))) if data.Data[1][i] else Decimal("0"),
                    low=Decimal(str(round(data.Data[2][i], 2))) if data.Data[2][i] else Decimal("0"),
                    close=Decimal(str(round(data.Data[3][i], 2))) if data.Data[3][i] else Decimal("0"),
                    volume=int(data.Data[4][i]) if data.Data[4][i] else 0,
                    amount=Decimal(str(round(data.Data[5][i], 2))) if data.Data[5][i] else Decimal("0"),
                )
                bars.append(bar)

            return bars
        except Exception:
            return []

    def get_latest_price(self, symbol: str) -> Optional[Decimal]:
        if self._w is None:
            return None

        try:
            wind_code = self._to_wind_code(symbol)
            data = self._w.wsq(wind_code, "rt_last")
            if data.ErrorCode != 0:
                return None
            return Decimal(str(round(data.Data[0][0], 2)))
        except Exception:
            return None

    def get_symbols(self) -> list[str]:
        if self._w is None:
            return []

        try:
            data = self._w.wset("sectorconstituent", "date=;sectorid=a001010100000000")
            if data.ErrorCode != 0:
                return []
            return [code.split(".")[0] for code in data.Data[1]]
        except Exception:
            return []

    @staticmethod
    def _to_wind_code(symbol: str) -> str:
        if "." in symbol:
            return symbol
        if symbol.startswith(("6",)):
            return f"{symbol}.SH"
        return f"{symbol}.SZ"
