from chixiao.alpha.factor_fusion import FactorFusion


class TestFactorFusion:
    def test_fuse_technical_and_news(self):
        tech_factors = {"ma_5": 10.5, "rsi_14": 55.0, "macd_hist": 0.02}
        news_factors = {"news_sentiment_score": 0.6, "news_momentum": 0.1}
        semi_factors = {"semi_turnover_rate": 0.05, "semi_price_momentum_5d": 0.03}

        fusion = FactorFusion(
            tech_weight=0.50,
            news_weight=0.30,
            semi_weight=0.20,
        )
        result = fusion.fuse(tech_factors, news_factors, semi_factors)

        assert "composite_score" in result
        assert -1.0 <= result["composite_score"] <= 1.0
        assert "tech_score" in result
        assert "news_score" in result
        assert "semi_score" in result

    def test_fuse_without_news(self):
        tech_factors = {"ma_5": 10.5, "rsi_14": 55.0}
        fusion = FactorFusion(tech_weight=0.70, news_weight=0.30, semi_weight=0.0)
        result = fusion.fuse(tech_factors, {}, {})
        assert "composite_score" in result

    def test_fuse_all_empty(self):
        fusion = FactorFusion()
        result = fusion.fuse({}, {}, {})
        assert result["composite_score"] == 0.0
