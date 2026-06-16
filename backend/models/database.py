from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Float, Boolean, DateTime, Integer, Text, JSON, ForeignKey, Enum
from datetime import datetime, timezone
from typing import Optional, List
import enum
from config import settings


engine = create_async_engine(settings.database_url, echo=settings.debug)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class TradeStatus(str, enum.Enum):
    PENDING = "pending"
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class TradeSide(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"


class SignalStrength(str, enum.Enum):
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    NEUTRAL = "neutral"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    symbol: Mapped[str] = mapped_column(String(20), index=True)
    side: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(20), default=TradeStatus.PENDING)

    entry_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    exit_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    quantity: Mapped[float] = mapped_column(Float)
    notional_value: Mapped[float] = mapped_column(Float)

    stop_loss: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    take_profit: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    pnl: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pnl_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fee: Mapped[float] = mapped_column(Float, default=0.0)

    # Signal data
    fibonacci_signal: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    pattern_signal: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ai_signal: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ai_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    signal_strength: Mapped[int] = mapped_column(Integer, default=0)

    # Exchange order IDs
    order_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    sl_order_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tp_order_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # AI analysis snapshot
    ai_analysis: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    opened_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc),
                                                  onupdate=lambda: datetime.now(timezone.utc))


class BotSettings(Base):
    __tablename__ = "bot_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bot_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    max_risk_per_trade: Mapped[float] = mapped_column(Float, default=0.02)
    daily_loss_limit: Mapped[float] = mapped_column(Float, default=0.05)
    min_ai_confidence: Mapped[float] = mapped_column(Float, default=0.70)
    min_signal_strength: Mapped[int] = mapped_column(Integer, default=2)
    trading_pairs: Mapped[str] = mapped_column(String(200), default="BTC/USDT,ETH/USDT,SOL/USDT")
    ai_model: Mapped[str] = mapped_column(String(100), default="google/gemini-flash-1.5")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class MarketSignal(Base):
    __tablename__ = "market_signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    symbol: Mapped[str] = mapped_column(String(20), index=True)
    timeframe: Mapped[str] = mapped_column(String(10))

    # Fibonacci
    fib_retracement_levels: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    fib_extension_levels: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    fib_signal: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    fib_zone: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Patterns
    patterns_detected: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    trend: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    rsi: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    macd_signal: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    ema_signal: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # AI
    ai_recommendation: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    ai_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ai_reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_entry: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ai_stop_loss: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ai_take_profit: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Combined
    overall_signal: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    signal_strength: Mapped[int] = mapped_column(Integer, default=0)
    current_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
