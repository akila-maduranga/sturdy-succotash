"""
OpenRouter AI Analysis Service
Sends market data to OpenRouter and gets structured trade recommendations.
"""
import json
import httpx
from typing import Optional
from models.schemas import AISignal, FibonacciAnalysis, PatternAnalysis
from config import settings
from loguru import logger


OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def build_analysis_prompt(
    symbol: str,
    current_price: float,
    fib: Optional[FibonacciAnalysis],
    patterns: Optional[PatternAnalysis],
    ticker_data: dict
) -> str:
    fib_section = ""
    if fib:
        levels_str = ", ".join([f"{l.label}: {l.price:.4f}" for l in fib.retracement_levels])
        fib_section = f"""
FIBONACCI ANALYSIS:
- Swing High: {fib.swing_high:.4f}
- Swing Low: {fib.swing_low:.4f}
- Retracement Levels: {levels_str}
- Fibonacci Signal: {fib.signal} (Zone Score: {fib.zone_score:.2f})
- Nearest Support: {fib.nearest_support}
- Nearest Resistance: {fib.nearest_resistance}
"""

    pattern_section = ""
    if patterns:
        pattern_section = f"""
TECHNICAL ANALYSIS:
- Trend: {patterns.trend}
- RSI: {patterns.rsi:.1f}
- MACD: {patterns.macd_signal}
- EMA Signal: {patterns.ema_signal}
- Bollinger Bands: {patterns.bollinger_signal}
- Volume: {patterns.volume_signal}
- Detected Patterns: {', '.join(patterns.patterns) if patterns.patterns else 'None'}
- Pattern Signal: {patterns.signal} (Strength: {patterns.strength:.2f})
"""

    return f"""You are an expert cryptocurrency spot trader specializing in short-term analysis.

MARKET DATA FOR {symbol}:
- Current Price: {current_price:.4f} USDT
- 24h Change: {ticker_data.get('change_pct_24h', 0):.2f}%
- 24h High: {ticker_data.get('high_24h', 0):.4f}
- 24h Low: {ticker_data.get('low_24h', 0):.4f}
- 24h Volume: {ticker_data.get('volume_24h', 0):.2f} USDT

{fib_section}
{pattern_section}

TASK: Analyze the above data and provide a trading recommendation for SPOT trading only.

Respond ONLY with a valid JSON object in this exact format:
{{
  "recommendation": "buy" | "sell" | "hold",
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation (max 150 words)",
  "entry_price": null or number,
  "stop_loss": null or number,
  "take_profit": null or number,
  "risk_reward_ratio": null or number,
  "key_levels": {{"support": null or number, "resistance": null or number}},
  "time_horizon": "1h" | "4h" | "1d"
}}

RULES:
- Only recommend "buy" or "sell" if confidence >= 0.65
- Stop loss must limit loss to maximum 2% of position value
- Take profit should be at least 2x the stop loss distance (2:1 RR minimum)
- Consider small balance ($10 USDT) - entry must be achievable
- If signals conflict, choose "hold"
"""


async def get_ai_analysis(
    symbol: str,
    current_price: float,
    fib: Optional[FibonacciAnalysis],
    patterns: Optional[PatternAnalysis],
    ticker_data: dict
) -> Optional[AISignal]:
    if not settings.openrouter_api_key or settings.openrouter_api_key == "your_openrouter_api_key_here":
        logger.warning("OpenRouter API key not configured, skipping AI analysis")
        return None

    prompt = build_analysis_prompt(symbol, current_price, fib, patterns, ticker_data)

    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://trading-bot.local",
        "X-Title": "AutoTradingBot"
    }

    payload = {
        "model": settings.ai_model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 500,
        "response_format": {"type": "json_object"}
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()

        content = data['choices'][0]['message']['content']
        result = json.loads(content)

        signal = AISignal(
            symbol=symbol,
            recommendation=result.get('recommendation', 'hold'),
            confidence=float(result.get('confidence', 0.0)),
            reasoning=result.get('reasoning', 'No reasoning provided'),
            entry_price=result.get('entry_price'),
            stop_loss=result.get('stop_loss'),
            take_profit=result.get('take_profit'),
            risk_reward_ratio=result.get('risk_reward_ratio'),
            model_used=settings.ai_model
        )

        logger.info(
            f"[AI] {symbol} | {signal.recommendation} "
            f"(confidence={signal.confidence:.2f}) | {signal.reasoning[:80]}..."
        )
        return signal

    except httpx.HTTPStatusError as e:
        logger.error(f"[AI] HTTP error: {e.response.status_code} - {e.response.text}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"[AI] JSON parse error: {e}")
        return None
    except Exception as e:
        logger.error(f"[AI] Unexpected error: {e}")
        return None
