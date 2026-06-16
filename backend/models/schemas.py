from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class TradeStatusEnum(str, Enum):
    PENDING = "pending"
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class TradeSideEnum(str, Enum):
    BUY = "buy"
    SELL = "sell"


# ── Trade Schemas ─────────────────────────────────────────────────────────────

class TradeBase(BaseModel):
    symbol: str
    side: str
    quantity: float
    notional_value: float
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


class TradeCreate(TradeBase):
    pass


class TradeResponse(TradeBase):
    id: int
    status: str
    exit_price: Optional[float] = None
    pnl: Optional[float] = None
    pnl_percent: Optional[float] = None
    fee: float = 0.0
    fibonacci_signal: Optional[str] = None
    pattern_signal: Optional[str] = None
    ai_signal: Optional[str] = None
    ai_confidence: Optional[float] = None
    signal_strength: int = 0
    order_id: Optional[str] = None
    ai_analysis: Optional[Dict[str, Any]] = None
    opened_at: datetime
    closed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TradeListResponse(BaseModel):
    trades: List[TradeResponse]
    total: int
    open_count: int
    closed_count: int


# ── Signal Schemas ────────────────────────────────────────────────────────────

class FibonacciLevel(BaseModel):
    level: float
    price: float
    label: str


class FibonacciAnalysis(BaseModel):
    symbol: str
    timeframe: str
    swing_high: float
    swing_low: float
    retracement_levels: List[FibonacciLevel]
    extension_levels: List[FibonacciLevel]
    current_price: float
    nearest_support: Optional[float] = None
    nearest_resistance: Optional[float] = None
    signal: str  # buy / sell / neutral
    zone_score: float  # 0-1


class PatternAnalysis(BaseModel):
    symbol: str
    timeframe: str
    patterns: List[str]
    trend: str
    rsi: float
    macd_signal: str
    ema_signal: str
    bollinger_signal: str
    volume_signal: str
    signal: str  # buy / sell / neutral
    strength: float  # 0-1


class AISignal(BaseModel):
    symbol: str
    recommendation: str  # buy / sell / hold
    confidence: float  # 0-1
    reasoning: str
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    risk_reward_ratio: Optional[float] = None
    model_used: str


class CombinedSignal(BaseModel):
    symbol: str
    timeframe: str
    current_price: float
    overall_signal: str  # buy / sell / neutral
    signal_strength: int  # 0-3 (one point each: fib, pattern, ai)
    fibonacci: Optional[FibonacciAnalysis] = None
    patterns: Optional[PatternAnalysis] = None
    ai: Optional[AISignal] = None
    recommended_entry: Optional[float] = None
    recommended_sl: Optional[float] = None
    recommended_tp: Optional[float] = None
    risk_reward: Optional[float] = None
    trade_executable: bool = False
    reason: str = ""
    timestamp: datetime


# ── Market Data ───────────────────────────────────────────────────────────────

class OHLCV(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class Ticker(BaseModel):
    symbol: str
    price: float
    change_24h: float
    change_pct_24h: float
    volume_24h: float
    high_24h: float
    low_24h: float
    timestamp: datetime


class MarketSummary(BaseModel):
    symbol: str
    ticker: Ticker
    signal: Optional[CombinedSignal] = None


# ── Portfolio / Balance ───────────────────────────────────────────────────────

class Balance(BaseModel):
    total_usdt: float
    free_usdt: float
    locked_usdt: float
    assets: Dict[str, float]
    pnl_today: float
    pnl_today_pct: float
    pnl_total: float
    pnl_total_pct: float


# ── Settings Schemas ──────────────────────────────────────────────────────────

class BotSettingsUpdate(BaseModel):
    bot_enabled: Optional[bool] = None
    max_risk_per_trade: Optional[float] = Field(None, ge=0.005, le=0.05)
    daily_loss_limit: Optional[float] = Field(None, ge=0.01, le=0.20)
    min_ai_confidence: Optional[float] = Field(None, ge=0.5, le=1.0)
    min_signal_strength: Optional[int] = Field(None, ge=1, le=3)
    trading_pairs: Optional[str] = None
    ai_model: Optional[str] = None


class BotSettingsResponse(BaseModel):
    bot_enabled: bool
    max_risk_per_trade: float
    daily_loss_limit: float
    min_ai_confidence: float
    min_signal_strength: int
    trading_pairs: str
    ai_model: str
    read_only_mode: bool
    exchange: str

    class Config:
        from_attributes = True


# ── Analytics ─────────────────────────────────────────────────────────────────

class PerformanceMetrics(BaseModel):
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_pnl: float
    total_pnl: float
    best_trade_pnl: float
    worst_trade_pnl: float
    avg_risk_reward: float
    sharpe_ratio: Optional[float] = None
    max_drawdown: float
    profit_factor: float


# ── WebSocket Messages ────────────────────────────────────────────────────────

class WSMessageType(str, Enum):
    TICKER = "ticker"
    SIGNAL = "signal"
    TRADE = "trade"
    BALANCE = "balance"
    ERROR = "error"
    PING = "ping"


class WSMessage(BaseModel):
    type: str
    data: Any
    timestamp: datetime
