import { useState, useEffect } from 'react'
import axios from 'axios'

const API = '/api'

export function useTrades() {
  const [trades, setTrades] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  const fetchTrades = async () => {
    try {
      const { data } = await axios.get(`${API}/trades`)
      setTrades(data.trades || [])
      setStats({ total: data.total, open: data.open_count, closed: data.closed_count })
    } catch (e) {
      console.error('Trades fetch error:', e)
    } finally {
      setLoading(false)
    }
  }

  const closeTrade = async (id) => {
    try {
      await axios.post(`${API}/trades/${id}/close`)
      await fetchTrades()
    } catch (e) {
      console.error('Close trade error:', e)
    }
  }

  useEffect(() => {
    fetchTrades()
    const interval = setInterval(fetchTrades, 10000)
    return () => clearInterval(interval)
  }, [])

  return { trades, stats, loading, fetchTrades, closeTrade }
}

export function useAnalytics() {
  const [performance, setPerformance] = useState(null)
  const [signals, setSignals] = useState([])
  const [pnlHistory, setPnlHistory] = useState([])
  const [hasOpenRouterKey, setHasOpenRouterKey] = useState(true)

  useEffect(() => {
    const fetch = async () => {
      try {
        const [perf, sigs, pnl] = await Promise.all([
          axios.get(`${API}/analytics/performance`),
          axios.get(`${API}/analytics/signals`),
          axios.get(`${API}/analytics/pnl-history`)
        ])
        setPerformance(perf.data)
        setSignals(sigs.data.signals || [])
        setPnlHistory(pnl.data.history || [])
        setHasOpenRouterKey(sigs.data.has_openrouter_key ?? true)
      } catch (e) {
        console.error('Analytics fetch error:', e)
      }
    }
    fetch()
    const interval = setInterval(fetch, 30000)
    return () => clearInterval(interval)
  }, [])

  return { performance, signals, pnlHistory, hasOpenRouterKey }
}

export function useBalance() {
  const [balance, setBalance] = useState(null)

  useEffect(() => {
    const fetch = async () => {
      try {
        const { data } = await axios.get(`${API}/balance`)
        setBalance(data)
      } catch (e) {
        console.error('Balance fetch error:', e)
      }
    }
    fetch()
    const interval = setInterval(fetch, 15000)
    return () => clearInterval(interval)
  }, [])

  return { balance }
}
