from datetime import datetime
import pandas as pd
from sqlalchemy import text
from src.data_pipeline.binance_client import get_klines, klines_to_df
from src.data_pipeline.database import get_engine, init_klines_table, insert_klines
from src.config import DEFAULT_SYMBOLS  # if you have this; otherwise hardcode list

import time
from src.data_pipeline.binance_client import get_order_book_df
from src.data_pipeline.database import (
    get_engine,
    test_connection,
    init_order_book_table,
    insert_order_book_snapshot,
)


def fetch_and_store_klines(symbol: str = "BTCUSDT", interval: str = "1m", limit: int = 500):
    """
    Simple ETL: fetch klines from Binance and store them in a table.
    For now, we'll just print them and later we wire to PostgreSQL.
    """
    raw = get_klines(symbol=symbol, interval=interval, limit=limit)

    cols = [
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "num_trades",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ]
    df = pd.DataFrame(raw, columns=cols)

    # Convert timestamps
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    df["close_time"] = pd.to_datetime(df["close_time"], unit="ms")
    print(df.head())

    # TODO: Create table + insert data into PostgreSQL
    # engine = get_engine()
    # df.to_sql("price_bars", engine, if_exists="append", index=False)


def snapshot_order_book(symbol: str = "BTCUSDT", limit: int = 80) -> None:
    """
    Fetch one order book snapshot from Binance and store it in PostgreSQL.
    """
    print("Testing DB connection...")
    test_connection()

    print("Ensuring table exists...")
    init_order_book_table()

    print(f"Fetching order book for {symbol}...")
    df = get_order_book_df(symbol=symbol, limit=limit)

    print("Inserting snapshot into database...")
    insert_order_book_snapshot(symbol, df)

    print("Done.")



def load_recent_klines_to_db(symbol: str = "BTCUSDT", interval: str = "1m", limit: int = 500):
    """
    Fetch recent klines from Binance and insert them into PostgreSQL.
    Idempotent: duplicates are skipped via ON CONFLICT.
    """
    print(f"Fetching {limit} recent klines for {symbol} @ {interval}...")
    klines = get_klines(symbol=symbol, interval=interval, limit=limit)
    df = klines_to_df(klines)
    insert_klines(symbol, interval, df)
    print("ETL batch complete.")


def run_realtime_klines_etl(
    symbols: list[str] | None = None,
    interval: str = "1m",
    limit: int = 500,
    sleep_seconds: int = 60,
):
    """
    Simple realtime-ish loop:
      - every sleep_seconds, fetch recent klines for each symbol
      - write them to PostgreSQL
    """
    if symbols is None:
        # fallback list if you don't want to use DEFAULT_SYMBOLS
        symbols = ["BTCUSDT", "ETHUSDT"]

    init_klines_table()

    print(f"Starting realtime ETL loop for symbols={symbols}, interval={interval}...")
    while True:
        for sym in symbols:
            try:
                load_recent_klines_to_db(symbol=sym, interval=interval, limit=limit)
            except Exception as e:
                print(f"[ERROR] Failed ETL for {sym}: {e}")
        print(f"Sleeping {sleep_seconds} seconds...\n")
        time.sleep(sleep_seconds)



def snapshot_order_book_loop(symbol: str = "BTCUSDT", limit: int = 80, interval_seconds: int = 5, cycles: int = 60):
    """
    Take repeated snapshots every `interval_seconds` seconds.
    """
    test_connection()
    init_order_book_table()

    for i in range(cycles):
        print(f"[{i+1}/{cycles}] Fetching snapshot for {symbol}...")
        df = get_order_book_df(symbol=symbol, limit=limit)
        insert_order_book_snapshot(symbol, df)
        time.sleep(interval_seconds)


if __name__ == "__main__":
    fetch_and_store_klines()
    
    # For now, just snapshot BTCUSDT once
    #snapshot_order_book(symbol="BTCUSDT", limit=80)
    snapshot_order_book_loop(symbol="BTCUSDT", limit=80, interval_seconds=5, cycles=20)
    # Example: run realtime ETL for BTC and ETH on 1-minute candles
    run_realtime_klines_etl(symbols=["BTCUSDT", "ETHUSDT"], interval="1m", limit=500, sleep_seconds=60)
