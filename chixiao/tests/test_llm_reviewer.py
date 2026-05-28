from unittest.mock import patch
from datetime import datetime
from decimal import Decimal
from chixiao.review.llm_reviewer import LLMReviewer, ReviewComment
from chixiao.review.trade_review import ReviewResult, ClosedTrade


class TestLLMReviewer:
    def test_review_with_result(self):
        reviewer = LLMReviewer(api_key="test-key", model="deepseek-chat")
        result = ReviewResult(
            total_trades=4,
            closed_trades=2,
            win_count=1,
            loss_count=1,
            win_rate=0.5,
            total_pnl=Decimal("500"),
            avg_holding_days=5.0,
            max_drawdown=Decimal("-1000"),
            profit_factor=1.5,
            details=[
                ClosedTrade("000001", "平安银行", Decimal("10"), Decimal("11"), 1000,
                           datetime(2024, 1, 2), datetime(2024, 1, 7), Decimal("1000"), Decimal("10"), 5),
                ClosedTrade("000002", "万科A", Decimal("8"), Decimal("7.5"), 500,
                           datetime(2024, 1, 3), datetime(2024, 1, 8), Decimal("-250"), Decimal("-6.25"), 5),
            ],
        )

        with patch.object(reviewer, "_call_llm") as mock_llm:
            mock_llm.return_value = '{"score": 6, "strengths": ["盈利交易占比合理"], "weaknesses": ["止损不够果断"], "suggestions": ["建议设置更严格的止损线"]}'
            comment = reviewer.review(result)
            assert isinstance(comment, ReviewComment)
            assert 1 <= comment.score <= 10
            assert len(comment.strengths) > 0
            assert len(comment.suggestions) > 0

    def test_review_empty_result(self):
        reviewer = LLMReviewer(api_key="test-key", model="deepseek-chat")
        result = ReviewResult()
        comment = reviewer.review(result)
        assert comment.score == 0
        assert "暂无交易数据" in comment.summary
