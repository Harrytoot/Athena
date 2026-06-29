import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from app.providers.stock.mock_provider import MOCK_STOCKS

logger = logging.getLogger(__name__)

UNIVERSE_SYMBOLS: list[dict] = [
    {"symbol": s[0], "name": s[1], "market": s[2]}
    for s in MOCK_STOCKS
]


class UniverseLoader:

    def __init__(self):
        self._symbols: list[dict] = []
        self._loaded = False

    async def load(self) -> list[dict]:
        if self._loaded:
            return self._symbols

        symbols = await self._try_akshare()
        if not symbols:
            logger.info("AkShare unavailable, loading built-in fallback universe")
            symbols = UNIVERSE_SYMBOLS

        self._symbols = symbols
        self._loaded = True
        logger.info("Universe loaded: %d symbols", len(self._symbols))
        return self._symbols

    async def _try_akshare(self) -> list[dict]:
        try:
            import akshare as ak

            loop = asyncio.get_running_loop()
            with ThreadPoolExecutor(max_workers=1) as pool:
                df = await loop.run_in_executor(pool, ak.stock_info_a_code_name)
            if df is None or df.empty:
                return []

            symbols = []
            for _, row in df.head(200).iterrows():
                code = str(row.get("code", "")).strip()
                name = str(row.get("name", "")).strip()
                if len(code) == 6 and code.isdigit():
                    market = "SH" if code.startswith(("6", "5", "9")) else "SZ"
                    symbols.append({"symbol": code, "name": name, "market": market})
            return symbols
        except Exception as e:
            logger.warning("Failed to load universe via akshare: %s", e)
            return []

    def get_symbols(self) -> list[str]:
        return [s["symbol"] for s in self._symbols]

    def get_registry(self) -> dict[str, dict]:
        return {s["symbol"]: s for s in self._symbols}


_universe_loader: Optional[UniverseLoader] = None


def get_universe_loader() -> UniverseLoader:
    global _universe_loader
    if _universe_loader is None:
        _universe_loader = UniverseLoader()
    return _universe_loader
