from __future__ import annotations

import numpy as np

from chixiao.core.models import Bar


class SemiFactorLib:
    SEMI_SYMBOLS = {
        "002415", "688981", "603501", "688012", "300782",
        "688396", "688256", "300661", "002371", "688008",
    }

    def is_semi_conductor(self, symbol: str) -> bool:
        return symbol in self.SEMI_SYMBOLS

    def compute(self, bars: list[Bar]) -> dict[str, float]:
        if not bars:
            return {}

        closes = np.array([float(b.close) for b in bars])
        volumes = np.array([float(b.volume) for b in bars])
        amounts = np.array([float(b.amount) for b in bars])

        factors: dict[str, float] = {}

        factors["semi_turnover_rate"] = self._turnover_rate(volumes, amounts)
        factors["semi_price_momentum_5d"] = self._price_momentum(closes, 5)
        factors["semi_price_momentum_20d"] = self._price_momentum(closes, 20)
        factors["semi_volatility_rank"] = self._volatility_rank(closes)
        factors["semi_volume_ratio"] = self._volume_ratio(volumes)
        factors["semi_amplitude"] = self._amplitude(bars)

        return factors

    def _turnover_rate(self, volumes: np.ndarray, amounts: np.ndarray) -> float:
        if len(volumes) < 2:
            return 0.0
        avg_volume = float(np.mean(volumes[-5:]))
        avg_amount = float(np.mean(amounts[-5:]))
        if avg_amount == 0:
            return 0.0
        avg_price = avg_amount / avg_volume
        estimated_shares = avg_amount / avg_price if avg_price > 0 else 1.0
        turnover = avg_volume / estimated_shares if estimated_shares > 0 else 0.0
        return round(min(turnover, 1.0), 4)

    def _price_momentum(self, closes: np.ndarray, period: int) -> float:
        if len(closes) < period + 1:
            return 0.0
        momentum = (closes[-1] - closes[-1 - period]) / closes[-1 - period]
        return round(float(momentum), 4)

    def _volatility_rank(self, closes: np.ndarray) -> float:
        if len(closes) < 5:
            return 0.5
        returns = np.diff(closes) / closes[:-1]
        vol = float(np.std(returns[-20:])) if len(returns) >= 20 else float(np.std(returns))
        rank = min(vol / 0.05, 1.0)
        return round(rank, 4)

    def _volume_ratio(self, volumes: np.ndarray) -> float:
        if len(volumes) < 10:
            return 1.0
        recent = float(np.mean(volumes[-5:]))
        longer = float(np.mean(volumes[-10:]))
        if longer == 0:
            return 1.0
        return round(recent / longer, 4)

    def _amplitude(self, bars: list[Bar]) -> float:
        if not bars:
            return 0.0
        recent = bars[-min(5, len(bars)):]
        amplitudes = []
        for b in recent:
            mid = (float(b.high) + float(b.low)) / 2
            if mid > 0:
                amplitudes.append((float(b.high) - float(b.low)) / mid)
        return round(float(np.mean(amplitudes)), 4) if amplitudes else 0.0
