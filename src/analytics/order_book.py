import time
from datetime import datetime
import pandas as pd
import streamlit as st
import plotly.express as px
from src.data_pipeline.binance_client import get_order_book_df


def compute_liquidity_imbalance(df: pd.DataFrame) -> float:
    """
    Liquidity imbalance = (BidVolume - AskVolume) / (BidVolume + AskVolume)
    """
    bid_vol = df[df["side"] == "bid"]["volume"].sum()
    ask_vol = df[df["side"] == "ask"]["volume"].sum()

    if bid_vol + ask_vol == 0:
        return 0.0

    return (bid_vol - ask_vol) / (bid_vol + ask_vol)


def draw_order_book(symbol: str, container_metrics, container_depth, container_heat):
    df = get_order_book_df(symbol=symbol, limit=80)

    # --- Spread & imbalance ---
    best_bid = df[df["side"] == "bid"]["price"].max()
    best_ask = df[df["side"] == "ask"]["price"].min()
    spread = best_ask - best_bid
    imbalance = compute_liquidity_imbalance(df)
    last_updated = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    with container_metrics:
        st.markdown("#### 📌 Snapshot Metrics")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Best Bid", f"{best_bid:.2f}")
        col2.metric("Best Ask", f"{best_ask:.2f}")
        col3.metric("Spread", f"{spread:.2f}")
        col4.metric("Imbalance", f"{imbalance:.4f}")
        st.caption(f"Last updated: {last_updated}")

    # --- Depth bar chart ---
    with container_depth:
        st.markdown("#### 📊 Depth Chart (Bid/Ask Volume by Price)")
        fig_depth = px.bar(
            df,
            x="price",
            y="volume",
            color="side",
            barmode="group",
            labels={"price": "Price", "volume": "Volume", "side": "Side"},
            height=400,
            title=f"Order Book Depth for {symbol}",
        )
        fig_depth.update_layout(xaxis={"type": "category"})
        st.plotly_chart(fig_depth, use_container_width=True)

    # --- Heatmap of depth ---
    with container_heat:
        st.markdown("#### 🔥 Depth Heatmap (Price × Side)")
        heat_data = df.pivot_table(
            values="volume",
            index="price",
            columns="side",
            fill_value=0,
        ).sort_index(ascending=False)

        fig_heat = px.imshow(
            heat_data,
            aspect="auto",
            color_continuous_scale="Viridis",
            title=f"Bid/Ask Depth Heatmap for {symbol}",
        )
        st.plotly_chart(fig_heat, use_container_width=True)


def render_order_book_section(symbol: str):
    st.subheader(f"📊 Order Book Heatmap & Liquidity Radar – {symbol}")

    st.markdown(
        "This view pulls the **live Binance order book** for the selected symbol "
        "and visualizes depth, spread, and liquidity imbalance."
    )

    auto_refresh = st.checkbox("Auto-refresh", value=True)
    refresh_rate = st.slider("Refresh every (seconds)", 1, 10, 3)
    cycles = st.slider("Number of refresh cycles (for auto-refresh)", 10, 300, 60)

    # Placeholders so we can redraw in the same place
    metrics_placeholder = st.empty()
    depth_placeholder = st.empty()
    heat_placeholder = st.empty()

    # Initial draw
    draw_order_book(symbol, metrics_placeholder, depth_placeholder, heat_placeholder)

    if auto_refresh:
        # Simple loop – runs for `cycles` iterations, then stops
        for i in range(cycles):
            time.sleep(refresh_rate)
            draw_order_book(symbol, metrics_placeholder, depth_placeholder, heat_placeholder)
            # A small visual cue in the UI
            st.caption(f"Auto-refresh {i + 1}/{cycles}")

