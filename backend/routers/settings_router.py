"""
Settings Router
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.database import get_db, BotSettings
from models.schemas import BotSettingsUpdate, BotSettingsResponse
from config import settings
from datetime import datetime, timezone

router = APIRouter(prefix="/settings", tags=["settings"])


async def get_or_create_settings(db: AsyncSession) -> BotSettings:
    result = await db.execute(select(BotSettings).limit(1))
    bot_settings = result.scalar_one_or_none()
    if not bot_settings:
        bot_settings = BotSettings(
            bot_enabled=settings.bot_enabled,
            max_risk_per_trade=settings.max_risk_per_trade,
            daily_loss_limit=settings.daily_loss_limit,
            min_ai_confidence=settings.min_ai_confidence,
            min_signal_strength=settings.min_signal_strength,
            trading_pairs=settings.trading_pairs,
            ai_model=settings.ai_model
        )
        db.add(bot_settings)
        await db.commit()
        await db.refresh(bot_settings)
    return bot_settings


@router.get("", response_model=BotSettingsResponse)
async def get_settings(db: AsyncSession = Depends(get_db)):
    bot_settings = await get_or_create_settings(db)
    return BotSettingsResponse(
        bot_enabled=bot_settings.bot_enabled,
        max_risk_per_trade=bot_settings.max_risk_per_trade,
        daily_loss_limit=bot_settings.daily_loss_limit,
        min_ai_confidence=bot_settings.min_ai_confidence,
        min_signal_strength=bot_settings.min_signal_strength,
        trading_pairs=bot_settings.trading_pairs,
        ai_model=bot_settings.ai_model,
        read_only_mode=settings.read_only,
        exchange=settings.exchange
    )


@router.patch("", response_model=BotSettingsResponse)
async def update_settings(
    update: BotSettingsUpdate,
    db: AsyncSession = Depends(get_db)
):
    bot_settings = await get_or_create_settings(db)

    if update.bot_enabled is not None:
        if update.bot_enabled and settings.read_only:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=400,
                detail="Cannot enable bot in read-only mode. Add API secret first."
            )
        bot_settings.bot_enabled = update.bot_enabled
        settings.bot_enabled = update.bot_enabled

    if update.max_risk_per_trade is not None:
        bot_settings.max_risk_per_trade = update.max_risk_per_trade
    if update.daily_loss_limit is not None:
        bot_settings.daily_loss_limit = update.daily_loss_limit
    if update.min_ai_confidence is not None:
        bot_settings.min_ai_confidence = update.min_ai_confidence
    if update.min_signal_strength is not None:
        bot_settings.min_signal_strength = update.min_signal_strength
    if update.trading_pairs is not None:
        bot_settings.trading_pairs = update.trading_pairs
    if update.ai_model is not None:
        bot_settings.ai_model = update.ai_model

    bot_settings.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(bot_settings)

    return BotSettingsResponse(
        bot_enabled=bot_settings.bot_enabled,
        max_risk_per_trade=bot_settings.max_risk_per_trade,
        daily_loss_limit=bot_settings.daily_loss_limit,
        min_ai_confidence=bot_settings.min_ai_confidence,
        min_signal_strength=bot_settings.min_signal_strength,
        trading_pairs=bot_settings.trading_pairs,
        ai_model=bot_settings.ai_model,
        read_only_mode=settings.read_only,
        exchange=settings.exchange
    )


@router.post("/trigger-analysis")
async def trigger_analysis():
    """Manually trigger a strategy analysis cycle."""
    from workers.tasks import run_strategy_task
    task = run_strategy_task.delay()
    return {"message": "Analysis triggered", "task_id": task.id}
