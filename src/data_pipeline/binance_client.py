import requests
from typing import Dict, Any, List
from src.config import BINANCE_BASE_URL
import pandas as pd
from datetime import datetime, timezone

def get_order_book(symbol: str = "BTCUSDT", limit: int = 50) -> Dict[str, Any]:
    """
    Fetch order book snapshot from Binance.
    """
    url = f"{BINANCE_BASE_URL}/api/v3/depth"
    params = {"symbol": symbol, "limit": limit}
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


def get_klines(symbol: str = "BTCUSDT", interval: str = "1m", limit: int = 500) -> List[List[Any]]:
    """
    Fetch historical klines (candles) from Binance.
    """
    url = f"{BINANCE_BASE_URL}/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()

def klines_to_df(klines: list) -> pd.DataFrame:
    """
    Convert Binance /klines response to DataFrame with named columns.
    Expected kline format:
      [ open_time, open, high, low, close, volume, close_time,
        quote_asset_volume, number_of_trades,
        taker_buy_base, taker_buy_quote, ignore ]
    """
    cols = [
        "open_time_ms",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "close_time_ms",
        "quote_asset_volume",
        "number_of_trades",
        "taker_buy_base",
        "taker_buy_quote",
        "ignore",
    ]
    df = pd.DataFrame(klines, columns=cols)

    # Convert ms to UTC timestamps
    df["open_time"] = df["open_time_ms"].apply(
        lambda x: datetime.fromtimestamp(x / 1000.0, tz=timezone.utc)
    )
    df["close_time"] = df["close_time_ms"].apply(
        lambda x: datetime.fromtimestamp(x / 1000.0, tz=timezone.utc)
    )

    # Cast numeric columns
    num_cols = [
        "open",
        "high",
        "low",
        "close",
        "volume",
        "quote_asset_volume",
        "taker_buy_base",
        "taker_buy_quote",
    ]
    for c in num_cols:
        df[c] = df[c].astype(float)

    df["number_of_trades"] = df["number_of_trades"].astype(int)

    return df[
        [
            "open_time",
            "close_time",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "quote_asset_volume",
            "number_of_trades",
            "taker_buy_base",
            "taker_buy_quote",
        ]
    ]


def get_order_book_df(symbol: str = "BTCUSDT", limit: int = 100) -> pd.DataFrame:
    """
    Returns order book in a clean DataFrame format:
    columns: ['side', 'price', 'volume']
    """
    data = get_order_book(symbol, limit)

    bids = [
        {"side": "bid", "price": float(b[0]), "volume": float(b[1])}
        for b in data["bids"]
    ]
    asks = [
        {"side": "ask", "price": float(a[0]), "volume": float(a[1])}
        for a in data["asks"]
    ]

    return pd.DataFrame(bids + asks)
