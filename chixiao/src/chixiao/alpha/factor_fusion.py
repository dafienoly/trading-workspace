from __future__ import annotations


class FactorFusion:
    def __init__(
        self,
        tech_weight: float = 0.50,
        news_weight: float = 0.30,
        semi_weight: float = 0.20,
    ):
        self._tech_weight = tech_weight
        self._news_weight = news_weight
        self._semi_weight = semi_weight

    def fuse(
        self,
        tech_factors: dict[str, float],
        news_factors: dict[str, float],
        semi_factors: dict[str, float],
    ) -> dict[str, float]:
        tech_score = self._normalize_tech(tech_factors)
        news_score = self._normalize_news(news_factors)
        semi_score = self._normalize_semi(semi_factors)

        total_weight = 0.0
        composite = 0.0

        if tech_factors:
            composite += tech_score * self._tech_weight
            total_weight += self._tech_weight
        if news_factors:
            composite += news_score * self._news_weight
            total_weight += self._news_weight
        if semi_factors:
            composite += semi_score * self._semi_weight
            total_weight += self._semi_weight

        if total_weight > 0:
            composite = composite / total_weight

        return {
            "composite_score": round(max(min(composite, 1.0), -1.0), 4),
            "tech_score": round(tech_score, 4),
            "news_score": round(news_score, 4),
            "semi_score": round(semi_score, 4),
        }

    def _normalize_tech(self, factors: dict[str, float]) -> float:
        if not factors:
            return 0.0

        score = 0.0
        count = 0

        rsi = factors.get("rsi_14")
        if rsi is not None:
            if rsi < 30:
                score += 0.5
            elif rsi > 70:
                score -= 0.5
            count += 1

        macd_hist = factors.get("macd_hist")
        if macd_hist is not None:
            score += max(min(macd_hist * 50, 0.5), -0.5)
            count += 1

        momentum = factors.get("momentum_5")
        if momentum is not None:
            score += max(min(momentum * 5, 0.5), -0.5)
            count += 1

        return score / count if count > 0 else 0.0

    def _normalize_news(self, factors: dict[str, float]) -> float:
        if not factors:
            return 0.0
        sentiment = factors.get("news_sentiment_score", 0.0)
        momentum = factors.get("news_momentum", 0.0)
        return max(min(sentiment * 0.7 + momentum * 0.3, 1.0), -1.0)

    def _normalize_semi(self, factors: dict[str, float]) -> float:
        if not factors:
            return 0.0
        momentum = factors.get("semi_price_momentum_5d", 0.0)
        vol_rank = factors.get("semi_volatility_rank", 0.5)
        vol_adjust = 1.0 - vol_rank * 0.5
        return max(min(momentum * 10 * vol_adjust, 1.0), -1.0)
