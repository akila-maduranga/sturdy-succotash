"""
WebSocket Router - Real-time price and signal streaming
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Set, Dict
import asyncio
import json
from datetime import datetime, timezone
from loguru import logger

router = APIRouter(tags=["websocket"])

# Connected clients
connected_clients: Set[WebSocket] = set()


async def broadcast(message: dict):
    """Send message to all connected WebSocket clients."""
    if not connected_clients:
        return
    data = json.dumps(message, default=str)
    disconnected = set()
    for ws in connected_clients.copy():
        try:
            await ws.send_text(data)
        except Exception:
            disconnected.add(ws)
    for ws in disconnected:
        connected_clients.discard(ws)


@router.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    logger.info(f"[WS] Client connected. Total: {len(connected_clients)}")

    try:
        # Send initial data immediately
        await send_initial_data(websocket)

        # Start price streaming
        price_task = asyncio.create_task(stream_prices(websocket))

        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }))
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_text(json.dumps({"type": "ping"}))
            except WebSocketDisconnect:
                break

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"[WS] Error: {e}")
    finally:
        connected_clients.discard(websocket)
        if 'price_task' in locals():
            price_task.cancel()
        logger.info(f"[WS] Client disconnected. Total: {len(connected_clients)}")


async def send_initial_data(websocket: WebSocket):
    """Send initial market data on connection."""
    try:
        from services.exchange import get_exchange
        import redis.asyncio as aioredis
        from config import settings

        r = aioredis.from_url(settings.redis_url)
        exchange = await get_exchange()

        for symbol in settings.trading_pairs_list:
            # Try cache first
            cached = await r.get(f"price:{symbol}")
            if cached:
                price_data = json.loads(cached)
            else:
                ticker = await exchange.get_ticker(symbol)
                price_data = {
                    "price": ticker.price if ticker else 0,
                    "change_pct_24h": ticker.change_pct_24h if ticker else 0,
                    "volume_24h": ticker.volume_24h if ticker else 0,
                } if ticker else {}

            await websocket.send_text(json.dumps({
                "type": "ticker",
                "symbol": symbol,
                "data": price_data,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }))

        await r.aclose()
    except Exception as e:
        logger.error(f"[WS] send_initial_data error: {e}")


async def stream_prices(websocket: WebSocket):
    """Stream price updates every 5 seconds."""
    from services.exchange import get_exchange
    from config import settings

    while True:
        try:
            await asyncio.sleep(5)
            exchange = await get_exchange()

            for symbol in settings.trading_pairs_list:
                ticker = await exchange.get_ticker(symbol)
                if ticker:
                    await websocket.send_text(json.dumps({
                        "type": "ticker",
                        "symbol": symbol,
                        "data": {
                            "price": ticker.price,
                            "change_pct_24h": ticker.change_pct_24h,
                            "volume_24h": ticker.volume_24h,
                            "high_24h": ticker.high_24h,
                            "low_24h": ticker.low_24h,
                        },
                        "timestamp": ticker.timestamp.isoformat()
                    }))
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"[WS] stream_prices error: {e}")
            break
