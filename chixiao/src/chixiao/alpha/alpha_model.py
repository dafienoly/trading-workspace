from __future__ import annotations

from typing import Optional

from chixiao.core.interfaces import FactorProvider
from chixiao.core.models import Bar, Signal, SignalDirection


class AlphaModel:
    def __init__(self, factor_provider: FactorProvider):
        self._factor_provider = factor_provider

    def generate_signal(self, symbol: str, bars: list[Bar]) -> Optional[Signal]:
        if not bars:
            return None

        factors = self._factor_provider.compute_factors(symbol, bars)
        if not factors:
            return None

        score = self._compute_score(factors)
        direction = self._score_to_direction(score)

        return Signal(
            symbol=symbol,
            direction=direction,
            strength=min(abs(score), 1.0),
            timestamp=bars[-1].timestamp,
            factors=factors,
        )

    def generate_signals(
        self, bars_map: dict[str, list[Bar]]
    ) -> list[Signal]:
        signals = []
        for symbol, bars in bars_map.items():
            signal = self.generate_signal(symbol, bars)
            if signal is not None:
                signals.append(signal)
        return signals

    def _compute_score(self, factors: dict[str, float]) -> float:
        score = 0.0
        weight_sum = 0.0

        ma_score = self._ma_score(factors)
        if ma_score is not None:
            score += ma_score * 0.25
            weight_sum += 0.25

        rsi_score = self._rsi_score(factors)
        if rsi_score is not None:
            score += rsi_score * 0.20
            weight_sum += 0.20

        macd_score = self._macd_score(factors)
        if macd_score is not None:
            score += macd_score * 0.25
            weight_sum += 0.25

        momentum_score = self._momentum_score(factors)
        if momentum_score is not None:
            score += momentum_score * 0.20
            weight_sum += 0.20

        volume_score = self._volume_score(factors)
        if volume_score is not None:
            score += volume_score * 0.10
            weight_sum += 0.10

        if weight_sum == 0:
            return 0.0

        return score / weight_sum

    def _ma_score(self, factors: dict[str, float]) -> Optional[float]:
        ma_5 = factors.get("ma_5")
        ma_20 = factors.get("ma_20")
        if ma_5 is None or ma_20 is None:
            return None
        if ma_5 > ma_20:
            return 0.5 + min((ma_5 - ma_20) / ma_20 * 10, 0.5)
        else:
            return -0.5 - min((ma_20 - ma_5) / ma_20 * 10, 0.5)

    def _rsi_score(self, factors: dict[str, float]) -> Optional[float]:
        rsi = factors.get("rsi_14")
        if rsi is None:
            return None
        if rsi < 30:
            return 0.8
        elif rsi < 40:
            return 0.4
        elif rsi > 70:
            return -0.8
        elif rsi > 60:
            return -0.4
        return 0.0

    def _macd_score(self, factors: dict[str, float]) -> Optional[float]:
        hist = factors.get("macd_hist")
        if hist is None:
            return None
        if hist > 0:
            return min(hist * 100, 1.0)
        else:
            return max(hist * 100, -1.0)

    def _momentum_score(self, factors: dict[str, float]) -> Optional[float]:
        momentum = factors.get("momentum_5")
        if momentum is None:
            return None
        return max(min(momentum * 5, 1.0), -1.0)

    def _volume_score(self, factors: dict[str, float]) -> Optional[float]:
        ratio = factors.get("volume_ratio")
        if ratio is None:
            return None
        if ratio > 1.5:
            return 0.3
        elif ratio < 0.5:
            return -0.3
        return 0.0

    def _score_to_direction(self, score: float) -> SignalDirection:
        if score > 0.3:
            return SignalDirection.BUY
        elif score < -0.3:
            return SignalDirection.SELL
        return SignalDirection.HOLD
