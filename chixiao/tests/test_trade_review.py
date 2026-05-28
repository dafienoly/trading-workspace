from datetime import datetime
from decimal import Decimal
from chixiao.review.trade_review import TradeReviewAnalyzer, TradeRecord, ReviewResult


class TestTradeReviewAnalyzer:
    def test_analyze_profitable_trades(self):
        analyzer = TradeReviewAnalyzer()
        trades = [
            TradeRecord("000001", "平安银行", "BUY", 1000, Decimal("10.00"), datetime(2024, 1, 2)),
            TradeRecord("000001", "平安银行", "SELL", 1000, Decimal("11.00"), datetime(2024, 1, 10)),
        ]
        result = analyzer.analyze(trades)
        assert isinstance(result, ReviewResult)
        assert result.total_trades == 2
        assert result.win_rate >= 0
        assert result.total_pnl == Decimal("1000.00")

    def test_analyze_losing_trades(self):
        analyzer = TradeReviewAnalyzer()
        trades = [
            TradeRecord("000001", "平安银行", "BUY", 1000, Decimal("10.00"), datetime(2024, 1, 2)),
            TradeRecord("000001", "平安银行", "SELL", 1000, Decimal("9.00"), datetime(2024, 1, 10)),
        ]
        result = analyzer.analyze(trades)
        assert result.total_pnl == Decimal("-1000.00")

    def test_analyze_empty(self):
        analyzer = TradeReviewAnalyzer()
        result = analyzer.analyze([])
        assert result.total_trades == 0
        assert result.win_rate == 0.0

    def test_holding_period(self):
        analyzer = TradeReviewAnalyzer()
        trades = [
            TradeRecord("000001", "平安银行", "BUY", 1000, Decimal("10.00"), datetime(2024, 1, 2)),
            TradeRecord("000001", "平安银行", "SELL", 1000, Decimal("11.00"), datetime(2024, 1, 12)),
        ]
        result = analyzer.analyze(trades)
        assert result.avg_holding_days > 0

    def test_max_drawdown(self):
        analyzer = TradeReviewAnalyzer()
        trades = [
            TradeRecord("000001", "平安银行", "BUY", 1000, Decimal("10.00"), datetime(2024, 1, 2)),
            TradeRecord("000001", "平安银行", "SELL", 1000, Decimal("9.00"), datetime(2024, 1, 5)),
            TradeRecord("000002", "万科A", "BUY", 500, Decimal("8.00"), datetime(2024, 1, 6)),
            TradeRecord("000002", "万科A", "SELL", 500, Decimal("9.00"), datetime(2024, 1, 10)),
        ]
        result = analyzer.analyze(trades)
        assert result.max_drawdown <= 0
