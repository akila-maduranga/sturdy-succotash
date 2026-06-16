"""
Exchange Service - Binance via CCXT
Handles all exchange interactions: market data, orders, balance.
"""
import ccxt.async_support as ccxt
import pandas as pd
import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
from models.schemas import OHLCV, Ticker, Balance
from config import settings
from loguru import logger


class ExchangeService:
    def __init__(self):
        self.exchange: Optional[ccxt.Exchange] = None
        self._initialized = False

    async def initialize(self):
        """Initialize CCXT exchange connection."""
        exchange_class = getattr(ccxt, settings.exchange)
        self.exchange = exchange_class({
            'apiKey': settings.exchange_api_key,
            'secret': settings.exchange_api_secret,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot',
                'adjustForTimeDifference': True,
            }
        })

        if settings.testnet:
            self.exchange.set_sandbox_mode(True)

        try:
            await self.exchange.load_markets()
            self._initialized = True
            logger.info(f"[Exchange] Connected to {settings.exchange} ({'testnet' if settings.testnet else 'live'})")
        except Exception as e:
            logger.error(f"[Exchange] Connection failed: {e}")
            raise

    async def close(self):
        if self.exchange:
            await self.exchange.close()

    async def get_ticker(self, symbol: str) -> Optional[Ticker]:
        try:
            t = await self.exchange.fetch_ticker(symbol)
            return Ticker(
                symbol=symbol,
                price=float(t['last'] or 0),
                change_24h=float(t['change'] or 0),
                change_pct_24h=float(t['percentage'] or 0),
                volume_24h=float(t['quoteVolume'] or 0),
                high_24h=float(t['high'] or 0),
                low_24h=float(t['low'] or 0),
                timestamp=datetime.fromtimestamp(t['timestamp'] / 1000, tz=timezone.utc)
            )
        except Exception as e:
            logger.error(f"[Exchange] get_ticker {symbol} error: {e}")
            return None

    async def get_ohlcv(
        self,
        symbol: str,
        timeframe: str = '1h',
        limit: int = 200
    ) -> Optional[pd.DataFrame]:
        try:
            ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            if not ohlcv:
                return None
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
            df = df.set_index('timestamp')
            df = df.astype(float)
            return df
        except Exception as e:
            logger.error(f"[Exchange] get_ohlcv {symbol} {timeframe} error: {e}")
            return None

    async def get_multi_timeframe_ohlcv(
        self,
        symbol: str,
        timeframes: List[str],
        limit: int = 200
    ) -> Dict[str, pd.DataFrame]:
        tasks = [self.get_ohlcv(symbol, tf, limit) for tf in timeframes]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return {
            tf: result
            for tf, result in zip(timeframes, results)
            if isinstance(result, pd.DataFrame) and not result.empty
        }

    async def get_balance(self) -> Optional[Balance]:
        if settings.read_only:
            logger.warning("[Exchange] Read-only mode: returning mock balance")
            return Balance(
                total_usdt=10.0, free_usdt=10.0, locked_usdt=0.0,
                assets={}, pnl_today=0.0, pnl_today_pct=0.0,
                pnl_total=0.0, pnl_total_pct=0.0
            )
        try:
            bal = await self.exchange.fetch_balance()
            usdt = bal.get('USDT', {})
            total = float(usdt.get('total', 0))
            free = float(usdt.get('free', 0))
            locked = float(usdt.get('used', 0))
            assets = {k: float(v['total']) for k, v in bal.items()
                      if isinstance(v, dict) and v.get('total', 0) > 0 and k != 'USDT'}
            return Balance(
                total_usdt=total, free_usdt=free, locked_usdt=locked,
                assets=assets, pnl_today=0.0, pnl_today_pct=0.0,
                pnl_total=0.0, pnl_total_pct=0.0
            )
        except Exception as e:
            logger.error(f"[Exchange] get_balance error: {e}")
            return None

    async def place_market_order(
        self,
        symbol: str,
        side: str,
        quantity: float
    ) -> Optional[Dict]:
        if settings.read_only:
            logger.warning(f"[Exchange] READ-ONLY: would place {side} {quantity} {symbol}")
            return {"id": f"SIMULATED_{side.upper()}_{symbol}", "status": "simulated"}

        try:
            order = await self.exchange.create_order(
                symbol=symbol,
                type='market',
                side=side,
                amount=quantity
            )
            logger.info(f"[Exchange] Order placed: {order['id']} {side} {quantity} {symbol}")
            return order
        except Exception as e:
            logger.error(f"[Exchange] place_market_order error: {e}")
            return None

    async def place_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float
    ) -> Optional[Dict]:
        if settings.read_only:
            logger.warning(f"[Exchange] READ-ONLY: would place limit {side} {quantity} {symbol} @ {price}")
            return {"id": f"SIMULATED_LIMIT_{side.upper()}", "status": "simulated"}

        try:
            order = await self.exchange.create_order(
                symbol=symbol,
                type='limit',
                side=side,
                amount=quantity,
                price=price
            )
            return order
        except Exception as e:
            logger.error(f"[Exchange] place_limit_order error: {e}")
            return None

    async def set_stop_loss_take_profit(
        self,
        symbol: str,
        side: str,
        quantity: float,
        stop_loss: float,
        take_profit: float
    ) -> Dict:
        """Place stop-loss and take-profit orders."""
        if settings.read_only:
            return {"sl": "SIMULATED_SL", "tp": "SIMULATED_TP"}

        results = {}
        exit_side = "sell" if side == "buy" else "buy"

        # Stop Loss
        try:
            sl_order = await self.exchange.create_order(
                symbol=symbol,
                type='stop_loss_limit',
                side=exit_side,
                amount=quantity,
                price=stop_loss * 0.999,
                params={'stopPrice': stop_loss}
            )
            results['sl'] = sl_order['id']
        except Exception as e:
            logger.error(f"[Exchange] SL order error: {e}")
            results['sl'] = None

        # Take Profit
        try:
            tp_order = await self.exchange.create_order(
                symbol=symbol,
                type='take_profit_limit',
                side=exit_side,
                amount=quantity,
                price=take_profit * 1.001,
                params={'stopPrice': take_profit}
            )
            results['tp'] = tp_order['id']
        except Exception as e:
            logger.error(f"[Exchange] TP order error: {e}")
            results['tp'] = None

        return results

    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        if settings.read_only:
            return True
        try:
            await self.exchange.cancel_order(order_id, symbol)
            return True
        except Exception as e:
            logger.error(f"[Exchange] cancel_order error: {e}")
            return False

    async def get_order_status(self, order_id: str, symbol: str) -> Optional[Dict]:
        try:
            return await self.exchange.fetch_order(order_id, symbol)
        except Exception as e:
            logger.error(f"[Exchange] get_order_status error: {e}")
            return None


# Singleton
_exchange_service: Optional[ExchangeService] = None


async def get_exchange() -> ExchangeService:
    global _exchange_service
    current_loop = asyncio.get_event_loop()
    
    needs_init = False
    if _exchange_service is None or not _exchange_service._initialized or _exchange_service.exchange is None:
        needs_init = True
    else:
        # Check if exchange is bound to a different or closed event loop
        exchange_loop = getattr(_exchange_service.exchange, 'asyncio_loop', None) or getattr(_exchange_service.exchange, 'loop', None)
        if exchange_loop != current_loop or current_loop.is_closed():
            needs_init = True
            if _exchange_service.exchange:
                try:
                    # Try closing exchange connection associated with the old loop
                    asyncio.create_task(_exchange_service.close())
                except Exception:
                    pass

    if needs_init:
        _exchange_service = ExchangeService()
        await _exchange_service.initialize()
        
    return _exchange_service
