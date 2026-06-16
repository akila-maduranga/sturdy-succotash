import React, { useState, useEffect } from 'react'
import {
  DollarSign, TrendingUp, TrendingDown, Activity,
  Zap, BarChart2, RefreshCw, Play, Square
} from 'lucide-react'
import axios from 'axios'
import { useAnalytics, useBalance } from '../hooks/useTrades.js'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

const API = '/api'

function StatCard({ label, value, change, icon: Icon, color, prefix = '', suffix = '' }) {
  const isPos = typeof change === 'number' ? change >= 0 : null
  return (
    <div className="stat-card fade-in">
      <div className="stat-label">{label}</div>
      <div className="stat-value" style={{ color: color || 'var(--text-primary)' }}>
        {prefix}{typeof value === 'number' ? value.toLocaleString('en-US', { maximumFractionDigits: 4 }) : value}{suffix}
      </div>
      {typeof change === 'number' && (
        <div className="stat-change" style={{ color: isPos ? 'var(--green)' : 'var(--red)' }}>
          {isPos ? '▲' : '▼'} {Math.abs(change).toFixed(2)}%
        </div>
      )}
      {Icon && (
        <div className="stat-icon" style={{ background: `${color || 'var(--accent)'}20` }}>
          <Icon size={18} color={color || 'var(--accent)'} />
        </div>
      )}
    </div>
  )
}

function SignalCard({ signal }) {
  const colors = { buy: 'var(--green)', sell: 'var(--red)', neutral: 'var(--yellow)', hold: 'var(--yellow)' }
  const color = colors[signal?.signal || 'neutral'] || 'var(--yellow)'
  const strength = signal?.strength || 0

  return (
    <div className="card" style={{ borderColor: `${color}30` }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
        <div>
          <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>{signal?.symbol}</div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
            ${(signal?.current_price || 0).toLocaleString('en-US', { maximumFractionDigits: 2 })}
          </div>
        </div>
        <span className={`badge badge-${signal?.signal || 'neutral'}`}>
          {(signal?.signal || 'neutral').toUpperCase()}
        </span>
      </div>

      {/* Signal Strength Bars */}
      <div style={{ marginBottom: 10 }}>
        <div style={{ fontSize: 10, color: 'var(--text-muted)', marginBottom: 6, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
          Signal Strength {strength}/3
        </div>
        <div style={{ display: 'flex', gap: 4 }}>
          {[1, 2, 3].map(i => (
            <div key={i} style={{
              flex: 1, height: 5, borderRadius: 3,
              background: i <= strength ? color : 'var(--border)',
              transition: 'background 0.3s'
            }} />
          ))}
        </div>
      </div>

      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
        {signal?.fib_signal && (
          <span style={{ fontSize: 10, padding: '2px 7px', borderRadius: 10, background: 'var(--accent-dim)', color: 'var(--accent-light)' }}>
            Fib: {signal.fib_signal}
          </span>
        )}
        {signal?.trend && (
          <span style={{ fontSize: 10, padding: '2px 7px', borderRadius: 10, background: 'rgba(148,163,184,0.08)', color: 'var(--text-secondary)' }}>
            {signal.trend}
          </span>
        )}
        {signal?.rsi && (
          <span style={{ fontSize: 10, padding: '2px 7px', borderRadius: 10, background: 'rgba(148,163,184,0.08)', color: 'var(--text-secondary)' }}>
            RSI: {signal.rsi?.toFixed(0)}
          </span>
        )}
      </div>
    </div>
  )
}

export default function Dashboard({ prices, botEnabled, setBotEnabled }) {
  const { performance, signals, pnlHistory } = useAnalytics()
  const { balance } = useBalance()
  const [analyzing, setAnalyzing] = useState(false)

  const handleAnalyze = async () => {
    setAnalyzing(true)
    try {
      await axios.post(`${API}/settings/trigger-analysis`)
      setTimeout(() => window.location.reload(), 3000)
    } catch (e) {
      console.error(e)
    }
    setTimeout(() => setAnalyzing(false), 5000)
  }

  const totalBalance = balance?.total_usdt ?? 10.0
  const pnlTotal = performance?.total_pnl ?? 0
  const pnlPct = ((pnlTotal / 10.0) * 100)

  return (
    <div className="fade-in">
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 800, color: 'var(--text-primary)' }}>
            Trading Dashboard
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 4 }}>
            AI-powered Fibonacci spot trading · Binance
          </p>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn btn-ghost" onClick={handleAnalyze} disabled={analyzing}>
            <RefreshCw size={14} style={{ animation: analyzing ? 'spin 0.8s linear infinite' : 'none' }} />
            {analyzing ? 'Analyzing...' : 'Run Analysis'}
          </button>
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid-4" style={{ marginBottom: 20 }}>
        <StatCard
          label="Total Balance"
          value={totalBalance.toFixed(4)}
          prefix="$"
          icon={DollarSign}
          color="var(--accent)"
          change={pnlPct}
        />
        <StatCard
          label="Total P&L"
          value={`${pnlTotal >= 0 ? '+' : ''}${pnlTotal.toFixed(4)}`}
          prefix="$"
          icon={pnlTotal >= 0 ? TrendingUp : TrendingDown}
          color={pnlTotal >= 0 ? 'var(--green)' : 'var(--red)'}
        />
        <StatCard
          label="Win Rate"
          value={((performance?.win_rate ?? 0) * 100).toFixed(1)}
          suffix="%"
          icon={Activity}
          color="var(--purple)"
        />
        <StatCard
          label="Total Trades"
          value={performance?.total_trades ?? 0}
          icon={BarChart2}
          color="var(--yellow)"
        />
      </div>

      {/* Signals + Chart */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 20 }}>
        {/* Market Signals */}
        <div>
          <div className="section-title">
            <Zap size={16} color="var(--accent)" />
            Market Signals
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {signals.length > 0 ? signals.map(s => (
              <SignalCard key={s.symbol} signal={s} />
            )) : (
              ['BTC/USDT', 'ETH/USDT', 'SOL/USDT'].map(sym => (
                <div key={sym} className="card" style={{ opacity: 0.6 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ fontWeight: 700 }}>{sym}</div>
                    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                      <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                        ${(prices[sym]?.price || 0).toLocaleString('en-US', { maximumFractionDigits: 2 })}
                      </div>
                      <span className="badge badge-neutral">NEUTRAL</span>
                    </div>
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 8 }}>
                    Click "Run Analysis" to get signals
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* P&L Chart */}
        <div className="card">
          <div className="section-title">
            <TrendingUp size={16} color="var(--green)" />
            Portfolio Growth
          </div>
          {pnlHistory.length > 1 ? (
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={pnlHistory} margin={{ top: 5, right: 5, left: 0, bottom: 5 }}>
                <defs>
                  <linearGradient id="balanceGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--accent)" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="var(--accent)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="date" tick={{ fill: 'var(--text-muted)', fontSize: 10 }} tickLine={false} axisLine={false} />
                <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 10 }} tickLine={false} axisLine={false} tickFormatter={v => `$${v.toFixed(2)}`} />
                <Tooltip
                  contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8 }}
                  labelStyle={{ color: 'var(--text-secondary)' }}
                  formatter={(v) => [`$${v.toFixed(4)}`, 'Balance']}
                />
                <Area type="monotone" dataKey="balance" stroke="var(--accent)" fill="url(#balanceGrad)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ height: 220, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
              <div style={{ textAlign: 'center' }}>
                <TrendingUp size={40} style={{ opacity: 0.2, marginBottom: 12 }} />
                <div>No trade history yet</div>
                <div style={{ fontSize: 12, marginTop: 6 }}>P&L chart will appear after first trades</div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Performance Details */}
      {performance && performance.total_trades > 0 && (
        <div className="card">
          <div className="section-title">
            <Activity size={16} color="var(--purple)" />
            Performance Metrics
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: 16 }}>
            {[
              { label: 'Winning', value: performance.winning_trades, color: 'var(--green)' },
              { label: 'Losing', value: performance.losing_trades, color: 'var(--red)' },
              { label: 'Avg P&L', value: `$${performance.avg_pnl?.toFixed(4)}`, color: 'var(--text-primary)' },
              { label: 'Best Trade', value: `$${performance.best_trade_pnl?.toFixed(4)}`, color: 'var(--green)' },
              { label: 'Worst Trade', value: `$${performance.worst_trade_pnl?.toFixed(4)}`, color: 'var(--red)' },
              { label: 'Profit Factor', value: performance.profit_factor?.toFixed(2), color: 'var(--purple)' },
            ].map(m => (
              <div key={m.label} style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 10, color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', marginBottom: 6 }}>{m.label}</div>
                <div style={{ fontSize: 18, fontWeight: 700, color: m.color, fontFamily: 'var(--font-mono)' }}>{m.value}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
