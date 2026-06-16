"""
Trades Router
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List, Optional
from models.database import get_db, Trade, TradeStatus
from models.schemas import TradeResponse, TradeListResponse
from loguru import logger

router = APIRouter(prefix="/trades", tags=["trades"])


@router.get("", response_model=TradeListResponse)
async def get_trades(
    status: Optional[str] = Query(None),
    symbol: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db)
):
    query = select(Trade).order_by(desc(Trade.opened_at))
    count_query = select(func.count(Trade.id))

    if status:
        query = query.where(Trade.status == status)
        count_query = count_query.where(Trade.status == status)
    if symbol:
        query = query.where(Trade.symbol == symbol)
        count_query = count_query.where(Trade.symbol == symbol)

    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    trades = result.scalars().all()

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    open_result = await db.execute(select(func.count(Trade.id)).where(Trade.status == TradeStatus.OPEN))
    open_count = open_result.scalar()

    closed_result = await db.execute(select(func.count(Trade.id)).where(Trade.status == TradeStatus.CLOSED))
    closed_count = closed_result.scalar()

    return TradeListResponse(
        trades=[TradeResponse.model_validate(t) for t in trades],
        total=total or 0,
        open_count=open_count or 0,
        closed_count=closed_count or 0
    )


@router.get("/{trade_id}", response_model=TradeResponse)
async def get_trade(trade_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Trade).where(Trade.id == trade_id))
    trade = result.scalar_one_or_none()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return TradeResponse.model_validate(trade)


@router.post("/{trade_id}/close")
async def close_trade(trade_id: int, db: AsyncSession = Depends(get_db)):
    """Manually close an open trade."""
    result = await db.execute(select(Trade).where(Trade.id == trade_id))
    trade = result.scalar_one_or_none()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    if trade.status != TradeStatus.OPEN:
        raise HTTPException(status_code=400, detail=f"Trade is not open (status: {trade.status})")

    from services.exchange import get_exchange
    from datetime import datetime, timezone

    exchange = await get_exchange()
    ticker = await exchange.get_ticker(trade.symbol)
    current_price = ticker.price if ticker else trade.entry_price

    # Cancel SL/TP orders
    if trade.sl_order_id:
        await exchange.cancel_order(trade.sl_order_id, trade.symbol)
    if trade.tp_order_id:
        await exchange.cancel_order(trade.tp_order_id, trade.symbol)

    # Place market close order
    exit_side = "sell" if trade.side == "buy" else "buy"
    await exchange.place_market_order(trade.symbol, exit_side, trade.quantity)

    # Update trade record
    trade.status = TradeStatus.CLOSED
    trade.exit_price = current_price
    trade.closed_at = datetime.now(timezone.utc)
    if trade.entry_price and current_price:
        if trade.side == "buy":
            trade.pnl = (current_price - trade.entry_price) * trade.quantity - trade.fee
        else:
            trade.pnl = (trade.entry_price - current_price) * trade.quantity - trade.fee
        trade.pnl_percent = trade.pnl / trade.notional_value if trade.notional_value else 0

    await db.commit()
    return {"message": "Trade closed", "exit_price": current_price, "pnl": trade.pnl}
