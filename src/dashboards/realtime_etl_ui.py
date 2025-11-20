import plotly.express as px
import streamlit as st

from src.analytics.realtime_dashboard import load_recent_klines_from_db


def render_realtime_etl_section(symbol: str):
    st.subheader(f"🚰 Real-Time ETL Dashboard — {symbol}")

    st.markdown(
        "This dashboard reads **live OHLCV data** from the `price_klines` table in PostgreSQL, "
        "populated continuously by the Binance → Postgres ETL loop."
    )

    col_side, col_main = st.columns([1, 3])

    with col_side:
        interval = st.selectbox("Interval", ["1m", "5m", "15m"], index=0)
        lookback = st.slider("Lookback (minutes)", 30, 720, 120, step=30)
        run_button = st.button("Load Latest Data")

    with col_main:
        if not run_button:
            st.info("Choose interval + lookback on the left and click **Load Latest Data**.")
            return

        with st.spinner("Querying recent klines from PostgreSQL..."):
            try:
                df = load_recent_klines_from_db(
                    symbol=symbol,
                    interval=interval,
                    lookback_minutes=lookback,
                )
            except Exception as e:
                st.error(f"Failed to load data from DB: {e}")
                return

        if df.empty:
            st.warning("No data found for this symbol / interval / lookback. "
                       "Make sure your ETL loop is running and inserting rows.")
            return

        st.success(f"Loaded {len(df)} candles from DB.")

        # 1) Price chart (close)
        st.markdown("### 📈 Price (Close)")

        fig_price = px.line(
            df,
            x="open_time",
            y="close",
            labels={"open_time": "Time", "close": "Close Price"},
            title=f"{symbol} — {interval} Close Price (last {lookback} min)",
        )
        st.plotly_chart(fig_price, use_container_width=True)

        # 2) Volume chart
        st.markdown("### 📊 Volume")

        fig_vol = px.bar(
            df,
            x="open_time",
            y="volume",
            labels={"open_time": "Time", "volume": "Volume"},
            title=f"{symbol} — {interval} Volume (last {lookback} min)",
        )
        st.plotly_chart(fig_vol, use_container_width=True)

        # 3) Quick stats
        st.markdown("### 🔍 Snapshot Stats")

        last_row = df.iloc[-1]
        st.write(f"**Last candle open time (UTC):** {last_row['open_time']}")
        st.write(f"**Last close price:** {last_row['close']}")
        st.write(f"**Last volume:** {last_row['volume']}")

