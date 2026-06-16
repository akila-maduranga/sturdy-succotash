"""
Analytics Router
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from models.database import get_db, Trade, TradeStatus, MarketSignal
from models.schemas import PerformanceMetrics, CombinedSignal
from config import settings
from typing import List, Optional
import json

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/performance", response_model=PerformanceMetrics)
async def get_performance(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Trade).where(Trade.status == TradeStatus.CLOSED))
    closed_trades = result.scalars().all()

    total = len(closed_trades)
    if total == 0:
        return PerformanceMetrics(
            total_trades=0, winning_trades=0, losing_trades=0,
            win_rate=0.0, avg_pnl=0.0, total_pnl=0.0,
            best_trade_pnl=0.0, worst_trade_pnl=0.0,
            avg_risk_reward=0.0, max_drawdown=0.0, profit_factor=0.0
        )

    pnls = [t.pnl or 0.0 for t in closed_trades]
    winning = [p for p in pnls if p > 0]
    losing = [p for p in pnls if p < 0]

    total_profit = sum(winning)
    total_loss = abs(sum(losing))

    # Max drawdown
    running_balance = settings.initial_balance
    peak = running_balance
    max_dd = 0.0
    for pnl in pnls:
        running_balance += pnl
        if running_balance > peak:
            peak = running_balance
        drawdown = (peak - running_balance) / peak if peak > 0 else 0
        max_dd = max(max_dd, drawdown)

    rr_ratios = [t.pnl / abs(t.entry_price - t.stop_loss) / t.quantity
                 for t in closed_trades
                 if t.pnl and t.entry_price and t.stop_loss and t.quantity
                 and abs(t.entry_price - t.stop_loss) > 0]

    return PerformanceMetrics(
        total_trades=total,
        winning_trades=len(winning),
        losing_trades=len(losing),
        win_rate=len(winning) / total if total > 0 else 0.0,
        avg_pnl=sum(pnls) / total if total > 0 else 0.0,
        total_pnl=sum(pnls),
        best_trade_pnl=max(pnls) if pnls else 0.0,
        worst_trade_pnl=min(pnls) if pnls else 0.0,
        avg_risk_reward=sum(rr_ratios) / len(rr_ratios) if rr_ratios else 0.0,
        max_drawdown=max_dd,
        profit_factor=total_profit / total_loss if total_loss > 0 else 0.0
    )


@router.get("/signals")
async def get_latest_signals(db: AsyncSession = Depends(get_db)):
    """Get latest signal for each trading pair."""
    signals = []
    for symbol in settings.trading_pairs_list:
        result = await db.execute(
            select(MarketSignal)
            .where(MarketSignal.symbol == symbol)
            .order_by(MarketSignal.created_at.desc())
            .limit(1)
        )
        sig = result.scalar_one_or_none()
        if sig:
            signals.append({
                "symbol": symbol,
                "signal": sig.overall_signal,
                "strength": sig.signal_strength,
                "rsi": sig.rsi,
                "trend": sig.trend,
                "patterns": sig.patterns_detected,
                "ai_recommendation": sig.ai_recommendation,
                "ai_confidence": sig.ai_confidence,
                "ai_reasoning": sig.ai_reasoning,
                "fib_signal": sig.fib_signal,
                "current_price": sig.current_price,
                "timestamp": sig.created_at.isoformat() if sig.created_at else None
            })
        else:
            signals.append({"symbol": symbol, "signal": "neutral", "strength": 0})
    has_key = bool(settings.openrouter_api_key and settings.openrouter_api_key.strip() and "your_openrouter_api_key" not in settings.openrouter_api_key)
    return {"signals": signals, "has_openrouter_key": has_key}


@router.get("/pnl-history")
async def get_pnl_history(db: AsyncSession = Depends(get_db)):
    """Get P&L over time for chart."""
    result = await db.execute(
        select(Trade)
        .where(Trade.status == TradeStatus.CLOSED)
        .order_by(Trade.closed_at)
    )
    trades = result.scalars().all()

    cumulative = settings.initial_balance
    history = [{"date": "Start", "balance": cumulative, "pnl": 0.0}]

    for t in trades:
        pnl = t.pnl or 0.0
        cumulative += pnl
        history.append({
            "date": t.closed_at.strftime("%Y-%m-%d %H:%M") if t.closed_at else "N/A",
            "balance": round(cumulative, 4),
            "pnl": round(pnl, 4),
            "symbol": t.symbol
        })

    return {"history": history, "current_balance": cumulative}
