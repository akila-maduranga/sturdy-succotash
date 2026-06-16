"""
Celery Background Tasks
"""
import asyncio
import json
from datetime import datetime, timezone
from workers.celery_app import celery_app
from config import settings
from loguru import logger


def run_async(coro):
    """Run async coroutine in Celery sync context."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="workers.tasks.run_strategy_task", bind=True, max_retries=3)
def run_strategy_task(self):
    """Run full strategy cycle for all pairs."""
    try:
        async def _run():
            from services.exchange import get_exchange
            from services.strategy_engine import run_strategy_cycle
            from services.risk_manager import get_risk_manager
            from models.database import AsyncSessionLocal, MarketSignal
            from sqlalchemy import insert

            exchange = await get_exchange()
            balance = await exchange.get_balance()
            balance_val = balance.total_usdt if balance else settings.initial_balance
            risk_mgr = get_risk_manager(balance_val)

            signals = await run_strategy_cycle(exchange, risk_mgr)

            # Save signals to database
            async with AsyncSessionLocal() as session:
                for symbol, signal in signals.items():
                    if signal is None:
                        continue
                    db_signal = MarketSignal(
                        symbol=symbol,
                        timeframe=signal.timeframe,
                        fib_signal=signal.fibonacci.signal if signal.fibonacci else None,
                        fib_zone=signal.fibonacci.zone_score if signal.fibonacci else None,
                        patterns_detected=signal.patterns.patterns if signal.patterns else [],
                        trend=signal.patterns.trend if signal.patterns else None,
                        rsi=signal.patterns.rsi if signal.patterns else None,
                        macd_signal=signal.patterns.macd_signal if signal.patterns else None,
                        ai_recommendation=signal.ai.recommendation if signal.ai else None,
                        ai_confidence=signal.ai.confidence if signal.ai else None,
                        ai_reasoning=signal.ai.reasoning if signal.ai else None,
                        ai_entry=signal.ai.entry_price if signal.ai else None,
                        ai_stop_loss=signal.ai.stop_loss if signal.ai else None,
                        ai_take_profit=signal.ai.take_profit if signal.ai else None,
                        overall_signal=signal.overall_signal,
                        signal_strength=signal.signal_strength,
                        current_price=signal.current_price,
                    )
                    session.add(db_signal)
                await session.commit()

            logger.info(f"[Task] Strategy cycle complete. Processed {len(signals)} symbols.")
            return {sym: s.overall_signal if s else "error" for sym, s in signals.items()}

        return run_async(_run())

    except Exception as e:
        logger.error(f"[Task] run_strategy_task error: {e}")
        raise self.retry(exc=e, countdown=60)


@celery_app.task(name="workers.tasks.update_prices_task")
def update_prices_task():
    """Fetch current prices for all pairs and cache in Redis."""
    try:
        async def _run():
            import redis.asyncio as aioredis
            from services.exchange import get_exchange

            exchange = await get_exchange()
            r = aioredis.from_url(settings.redis_url)

            prices = {}
            for symbol in settings.trading_pairs_list:
                ticker = await exchange.get_ticker(symbol)
                if ticker:
                    prices[symbol] = {
                        "price": ticker.price,
                        "change_pct_24h": ticker.change_pct_24h,
                        "volume_24h": ticker.volume_24h,
                        "high_24h": ticker.high_24h,
                        "low_24h": ticker.low_24h,
                        "timestamp": ticker.timestamp.isoformat()
                    }
                    await r.setex(f"price:{symbol}", 60, json.dumps(prices[symbol]))

            await r.aclose()
            return prices

        return run_async(_run())
    except Exception as e:
        logger.error(f"[Task] update_prices_task error: {e}")


@celery_app.task(name="workers.tasks.check_open_trades_task")
def check_open_trades_task():
    """Check status of open trades and update P&L."""
    try:
        async def _run():
            from services.exchange import get_exchange
            from models.database import AsyncSessionLocal, Trade, TradeStatus
            from sqlalchemy import select
            from datetime import datetime, timezone

            exchange = await get_exchange()

            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(Trade).where(Trade.status == TradeStatus.OPEN)
                )
                open_trades = result.scalars().all()

                for trade in open_trades:
                    ticker = await exchange.get_ticker(trade.symbol)
                    if not ticker:
                        continue

                    current_price = ticker.price
                    if trade.entry_price:
                        if trade.side == "buy":
                            pnl = (current_price - trade.entry_price) * trade.quantity
                        else:
                            pnl = (trade.entry_price - current_price) * trade.quantity
                        pnl -= trade.fee
                        pnl_pct = pnl / trade.notional_value if trade.notional_value > 0 else 0
                        trade.pnl = pnl
                        trade.pnl_percent = pnl_pct

                await session.commit()
                logger.info(f"[Task] Checked {len(open_trades)} open trades")

        return run_async(_run())
    except Exception as e:
        logger.error(f"[Task] check_open_trades_task error: {e}")


@celery_app.task(name="workers.tasks.reset_daily_limits_task")
def reset_daily_limits_task():
    """Reset daily P&L counters."""
    from services.risk_manager import get_risk_manager
    rm = get_risk_manager()
    rm.reset_daily()
    logger.info("[Task] Daily limits reset")
