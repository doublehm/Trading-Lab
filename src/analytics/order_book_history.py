import pandas as pd
from sqlalchemy import text
from src.data_pipeline.database import get_engine


def load_order_book_history(symbol: str, start_time: str, end_time: str) -> pd.DataFrame:
    """
    Load historical order book snapshots from PostgreSQL.
    start_time / end_time should be ISO timestamps or 'YYYY-MM-DD HH:MM:SS' strings.

    Returns a DataFrame:
      symbol | snapshot_time | side | price | volume
    """
    query = text("""
        SELECT symbol, snapshot_time, side, price, volume
        FROM order_book_snapshots
        WHERE symbol = :symbol
        AND snapshot_time BETWEEN :start_time AND :end_time
        ORDER BY snapshot_time ASC, price ASC;
    """)

    engine = get_engine()
    df = pd.read_sql(query, engine, params={
        "symbol": symbol,
        "start_time": start_time,
        "end_time": end_time
    })

    return df

def build_heatmap_frames(df: pd.DataFrame):
    """
    Convert snapshot rows into a dict of:
    {
        timestamp1: pivot_table_df,
        timestamp2: pivot_table_df,
        ...
    }

    Each pivot table is price × side → volume.
    """
    frames = {}

    for ts, group in df.groupby("snapshot_time"):
        heat_df = group.pivot_table(
            values="volume",
            index="price",
            columns="side",
            fill_value=0
        ).sort_index(ascending=False)

        frames[ts] = heat_df

    return frames

