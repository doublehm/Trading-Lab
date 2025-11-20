import pandas as pd
import plotly.express as px
import streamlit as st

from src.analytics.volatility import compute_volatility_features, naive_vol_forecast
from src.analytics.volatility import (
    compute_volatility_features,
    naive_vol_forecast,
    xgboost_vol_forecast,
)

def render_volatility_section(symbol: str):
    st.subheader(f"⚡ Volatility Lab — {symbol}")

    col_side, col_main = st.columns([1, 3])

    with col_side:
        period = st.selectbox("Historical Period", ["6mo", "1y", "2y"], index=1)
        window_short = st.slider("Short Window (days)", 5, 30, 10)
        window_long = st.slider("Long Window (days)", 10, 90, 30)
        run_xgb = st.checkbox("Run XGBoost model", value=True)
        run_button = st.button("Compute Volatility (and XGBoost if checked)")

    with col_main:
        if not run_button:
            st.info("Choose parameters on the left and click **Compute Volatility (and XGBoost if checked)**.")
            return

        # --- Compute volatility features ---
        with st.spinner("Loading data and computing volatility..."):
            try:
                df = compute_volatility_features(
                    symbol=symbol,
                    period=period,
                    window_short=window_short,
                    window_long=window_long,
                )
            except Exception as e:
                st.error(str(e))
                return

        if df.empty:
            st.error("No data / volatility computed.")
            return

        st.success(f"Computed volatility for {len(df)} days.")

        # 1) Price chart
        st.markdown("### 📈 Price")
        fig_price = px.line(
            df,
            x="ds",
            y="y",
            title=f"{symbol} Price",
            labels={"ds": "Date", "y": "Price"},
        )
        st.plotly_chart(fig_price, use_container_width=True)

        # 2) Volatility chart
        st.markdown("### ⚡ Rolling Volatility (Annualized)")
        fig_vol = px.line(
            df,
            x="ds",
            y=["vol_short_ann", "vol_long_ann"],
            labels={"ds": "Date", "value": "Annualized Volatility", "variable": "Series"},
            title="Short vs Long Rolling Volatility",
        )
        st.plotly_chart(fig_vol, use_container_width=True)

        # 3) Distribution of returns
        st.markdown("### 🔍 Return Distribution")
        fig_hist = px.histogram(
            df,
            x="ret",
            nbins=50,
            title="Distribution of Daily Log Returns",
        )
        st.plotly_chart(fig_hist, use_container_width=True)

        # 4) Naive volatility forecast
        st.markdown("### 🧪 Naive Volatility Forecast (Baseline)")
        df_naive, metrics_naive = naive_vol_forecast(df)

        st.write(f"**MAE (Naive):** {metrics_naive['MAE']:.6f}")
        st.write(f"**RMSE (Naive):** {metrics_naive['RMSE']:.6f}")

        if not df_naive.empty:
            st.markdown("#### Naive: Predicted vs Realized Volatility Over Time")
            fig_naive = px.line(
                df_naive,
                x="ds",
                y=["realized_vol_next", "forecast_vol"],
                labels={"value": "Volatility", "variable": "Series"},
                title="Naive Model: Realized vs Forecast Volatility",
            )
            st.plotly_chart(fig_naive, use_container_width=True)

        # 5) XGBoost volatility forecast (optional)
        if run_xgb:
            st.markdown("### 🤖 XGBoost Volatility Forecast")
            with st.spinner("Training XGBoost..."):
                df_xgb, metrics_xgb, model_xgb = xgboost_vol_forecast(df)

            st.success("XGBoost training complete.")

            st.write(f"**MAE (XGBoost):** {metrics_xgb['MAE']:.6f}")
            st.write(f"**RMSE (XGBoost):** {metrics_xgb['RMSE']:.6f}")

            st.markdown("### Forecast vs Realized Volatility (Test Set)")
            fig_xgb = px.line(
                df_xgb,
                x="ds",
                y=["realized_vol_next", "forecast_vol_xgb"],
                labels={"value": "Volatility", "variable": "Series"},
                title="XGBoost: Predicted vs Actual Volatility",
            )
            st.plotly_chart(fig_xgb, use_container_width=True)
                        # Combined comparison: Naive vs XGBoost vs Realized (on overlapping region)
            st.markdown("### 🥊 Naive vs XGBoost vs Realized Volatility (Test Region)")

            # df_naive is from earlier naive_vol_forecast(df)
            merged = df_naive.merge(
                df_xgb[["ds", "forecast_vol_xgb"]],
                on="ds",
                how="inner",
            )

            if not merged.empty:
                fig_combined = px.line(
                    merged,
                    x="ds",
                    y=["realized_vol_next", "forecast_vol", "forecast_vol_xgb"],
                    labels={"value": "Volatility", "variable": "Series"},
                    title="Realized vs Naive vs XGBoost Predicted Volatility",
                )
                st.plotly_chart(fig_combined, use_container_width=True)
            else:
                st.info("No overlapping region between Naive and XGBoost predictions to plot.")


