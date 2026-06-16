import React, { useState } from 'react'
import { Brain, RefreshCw, TrendingUp, TrendingDown, Minus, Zap } from 'lucide-react'
import axios from 'axios'
import { useAnalytics } from '../hooks/useTrades.js'

const API = '/api'
const SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']

function SignalDetailCard({ sig }) {
  const rec = sig?.ai_recommendation || 'hold'
  const conf = sig?.ai_confidence || 0

  const recColor = rec === 'buy' ? 'var(--green)' : rec === 'sell' ? 'var(--red)' : 'var(--yellow)'
  const recBg = rec === 'buy' ? 'var(--green-dim)' : rec === 'sell' ? 'var(--red-dim)' : 'var(--yellow-dim)'
  const RecIcon = rec === 'buy' ? TrendingUp : rec === 'sell' ? TrendingDown : Minus

  return (
    <div className="card" style={{ borderColor: `${recColor}25` }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
        <div>
          <div style={{ fontSize: 16, fontWeight: 800 }}>{sig.symbol}</div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
            ${(sig.current_price || 0).toLocaleString('en-US', { maximumFractionDigits: 2 })}
          </div>
        </div>
        <div style={{
          display: 'flex', alignItems: 'center', gap: 8,
          padding: '8px 14px', borderRadius: 10,
          background: recBg, color: recColor
        }}>
          <RecIcon size={16} />
          <span style={{ fontWeight: 700, fontSize: 14, textTransform: 'uppercase' }}>{rec}</span>
        </div>
      </div>

      {/* Confidence Bar */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
          <span style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>
            AI Confidence
          </span>
          <span style={{ fontSize: 12, fontWeight: 700, color: recColor, fontFamily: 'var(--font-mono)' }}>
            {(conf * 100).toFixed(0)}%
          </span>
        </div>
        <div className="progress-bar">
          <div className="progress-fill" style={{
            width: `${conf * 100}%`,
            background: `linear-gradient(90deg, ${recColor}, ${recColor}88)`
          }} />
        </div>
      </div>

      {/* Signal Breakdown */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8, marginBottom: 16 }}>
        {[
          { label: 'Fibonacci', value: sig.fib_signal || 'N/A', icon: '📐' },
          { label: 'Pattern', value: sig.signal || 'N/A', icon: '🕯️' },
          { label: 'AI', value: sig.ai_recommendation || 'N/A', icon: '🤖' },
        ].map(item => (
          <div key={item.label} style={{
            padding: '8px', borderRadius: 8,
            background: 'var(--bg-secondary)',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: 16, marginBottom: 4 }}>{item.icon}</div>
            <div style={{ fontSize: 10, color: 'var(--text-muted)', marginBottom: 3 }}>{item.label}</div>
            <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-primary)', textTransform: 'uppercase' }}>
              {item.value}
            </div>
          </div>
        ))}
      </div>

      {/* Technical Data */}
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
        {sig.rsi && (
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>RSI</div>
            <div style={{
              fontSize: 14, fontWeight: 700, fontFamily: 'var(--font-mono)',
              color: sig.rsi < 30 ? 'var(--green)' : sig.rsi > 70 ? 'var(--red)' : 'var(--text-primary)'
            }}>
              {sig.rsi.toFixed(1)}
            </div>
          </div>
        )}
        {sig.trend && (
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>Trend</div>
            <div style={{ fontSize: 12, fontWeight: 600, color: sig.trend.includes('up') ? 'var(--green)' : sig.trend.includes('down') ? 'var(--red)' : 'var(--yellow)' }}>
              {sig.trend.replace('_', ' ')}
            </div>
          </div>
        )}
        {sig.strength !== undefined && (
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>Strength</div>
            <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--purple)', fontFamily: 'var(--font-mono)' }}>
              {sig.strength}/3
            </div>
          </div>
        )}
      </div>

      {/* Patterns */}
      {sig.patterns && sig.patterns.length > 0 && (
        <div style={{ marginTop: 12, paddingTop: 12, borderTop: '1px solid var(--border)' }}>
          <div style={{ fontSize: 10, color: 'var(--text-muted)', fontWeight: 600, marginBottom: 6 }}>DETECTED PATTERNS</div>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {sig.patterns.map(p => (
              <span key={p} style={{
                padding: '3px 9px', borderRadius: 20,
                background: 'var(--accent-dim)', color: 'var(--accent-light)',
                fontSize: 11, fontWeight: 500
              }}>
                {p}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* AI Reasoning */}
      {sig.ai_reasoning && (
        <div style={{ marginTop: 12, paddingTop: 12, borderTop: '1px solid var(--border)' }}>
          <div style={{ fontSize: 10, color: 'var(--text-muted)', fontWeight: 600, marginBottom: 6 }}>
            AI REASONING
          </div>
          <p style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
            {sig.ai_reasoning}
          </p>
        </div>
      )}

      {sig.timestamp && (
        <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 12 }}>
          Last updated: {new Date(sig.timestamp).toLocaleString()}
        </div>
      )}
    </div>
  )
}

export default function AIInsights() {
  const { signals, hasOpenRouterKey } = useAnalytics()
  const [analyzing, setAnalyzing] = useState(null)
  const [liveResult, setLiveResult] = useState({})

  const runLiveAnalysis = async (symbol) => {
    setAnalyzing(symbol)
    try {
      const sym = symbol.replace('/', '-')
      const { data } = await axios.get(`${API}/market/analyze/${sym}`)
      setLiveResult(prev => ({ ...prev, [symbol]: data }))
    } catch (e) {
      console.error(e)
    }
    setAnalyzing(null)
  }

  const displaySignals = SYMBOLS.map(sym => {
    const live = liveResult[sym]
    const cached = signals.find(s => s.symbol === sym)

    if (live) {
      return {
        symbol: sym,
        signal: live.overall_signal,
        strength: live.signal_strength,
        current_price: live.current_price,
        fib_signal: live.fibonacci?.signal,
        ai_recommendation: live.ai?.recommendation,
        ai_confidence: live.ai?.confidence,
        ai_reasoning: live.ai?.reasoning,
        rsi: live.patterns?.rsi,
        trend: live.patterns?.trend,
        patterns: live.patterns?.patterns,
        timestamp: live.timestamp
      }
    }
    return cached || { symbol: sym }
  })

  return (
    <div className="fade-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 800, display: 'flex', alignItems: 'center', gap: 10 }}>
            <Brain size={24} color="var(--purple)" />
            AI Insights
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 4 }}>
            OpenRouter AI analysis with Fibonacci + pattern data
          </p>
        </div>
      </div>

      {/* Quick Analyze Buttons */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 20, flexWrap: 'wrap' }}>
        {SYMBOLS.map(sym => (
          <button key={sym} onClick={() => runLiveAnalysis(sym)}
            className="btn btn-primary" disabled={analyzing === sym}>
            {analyzing === sym ? (
              <RefreshCw size={14} style={{ animation: 'spin 0.8s linear infinite' }} />
            ) : (
              <Zap size={14} />
            )}
            Analyze {sym.replace('/USDT', '')}
          </button>
        ))}
      </div>

      {/* Signal Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
        {displaySignals.map(sig => (
          <SignalDetailCard key={sig.symbol} sig={sig} />
        ))}
      </div>

      {/* Note about OpenRouter */}
      {!hasOpenRouterKey && (
        <div style={{
          marginTop: 20, padding: 16, borderRadius: 10,
          background: 'var(--yellow-dim)', border: '1px solid rgba(245,158,11,0.2)'
        }}>
          <div style={{ fontWeight: 600, color: 'var(--yellow)', marginBottom: 4 }}>
            ⚠️ AI Analysis requires OpenRouter API Key
          </div>
          <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
            Add your OpenRouter API key to the .env file (OPENROUTER_API_KEY) to enable AI-powered recommendations.
            Fibonacci and pattern analysis work without it.
          </div>
        </div>
      )}
    </div>
  )
}
