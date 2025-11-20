import streamlit as st
import pandas as pd
import plotly.express as px

from src.analytics.forecasting import (
    load_price_data,
    train_prophet,
    evaluate_forecast,
)
from src.analytics.forecasting import (
    load_price_data,
    train_prophet,
    evaluate_forecast,
    train_lstm_forecast,
)


def render_forecasting_section(symbol: str):
    st.subheader(f"📈 Stock Price Forecasting — {symbol}")

    col_main, col_side = st.columns([3, 1])

    with col_side:
        period = st.selectbox("Historical Period", ["6mo", "1y", "2y", "5y"], index=1)
        horizon = st.slider("Forecast Horizon (days)", 5, 60, 30)
        window_size = st.slider("LSTM Window Size (days)", 10, 90, 30)
        epochs = st.slider("LSTM Epochs", 10, 100, 40)

        use_prophet = st.checkbox("Run Prophet", value=True)
        use_lstm = st.checkbox("Run LSTM (PyTorch)", value=True)

        run_button = st.button("Fetch & Forecast")

    with col_main:
        if not run_button:
            st.info("Select settings on the right and click **Fetch & Forecast**.")
            return

        # 1) Load data
        with st.spinner("Fetching price data..."):
            try:
                df = load_price_data(symbol, period=period)
            except Exception as e:
                st.error(str(e))
                return

        st.success(f"Loaded {len(df)} data points.")

        fig = px.line(title=f"{symbol} Price Forecast")
        fig.add_scatter(x=df["ds"], y=df["y"], mode="lines", name="Actual Price")

        metrics_table = {}

        # 2) Prophet
        if use_prophet:
            with st.spinner("Training Prophet model..."):
                forecast_p, model_p = train_prophet(df, periods=horizon)

            # Plot Prophet forecast
            fig.add_scatter(
                x=forecast_p["ds"],
                y=forecast_p["yhat"],
                mode="lines",
                name="Prophet Forecast",
            )

            # Evaluate Prophet
            metrics_p = evaluate_forecast(df, forecast_p)
            metrics_table["Prophet"] = metrics_p

        # 3) LSTM
        if use_lstm:
            with st.spinner("Training LSTM model..."):
                in_sample_lstm, future_lstm, metrics_lstm = train_lstm_forecast(
                    df,
                    window_size=window_size,
                    epochs=epochs,
                    forecast_horizon=horizon,
                )

            # Combine in-sample + future for plotting
            full_lstm = pd.concat([in_sample_lstm, future_lstm], ignore_index=True)

            fig.add_scatter(
                x=full_lstm["ds"],
                y=full_lstm["yhat_lstm"],
                mode="lines",
                name="LSTM Forecast",
            )

            metrics_table["LSTM"] = metrics_lstm

        st.markdown("### Forecast Visualization")
        st.plotly_chart(fig, use_container_width=True)

        # 4) Metrics summary
        if metrics_table:
            st.markdown("### Model Accuracy (on historical region)")
            for model_name, m in metrics_table.items():
                st.write(f"**{model_name}** — MAE: `{m['MAE']:.4f}`, RMSE: `{m['RMSE']:.4f}`")

