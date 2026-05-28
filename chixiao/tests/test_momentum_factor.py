from chixiao.news.momentum_factor import NewsMomentumFactor
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
