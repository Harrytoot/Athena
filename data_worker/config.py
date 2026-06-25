import os

REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

REDIS_NAMESPACE = "athena"
REDIS_KEY_MARKET_OVERVIEW = f"{REDIS_NAMESPACE}:market:overview"
REDIS_KEY_HOT_SECTORS = f"{REDIS_NAMESPACE}:market:hot_sectors"
REDIS_KEY_STOCK_DETAIL = f"{REDIS_NAMESPACE}:stock:detail"
REDIS_KEY_STOCK_SEARCH_INDEX = f"{REDIS_NAMESPACE}:stock:search_index"

RETRY_MAX_ATTEMPTS = 3
RETRY_BACKOFF_FACTOR = 2
