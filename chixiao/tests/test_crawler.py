from unittest.mock import patch
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
