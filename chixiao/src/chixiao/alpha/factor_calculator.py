from __future__ import annotations


import numpy as np
import pandas as pd

from chixiao.core.interfaces import FactorProvider
from chixiao.core.models import Bar


class FactorCalculator(FactorProvider):
    def compute_factors(self, symbol: str, bars: list[Bar]) -> dict[str, float]:
        if not bars:
            return {}

        closes = np.array([float(b.close) for b in bars])
        volumes = np.array([float(b.volume) for b in bars])
        highs = np.array([float(b.high) for b in bars])
        lows = np.array([float(b.low) for b in bars])

        factors: dict[str, float] = {}

        factors.update(self._moving_averages(closes))
        factors.update(self._rsi(closes))
        factors.update(self._macd(closes))
        factors.update(self._bollinger(closes))
        factors.update(self._volume_factors(volumes))
        factors.update(self._price_factors(closes, highs, lows))

        return factors

    def _moving_averages(self, closes: np.ndarray) -> dict[str, float]:
        result: dict[str, float] = {}
        for period in [5, 10, 20, 60]:
            if len(closes) >= period:
                result[f"ma_{period}"] = float(np.mean(closes[-period:]))
            else:
                result[f"ma_{period}"] = float(np.mean(closes))
        return result

    def _rsi(self, closes: np.ndarray, period: int = 14) -> dict[str, float]:
        if len(closes) < period + 1:
            return {"rsi_14": 50.0}

        deltas = np.diff(closes)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = float(np.mean(gains[-period:]))
        avg_loss = float(np.mean(losses[-period:]))

        if avg_loss == 0:
            return {"rsi_14": 100.0}

        rs = avg_gain / avg_loss
        rsi = 100.0 - (100.0 / (1.0 + rs))
        return {"rsi_14": rsi}

    def _macd(self, closes: np.ndarray) -> dict[str, float]:
        if len(closes) < 26:
            return {"macd": 0.0, "macd_signal": 0.0, "macd_hist": 0.0}

        ema_12 = pd.Series(closes).ewm(span=12, adjust=False).mean()
        ema_26 = pd.Series(closes).ewm(span=26, adjust=False).mean()
        macd_line = ema_12 - ema_26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        hist = macd_line - signal_line

        return {
            "macd": float(macd_line.iloc[-1]),
            "macd_signal": float(signal_line.iloc[-1]),
            "macd_hist": float(hist.iloc[-1]),
        }

    def _bollinger(self, closes: np.ndarray, period: int = 20) -> dict[str, float]:
        if len(closes) < period:
            period = len(closes)
        if period == 0:
            return {"bollinger_upper": 0.0, "bollinger_lower": 0.0, "bollinger_width": 0.0}

        sma = float(np.mean(closes[-period:]))
        std = float(np.std(closes[-period:]))

        upper = sma + 2 * std
        lower = sma - 2 * std
        width = (upper - lower) / sma if sma != 0 else 0.0

        return {
            "bollinger_upper": upper,
            "bollinger_lower": lower,
            "bollinger_width": width,
        }

    def _volume_factors(self, volumes: np.ndarray) -> dict[str, float]:
        if len(volumes) < 5:
            return {"volume_ratio": 1.0}

        avg_vol = float(np.mean(volumes[-5:]))
        current_vol = float(volumes[-1])
        ratio = current_vol / avg_vol if avg_vol > 0 else 1.0

        return {"volume_ratio": ratio}

    def _price_factors(
        self, closes: np.ndarray, highs: np.ndarray, lows: np.ndarray
    ) -> dict[str, float]:
        if len(closes) < 2:
            return {"momentum_5": 0.0, "volatility": 0.0}

        n = min(5, len(closes) - 1)
        momentum = (float(closes[-1]) - float(closes[-1 - n])) / float(closes[-1 - n]) if float(closes[-1 - n]) != 0 else 0.0

        returns = np.diff(closes) / closes[:-1]
        volatility = float(np.std(returns[-20:])) if len(returns) >= 20 else float(np.std(returns))

        return {"momentum_5": momentum, "volatility": volatility}
