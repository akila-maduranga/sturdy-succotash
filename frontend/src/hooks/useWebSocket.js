import { useState, useEffect, useRef, useCallback } from 'react'

const WS_URL = '/ws/stream'

export function useWebSocket() {
  const [prices, setPrices] = useState({
    'BTC/USDT': { price: 0, change_pct_24h: 0 },
    'ETH/USDT': { price: 0, change_pct_24h: 0 },
    'SOL/USDT': { price: 0, change_pct_24h: 0 },
  })
  const [signals, setSignals] = useState({})
  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState(null)
  const wsRef = useRef(null)
  const reconnectTimer = useRef(null)

  const connect = useCallback(() => {
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const host = window.location.host
      const url = `${protocol}//${host}${WS_URL}`

      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen = () => {
        setIsConnected(true)
        console.log('[WS] Connected')
      }

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data)
          setLastMessage(msg)

          if (msg.type === 'ticker' && msg.symbol && msg.data) {
            setPrices(prev => ({ ...prev, [msg.symbol]: msg.data }))
          } else if (msg.type === 'signal' && msg.symbol) {
            setSignals(prev => ({ ...prev, [msg.symbol]: msg.data }))
          } else if (msg.type === 'ping') {
            ws.send(JSON.stringify({ type: 'ping' }))
          }
        } catch (e) {
          console.error('[WS] Parse error:', e)
        }
      }

      ws.onclose = () => {
        setIsConnected(false)
        console.log('[WS] Disconnected, reconnecting in 3s...')
        reconnectTimer.current = setTimeout(connect, 3000)
      }

      ws.onerror = (err) => {
        console.error('[WS] Error:', err)
        ws.close()
      }
    } catch (e) {
      console.error('[WS] Connection failed:', e)
      reconnectTimer.current = setTimeout(connect, 5000)
    }
  }, [])

  useEffect(() => {
    connect()
    return () => {
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current)
      if (wsRef.current) wsRef.current.close()
    }
  }, [connect])

  return { prices, signals, isConnected, lastMessage }
}
