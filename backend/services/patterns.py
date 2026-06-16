"""
Chart Pattern & Technical Indicator Analysis Service
"""
import numpy as np
import pandas as pd
import ta
from typing import List, Tuple, Dict
from models.schemas import PatternAnalysis
from loguru import logger


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
    macd = ta.trend.MACD(df['close'])
    df['macd'] = macd.macd()
    df['macd_signal_line'] = macd.macd_signal()
    df['ema_9'] = ta.trend.EMAIndicator(df['close'], window=9).ema_indicator()
    df['ema_21'] = ta.trend.EMAIndicator(df['close'], window=21).ema_indicator()
    df['ema_50'] = ta.trend.EMAIndicator(df['close'], window=50).ema_indicator()
    df['ema_200'] = ta.trend.EMAIndicator(df['close'], window=200).ema_indicator()
    bb = ta.volatility.BollingerBands(df['close'], window=20, window_dev=2)
    df['bb_upper'] = bb.bollinger_hband()
    df['bb_lower'] = bb.bollinger_lband()
    df['bb_mid'] = bb.bollinger_mavg()
    df['bb_percent'] = bb.bollinger_pband()
    df['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], window=14).average_true_range()
    df['volume_sma'] = df['volume'].rolling(window=20).mean()
    df['volume_ratio'] = df['volume'] / df['volume_sma']
    return df.dropna()


def detect_candlestick_patterns(df: pd.DataFrame) -> List[str]:
    patterns = []
    if len(df) < 3:
        return patterns
    last = df.iloc[-1]
    prev = df.iloc[-2]
    prev2 = df.iloc[-3]
    body = abs(last['close'] - last['open'])
    total_range = last['high'] - last['low']
    upper_wick = last['high'] - max(last['close'], last['open'])
    lower_wick = min(last['close'], last['open']) - last['low']

    if total_range > 0 and body / total_range < 0.1:
        patterns.append("Doji")
    if total_range > 0 and lower_wick > 2 * body and upper_wick < 0.3 * body and last['close'] > last['open']:
        patterns.append("Hammer")
    if total_range > 0 and upper_wick > 2 * body and lower_wick < 0.3 * body and last['close'] < last['open']:
        patterns.append("Shooting Star")
    if prev['close'] < prev['open'] and last['close'] > last['open'] and last['open'] < prev['close'] and last['close'] > prev['open']:
        patterns.append("Bullish Engulfing")
    if prev['close'] > prev['open'] and last['close'] < last['open'] and last['open'] > prev['close'] and last['close'] < prev['open']:
        patterns.append("Bearish Engulfing")
    if (prev2['close'] < prev2['open'] and
            abs(prev['close'] - prev['open']) < abs(prev2['close'] - prev2['open']) * 0.3 and
            last['close'] > last['open'] and last['close'] > (prev2['open'] + prev2['close']) / 2):
        patterns.append("Morning Star")
    if (prev2['close'] > prev2['open'] and
            abs(prev['close'] - prev['open']) < abs(prev2['close'] - prev2['open']) * 0.3 and
            last['close'] < last['open'] and last['close'] < (prev2['open'] + prev2['close']) / 2):
        patterns.append("Evening Star")
    return patterns


def detect_chart_patterns(df: pd.DataFrame) -> List[str]:
    patterns = []
    if len(df) < 30:
        return patterns
    recent_highs = df['high'].values[-30:]
    recent_lows = df['low'].values[-30:]

    local_mins = [(i, recent_lows[i]) for i in range(1, len(recent_lows) - 1)
                  if recent_lows[i] < recent_lows[i-1] and recent_lows[i] < recent_lows[i+1]]
    if len(local_mins) >= 2:
        last_two = local_mins[-2:]
        if abs(last_two[0][1] - last_two[1][1]) / last_two[0][1] < 0.03:
            patterns.append("Double Bottom")

    local_maxs = [(i, recent_highs[i]) for i in range(1, len(recent_highs) - 1)
                  if recent_highs[i] > recent_highs[i-1] and recent_highs[i] > recent_highs[i+1]]
    if len(local_maxs) >= 2:
        last_two = local_maxs[-2:]
        if abs(last_two[0][1] - last_two[1][1]) / last_two[0][1] < 0.03:
            patterns.append("Double Top")

    return patterns


def get_trend(df: pd.DataFrame) -> str:
    last = df.iloc[-1]
    if pd.isna(last.get('ema_50')) or pd.isna(last.get('ema_200')):
        return "neutral"
    price, ema50, ema200 = last['close'], last['ema_50'], last['ema_200']
    if price > ema50 > ema200: return "strong_uptrend"
    if price < ema50 < ema200: return "strong_downtrend"
    if price > ema50: return "uptrend"
    if price < ema50: return "downtrend"
    return "sideways"


def get_signals(df: pd.DataFrame) -> Tuple[str, str, str, str]:
    last = df.iloc[-1]
    prev = df.iloc[-2]

    macd = "neutral"
    if not pd.isna(last.get('macd')):
        if prev['macd'] < prev['macd_signal_line'] and last['macd'] > last['macd_signal_line']:
            macd = "bullish_crossover"
        elif prev['macd'] > prev['macd_signal_line'] and last['macd'] < last['macd_signal_line']:
            macd = "bearish_crossover"
        elif last['macd'] > last['macd_signal_line']:
            macd = "bullish"
        else:
            macd = "bearish"

    ema = "neutral"
    if not pd.isna(last.get('ema_9')) and not pd.isna(last.get('ema_21')):
        if prev['ema_9'] < prev['ema_21'] and last['ema_9'] > last['ema_21']:
            ema = "bullish_crossover"
        elif prev['ema_9'] > prev['ema_21'] and last['ema_9'] < last['ema_21']:
            ema = "bearish_crossover"
        elif last['ema_9'] > last['ema_21']:
            ema = "bullish"
        else:
            ema = "bearish"

    bb = "neutral"
    if not pd.isna(last.get('bb_percent')):
        bp = last['bb_percent']
        if bp < 0.05: bb = "oversold"
        elif bp > 0.95: bb = "overbought"
        elif bp < 0.3: bb = "bullish"
        elif bp > 0.7: bb = "bearish"

    vol = "normal"
    if not pd.isna(last.get('volume_ratio')):
        vr = last['volume_ratio']
        if vr > 1.5 and last['close'] > last['open']: vol = "high_volume_bullish"
        elif vr > 1.5 and last['close'] < last['open']: vol = "high_volume_bearish"

    return macd, ema, bb, vol


def analyze_patterns(df: pd.DataFrame, symbol: str, timeframe: str) -> PatternAnalysis:
    df = calculate_indicators(df.copy())
    if len(df) < 5:
        return PatternAnalysis(symbol=symbol, timeframe=timeframe, patterns=[],
                               trend="neutral", rsi=50.0, macd_signal="neutral",
                               ema_signal="neutral", bollinger_signal="neutral",
                               volume_signal="normal", signal="neutral", strength=0.0)

    trend = get_trend(df)
    rsi = float(df['rsi'].iloc[-1]) if not pd.isna(df['rsi'].iloc[-1]) else 50.0
    macd_sig, ema_sig, bb_sig, vol_sig = get_signals(df)
    candles = detect_candlestick_patterns(df)
    charts = detect_chart_patterns(df)
    all_patterns = candles + charts

    # Score
    buy = 0.0
    sell = 0.0
    if "uptrend" in trend: buy += 0.2
    if "downtrend" in trend: sell += 0.2
    if rsi < 30: buy += 0.2
    elif rsi > 70: sell += 0.2
    if "bullish" in macd_sig: buy += 0.15
    elif "bearish" in macd_sig: sell += 0.15
    if "bullish" in ema_sig: buy += 0.1
    elif "bearish" in ema_sig: sell += 0.1
    if bb_sig == "oversold": buy += 0.1
    elif bb_sig == "overbought": sell += 0.1
    if "bullish" in vol_sig: buy += 0.1
    elif "bearish" in vol_sig: sell += 0.1
    for p in all_patterns:
        if p in ["Hammer", "Bullish Engulfing", "Morning Star", "Double Bottom"]: buy += 0.15
        elif p in ["Shooting Star", "Bearish Engulfing", "Evening Star", "Double Top"]: sell += 0.15

    if buy > sell * 1.3: signal, strength = "buy", min(buy, 1.0)
    elif sell > buy * 1.3: signal, strength = "sell", min(sell, 1.0)
    else: signal, strength = "neutral", 0.0

    logger.info(f"[Patterns] {symbol} {timeframe} | {trend} RSI={rsi:.1f} | {all_patterns} | {signal} ({strength:.2f})")

    return PatternAnalysis(symbol=symbol, timeframe=timeframe, patterns=all_patterns,
                           trend=trend, rsi=rsi, macd_signal=macd_sig, ema_signal=ema_sig,
                           bollinger_signal=bb_sig, volume_signal=vol_sig,
                           signal=signal, strength=strength)
