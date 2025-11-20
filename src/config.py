import os
from dotenv import load_dotenv

# Load .env for local development (has no effect on Render unless you add one there)
load_dotenv()

# --- Database configuration ---

# In production (Render), DATABASE_URL will be provided via env var.
# In local dev, if it's not set, we fall back to your local Postgres.
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Local development fallback WITHOUT password
    # The password will come from your system environment (.env or shell)
    # Example structure (change to match your DB):
    USER = os.getenv("DB_USER", "")
    PASS = os.getenv("DB_PASS", "")
    HOST = os.getenv("DB_HOST", "")
    NAME = os.getenv("DB_NAME", "")
    PORT = os.getenv("DB_PORT", "")

    DATABASE_URL = f"postgresql://{USER}:{PASS}@{HOST}:{PORT}/{NAME}"

# --- App configuration ---

# Default symbols to play with
DEFAULT_SYMBOLS = ["BTCUSDT", "ETHUSDT", "AAPL", "SPY"]

# Binance base URL
BINANCE_BASE_URL = "https://api.binance.com"

