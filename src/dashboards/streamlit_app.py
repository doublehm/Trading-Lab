import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

import streamlit as st
from src.config import DEFAULT_SYMBOLS
from src.analytics.order_book import render_order_book_section
from src.analytics.order_book_history import load_order_book_history, build_heatmap_frames
from src.analytics.order_book_replay import render_order_book_replay_section
from src.dashboards.forecasting_ui import render_forecasting_section
from src.dashboards.volatility_ui import render_volatility_section
from src.dashboards.alternative_data_ui import render_alt_data_section
from src.dashboards.realtime_etl_ui import render_realtime_etl_section


# Later you will import:
# from src.analytics.order_book import render_order_book_section
# from src.analytics.forecasting import render_forecasting_section
# etc.


def main():
    st.set_page_config(
        page_title="Trading Lab",
        layout="wide",
    )

    st.title("Trading Lab")
    st.caption("Multi-lab trading analytics platform: order books, forecasting, volatility, alternative data, and sentiment.")

    # Sidebar navigation
    section = st.sidebar.radio(
        "Select Lab",
        [
            "Order Book Heatmap & Liquidity Radar",
            "Historical Liquidity Replay",
            "Stock Price Forecasting (Prophet / LSTM)",
            "Volatility Prediction",
            "Real-Time ETL Dashboard",
            "Alternative Data Alpha (Google Trends)",
            "Sentiment-Driven Strategy (Reddit + SEC)",
        ],
    )

    symbol = st.sidebar.selectbox("Symbol", DEFAULT_SYMBOLS)

    if section == "Order Book Heatmap & Liquidity Radar":
        st.header("📊 Order Book Heatmap & Liquidity Radar")
        render_order_book_section(symbol)

    elif section == "Historical Liquidity Replay":
        st.header("Historical Liquidity Replay")
        render_order_book_replay_section(symbol)

    elif section == "Stock Price Forecasting (Prophet / LSTM)":
        st.header("📈 Stock Price Forecasting")
        st.write("Placeholder: here you'll forecast prices with Prophet & LSTM.")
        render_forecasting_section(symbol)

    elif section == "Volatility Prediction":
        st.header("⚡ Volatility Prediction")
        st.write("Placeholder: here you'll model and visualize volatility.")
        render_volatility_section(symbol)

    elif section == "Real-Time ETL Dashboard":
        st.header("🔄 Real-Time ETL Dashboard")
        render_realtime_etl_section(symbol)

    elif section == "Alternative Data Alpha (Google Trends)":
        st.header("🌍 Alternative Data Alpha")
        st.write("Placeholder: Google Trends + simple alpha strategies.")
        render_alt_data_section(symbol)

    elif section == "Sentiment-Driven Strategy (Reddit + SEC)":
        st.header("🧠 Sentiment-Driven Strategy")
        st.write("Placeholder: sentiment scores + backtest results.")
        # render_sentiment_section(symbol)


if __name__ == "__main__":
    main()

