import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from src.config import DATABASE_URL

_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(DATABASE_URL, future=True)
    return _engine


def test_connection() -> None:
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("DB connection OK, result:", list(result))


def init_order_book_table() -> None:
    """
    create the order_book_snapshots table if it does not exist.
    one row per price level in a given snapshot.
    """
    ddl = """
    CREATE TABLE IF NOT EXISTS order_book_snapshots (
        id BIGSERIAL PRIMARY KEY,
        symbol TEXT NOT NULL,
        snapshot_time TIMESTAMPTZ NOT NULL,
        side TEXT NOT NULL CHECK (side IN ('bid', 'ask')),
        price NUMERIC NOT NULL,
        volume NUMERIC NOT NULL
    );
    """
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text(ddl))
    print("Ensured order_book_snapshots table exist")


def insert_order_book_snapshot(symbol: str, df: pd.DataFrame) -> None:
    """
    Insert a single snapshot (all price levels) into order_book_snapshots.
    df must have columns: ['side', 'price', 'volume'].
    """
    engine = get_engine()

    snapshot_time = datetime.utcnow()

    snapshot_df = df.copy()
    snapshot_df["symbol"] = symbol
    snapshot_df["snapshot_time"] = snapshot_time

    # Reorder columns to match table definition
    snapshot_df = snapshot_df[["symbol", "snapshot_time", "side", "price", "volume"]]

    snapshot_df.to_sql(
        "order_book_snapshots",
        engine,
        if_exists="append",
        index=False,
        method="multi",
    )

    print(f"Inserted snapshot for {symbol} at {snapshot_time} with {len(snapshot_df)} levels.")

def init_klines_table() -> None:
    """
    Create a price_klines table if it does not exist.
    Stores OHLCV candles from Binance (any symbol/interval).
    """
    ddl = """
    CREATE TABLE IF NOT EXISTS price_klines (
        id BIGSERIAL PRIMARY KEY,
        symbol TEXT NOT NULL,
        interval TEXT NOT NULL,
        open_time TIMESTAMPTZ NOT NULL,
        close_time TIMESTAMPTZ NOT NULL,
        open NUMERIC NOT NULL,
        high NUMERIC NOT NULL,
        low NUMERIC NOT NULL,
        close NUMERIC NOT NULL,
        volume NUMERIC NOT NULL,
        quote_asset_volume NUMERIC,
        number_of_trades BIGINT,
        taker_buy_base NUMERIC,
        taker_buy_quote NUMERIC,
        UNIQUE (symbol, interval, open_time)
    );
    """
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text(ddl))
    print("Ensured price_klines table exists.")


def insert_klines(symbol: str, interval: str, df: pd.DataFrame) -> None:
    """
    Insert a batch of klines into price_klines.
    df is expected to have columns:
      open_time, close_time, open, high, low, close, volume,
      quote_asset_volume, number_of_trades, taker_buy_base, taker_buy_quote
    """
    if df.empty:
        print("No klines to insert.")
        return

    engine = get_engine()

    # Add symbol + interval columns
    df = df.copy()
    df["symbol"] = symbol
    df["interval"] = interval

    # Convert to dicts for executemany
    records = df.to_dict(orient="records")

    sql = text("""
        INSERT INTO price_klines (
            symbol, interval, open_time, close_time,
            open, high, low, close, volume,
            quote_asset_volume, number_of_trades,
            taker_buy_base, taker_buy_quote
        )
        VALUES (
            :symbol, :interval, :open_time, :close_time,
            :open, :high, :low, :close, :volume,
            :quote_asset_volume, :number_of_trades,
            :taker_buy_base, :taker_buy_quote
        )
        ON CONFLICT (symbol, interval, open_time) DO NOTHING;
    """)

    with engine.begin() as conn:
        conn.execute(sql, records)

    print(f"Inserted {len(records)} klines (symbol={symbol}, interval={interval}).")

