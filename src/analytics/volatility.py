import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_squared_error

from src.analytics.forecasting import load_price_data


def compute_volatility_features(
    symbol: str,
    period: str = "1y",
    window_short: int = 5,
    window_long: int = 20,
) -> pd.DataFrame:
    """
    Load price data and compute:
      - log returns
      - short / long rolling realized volatility
      - daily volatility (σ) annualized

    Returns a DataFrame with columns:
      ds, y, ret, vol_short, vol_long
    """
    df = load_price_data(symbol, period=period, interval="1d").copy()

    # log returns
    df["ret"] = np.log(df["y"] / df["y"].shift(1))
    df["ret"] = df["ret"].fillna(0.0)

    # rolling volatility (daily)
    df["vol_short"] = df["ret"].rolling(window_short).std()
    df["vol_long"] = df["ret"].rolling(window_long).std()

    # annualize volatility (sqrt(252))
    ann_factor = np.sqrt(252)
    df["vol_short_ann"] = df["vol_short"] * ann_factor
    df["vol_long_ann"] = df["vol_long"] * ann_factor

    df = df.dropna().reset_index(drop=True)
    return df


def naive_vol_forecast(df: pd.DataFrame, horizon: int = 1):
    """
    Simple baseline: use long-window volatility as a forecast for next-day volatility.
    Evaluate against realized next-day volatility.

    Returns:
      df_valid: DataFrame with ds, realized_vol_next, forecast_vol
      metrics:  dict with MAE / RMSE
    """
    df = df.copy()

    # realized vol ~ abs(return) as a naive proxy
    df["realized_vol_next"] = df["ret"].abs().shift(-horizon)

    # forecast: use today's long-window annualized vol
    df["forecast_vol"] = df["vol_long_ann"]

    valid = df.dropna(subset=["realized_vol_next", "forecast_vol"]).reset_index(drop=True)
    if valid.empty:
        return valid, {"MAE": np.nan, "RMSE": np.nan}

    mae = mean_absolute_error(valid["realized_vol_next"], valid["forecast_vol"])
    rmse = np.sqrt(mean_squared_error(valid["realized_vol_next"], valid["forecast_vol"]))

    return valid[["ds", "realized_vol_next", "forecast_vol"]], {"MAE": mae, "RMSE": rmse}

def xgboost_vol_forecast(
    df: pd.DataFrame,
    horizon: int = 1,
    test_size: float = 0.2,
):
    """
    Predict next-day realized volatility using XGBoost.
    Uses lagged volatility, lagged returns, etc. as features.

    Returns:
      df_pred: DataFrame with ds, realized_vol_next, forecast_vol_xgb
      metrics: MAE, RMSE
      model: trained XGBoost model
    """

    df = df.copy()

    # Target = next-day realized vol (absolute log return)
    df["realized_vol_next"] = df["ret"].abs().shift(-horizon)

    # Features
    df["lag_ret"] = df["ret"].shift(1)
    df["lag2_ret"] = df["ret"].shift(2)
    df["lag_vol_short"] = df["vol_short_ann"].shift(1)
    df["lag_vol_long"] = df["vol_long_ann"].shift(1)

    df = df.dropna().reset_index(drop=True)

    feature_cols = [
        "lag_ret",
        "lag2_ret",
        "lag_vol_short",
        "lag_vol_long",
    ]

    X = df[feature_cols].values
    y = df["realized_vol_next"].values

    # Train/Test split
    split = int(len(X) * (1 - test_size))
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    # XGBoost model
    model = xgb.XGBRegressor(
        n_estimators=400,
        learning_rate=0.03,
        max_depth=4,
        subsample=0.9,
        colsample_bytree=0.9,
        objective="reg:squarederror",
    )

    model.fit(X_train, y_train)

    preds = model.predict(X_test)

    mae = mean_absolute_error(y_test, preds)
    rmse = np.sqrt(mean_squared_error(y_test, preds))

    df_pred = df.iloc[split:].copy()
    df_pred["forecast_vol_xgb"] = preds

    return df_pred, {"MAE": mae, "RMSE": rmse}, model

