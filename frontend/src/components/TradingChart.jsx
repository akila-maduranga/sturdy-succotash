import React, { useEffect, useRef, useState } from 'react'
import { createChart, CrosshairMode } from 'lightweight-charts'
import axios from 'axios'
import { TrendingUp, RefreshCw } from 'lucide-react'

const API = '/api'
const SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
const TIMEFRAMES = ['5m', '15m', '1h', '4h', '1d']

export default function TradingChart() {
  const chartRef = useRef(null)
  const chartInstance = useRef(null)
  const candleSeries = useRef(null)
  const fibLines = useRef([])

  const [symbol, setSymbol] = useState('BTC/USDT')
  const [timeframe, setTimeframe] = useState('1h')
  const [loading, setLoading] = useState(false)
  const [analysis, setAnalysis] = useState(null)
  const [price, setPrice] = useState(null)

  useEffect(() => {
    if (!chartRef.current) return

    const chart = createChart(chartRef.current, {
      layout: {
        background: { color: 'transparent' },
        textColor: '#94a3b8',
      },
      grid: {
        vertLines: { color: 'rgba(255,255,255,0.04)' },
        horzLines: { color: 'rgba(255,255,255,0.04)' },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: { color: 'rgba(99,102,241,0.4)', labelBackgroundColor: '#6366f1' },
        horzLine: { color: 'rgba(99,102,241,0.4)', labelBackgroundColor: '#6366f1' },
      },
      rightPriceScale: {
        borderColor: 'rgba(255,255,255,0.07)',
        textColor: '#94a3b8',
      },
      timeScale: {
        borderColor: 'rgba(255,255,255,0.07)',
        textColor: '#94a3b8',
        timeVisible: true,
        secondsVisible: false,
      },
      width: chartRef.current.clientWidth,
      height: 480,
    })

    const series = chart.addCandlestickSeries({
      upColor: '#10b981',
      downColor: '#ef4444',
      borderUpColor: '#10b981',
      borderDownColor: '#ef4444',
      wickUpColor: '#10b981',
      wickDownColor: '#ef4444',
    })

    chartInstance.current = chart
    candleSeries.current = series

    const handleResize = () => {
      if (chartRef.current) chart.applyOptions({ width: chartRef.current.clientWidth })
    }
    window.addEventListener('resize', handleResize)
    return () => {
      window.removeEventListener('resize', handleResize)
      chart.remove()
    }
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const sym = symbol.replace('/', '-')
      const { data } = await axios.get(`${API}/market/ohlcv/${sym}?timeframe=${timeframe}&limit=150`)

      if (data.candles && candleSeries.current) {
        const formatted = data.candles.map(c => ({
          time: c.time,
          open: c.open,
          high: c.high,
          low: c.low,
          close: c.close,
        }))
        candleSeries.current.setData(formatted)
        if (formatted.length > 0) {
          setPrice(formatted[formatted.length - 1].close)
        }

        // Fit chart
        chartInstance.current?.timeScale().fitContent()
      }

      // Run analysis to get Fibonacci levels
      try {
        const { data: anal } = await axios.get(`${API}/market/analyze/${sym}`)
        setAnalysis(anal)
        drawFibLevels(anal)
      } catch (e) {
        console.log('Analysis not available:', e.message)
      }
    } catch (e) {
      console.error('Load data error:', e)
    }
    setLoading(false)
  }

  const drawFibLevels = (anal) => {
    if (!chartInstance.current || !candleSeries.current) return

    // Remove old Fibonacci lines
    fibLines.current.forEach(line => {
      try { chartInstance.current.removePriceLine(line) } catch (e) {}
    })
    fibLines.current = []

    const fib = anal?.fibonacci
    if (!fib?.retracement_levels) return

    const fibColors = {
      '0%': 'rgba(239,68,68,0.6)',
      '23.6%': 'rgba(245,158,11,0.6)',
      '38.2%': 'rgba(99,102,241,0.8)',
      '50%': 'rgba(168,85,247,0.8)',
      '61.8%': 'rgba(16,185,129,0.9)',
      '78.6%': 'rgba(99,102,241,0.6)',
      '100%': 'rgba(239,68,68,0.6)',
    }

    fib.retracement_levels.forEach(level => {
      try {
        const pct = level.label.replace('Fib ', '')
        const line = candleSeries.current.createPriceLine({
          price: level.price,
          color: fibColors[pct] || 'rgba(255,255,255,0.3)',
          lineWidth: 1,
          lineStyle: 1, // dashed
          axisLabelVisible: true,
          title: level.label,
        })
        fibLines.current.push(line)
      } catch (e) {}
    })
  }

  useEffect(() => {
    loadData()
  }, [symbol, timeframe])

  return (
    <div className="fade-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 800 }}>Live Chart</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 4 }}>
            Candlestick chart with Fibonacci retracement levels
          </p>
        </div>
        <button className="btn btn-ghost" onClick={loadData} disabled={loading}>
          <RefreshCw size={14} style={{ animation: loading ? 'spin 0.8s linear infinite' : 'none' }} />
          Refresh
        </button>
      </div>

      {/* Controls */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
          {/* Symbol selector */}
          <div>
            <div style={{ fontSize: 10, color: 'var(--text-muted)', marginBottom: 6, fontWeight: 600, textTransform: 'uppercase' }}>Symbol</div>
            <div style={{ display: 'flex', gap: 6 }}>
              {SYMBOLS.map(s => (
                <button key={s} onClick={() => setSymbol(s)}
                  style={{
                    padding: '6px 12px', borderRadius: 6, border: 'none',
                    cursor: 'pointer', fontSize: 12, fontWeight: 600, fontFamily: 'var(--font-sans)',
                    background: symbol === s ? 'var(--accent)' : 'var(--bg-input)',
                    color: symbol === s ? 'white' : 'var(--text-secondary)',
                    transition: 'all 0.2s'
                  }}>
                  {s.replace('/USDT', '')}
                </button>
              ))}
            </div>
          </div>

          {/* Timeframe selector */}
          <div>
            <div style={{ fontSize: 10, color: 'var(--text-muted)', marginBottom: 6, fontWeight: 600, textTransform: 'uppercase' }}>Timeframe</div>
            <div style={{ display: 'flex', gap: 4 }}>
              {TIMEFRAMES.map(tf => (
                <button key={tf} onClick={() => setTimeframe(tf)}
                  style={{
                    padding: '6px 10px', borderRadius: 6, border: 'none',
                    cursor: 'pointer', fontSize: 12, fontFamily: 'var(--font-sans)',
                    background: timeframe === tf ? 'var(--accent)' : 'var(--bg-input)',
                    color: timeframe === tf ? 'white' : 'var(--text-secondary)',
                    transition: 'all 0.2s'
                  }}>
                  {tf}
                </button>
              ))}
            </div>
          </div>

          {price && (
            <div style={{ marginLeft: 'auto', textAlign: 'right' }}>
              <div style={{ fontSize: 10, color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>{symbol}</div>
              <div style={{ fontSize: 22, fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>
                ${price.toLocaleString('en-US', { maximumFractionDigits: 4 })}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Chart */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        {loading && (
          <div style={{
            position: 'absolute', inset: 0, display: 'flex',
            alignItems: 'center', justifyContent: 'center',
            background: 'rgba(8,12,20,0.8)', zIndex: 10, borderRadius: 12
          }}>
            <div className="spinner" />
          </div>
        )}
        <div ref={chartRef} style={{ width: '100%' }} />
      </div>

      {/* Fibonacci Levels */}
      {analysis?.fibonacci && (
        <div className="card" style={{ marginTop: 16 }}>
          <div className="section-title">
            <TrendingUp size={16} color="var(--accent)" />
            Fibonacci Analysis — {symbol}
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 8 }}>
            {analysis.fibonacci.retracement_levels?.map(level => (
              <div key={level.label} style={{
                textAlign: 'center', padding: '10px 6px', borderRadius: 8,
                background: analysis.fibonacci.nearest_support === level.price ||
                  analysis.fibonacci.nearest_resistance === level.price
                  ? 'var(--accent-dim)' : 'var(--bg-secondary)',
                border: `1px solid ${analysis.fibonacci.nearest_support === level.price ||
                  analysis.fibonacci.nearest_resistance === level.price
                  ? 'var(--accent)' : 'var(--border)'}`
              }}>
                <div style={{ fontSize: 10, color: 'var(--text-muted)', marginBottom: 4 }}>{level.label}</div>
                <div style={{ fontSize: 11, fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--text-primary)' }}>
                  ${level.price.toLocaleString('en-US', { maximumFractionDigits: 2 })}
                </div>
              </div>
            ))}
          </div>
          <div style={{ display: 'flex', gap: 20, marginTop: 12, paddingTop: 12, borderTop: '1px solid var(--border)' }}>
            <div>
              <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Signal: </span>
              <span className={`badge badge-${analysis.fibonacci.signal}`}>{analysis.fibonacci.signal}</span>
            </div>
            <div>
              <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Zone Score: </span>
              <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--accent)' }}>{(analysis.fibonacci.zone_score * 100).toFixed(0)}%</span>
            </div>
            <div>
              <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Swing High: </span>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>${analysis.fibonacci.swing_high?.toFixed(2)}</span>
            </div>
            <div>
              <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Swing Low: </span>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>${analysis.fibonacci.swing_low?.toFixed(2)}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
