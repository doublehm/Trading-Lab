import pandas as pd
import yfinance as yf
from prophet import Prophet
from sklearn.metrics import mean_absolute_error, mean_squared_error
import numpy as np
import torch
import torch.nn as nn

YF_SYMBOL_MAP = {
    "BTCUSDT": "BTC-USD",
    "ETHUSDT": "ETH-USD",
    # you can add more mappings here if needed
}


def map_to_yf_symbol(symbol: str) -> str:
    """
    Map internal / Binance-style symbols to Yahoo Finance symbols.
    If no mapping is found, we assume the symbol is already a valid yfinance ticker.
    """
    return YF_SYMBOL_MAP.get(symbol, symbol)

# ------------------------------
# 1. DATA LOADER
# ------------------------------
def load_price_data(symbol: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    """
    Fetch OHLCV data from Yahoo Finance and return a clean DataFrame
    with ['ds', 'y'] where:
      - ds: datetime
      - y: numeric close price
    Handles both normal and MultiIndex columns from yfinance.
    """
    yf_symbol = map_to_yf_symbol(symbol)

    raw = yf.download(yf_symbol, period=period, interval=interval)

    if raw is None or raw.empty:
        raise ValueError(f"No data returned for {symbol} (mapped to {yf_symbol})")

    df = raw.copy()

    # If yfinance returns MultiIndex columns (e.g. ('Close', 'BTC-USD')),
    # flatten them into single strings like 'Close_BTC-USD'
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [
            "_".join([str(part) for part in col if part]) for col in df.columns
        ]

    # Move index to a column so we can treat it uniformly
    df = df.reset_index()

    # --- Find the date column ---
    date_col = None
    for c in df.columns:
        cl = str(c).lower()
        if "date" in cl:  # catches 'Date', 'Datetime', etc.
            date_col = c
            break

    if date_col is None:
        raise ValueError(
            f"Could not find a date column in downloaded data: {df.columns.tolist()}"
        )

    # --- Find the close column ---
    close_col = None
    for c in df.columns:
        cl = str(c).lower()
        if "close" in cl:  # works for 'Close' or 'Close_BTC-USD'
            close_col = c
            break

    if close_col is None:
        raise ValueError(
            f"Could not find a close column in downloaded data: {df.columns.tolist()}"
        )

    # Keep only date + close columns
    df = df[[date_col, close_col]].copy()
    df.rename(columns={date_col: "ds", close_col: "y"}, inplace=True)

    # Ensure correct types
    df["ds"] = pd.to_datetime(df["ds"])
    df["y"] = pd.to_numeric(df["y"], errors="coerce")

    # Drop rows where y is NaN
    df = df.dropna(subset=["y"])

    if df.empty:
        raise ValueError(
            f"All 'y' values are NaN after cleaning for {symbol} (mapped to {yf_symbol}). "
            f"Columns were: {raw.columns.tolist()}"
        )

    return df
# ------------------------------
# 2. PROPHET FORECASTING
# ------------------------------
def train_prophet(df: pd.DataFrame, periods: int = 30) -> tuple[pd.DataFrame, Prophet]:
    """
    Train a Prophet model and return forecast + model.
    """
    model = Prophet()
    model.fit(df)

    future = model.make_future_dataframe(periods=periods)
    forecast = model.predict(future)

    return forecast, model


def evaluate_forecast(df: pd.DataFrame, forecast: pd.DataFrame) -> dict:
    """
    Compare Prophet predictions against actual values (only for overlapping dates).
    """
    merged = df.merge(
        forecast[["ds", "yhat"]],
        on="ds",
        how="inner"
    )

    mae = mean_absolute_error(merged["y"], merged["yhat"])
    rmse = np.sqrt(mean_squared_error(merged["y"], merged["yhat"]))

    return {"MAE": mae, "RMSE": rmse}

# ------------------------------
# 3. LSTM FORECASTING (PyTorch)
# ------------------------------


class LSTMForecast(nn.Module):
    def __init__(self, input_size: int = 1, hidden_size: int = 32, num_layers: int = 2, dropout: float = 0.2):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.fc = nn.Linear(hidden_size, 1)

    def forward(self, x):
        """
        x: (batch, seq_len, input_size)
        """
        out, _ = self.lstm(x)
        out = out[:, -1, :]  # last time step
        out = self.fc(out)
        return out


def _create_lstm_sequences(values: np.ndarray, window_size: int):
    """
    Convert 1D series into supervised sequences for LSTM.
    Returns X, y where:
      X: (num_samples, window_size)
      y: (num_samples,)
    """
    X, y = [], []
    for i in range(len(values) - window_size):
        X.append(values[i : i + window_size])
        y.append(values[i + window_size])
    return np.array(X, dtype="float32"), np.array(y, dtype="float32")


def train_lstm_forecast(
    df: pd.DataFrame,
    window_size: int = 30,
    epochs: int = 30,
    lr: float = 1e-3,
    forecast_horizon: int = 30,
    device: str | None = None,
):
    """
    Train an LSTM on the 'y' series in df and:
      - return in-sample predictions (aligned to history)
      - return future predictions for `forecast_horizon` days

    Returns:
      in_sample_df: ds, yhat_lstm (aligned to df[window_size:])
      future_df:    ds, yhat_lstm (next forecast_horizon days)
      metrics:      dict with MAE, RMSE on in-sample region
    """
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    series = df["y"].values.astype("float32")

    # Normalize for stable training
    mean = series.mean()
    std = series.std() if series.std() > 0 else 1.0
    series_norm = (series - mean) / std

    # Build sequences
    X, y = _create_lstm_sequences(series_norm, window_size)
    if len(X) == 0:
        raise ValueError("Not enough data to create sequences for LSTM. Try shorter window_size or longer period.")

    # For simplicity, we train on all but the last forecast_horizon samples
    cutoff = max(1, len(X) - forecast_horizon)
    X_train = X[:cutoff]
    y_train = y[:cutoff]

    X_train_t = torch.from_numpy(X_train).unsqueeze(-1).to(device)  # (batch, seq_len, 1)
    y_train_t = torch.from_numpy(y_train).unsqueeze(-1).to(device)  # (batch, 1)

    model = LSTMForecast(input_size=1, hidden_size=32, num_layers=2, dropout=0.2).to(device)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    model.train()
    for epoch in range(epochs):
        optimizer.zero_grad()
        out = model(X_train_t)
        loss = criterion(out, y_train_t)
        loss.backward()
        optimizer.step()

    # In-sample predictions for all sequences (including the last ones)
    model.eval()
    with torch.no_grad():
        X_all_t = torch.from_numpy(X).unsqueeze(-1).to(device)
        preds_norm = model(X_all_t).cpu().numpy().flatten()

    preds = preds_norm * std + mean

    # Align predictions to df dates
    ds_all = df["ds"].iloc[window_size:]
    in_sample_df = pd.DataFrame({"ds": ds_all.values, "yhat_lstm": preds})

    # Evaluate on overlapping in-sample region
    merged = df.merge(in_sample_df, on="ds", how="inner")
    mae = mean_absolute_error(merged["y"], merged["yhat_lstm"])
    rmse = np.sqrt(mean_squared_error(merged["y"], merged["yhat_lstm"]))
    metrics = {"MAE": mae, "RMSE": rmse}

    # Future forecasts: iterative one-step ahead
    future_dates = []
    future_preds = []

    last_window = series_norm[-window_size:].copy()
    last_date = df["ds"].iloc[-1]

    for i in range(forecast_horizon):
        x_in = torch.from_numpy(last_window).view(1, window_size, 1).to(device)
        with torch.no_grad():
            next_norm = model(x_in).cpu().numpy().flatten()[0]

        next_value = next_norm * std + mean
        future_preds.append(next_value)

        # roll window and append prediction
        last_window = np.roll(last_window, -1)
        last_window[-1] = next_norm

        future_dates.append(last_date + pd.Timedelta(days=i + 1))

    future_df = pd.DataFrame({"ds": future_dates, "yhat_lstm": future_preds})

    return in_sample_df, future_df, metrics
