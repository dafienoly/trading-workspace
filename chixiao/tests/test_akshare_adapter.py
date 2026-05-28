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
