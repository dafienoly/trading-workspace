from __future__ import annotations

from chixiao.news.llm_analyzer import SentimentResult


class NewsMomentumFactor:
    def compute(self, sentiments: list[SentimentResult]) -> dict[str, float]:
        if not sentiments:
            return {
                "news_sentiment_score": 0.0,
                "news_momentum": 0.0,
                "news_positive_ratio": 0.0,
                "news_negative_ratio": 0.0,
                "news_count": 0,
            }

        n = len(sentiments)
        decay_weights = [0.9 ** i for i in range(n)]
        decay_weights.reverse()
        total_weight = sum(decay_weights)

        weighted_score = sum(
            s.score * w for s, w in zip(sentiments, decay_weights)
        ) / total_weight

        positive_count = sum(1 for s in sentiments if s.sentiment == "positive")
        negative_count = sum(1 for s in sentiments if s.sentiment == "negative")

        momentum = 0.0
        if n >= 2:
            recent_avg = sum(s.score for s in sentiments[:3]) / min(3, n)
            older_avg = sum(s.score for s in sentiments[3:]) / max(1, n - 3)
            momentum = recent_avg - older_avg

        return {
            "news_sentiment_score": round(weighted_score, 4),
            "news_momentum": round(momentum, 4),
            "news_positive_ratio": round(positive_count / n, 4),
            "news_negative_ratio": round(negative_count / n, 4),
            "news_count": n,
        }
