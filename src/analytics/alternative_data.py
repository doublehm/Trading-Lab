import numpy as np
import pandas as pd
from pytrends.request import TrendReq

from src.analytics.forecasting import load_price_data


def fetch_google_trends(keyword: str, timeframe: str = "today 12-m", geo: str = "") -> pd.DataFrame:
    """
    Fetch Google Trends interest_over_time for a given keyword.

    timeframe examples:
      - "today 3-m"
      - "today 12-m"
      - "2020-01-01 2024-01-01"

    Returns DataFrame with columns: ds, trend
    """
    pytrends = TrendReq(hl="en-US", tz=0)
    pytrends.build_payload([keyword], cat=0, timeframe=timeframe, geo=geo, gprop="")

    df_trends = pytrends.interest_over_time()
    if df_trends.empty:
        raise ValueError(f"No Google Trends data returned for keyword '{keyword}'.")

    df_trends = df_trends.reset_index()
    # Trends column is exactly the keyword
    if keyword not in df_trends.columns:
        raise ValueError(f"Keyword '{keyword}' not found in Google Trends columns: {df_trends.columns.tolist()}")

    df_trends.rename(columns={"date": "ds", keyword: "trend"}, inplace=True)
    df_trends["ds"] = pd.to_datetime(df_trends["ds"])

    # Drop the 'isPartial' column if present
    if "isPartial" in df_trends.columns:
        df_trends = df_trends.drop(columns=["isPartial"])

    return df_trends


def merge_trends_with_price(symbol: str, keyword: str, period: str = "1y", interval: str = "1d",
                            timeframe: str = "today 12-m", geo: str = "") -> pd.DataFrame:
    """
    Load price data and Google Trends and merge them on date.

    Returns DataFrame with:
      ds, price, trend
    """
    # Price data
    price_df = load_price_data(symbol, period=period, interval=interval)
    price_df = price_df.rename(columns={"y": "price"})

    # Trends data
    trends_df = fetch_google_trends(keyword, timeframe=timeframe, geo=geo)

    # Align by date (inner join)
    merged = pd.merge(
        price_df[["ds", "price"]],
        trends_df[["ds", "trend"]],
        on="ds",
        how="inner",
    ).sort_values("ds").reset_index(drop=True)

    if merged.empty:
        raise ValueError("Merged dataset is empty. Try adjusting period/timeframe or keyword.")

    return merged


def compute_lagged_correlations(df: pd.DataFrame, max_lag: int = 30) -> pd.DataFrame:
    """
    Compute correlation between price and trend at different lags.

    Positive lag: trend leads price (trend_t vs price_{t+lag})
    Negative lag: trend lags price.

    Returns DataFrame with columns: lag, correlation
    """
    correlations = []

    price = df["price"].values.astype(float)
    trend = df["trend"].values.astype(float)

    for lag in range(-max_lag, max_lag + 1):
        if lag < 0:
            # trend_t vs price_{t+|lag|}
            x = trend[-lag:]
            y = price[: len(price) + lag]
        elif lag > 0:
            # trend_{t-lag} vs price_t
            x = trend[:-lag]
            y = price[lag:]
        else:
            x = trend
            y = price

        if len(x) < 5:
            corr = np.nan
        else:
            corr = np.corrcoef(x, y)[0, 1]

        correlations.append({"lag": lag, "correlation": corr})

    return pd.DataFrame(correlations)

def find_best_leading_lag(corr_df: pd.DataFrame) -> dict | None:
    """
    From the lagged correlation table, find the strongest *leading* lag
    (lag > 0, where trends lead price).
    Returns dict {'lag': int, 'correlation': float} or None if not found.
    """
    leading = corr_df[corr_df["lag"] > 0].dropna(subset=["correlation"])
    if leading.empty:
        return None

    idx = leading["correlation"].abs().values.argmax()
    row = leading.iloc[idx]
    return {"lag": int(row["lag"]), "correlation": float(row["correlation"])}

def backtest_trend_signal(
    df: pd.DataFrame,
    best_lag: int,
    z_threshold: float = 0.5,
    roll_window: int = 7,
):
    """
    Turn Google Trends into a trading signal:

    - Compute a z-score of the trend (vs rolling mean/std)
    - Go long when:
        trend_z > z_threshold and trend is rising (slope > 0)
    - Flat otherwise.

    We then apply that signal to future L-day returns, where L = best_lag.

    Returns:
      bt_df: ds, signal, strategy_ret, bh_ret, equity_strategy, equity_bh
      metrics: dict with total returns & Sharpe-like ratio
    """
    df = df.copy()

    # L-day forward return using price (so we compare on same horizon as the best lag)
    L = best_lag
    df["future_ret_L"] = df["price"].shift(-L) / df["price"] - 1.0

    # Rolling stats on trends
    df["trend_mean"] = df["trend"].rolling(roll_window).mean()
    df["trend_std"] = df["trend"].rolling(roll_window).std()
    df["trend_z"] = (df["trend"] - df["trend_mean"]) / df["trend_std"]
    df["trend_slope"] = df["trend"].diff()

    # Simple long-only signal: 1 when trend is high & rising, else 0
    df["signal"] = 0
    df.loc[
        (df["trend_z"] > z_threshold) & (df["trend_slope"] > 0),
        "signal",
    ] = 1

    # Drop rows where we don't have future return yet
    bt_df = df.dropna(subset=["future_ret_L"]).copy()

    # Strategy return = signal * future L-day return
    bt_df["strategy_ret"] = bt_df["signal"] * bt_df["future_ret_L"]

    # Buy-and-hold on same horizon (always 1 unit of risk)
    bt_df["bh_ret"] = bt_df["future_ret_L"]

    # Equity curves
    bt_df["equity_strategy"] = (1 + bt_df["strategy_ret"]).cumprod()
    bt_df["equity_bh"] = (1 + bt_df["bh_ret"]).cumprod()

    # Metrics
    total_strategy = bt_df["equity_strategy"].iloc[-1] - 1.0
    total_bh = bt_df["equity_bh"].iloc[-1] - 1.0

    avg = bt_df["strategy_ret"].mean()
    std = bt_df["strategy_ret"].std()
    if std > 0:
        # Very rough Sharpe approximation (scale by sqrt of 252/L)
        sharpe = avg / std * np.sqrt(252.0 / L)
    else:
        sharpe = np.nan

    metrics = {
        "total_return_strategy": total_strategy,
        "total_return_bh": total_bh,
        "sharpe_like": sharpe,
        "n_trades_periods": int(bt_df["signal"].sum()),
        "lag_used": int(L),
    }

    return bt_df[["ds", "signal", "strategy_ret", "bh_ret", "equity_strategy", "equity_bh"]], metrics

