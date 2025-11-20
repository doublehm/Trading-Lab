import pandas as pd
import plotly.express as px
import streamlit as st

from src.analytics.alternative_data import (
    merge_trends_with_price,
    compute_lagged_correlations,
     find_best_leading_lag,
    backtest_trend_signal,
)


def render_alt_data_section(symbol: str):
    st.subheader(f"🌍 Alternative Data Lab — {symbol}")

    st.markdown(
        "Analyze how **Google search interest** (Google Trends) relates to the asset's price. "
        "This can reveal whether search activity **leads** or **lags** market moves."
    )

    col_side, col_main = st.columns([1, 3])

    with col_side:
        keyword = st.text_input("Google Trends Keyword", value="bitcoin")
        period = st.selectbox("Price History Period", ["6mo", "1y", "2y"], index=1)
        timeframe = st.selectbox(
            "Google Trends Timeframe",
            ["today 3-m", "today 12-m", "today 5-y"],
            index=1,
        )
        geo = st.text_input("Geo (optional, e.g. 'US', 'CA')", value="")
        max_lag = st.slider("Max Lag (days)", 5, 60, 30)
        run_button = st.button("Fetch & Analyze")

    with col_main:
        if not run_button:
            st.info("Set parameters on the left and click **Fetch & Analyze**.")
            return

        # Fetch + merge
        with st.spinner("Fetching price and Google Trends data..."):
            try:
                df = merge_trends_with_price(
                    symbol=symbol,
                    keyword=keyword,
                    period=period,
                    interval="1d",
                    timeframe=timeframe,
                    geo=geo,
                )
            except Exception as e:
                st.error(str(e))
                return

        st.success(f"Merged {len(df)} daily points with price + trends.")
        st.write(df.tail())

        # 1) Time-series view
        st.markdown("### 📈 Price vs Google Trends Over Time")

        fig_ts = px.line(
            df,
            x="ds",
            y=["price", "trend"],
            labels={"value": "Value", "variable": "Series"},
            title=f"{symbol} Price vs Google Trends: '{keyword}'",
        )
        st.plotly_chart(fig_ts, use_container_width=True)

        # 2) Scatter view
        st.markdown("### 🔍 Scatter: Trends vs Price (Same Day)")

        fig_scatter = px.scatter(
            df,
            x="trend",
            y="price",
            trendline="ols",
            labels={"trend": "Google Trends Score", "price": "Price"},
            title="Price vs Google Trends (Same Day)",
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

        # 3) Lagged correlations
        st.markdown("### ⏱ Lagged Correlations (Does Trends Lead Price?)")

        corr_df = compute_lagged_correlations(df, max_lag=max_lag)

        fig_corr = px.bar(
            corr_df,
            x="lag",
            y="correlation",
            title="Correlation between Price and Trends at Different Lags",
            labels={"lag": "Lag (days)", "correlation": "Correlation"},
        )
        st.plotly_chart(fig_corr, use_container_width=True)

        st.markdown(
            "- **Positive lag**: Trends move first, price follows → search interest may **lead** price.\n"
            "- **Negative lag**: Price moves first, search interest follows → search may **react** to moves."
        )
 
        # 4) Trading signal using strongest leading lag
        st.markdown("### 🧪 Trading Signal from Strongest Leading Lag")

        best = find_best_leading_lag(corr_df)
        if best is None:
            st.info("No positive (leading) lag found with valid correlation. Cannot build a leading signal.")
            return

        st.write(
            f"Strongest leading lag: **{best['lag']} days**, "
            f"correlation = **{best['correlation']:.3f}**"
        )

        z_threshold = st.slider("Trend z-score threshold", 0.0, 3.0, 0.5, 0.1)
        roll_window = st.slider("Trend rolling window (days)", 3, 30, 7)

        if st.checkbox("Run trading signal backtest", value=True):
            with st.spinner("Backtesting trend-based strategy..."):
                bt_df, bt_metrics = backtest_trend_signal(
                    df,
                    best_lag=best["lag"],
                    z_threshold=z_threshold,
                    roll_window=roll_window,
                )

            st.success("Backtest complete.")

            st.markdown("#### 📈 Equity Curve: Strategy vs Buy & Hold")
            fig_eq = px.line(
                bt_df,
                x="ds",
                y=["equity_strategy", "equity_bh"],
                labels={"value": "Equity", "variable": "Series"},
                title="Trend-based Strategy vs Buy & Hold",
            )
            st.plotly_chart(fig_eq, use_container_width=True)

            st.markdown("#### 📊 Backtest Metrics")
            st.write(f"**Total Return (Strategy):** {bt_metrics['total_return_strategy'] * 100:.2f}%")
            st.write(f"**Total Return (Buy & Hold, same horizon):** {bt_metrics['total_return_bh'] * 100:.2f}%")
            st.write(f"**Sharpe-like Ratio (rough):** {bt_metrics['sharpe_like']:.2f}")
            st.write(f"**Lag used:** {bt_metrics['lag_used']} days")
            st.write(f"**Signal-on periods (approx trades):** {bt_metrics['n_trades_periods']}")

