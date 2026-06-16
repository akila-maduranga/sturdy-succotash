"""
Strategy Engine - Core Trading Logic
Combines Fibonacci, Pattern, and AI signals to make trade decisions.
"""
import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, List
from models.schemas import CombinedSignal, FibonacciAnalysis, PatternAnalysis, AISignal
from services.fibonacci import multi_timeframe_fibonacci, get_fibonacci_consensus
from services.patterns import analyze_patterns
from services.ai_analysis import get_ai_analysis
from services.exchange import ExchangeService
from services.risk_manager import RiskManager
from config import settings
from loguru import logger


async def analyze_symbol(
    symbol: str,
    exchange: ExchangeService,
    risk_manager: RiskManager
) -> Optional[CombinedSignal]:
    """
    Full analysis pipeline for one symbol.
    Returns CombinedSignal with trade decision.
    """
    logger.info(f"[Strategy] Starting analysis for {symbol}")

    # 1. Get market data
    ticker = await exchange.get_ticker(symbol)
    if not ticker:
        logger.warning(f"[Strategy] No ticker for {symbol}")
        return None

    current_price = ticker.price
    ticker_data = {
        "change_pct_24h": ticker.change_pct_24h,
        "high_24h": ticker.high_24h,
        "low_24h": ticker.low_24h,
        "volume_24h": ticker.volume_24h,
    }

    # 2. Get OHLCV for multiple timeframes
    timeframes = settings.fibonacci_timeframes_list
    all_dfs = await exchange.get_multi_timeframe_ohlcv(
        symbol, timeframes, limit=settings.candle_limit
    )

    if not all_dfs:
        logger.warning(f"[Strategy] No OHLCV data for {symbol}")
        return None

    # 3. Fibonacci Analysis (multi-timeframe)
    fib_analyses: Dict[str, FibonacciAnalysis] = {}
    fib_signal_overall = "neutral"
    fib_score = 0.0
    primary_fib = None

    try:
        fib_analyses = multi_timeframe_fibonacci(all_dfs, symbol)
        if fib_analyses:
            fib_signal_overall, fib_score = get_fibonacci_consensus(fib_analyses)
            # Use 1h as primary for display
            primary_fib = fib_analyses.get("1h") or list(fib_analyses.values())[0]
        logger.info(f"[Strategy] {symbol} Fibonacci consensus: {fib_signal_overall} ({fib_score:.2f})")
    except Exception as e:
        logger.error(f"[Strategy] Fibonacci error for {symbol}: {e}")

    # 4. Pattern Analysis (primary timeframe)
    primary_tf = settings.pattern_timeframe
    pattern_result: Optional[PatternAnalysis] = None
    pattern_signal = "neutral"

    try:
        if primary_tf in all_dfs:
            pattern_result = analyze_patterns(all_dfs[primary_tf], symbol, primary_tf)
            pattern_signal = pattern_result.signal
        logger.info(f"[Strategy] {symbol} Pattern signal: {pattern_signal}")
    except Exception as e:
        logger.error(f"[Strategy] Pattern error for {symbol}: {e}")

    # 5. AI Analysis
    ai_result: Optional[AISignal] = None
    ai_signal = "hold"

    try:
        ai_result = await get_ai_analysis(
            symbol, current_price, primary_fib, pattern_result, ticker_data
        )
        if ai_result:
            ai_signal = ai_result.recommendation
    except Exception as e:
        logger.error(f"[Strategy] AI error for {symbol}: {e}")

    # 6. Combine Signals
    signal_strength = 0
    buy_votes = 0
    sell_votes = 0

    if fib_signal_overall == "buy":
        buy_votes += 1
        signal_strength += 1
    elif fib_signal_overall == "sell":
        sell_votes += 1
        signal_strength += 1

    if pattern_signal == "buy":
        buy_votes += 1
        signal_strength += 1
    elif pattern_signal == "sell":
        sell_votes += 1
        signal_strength += 1

    if ai_signal == "buy":
        buy_votes += 1
        signal_strength += 1
    elif ai_signal == "sell":
        sell_votes += 1
        signal_strength += 1

    if buy_votes > sell_votes:
        overall_signal = "buy"
    elif sell_votes > buy_votes:
        overall_signal = "sell"
    else:
        overall_signal = "neutral"

    # 7. Determine entry/SL/TP
    recommended_entry = None
    recommended_sl = None
    recommended_tp = None
    risk_reward = None
    trade_executable = False
    reason = "Insufficient signal alignment"

    if overall_signal in ("buy", "sell") and signal_strength >= settings.min_signal_strength:
        # Use AI levels if available and confident
        if ai_result and ai_result.confidence >= settings.min_ai_confidence:
            if ai_result.entry_price and ai_result.stop_loss and ai_result.take_profit:
                recommended_entry = ai_result.entry_price
                recommended_sl = ai_result.stop_loss
                recommended_tp = ai_result.take_profit
                risk_reward = ai_result.risk_reward_ratio
            else:
                # Calculate from ATR
                if primary_tf in all_dfs and 'atr' in all_dfs[primary_tf].columns:
                    atr = float(all_dfs[primary_tf]['atr'].iloc[-1])
                    recommended_entry = current_price
                    if overall_signal == "buy":
                        recommended_sl = risk_manager.calculate_stop_loss(current_price, atr, "buy")
                        recommended_tp = risk_manager.calculate_take_profit(current_price, recommended_sl, "buy")
                    else:
                        recommended_sl = risk_manager.calculate_stop_loss(current_price, atr, "sell")
                        recommended_tp = risk_manager.calculate_take_profit(current_price, recommended_sl, "sell")

                    if recommended_sl:
                        risk = abs(recommended_entry - recommended_sl)
                        reward = abs(recommended_tp - recommended_entry) if recommended_tp else 0
                        risk_reward = reward / risk if risk > 0 else 0

        # Check if trade is executable
        if recommended_entry and recommended_sl and recommended_tp:
            qty, notional, err = risk_manager.calculate_position_size(
                recommended_entry, recommended_sl, symbol
            )
            if err:
                reason = f"Position sizing: {err}"
            else:
                valid, val_msg = risk_manager.validate_trade(
                    symbol, recommended_entry, recommended_sl, recommended_tp, qty
                )
                if valid:
                    trade_executable = not settings.read_only and settings.bot_enabled
                    reason = f"Signal strength {signal_strength}/3, AI confidence {ai_result.confidence:.0%}" if ai_result else f"Signal strength {signal_strength}/3"
                else:
                    reason = f"Validation failed: {val_msg}"
        else:
            reason = f"Signal={overall_signal} strength={signal_strength} but missing SL/TP levels"
    else:
        if overall_signal == "neutral":
            reason = "Signals conflict or insufficient"
        else:
            reason = f"Signal {overall_signal} strength {signal_strength} below minimum {settings.min_signal_strength}"

    if settings.read_only:
        reason = f"[READ-ONLY] {reason}"

    combined = CombinedSignal(
        symbol=symbol,
        timeframe=primary_tf,
        current_price=current_price,
        overall_signal=overall_signal,
        signal_strength=signal_strength,
        fibonacci=primary_fib,
        patterns=pattern_result,
        ai=ai_result,
        recommended_entry=recommended_entry,
        recommended_sl=recommended_sl,
        recommended_tp=recommended_tp,
        risk_reward=risk_reward,
        trade_executable=trade_executable,
        reason=reason,
        timestamp=datetime.now(timezone.utc)
    )

    logger.info(
        f"[Strategy] {symbol} → {overall_signal.upper()} "
        f"(strength={signal_strength}/3, executable={trade_executable})"
    )

    return combined


async def run_strategy_cycle(
    exchange: ExchangeService,
    risk_manager: RiskManager
) -> Dict[str, Optional[CombinedSignal]]:
    """Run full strategy cycle for all configured trading pairs."""
    symbols = settings.trading_pairs_list
    tasks = [analyze_symbol(sym, exchange, risk_manager) for sym in symbols]
    results_list = await asyncio.gather(*tasks, return_exceptions=True)

    results = {}
    for sym, result in zip(symbols, results_list):
        if isinstance(result, Exception):
            logger.error(f"[Strategy] Error analyzing {sym}: {result}")
            results[sym] = None
        else:
            results[sym] = result

    return results
