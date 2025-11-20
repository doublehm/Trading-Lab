import pandas as pd
from sqlalchemy import text

from src.data_pipeline.database import get_engine

def load_recent_klines_from_db(
    symbol: str,
    interval: str = "1m",
    lookback_minutes: int = 60,  # kept for signature compatibility; not used
) -> pd.DataFrame:
    """
    Load recent OHLCV data from price_klines for a given symbol/interval.
    DEBUG VERSION: ignore time filter and just fetch the last 500 rows.
    """
    engine = get_engine()

    sql = text(
        """
        SELECT
            open_time,
            close_time,
            open,
            high,
            low,
            close,
            volume,
            quote_asset_volume,
            number_of_trades,
            taker_buy_base,
            taker_buy_quote
        FROM price_klines
        WHERE symbol = :symbol
          AND interval = :interval
        ORDER BY open_time DESC
        LIMIT 500;
        """
    )

    with engine.connect() as conn:
        df = pd.read_sql(
            sql,
            conn,
            params={
                "symbol": symbol,
                "interval": interval,
            },
        )

    # sort oldest → newest for plotting
    df = df.sort_values("open_time").reset_index(drop=True)
    print(f"[DEBUG] Loaded {len(df)} rows from price_klines for {symbol} @ {interval}")
    return df
