from unittest.mock import patch
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
