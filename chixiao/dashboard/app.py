import csv
import io
from datetime import date, datetime, timedelta
from decimal import Decimal

import streamlit as st

from chixiao.core.config import load_config
from chixiao.data.akshare_adapter import AKShareAdapter
from chixiao.data.cleaner import DataCleaner
from chixiao.alpha.factor_calculator import FactorCalculator
from chixiao.alpha.alpha_model import AlphaModel
from chixiao.execution.mode_a import ModeAExecutor
from chixiao.portfolio.position_manager import PositionManager
from chixiao.portfolio.risk_manager import RiskManager

st.set_page_config(page_title="赤霄量化交易系统", layout="wide")
st.title("🔥 赤霄量化交易决策辅助系统")

config = load_config()
data_adapter = AKShareAdapter()
factor_calc = FactorCalculator()
alpha_model = AlphaModel(factor_calc)
executor = ModeAExecutor(csv_dir=config.csv_dir)
position_mgr = PositionManager()
risk_mgr = RiskManager(
    max_position_pct=config.risk_max_position_pct,
    max_drawdown_pct=config.risk_max_portfolio_drawdown_pct,
)

(
    tab_signals,
    tab_positions,
    tab_risk,
    tab_orders,
    tab_news,
    tab_factors,
    tab_review,
) = st.tabs(
    [
        "📊 策略信号",
        "💼 持仓管理",
        "🛡️ 风控监控",
        "📋 订单管理",
        "📰 新闻情报",
        "🔬 因子暴露",
        "📝 交易复盘",
    ]
)

with tab_signals:
    st.header("策略信号分析")
    col1, col2 = st.columns([1, 3])
    with col1:
        symbol_input = st.text_input("股票代码", value="000001")
        days = st.slider("回溯天数", min_value=30, max_value=120, value=60)
        analyze_btn = st.button("分析信号", type="primary")

    with col2:
        if analyze_btn:
            with st.spinner("正在获取数据并计算因子..."):
                end = date.today()
                start = end - timedelta(days=days)
                bars = data_adapter.get_bars(symbol_input, start, end)
                if bars:
                    bars = DataCleaner.clean(bars)
                    signal = alpha_model.generate_signal(symbol_input, bars)
                    if signal:
                        direction_emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}
                        st.metric(
                            label=f"{symbol_input} 信号方向",
                            value=f"{direction_emoji.get(signal.direction.value, '')} {signal.direction.value}",
                            delta=f"强度: {signal.strength:.2f}",
                        )
                        st.subheader("因子详情")
                        factors_df = {
                            "因子名称": list(signal.factors.keys()),
                            "因子值": [round(v, 4) if v else "N/A" for v in signal.factors.values()],
                        }
                        st.dataframe(factors_df, use_container_width=True)

                        import pandas as pd

                        chart_data = pd.DataFrame({
                            "日期": [b.timestamp for b in bars],
                            "收盘价": [float(b.close) for b in bars],
                        })
                        st.line_chart(chart_data, x="日期", y="收盘价")
                    else:
                        st.warning("无法生成信号，数据不足")
                else:
                    st.error("未获取到数据，请检查股票代码")

with tab_positions:
    st.header("持仓管理")
    col_sync, col_upload = st.columns(2)
    with col_sync:
        if st.button("从CSV同步持仓"):
            positions = executor.sync_positions()
            if positions:
                st.success(f"成功同步 {len(positions)} 个持仓")
                for pos in positions:
                    position_mgr.update_position(pos.symbol, pos.name, pos.quantity, pos.current_price)
            else:
                st.warning("未找到持仓数据，请先上传CSV文件")

    with col_upload:
        uploaded = st.file_uploader("上传持仓CSV", type=["csv"])
        if uploaded:
            content = uploaded.read().decode("utf-8")
            reader = csv.DictReader(io.StringIO(content))
            count = 0
            for row in reader:
                try:
                    position_mgr.update_position(
                        row["symbol"],
                        row.get("name", ""),
                        int(row["quantity"]),
                        Decimal(row["current_price"]),
                    )
                    count += 1
                except (KeyError, ValueError):
                    continue
            st.success(f"成功导入 {count} 个持仓")

    portfolio = position_mgr.get_portfolio()
    if portfolio.positions:
        st.subheader("当前持仓")
        pos_data = []
        for p in portfolio.positions:
            pos_data.append({
                "代码": p.symbol,
                "名称": p.name,
                "数量": p.quantity,
                "成本价": float(p.avg_cost),
                "现价": float(p.current_price),
                "市值": float(p.market_value),
                "浮盈": float(p.unrealized_pnl),
                "浮盈%": f"{float(p.unrealized_pnl_pct)}%",
            })
        st.dataframe(pos_data, use_container_width=True)
        st.metric("总资产", value=f"¥{float(portfolio.total_value):,.2f}")
    else:
        st.info("暂无持仓数据")

with tab_risk:
    st.header("风控监控")
    portfolio = position_mgr.get_portfolio()
    if portfolio.positions:
        weights = position_mgr.get_position_weights()
        st.subheader("仓位分布")
        import pandas as pd

        weight_df = pd.DataFrame({
            "股票代码": list(weights.keys()),
            "仓位占比": [f"{w:.1%}" for w in weights.values()],
        })
        st.dataframe(weight_df, use_container_width=True)

        peak = st.number_input("历史最高资产", value=float(portfolio.total_value) * 1.05)
        dd_result = risk_mgr.check_drawdown(portfolio, Decimal(str(peak)))
        if dd_result.triggered:
            st.error(f"⚠️ 回撤预警: {dd_result.reason}")
        else:
            st.success(f"✅ 当前回撤: {dd_result.drawdown_pct:.1%}，在安全范围内")
    else:
        st.info("暂无持仓数据，无法进行风控分析")

with tab_orders:
    st.header("订单管理")
    col_buy, col_sell = st.columns(2)
    with col_buy:
        st.subheader("买入下单")
        buy_symbol = st.text_input("买入代码", key="buy_symbol")
        buy_qty = st.number_input("买入数量", min_value=100, step=100, key="buy_qty")
        buy_price = st.text_input("买入价格", key="buy_price")
        if st.button("提交买入", type="primary"):
            if buy_symbol and buy_price:
                from chixiao.core.models import Order, OrderSide

                order = Order(
                    symbol=buy_symbol,
                    side=OrderSide.BUY,
                    quantity=buy_qty,
                    price=Decimal(buy_price),
                    timestamp=datetime.now(),
                )
                order_id = executor.submit_order(order)
                st.success(f"买入订单已提交: {order_id}")

    with col_sell:
        st.subheader("卖出下单")
        sell_symbol = st.text_input("卖出代码", key="sell_symbol")
        sell_qty = st.number_input("卖出数量", min_value=100, step=100, key="sell_qty")
        sell_price = st.text_input("卖出价格", key="sell_price")
        if st.button("提交卖出"):
            if sell_symbol and sell_price:
                from chixiao.core.models import Order, OrderSide

                order = Order(
                    symbol=sell_symbol,
                    side=OrderSide.SELL,
                    quantity=sell_qty,
                    price=Decimal(sell_price),
                    timestamp=datetime.now(),
                )
                order_id = executor.submit_order(order)
                st.success(f"卖出订单已提交: {order_id}")

    st.subheader("待执行订单")
    pending = executor.get_pending_orders()
    if pending:
        for oid, order in pending.items():
            st.write(f"**{oid}** | {order.symbol} | {order.side.value} | {order.quantity}@{order.price}")
        if st.button("导出订单到CSV"):
            executor.export_orders()
            st.success("订单已导出到CSV文件")
    else:
        st.info("暂无待执行订单")

with tab_news:
    st.header("新闻情报墙")
    news_symbol = st.text_input("查询股票代码", value="000001", key="news_sym")
    news_limit = st.slider("新闻条数", min_value=5, max_value=30, value=10, key="news_limit")
    if st.button("获取新闻分析", key="fetch_news"):
        from chixiao.news.crawler import NewsCrawler
        from chixiao.news.llm_analyzer import LLMAnalyzer
        from chixiao.news.momentum_factor import NewsMomentumFactor

        crawler = NewsCrawler()
        analyzer = LLMAnalyzer(api_key=config.llm_api_key, model=config.llm_model)
        momentum = NewsMomentumFactor()

        with st.spinner("正在获取和分析新闻..."):
            items = crawler.fetch_news(news_symbol, limit=news_limit)
            if items:
                sentiments = analyzer.analyze_batch(items)
                news_factors = momentum.compute(sentiments)

                col1, col2, col3 = st.columns(3)
                col1.metric("新闻情感分数", value=f"{news_factors['news_sentiment_score']:.2f}")
                col2.metric("正面新闻占比", value=f"{news_factors['news_positive_ratio']:.1%}")
                col3.metric("新闻动量", value=f"{news_factors['news_momentum']:.2f}")

                st.subheader("新闻详情")
                for item, sent in zip(items, sentiments):
                    emoji = {"positive": "🟢", "negative": "🔴", "neutral": "🟡"}.get(
                        sent.sentiment, "⚪"
                    )
                    with st.expander(f"{emoji} {item.title} | {sent.event_type} | 评分: {sent.score:.2f}"):
                        st.write(f"**来源:** {item.source} | **时间:** {item.publish_time}")
                        st.write(item.content[:300] + ("..." if len(item.content) > 300 else ""))
                        st.write(f"**AI摘要:** {sent.summary}")
            else:
                st.warning("未获取到新闻数据")

with tab_factors:
    st.header("因子暴露分析")
    factor_symbol = st.text_input("股票代码", value="002415", key="factor_sym")
    factor_days = st.slider("回溯天数", min_value=30, max_value=120, value=60, key="factor_days")
    if st.button("分析因子", key="analyze_factors"):
        from chixiao.alpha.semi_factors import SemiFactorLib
        from chixiao.alpha.factor_fusion import FactorFusion

        with st.spinner("正在计算因子..."):
            end = date.today()
            start = end - timedelta(days=factor_days)
            bars = data_adapter.get_bars(factor_symbol, start, end)
            if bars:
                tech = factor_calc.compute_factors(factor_symbol, bars)
                semi_lib = SemiFactorLib()
                semi = semi_lib.compute(bars) if semi_lib.is_semi_conductor(factor_symbol) else {}
                fusion = FactorFusion()
                fused = fusion.fuse(tech, {}, semi)

                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("技术因子")
                    tech_data = {"因子": list(tech.keys()), "值": [round(v, 4) for v in tech.values()]}
                    st.dataframe(tech_data, use_container_width=True)
                with col2:
                    if semi:
                        st.subheader("半导体特色因子")
                        semi_data = {"因子": list(semi.keys()), "值": [round(v, 4) for v in semi.values()]}
                        st.dataframe(semi_data, use_container_width=True)
                    else:
                        st.info("非半导体行业股票，无特色因子")

                st.subheader("综合评分")
                score_col1, score_col2, score_col3, score_col4 = st.columns(4)
                score_col1.metric("综合得分", value=f"{fused['composite_score']:.4f}")
                score_col2.metric("技术得分", value=f"{fused['tech_score']:.4f}")
                score_col3.metric("新闻得分", value=f"{fused['news_score']:.4f}")
                score_col4.metric("半导体得分", value=f"{fused['semi_score']:.4f}")
            else:
                st.error("未获取到数据")

with tab_review:
    st.header("交易复盘点评")
    st.info("请上传交易记录CSV文件（格式: symbol, name, side, quantity, price, timestamp）")
    review_file = st.file_uploader("上传交易记录", type=["csv"], key="review_csv")
    if review_file and st.button("开始复盘", key="start_review"):
        from chixiao.review.trade_review import TradeReviewAnalyzer, TradeRecord
        from chixiao.review.llm_reviewer import LLMReviewer

        content = review_file.read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(content))
        records = []
        for row in reader:
            try:
                records.append(TradeRecord(
                    symbol=row["symbol"],
                    name=row.get("name", ""),
                    side=row["side"],
                    quantity=int(row["quantity"]),
                    price=Decimal(row["price"]),
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                ))
            except (KeyError, ValueError):
                continue

        if not records:
            st.error("未解析到有效交易记录，请检查CSV格式")
        else:
            analyzer = TradeReviewAnalyzer()
            result = analyzer.analyze(records)

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("胜率", f"{result.win_rate:.1%}")
            col2.metric("总盈亏", f"¥{float(result.total_pnl):,.2f}")
            col3.metric("盈亏比", f"{result.profit_factor:.2f}")
            col4.metric("平均持仓", f"{result.avg_holding_days:.1f}天")

            if result.details:
                st.subheader("交易明细")
                detail_data = []
                for d in result.details:
                    emoji = "🟢" if d.pnl > 0 else "🔴"
                    detail_data.append({
                        "结果": emoji,
                        "股票": f"{d.name}({d.symbol})",
                        "买入价": float(d.buy_price),
                        "卖出价": float(d.sell_price),
                        "盈亏%": f"{float(d.pnl_pct)}%",
                        "持仓天数": d.holding_days,
                    })
                st.dataframe(detail_data, use_container_width=True)

            reviewer = LLMReviewer(api_key=config.llm_api_key, model=config.llm_model)
            comment = reviewer.review(result)

            st.subheader(f"AI点评 (评分: {comment.score}/10)")
            st.write(comment.summary)
            review_col1, review_col2 = st.columns(2)
            with review_col1:
                if comment.strengths:
                    st.write("**优点:**")
                    for s in comment.strengths:
                        st.write(f"  ✅ {s}")
                if comment.weaknesses:
                    st.write("**不足:**")
                    for w in comment.weaknesses:
                        st.write(f"  ⚠️ {w}")
            with review_col2:
                if comment.suggestions:
                    st.write("**改进建议:**")
                    for s in comment.suggestions:
                        st.write(f"  💡 {s}")
