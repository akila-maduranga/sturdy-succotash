from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
import os


class Settings(BaseSettings):
    # Exchange
    exchange: str = "binance"
    exchange_api_key: str = ""
    exchange_api_secret: str = ""
    testnet: bool = False
    read_only: bool = True

    # OpenRouter AI
    openrouter_api_key: str = ""
    ai_model: str = "google/gemini-flash-1.5"

    # Trading
    trading_pairs: str = "BTC/USDT,ETH/USDT,SOL/USDT"
    initial_balance: float = 10.0
    max_risk_per_trade: float = 0.02      # 2% of balance
    daily_loss_limit: float = 0.05         # 5% max daily loss
    min_ai_confidence: float = 0.70
    min_signal_strength: int = 2
    bot_enabled: bool = False

    # Analysis
    fibonacci_timeframes: str = "1h,4h,1d"
    pattern_timeframe: str = "1h"
    candle_limit: int = 200

    # Database
    database_url: str = "postgresql+asyncpg://trader:trader_secret_2024@db:5432/tradingbot"

    # Redis / Celery
    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/1"

    # App
    secret_key: str = "change_this_secret_key"
    debug: bool = False
    log_level: str = "INFO"

    @property
    def trading_pairs_list(self) -> List[str]:
        return [p.strip() for p in self.trading_pairs.split(",")]

    @property
    def fibonacci_timeframes_list(self) -> List[str]:
        return [t.strip() for t in self.fibonacci_timeframes.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
