from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

from fastapi import FastAPI, Query
from pydantic import BaseModel

from chixiao.alpha.alpha_model import AlphaModel
from chixiao.alpha.factor_calculator import FactorCalculator
from chixiao.core.config import load_config
from chixiao.data.akshare_adapter import AKShareAdapter
from chixiao.execution.mode_a import ModeAExecutor
from chixiao.portfolio.position_manager import PositionManager

app = FastAPI(title="赤霄量化交易系统", version="0.2.0")

_config = load_config()
_data_adapter = AKShareAdapter()
_factor_calc = FactorCalculator()
_alpha_model = AlphaModel(_factor_calc)
_executor = ModeAExecutor(csv_dir=_config.csv_dir)
_position_mgr = PositionManager()


class OrderRequest(BaseModel):
    symbol: str
    side: str
    quantity: int
    price: str


class TradeRecordRequest(BaseModel):
    symbol: str
    name: str = ""
    side: str
    quantity: int
    price: str
    timestamp: str


@app.get("/health")
def health_check():
    return {"status": "ok", "version": "0.2.0"}


@app.get("/api/signals")
def get_signals(symbols: str = Query(..., description="逗号分隔的股票代码")):
    symbol_list = [s.strip() for s in symbols.split(",")]
    results = []
    for sym in symbol_list:
        try:
            bars = _data_adapter.get_bars(sym, datetime.now().date(), datetime.now().date())
            if bars:
                signal = _alpha_model.generate_signal(sym, bars)
                if signal:
                    results.append({
                        "symbol": signal.symbol,
                        "direction": signal.direction.value,
                        "strength": signal.strength,
                        "factors": signal.factors,
                    })
        except Exception:
            continue
    return {"signals": results}


@app.get("/api/positions")
def get_positions():
    positions = _executor.sync_positions()
    return {
        "positions": [
            {
                "symbol": p.symbol,
                "name": p.name,
                "quantity": p.quantity,
                "avg_cost": str(p.avg_cost),
                "current_price": str(p.current_price),
                "market_value": str(p.market_value),
                "unrealized_pnl": str(p.unrealized_pnl),
                "unrealized_pnl_pct": str(p.unrealized_pnl_pct) + "%",
            }
            for p in positions
        ]
    }


@app.post("/api/orders")
def submit_order(order: OrderRequest):
    from chixiao.core.models import Order, OrderSide

    side = OrderSide.BUY if order.side.upper() == "BUY" else OrderSide.SELL
    new_order = Order(
        symbol=order.symbol,
        side=side,
        quantity=order.quantity,
        price=Decimal(order.price),
        timestamp=datetime.now(),
    )
    order_id = _executor.submit_order(new_order)
    return {"order_id": order_id, "status": "pending"}


@app.get("/api/portfolio")
def get_portfolio():
    positions = _executor.sync_positions()
    for pos in positions:
        _position_mgr.update_position(pos.symbol, pos.name, pos.quantity, pos.current_price)
    portfolio = _position_mgr.get_portfolio()
    return {
        "total_value": str(portfolio.total_value),
        "cash": str(portfolio.cash),
        "positions_count": len(portfolio.positions),
    }


@app.get("/api/news/{symbol}")
def get_news_analysis(symbol: str, limit: int = 10):
    from chixiao.news.crawler import NewsCrawler
    from chixiao.news.llm_analyzer import LLMAnalyzer
    from chixiao.news.momentum_factor import NewsMomentumFactor

    crawler = NewsCrawler()
    analyzer = LLMAnalyzer(api_key=_config.llm_api_key, model=_config.llm_model)
    momentum = NewsMomentumFactor()

    items = crawler.fetch_news(symbol, limit=limit)
    sentiments = analyzer.analyze_batch(items)
    news_factors = momentum.compute(sentiments)

    return {
        "symbol": symbol,
        "news_count": len(items),
        "sentiments": [
            {
                "title": item.title,
                "sentiment": s.sentiment,
                "score": s.score,
                "event_type": s.event_type,
                "summary": s.summary,
            }
            for item, s in zip(items, sentiments)
        ],
        "factors": news_factors,
    }


@app.get("/api/factor-exposure/{symbol}")
def get_factor_exposure(symbol: str, days: int = 60):
    from chixiao.alpha.semi_factors import SemiFactorLib
    from chixiao.alpha.factor_fusion import FactorFusion

    end = datetime.now().date()
    start = end - timedelta(days=days)
    bars = _data_adapter.get_bars(symbol, start, end)
    if not bars:
        return {"symbol": symbol, "factors": {}}

    tech_factors = _factor_calc.compute_factors(symbol, bars)
    semi_lib = SemiFactorLib()
    semi_factors = semi_lib.compute(bars) if semi_lib.is_semi_conductor(symbol) else {}
    fusion = FactorFusion()
    fused = fusion.fuse(tech_factors, {}, semi_factors)

    return {
        "symbol": symbol,
        "tech_factors": tech_factors,
        "semi_factors": semi_factors,
        "fused_score": fused,
    }


@app.get("/api/accounts")
def get_accounts():
    from chixiao.account.account_manager import AccountManager

    mgr = AccountManager()
    accounts = mgr.list_accounts()
    return {
        "accounts": [
            {
                "account_id": a.account_id,
                "broker": a.broker,
                "mode": a.mode,
                "last_sync": a.last_sync,
            }
            for a in accounts
        ]
    }


@app.post("/api/trade-review")
def trade_review(trades: list[TradeRecordRequest]):
    from chixiao.review.trade_review import TradeReviewAnalyzer, TradeRecord
    from chixiao.review.llm_reviewer import LLMReviewer

    records = []
    for t in trades:
        records.append(TradeRecord(
            symbol=t.symbol,
            name=t.name,
            side=t.side,
            quantity=t.quantity,
            price=Decimal(t.price),
            timestamp=datetime.fromisoformat(t.timestamp),
        ))

    analyzer = TradeReviewAnalyzer()
    result = analyzer.analyze(records)

    reviewer = LLMReviewer(api_key=_config.llm_api_key, model=_config.llm_model)
    comment = reviewer.review(result)

    return {
        "statistics": {
            "total_trades": result.total_trades,
            "win_rate": result.win_rate,
            "total_pnl": str(result.total_pnl),
            "profit_factor": result.profit_factor,
            "avg_holding_days": result.avg_holding_days,
        },
        "review": {
            "score": comment.score,
            "summary": comment.summary,
            "strengths": comment.strengths,
            "weaknesses": comment.weaknesses,
            "suggestions": comment.suggestions,
        },
    }
