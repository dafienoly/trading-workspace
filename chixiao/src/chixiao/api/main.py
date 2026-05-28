from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from fastapi import FastAPI, Query
from pydantic import BaseModel

from chixiao.alpha.alpha_model import AlphaModel
from chixiao.alpha.factor_calculator import FactorCalculator
from chixiao.core.config import load_config
from chixiao.data.akshare_adapter import AKShareAdapter
from chixiao.execution.mode_a import ModeAExecutor
from chixiao.portfolio.position_manager import PositionManager

app = FastAPI(title="赤霄量化交易系统", version="0.1.0")

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


@app.get("/health")
def health_check():
    return {"status": "ok", "version": "0.1.0"}


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
