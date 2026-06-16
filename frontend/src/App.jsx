import React, { useState } from 'react'
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import {
  LayoutDashboard, TrendingUp, History, Brain,
  Shield, Settings, Bot, Activity, ChevronRight
} from 'lucide-react'
import Dashboard from './components/Dashboard.jsx'
import TradingChart from './components/TradingChart.jsx'
import TradeLog from './components/TradeLog.jsx'
import AIInsights from './components/AIInsights.jsx'
import RiskPanel from './components/RiskPanel.jsx'
import SettingsPage from './components/Settings.jsx'
import { useWebSocket } from './hooks/useWebSocket.js'

const NAV_ITEMS = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/chart', icon: TrendingUp, label: 'Live Chart' },
  { to: '/trades', icon: History, label: 'Trade Log' },
  { to: '/ai', icon: Brain, label: 'AI Insights' },
  { to: '/risk', icon: Shield, label: 'Risk Control' },
  { to: '/settings', icon: Settings, label: 'Settings' },
]

function Sidebar({ prices, botEnabled }) {
  return (
    <aside style={{
      position: 'fixed', left: 0, top: 0, bottom: 0,
      width: 'var(--sidebar-width)',
      background: 'var(--bg-secondary)',
      borderRight: '1px solid var(--border)',
      display: 'flex', flexDirection: 'column',
      zIndex: 50
    }}>
      {/* Logo */}
      <div style={{ padding: '20px 16px', borderBottom: '1px solid var(--border)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 36, height: 36, borderRadius: 10,
            background: 'linear-gradient(135deg, var(--accent), var(--purple))',
            display: 'flex', alignItems: 'center', justifyContent: 'center'
          }}>
            <Bot size={20} color="white" />
          </div>
          <div>
            <div style={{ fontWeight: 700, fontSize: 15, color: 'var(--text-primary)' }}>AutoTrader</div>
            <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>AI Bot v1.0</div>
          </div>
        </div>

        {/* Bot status */}
        <div style={{
          marginTop: 12, padding: '6px 10px', borderRadius: 8,
          background: botEnabled ? 'var(--green-dim)' : 'rgba(148,163,184,0.08)',
          display: 'flex', alignItems: 'center', gap: 8
        }}>
          <div style={{
            width: 7, height: 7, borderRadius: '50%',
            background: botEnabled ? 'var(--green)' : 'var(--text-muted)',
            boxShadow: botEnabled ? '0 0 8px var(--green)' : 'none',
            animation: botEnabled ? 'pulse-dot 2s infinite' : 'none'
          }} />
          <span style={{ fontSize: 11, color: botEnabled ? 'var(--green)' : 'var(--text-muted)', fontWeight: 600 }}>
            {botEnabled ? 'Bot Running' : 'Bot Stopped'}
          </span>
        </div>
      </div>

      {/* Navigation */}
      <nav style={{ flex: 1, padding: '12px 8px', overflowY: 'auto' }}>
        {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
          <NavLink key={to} to={to} end={to === '/'}
            style={({ isActive }) => ({
              display: 'flex', alignItems: 'center', gap: 10,
              padding: '9px 12px', borderRadius: 8,
              marginBottom: 2, textDecoration: 'none',
              color: isActive ? 'var(--accent-light)' : 'var(--text-secondary)',
              background: isActive ? 'var(--accent-dim)' : 'transparent',
              fontWeight: isActive ? 600 : 400,
              fontSize: 13, transition: 'all 0.15s'
            })}>
            <Icon size={16} />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Live Prices */}
      <div style={{ padding: '12px 12px', borderTop: '1px solid var(--border)' }}>
        <div style={{ fontSize: 10, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-muted)', marginBottom: 8 }}>
          Live Prices
        </div>
        {Object.entries(prices).map(([sym, data]) => (
          <div key={sym} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
            <span style={{ fontSize: 11, color: 'var(--text-secondary)', fontWeight: 600 }}>
              {sym.replace('/USDT', '')}
            </span>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>
                ${data.price?.toLocaleString('en-US', { maximumFractionDigits: 2 })}
              </div>
              <div style={{
                fontSize: 10, fontFamily: 'var(--font-mono)',
                color: (data.change_pct_24h || 0) >= 0 ? 'var(--green)' : 'var(--red)'
              }}>
                {(data.change_pct_24h || 0) >= 0 ? '+' : ''}{(data.change_pct_24h || 0).toFixed(2)}%
              </div>
            </div>
          </div>
        ))}
        <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginTop: 8 }}>
          <Activity size={10} color="var(--green)" />
          <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>Live • Updates every 5s</span>
        </div>
      </div>
    </aside>
  )
}

export default function App() {
  const { prices, isConnected } = useWebSocket()
  const [botEnabled, setBotEnabled] = useState(false)

  return (
    <BrowserRouter>
      <div className="app-layout">
        <Sidebar prices={prices} botEnabled={botEnabled} />
        <main className="main-content">
          {/* Top bar */}
          <header style={{
            height: 'var(--header-height)',
            background: 'var(--bg-secondary)',
            borderBottom: '1px solid var(--border)',
            display: 'flex', alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0 24px', flexShrink: 0
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--text-muted)', fontSize: 12 }}>
              <span>Binance</span>
              <ChevronRight size={12} />
              <span style={{ color: 'var(--text-secondary)' }}>Spot</span>
              <ChevronRight size={12} />
              <span style={{ color: 'var(--text-primary)' }}>BTC/USDT · ETH/USDT · SOL/USDT</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <div style={{
                  width: 7, height: 7, borderRadius: '50%',
                  background: isConnected ? 'var(--green)' : 'var(--red)',
                  boxShadow: isConnected ? '0 0 8px var(--green)' : 'none'
                }} />
                <span style={{ fontSize: 12, color: isConnected ? 'var(--green)' : 'var(--red)' }}>
                  {isConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
              <div style={{
                padding: '4px 10px', borderRadius: 6,
                background: 'var(--yellow-dim)', color: 'var(--yellow)',
                fontSize: 11, fontWeight: 600
              }}>
                🔒 READ-ONLY MODE
              </div>
            </div>
          </header>

          <div className="page-content">
            <Routes>
              <Route path="/" element={<Dashboard prices={prices} botEnabled={botEnabled} setBotEnabled={setBotEnabled} />} />
              <Route path="/chart" element={<TradingChart />} />
              <Route path="/trades" element={<TradeLog />} />
              <Route path="/ai" element={<AIInsights />} />
              <Route path="/risk" element={<RiskPanel />} />
              <Route path="/settings" element={<SettingsPage setBotEnabled={setBotEnabled} />} />
            </Routes>
          </div>
        </main>
      </div>
    </BrowserRouter>
  )
}
