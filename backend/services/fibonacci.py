"""
Fibonacci Analysis Service
Calculates Fibonacci retracement and extension levels,
detects swing highs/lows, and scores entry zones.
"""
import numpy as np
import pandas as pd
from typing import List, Tuple, Optional, Dict
from models.schemas import FibonacciAnalysis, FibonacciLevel
from loguru import logger


# Standard Fibonacci ratios
FIB_RETRACEMENT_RATIOS = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]
FIB_EXTENSION_RATIOS = [1.272, 1.414, 1.618, 2.0, 2.618]
ZONE_TOLERANCE = 0.005  # 0.5% tolerance around each Fibonacci level


def detect_swing_points(
    highs: np.ndarray,
    lows: np.ndarray,
    lookback: int = 5
) -> Tuple[List[int], List[int]]:
    """
    Detect swing highs and swing lows using a rolling window approach.
    A swing high is a candle whose high is the highest in the lookback window.
    A swing low is a candle whose low is the lowest in the lookback window.
    """
    swing_high_indices = []
    swing_low_indices = []

    for i in range(lookback, len(highs) - lookback):
        window_highs = highs[i - lookback: i + lookback + 1]
        window_lows = lows[i - lookback: i + lookback + 1]

        if highs[i] == np.max(window_highs):
            swing_high_indices.append(i)
        if lows[i] == np.min(window_lows):
            swing_low_indices.append(i)

    return swing_high_indices, swing_low_indices


def calculate_retracement_levels(
    swing_high: float,
    swing_low: float
) -> List[FibonacciLevel]:
    """
    Calculate Fibonacci retracement levels between swing high and low.
    Levels are measured from swing_high downward.
    """
    diff = swing_high - swing_low
    levels = []
    labels = ["0%", "23.6%", "38.2%", "50%", "61.8%", "78.6%", "100%"]

    for ratio, label in zip(FIB_RETRACEMENT_RATIOS, labels):
        price = swing_high - (diff * ratio)
        levels.append(FibonacciLevel(
            level=ratio,
            price=round(price, 8),
            label=f"Fib {label}"
        ))

    return levels


def calculate_extension_levels(
    swing_high: float,
    swing_low: float,
    direction: str = "up"
) -> List[FibonacciLevel]:
    """
    Calculate Fibonacci extension levels for price targets.
    """
    diff = swing_high - swing_low
    levels = []

    for ratio in FIB_EXTENSION_RATIOS:
        if direction == "up":
            price = swing_low + (diff * ratio)
        else:
            price = swing_high - (diff * ratio)

        levels.append(FibonacciLevel(
            level=ratio,
            price=round(price, 8),
            label=f"Ext {ratio*100:.1f}%"
        ))

    return levels


def find_nearest_level(
    current_price: float,
    levels: List[FibonacciLevel],
    side: str = "support"
) -> Optional[float]:
    """Find nearest Fibonacci support or resistance to current price."""
    if side == "support":
        candidates = [l.price for l in levels if l.price < current_price]
        return max(candidates) if candidates else None
    else:
        candidates = [l.price for l in levels if l.price > current_price]
        return min(candidates) if candidates else None


def score_fibonacci_zone(
    current_price: float,
    retracement_levels: List[FibonacciLevel],
    swing_high: float,
    swing_low: float
) -> Tuple[float, str]:
    """
    Score the current price's Fibonacci zone.
    Returns (score 0-1, signal: buy/sell/neutral)
    
    High-score buy zones: 38.2%, 50%, 61.8% (golden zone)
    High-score sell zones: 23.6%, 78.6%
    """
    key_buy_levels = {0.382: 0.85, 0.5: 0.90, 0.618: 0.95}  # Golden zone
    key_sell_levels = {0.236: 0.75, 0.786: 0.80}

    trend = "up" if current_price > (swing_high + swing_low) / 2 else "down"
    best_score = 0.0
    best_signal = "neutral"

    for level in retracement_levels:
        ratio = level.level
        if ratio in (0.0, 1.0):
            continue

        level_price = level.price
        tolerance_range = level_price * ZONE_TOLERANCE

        if abs(current_price - level_price) <= tolerance_range:
            # Price is near this Fibonacci level
            if ratio in key_buy_levels and trend == "up":
                score = key_buy_levels[ratio]
                if score > best_score:
                    best_score = score
                    best_signal = "buy"
            elif ratio in key_sell_levels and trend == "down":
                score = key_sell_levels[ratio]
                if score > best_score:
                    best_score = score
                    best_signal = "sell"
            else:
                score = 0.5
                if score > best_score:
                    best_score = score
                    best_signal = "neutral"

    return best_score, best_signal


def analyze_fibonacci(
    df: pd.DataFrame,
    symbol: str,
    timeframe: str
) -> FibonacciAnalysis:
    """
    Main Fibonacci analysis function.
    Takes an OHLCV DataFrame and returns full Fibonacci analysis.
    """
    highs = df['high'].values
    lows = df['low'].values
    current_price = float(df['close'].iloc[-1])

    # Detect swing points
    lookback = max(5, len(df) // 20)
    sh_indices, sl_indices = detect_swing_points(highs, lows, lookback=lookback)

    if not sh_indices or not sl_indices:
        # Fallback: use period high/low
        swing_high = float(highs.max())
        swing_low = float(lows.min())
    else:
        # Use the most recent significant swing points
        recent_sh = max(sh_indices[-3:]) if len(sh_indices) >= 3 else sh_indices[-1]
        recent_sl = max(sl_indices[-3:]) if len(sl_indices) >= 3 else sl_indices[-1]
        swing_high = float(highs[recent_sh])
        swing_low = float(lows[recent_sl])

    # Ensure swing_high > swing_low
    if swing_high <= swing_low:
        swing_high = float(highs[-len(highs)//4:].max())
        swing_low = float(lows[-len(lows)//4:].min())

    # Calculate levels
    retracement_levels = calculate_retracement_levels(swing_high, swing_low)

    # Determine trend direction for extensions
    trend_direction = "up" if current_price > (swing_high + swing_low) / 2 else "down"
    extension_levels = calculate_extension_levels(swing_high, swing_low, trend_direction)

    # Score the zone
    zone_score, fib_signal = score_fibonacci_zone(
        current_price, retracement_levels, swing_high, swing_low
    )

    # Find support/resistance
    nearest_support = find_nearest_level(current_price, retracement_levels, "support")
    nearest_resistance = find_nearest_level(current_price, retracement_levels, "resistance")

    logger.info(
        f"[Fibonacci] {symbol} {timeframe} | "
        f"High={swing_high:.4f} Low={swing_low:.4f} | "
        f"Signal={fib_signal} Score={zone_score:.2f}"
    )

    return FibonacciAnalysis(
        symbol=symbol,
        timeframe=timeframe,
        swing_high=swing_high,
        swing_low=swing_low,
        retracement_levels=retracement_levels,
        extension_levels=extension_levels,
        current_price=current_price,
        nearest_support=nearest_support,
        nearest_resistance=nearest_resistance,
        signal=fib_signal,
        zone_score=zone_score
    )


def multi_timeframe_fibonacci(
    dataframes: Dict[str, pd.DataFrame],
    symbol: str
) -> Dict[str, FibonacciAnalysis]:
    """Run Fibonacci analysis across multiple timeframes."""
    results = {}
    for timeframe, df in dataframes.items():
        try:
            results[timeframe] = analyze_fibonacci(df, symbol, timeframe)
        except Exception as e:
            logger.error(f"Fibonacci error for {symbol} {timeframe}: {e}")
    return results


def get_fibonacci_consensus(analyses: Dict[str, FibonacciAnalysis]) -> Tuple[str, float]:
    """
    Get consensus signal from multi-timeframe Fibonacci analysis.
    Higher timeframes get more weight.
    """
    weights = {"1h": 0.20, "4h": 0.35, "1d": 0.45}
    buy_score = 0.0
    sell_score = 0.0
    total_weight = 0.0

    for tf, analysis in analyses.items():
        w = weights.get(tf, 0.25)
        total_weight += w
        if analysis.signal == "buy":
            buy_score += w * analysis.zone_score
        elif analysis.signal == "sell":
            sell_score += w * analysis.zone_score

    if total_weight == 0:
        return "neutral", 0.0

    buy_score /= total_weight
    sell_score /= total_weight

    if buy_score > sell_score and buy_score > 0.35:
        return "buy", buy_score
    elif sell_score > buy_score and sell_score > 0.35:
        return "sell", sell_score
    else:
        return "neutral", max(buy_score, sell_score)
