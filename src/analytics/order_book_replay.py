import time
import streamlit as st
import plotly.express as px
import datetime
from datetime import datetime, timezone, timedelta
from src.analytics.order_book_history import load_order_book_history, build_heatmap_frames

SESSION_KEY_LOADED = "obr_loaded"
SESSION_KEY_FRAMES = "obr_frames"
SESSION_KEY_TIMESTAMPS = "obr_timestamps"
SESSION_KEY_IDX = "obr_idx"
SESSION_KEY_PLAY = "obr_play"

def render_order_book_replay_section(symbol: str):
    st.subheader(f"🎞 Historical Liquidity Replay — {symbol}")

    st.markdown(
        "Replay the depth of the order book over time based on previously collected snapshots."
    )
     # --- Init session state defaults ---
    if SESSION_KEY_LOADED not in st.session_state:
        st.session_state[SESSION_KEY_LOADED] = False
    if SESSION_KEY_IDX not in st.session_state:
        st.session_state[SESSION_KEY_IDX] = 0
    if SESSION_KEY_PLAY not in st.session_state:
        st.session_state[SESSION_KEY_PLAY] = False

    # --- Step 1: Choose time window ---
    start = st.text_input("Start Time (UTC)", (datetime.now(timezone.utc) - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S"))
    end = st.text_input("End Time (UTC)", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))

   
    # --- Load button ---
    if st.button("Load Snapshots"):
        with st.spinner("Loading data…"):
            df = load_order_book_history(symbol, start, end)

        if df.empty:
            st.session_state[SESSION_KEY_LOADED] = False
            st.error("No snapshots found in this time range.")
            return

        frames = build_heatmap_frames(df)
        timestamps = list(frames.keys())

        st.session_state[SESSION_KEY_FRAMES] = frames
        st.session_state[SESSION_KEY_TIMESTAMPS] = timestamps
        st.session_state[SESSION_KEY_LOADED] = True
        st.session_state[SESSION_KEY_IDX] = 0

        st.success(f"Loaded {len(timestamps)} snapshots.")

    # --- If not loaded yet, stop here ---
    if not st.session_state[SESSION_KEY_LOADED]:
        st.info("Load snapshots to start the replay.")
        return

    frames = st.session_state[SESSION_KEY_FRAMES]
    timestamps = st.session_state[SESSION_KEY_TIMESTAMPS]

    if not timestamps:
        st.error("No timestamps available.")
        return

    # --- Replay controls ---
    st.markdown("### 🔁 Replay Controls")

    # Auto-play checkbox linked to session_state
    play = st.checkbox(
        "Play (auto animation)",
        value=st.session_state[SESSION_KEY_PLAY],
        key=SESSION_KEY_PLAY,
    )

    speed = st.slider("Frame delay (seconds)", 0.1, 2.0, 0.5)

    # Slider WITHOUT key; we sync it manually with session_state
    current_idx = st.session_state[SESSION_KEY_IDX]
    manual_idx = st.slider(
        "Snapshot Index",
        0,
        len(timestamps) - 1,
        current_idx,
    )

    # Update session_state from manual slider movement
    st.session_state[SESSION_KEY_IDX] = manual_idx

    idx = st.session_state[SESSION_KEY_IDX]

    # --- Render current frame ---
    ts = timestamps[idx]
    heat_df = frames[ts]

    heatmap_container = st.empty()

    fig = px.imshow(
        heat_df,
        aspect="auto",
        color_continuous_scale="Viridis",
        title=f"Heatmap — {ts.strftime('%Y-%m-%d %H:%M:%S UTC')}",
    )
    heatmap_container.plotly_chart(fig, use_container_width=True)

    st.caption(f"Frame {idx + 1}/{len(timestamps)}")

    # --- Auto-play logic ---
    if st.session_state[SESSION_KEY_PLAY]:
        next_idx = (st.session_state[SESSION_KEY_IDX] + 1) % len(timestamps)
        st.session_state[SESSION_KEY_IDX] = next_idx

        time.sleep(speed)
        st.rerun()