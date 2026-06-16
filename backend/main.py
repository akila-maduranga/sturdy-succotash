"""
FastAPI Main Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger
import sys

from config import settings
from models.database import init_db
from routers import trades, analytics, settings_router, websocket


# Configure logging
logger.remove()
logger.add(sys.stdout, level=settings.log_level, colorize=True,
           format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | {message}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Trading Bot API starting...")
    await init_db()
    logger.info("✅ Database initialized")

    try:
        from services.exchange import get_exchange
        exchange = await get_exchange()
        logger.info(f"✅ Exchange connected: {settings.exchange}")
    except Exception as e:
        logger.warning(f"⚠️ Exchange connection failed (will retry): {e}")

    logger.info(f"📊 Trading pairs: {settings.trading_pairs}")
    logger.info(f"🔒 Read-only mode: {settings.read_only}")
    logger.info(f"🤖 Bot enabled: {settings.bot_enabled}")

    yield

    # Shutdown
    logger.info("🛑 Trading Bot API shutting down...")
    try:
        from services.exchange import _exchange_service
        if _exchange_service:
            await _exchange_service.close()
    except Exception:
        pass


app = FastAPI(
    title="AutoTrading Bot API",
    description="AI-powered cryptocurrency trading bot with Fibonacci analysis",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(trades.router)
app.include_router(analytics.router)
app.include_router(settings_router.router)
app.include_router(websocket.router)


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "exchange": settings.exchange,
        "read_only": settings.read_only,
        "bot_enabled": settings.bot_enabled,
        "trading_pairs": settings.trading_pairs_list
    }


@app.get("/market/prices")
async def get_prices():
    """Get current prices for all pairs."""
    from services.exchange import get_exchange
    exchange = await get_exchange()
    prices = {}
    for symbol in settings.trading_pairs_list:
        ticker = await exchange.get_ticker(symbol)
        if ticker:
            prices[symbol] = {
                "price": ticker.price,
                "change_pct_24h": ticker.change_pct_24h,
                "high_24h": ticker.high_24h,
                "low_24h": ticker.low_24h,
                "volume_24h": ticker.volume_24h,
            }
    return {"prices": prices}


@app.get("/market/ohlcv/{symbol}")
async def get_ohlcv(symbol: str, timeframe: str = "1h", limit: int = 100):
    """Get OHLCV candlestick data."""
    from services.exchange import get_exchange
    symbol = symbol.replace("-", "/").upper()
    exchange = await get_exchange()
    df = await exchange.get_ohlcv(symbol, timeframe, limit)
    if df is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="No data found")

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "candles": [
            {
                "time": int(idx.timestamp()),
                "open": row["open"],
                "high": row["high"],
                "low": row["low"],
                "close": row["close"],
                "volume": row["volume"]
            }
            for idx, row in df.iterrows()
        ]
    }


@app.get("/market/analyze/{symbol}")
async def analyze_symbol(symbol: str):
    """Run full analysis on a symbol on demand."""
    from services.exchange import get_exchange
    from services.strategy_engine import analyze_symbol as _analyze
    from services.risk_manager import get_risk_manager

    symbol = symbol.replace("-", "/").upper()
    exchange = await get_exchange()
    balance = await exchange.get_balance()
    balance_val = balance.total_usdt if balance else settings.initial_balance
    risk_mgr = get_risk_manager(balance_val)

    signal = await _analyze(symbol, exchange, risk_mgr)
    if not signal:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="Analysis failed")

    return signal


@app.get("/balance")
async def get_balance():
    """Get current account balance."""
    from services.exchange import get_exchange
    exchange = await get_exchange()
    balance = await exchange.get_balance()
    if not balance:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="Could not fetch balance")
    return balance
