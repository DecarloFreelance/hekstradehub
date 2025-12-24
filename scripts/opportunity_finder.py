import asyncio
import logging
import aiohttp
import pandas as pd
import sys
import os
# Add project root to sys.path for module resolution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.scoring import score_asset

# ========================= LOGGING SETUP =============================== #

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger("OpportunityFinder")


# ========================= ASYNC DATA FETCH ============================ #

async def fetch_ohlc(session, symbol, limit=300):
    """
    Fetch OHLC data for a given symbol asynchronously.
    """
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1h&limit={limit}"

    try:
        async with session.get(url, timeout=10) as resp:
            if resp.status != 200:
                logger.error(f"{symbol} | HTTP {resp.status}")
                return None

            data = await resp.json()

            df = pd.DataFrame(data, columns=[
                "open_time", "open", "high", "low", "close", "volume",
                "close_time", "qav", "num_trades", "tbbav", "tbqav", "ignore"
            ])

            df["open"] = df["open"].astype(float)
            df["high"] = df["high"].astype(float)
            df["low"] = df["low"].astype(float)
            df["close"] = df["close"].astype(float)
            df["volume"] = df["volume"].astype(float)

            return df

    except asyncio.TimeoutError:
        logger.error(f"{symbol} | Request timed out")
        return None
    except Exception as e:
        logger.exception(f"{symbol} | Unexpected error: {e}")
        return None


# ========================= PROCESS SYMBOL ============================== #

async def process_symbol(session, symbol):
    """
    Fetch data + calculate score for a symbol.
    """
    df = await fetch_ohlc(session, symbol)

    if df is None or df.shape[0] < 120:
        logger.warning(f"{symbol} | Not enough data or fetch failed")
        return None

    try:
        scores = score_asset(df)
        return symbol, scores
    except Exception as e:
        logger.exception(f"{symbol} | Scoring failed: {e}")
        return None


# ========================= MAIN ENTRYPOINT ============================= #

async def main():
    """
    Main async orchestrator: fetch + score all pairs.
    """

    symbols = [
        "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT",
        "XRPUSDT", "ADAUSDT", "DOGEUSDT"
    ]

    logger.info("Starting opportunity finder…")

    async with aiohttp.ClientSession() as session:
        tasks = [process_symbol(session, sym) for sym in symbols]
        results = await asyncio.gather(*tasks)

    signals = [r for r in results if r is not None]

    logger.info("---------- FINAL RESULTS ----------")

    for sym, scores in signals:
        logger.info(f"{sym} → {scores['signal']} (L:{scores['long_score']} / S:{scores['short_score']})")

    return signals


# ========================= RUN SCRIPT ================================== #

if __name__ == "__main__":
    asyncio.run(main())
