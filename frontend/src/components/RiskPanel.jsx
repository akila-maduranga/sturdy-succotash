import React, { useState, useEffect } from 'react'
import { Shield, AlertTriangle, Info, DollarSign } from 'lucide-react'
import axios from 'axios'

const API = '/api'

export default function RiskPanel() {
  const [settings, setSettings] = useState(null)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [local, setLocal] = useState({})

  useEffect(() => {
    axios.get(`${API}/settings`).then(({ data }) => {
      setSettings(data)
      setLocal({
        max_risk_per_trade: data.max_risk_per_trade,
        daily_loss_limit: data.daily_loss_limit,
        min_ai_confidence: data.min_ai_confidence,
        min_signal_strength: data.min_signal_strength,
      })
    })
  }, [])

  const save = async () => {
    setSaving(true)
    try {
      await axios.patch(`${API}/settings`, local)
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch (e) {
      console.error(e)
    }
    setSaving(false)
  }

  const BALANCE = 10.0
  const maxLossPerTrade = BALANCE * (local.max_risk_per_trade || 0.02)
  const dailyStopLoss = BALANCE * (local.daily_loss_limit || 0.05)

  if (!settings) return (
    <div style={{ display: 'flex', justifyContent: 'center', padding: 60 }}>
      <div className="spinner" />
    </div>
  )

  return (
    <div className="fade-in">
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 800, display: 'flex', alignItems: 'center', gap: 10 }}>
          <Shield size={24} color="var(--green)" />
          Risk Control
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 4 }}>
          Configure position sizing and loss limits
        </p>
      </div>

      {/* Read Only Warning */}
      {settings.read_only_mode && (
        <div style={{
          padding: '12px 16px', borderRadius: 10, marginBottom: 20,
          background: 'var(--yellow-dim)', border: '1px solid rgba(245,158,11,0.2)',
          display: 'flex', alignItems: 'center', gap: 10
        }}>
          <AlertTriangle size={16} color="var(--yellow)" />
          <div>
            <div style={{ fontWeight: 600, color: 'var(--yellow)', fontSize: 13 }}>
              Read-Only Mode — Bot Cannot Execute Trades
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>
              Add EXCHANGE_API_SECRET to .env and set READ_ONLY=false to enable live trading
            </div>
          </div>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        {/* Risk Calculator */}
        <div>
          <div className="card" style={{ marginBottom: 16 }}>
            <div className="section-title">
              <DollarSign size={16} color="var(--accent)" />
              Risk Calculator — $10 Balance
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 20 }}>
              <div style={{ padding: 16, borderRadius: 10, background: 'var(--bg-secondary)', textAlign: 'center' }}>
                <div style={{ fontSize: 10, color: 'var(--text-muted)', marginBottom: 6, fontWeight: 600 }}>MAX LOSS / TRADE</div>
                <div style={{ fontSize: 24, fontWeight: 800, color: 'var(--red)', fontFamily: 'var(--font-mono)' }}>
                  ${maxLossPerTrade.toFixed(2)}
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
                  {((local.max_risk_per_trade || 0.02) * 100).toFixed(1)}% of balance
                </div>
              </div>
              <div style={{ padding: 16, borderRadius: 10, background: 'var(--bg-secondary)', textAlign: 'center' }}>
                <div style={{ fontSize: 10, color: 'var(--text-muted)', marginBottom: 6, fontWeight: 600 }}>DAILY STOP LOSS</div>
                <div style={{ fontSize: 24, fontWeight: 800, color: 'var(--orange)', fontFamily: 'var(--font-mono)' }}>
                  ${dailyStopLoss.toFixed(2)}
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
                  {((local.daily_loss_limit || 0.05) * 100).toFixed(0)}% daily limit
                </div>
              </div>
            </div>

            <div style={{ padding: 12, borderRadius: 8, background: 'var(--green-dim)', border: '1px solid rgba(16,185,129,0.2)' }}>
              <div style={{ fontSize: 12, color: 'var(--green)', fontWeight: 600, marginBottom: 4 }}>
                ✅ Risk Management Active
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
                • Kelly Criterion position sizing<br />
                • ATR-based stop losses (1.5x ATR)<br />
                • Minimum 2:1 risk/reward ratio<br />
                • Auto-pause if daily limit breached<br />
                • Binance minimum order validation
              </div>
            </div>
          </div>
        </div>

        {/* Settings */}
        <div className="card">
          <div className="section-title">
            <Shield size={16} color="var(--green)" />
            Risk Parameters
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
            {/* Risk Per Trade */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                <label style={{ fontSize: 13, fontWeight: 600 }}>Max Risk Per Trade</label>
                <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--accent)', fontFamily: 'var(--font-mono)' }}>
                  {((local.max_risk_per_trade || 0.02) * 100).toFixed(1)}%
                </span>
              </div>
              <input type="range" min="0.5" max="5" step="0.5"
                value={(local.max_risk_per_trade || 0.02) * 100}
                onChange={e => setLocal(p => ({ ...p, max_risk_per_trade: e.target.value / 100 }))}
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: 'var(--text-muted)', marginTop: 4 }}>
                <span>0.5% (Conservative)</span>
                <span>5% (Aggressive)</span>
              </div>
            </div>

            {/* Daily Loss Limit */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                <label style={{ fontSize: 13, fontWeight: 600 }}>Daily Loss Limit</label>
                <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--red)', fontFamily: 'var(--font-mono)' }}>
                  {((local.daily_loss_limit || 0.05) * 100).toFixed(0)}%
                </span>
              </div>
              <input type="range" min="1" max="20" step="1"
                value={(local.daily_loss_limit || 0.05) * 100}
                onChange={e => setLocal(p => ({ ...p, daily_loss_limit: e.target.value / 100 }))}
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: 'var(--text-muted)', marginTop: 4 }}>
                <span>1% (Strict)</span>
                <span>20% (Loose)</span>
              </div>
            </div>

            {/* Min AI Confidence */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                <label style={{ fontSize: 13, fontWeight: 600 }}>Min AI Confidence</label>
                <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--purple)', fontFamily: 'var(--font-mono)' }}>
                  {((local.min_ai_confidence || 0.70) * 100).toFixed(0)}%
                </span>
              </div>
              <input type="range" min="50" max="95" step="5"
                value={(local.min_ai_confidence || 0.70) * 100}
                onChange={e => setLocal(p => ({ ...p, min_ai_confidence: e.target.value / 100 }))}
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: 'var(--text-muted)', marginTop: 4 }}>
                <span>50% (More trades)</span>
                <span>95% (Selective)</span>
              </div>
            </div>

            {/* Min Signal Strength */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                <label style={{ fontSize: 13, fontWeight: 600 }}>Min Signal Strength</label>
                <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--yellow)', fontFamily: 'var(--font-mono)' }}>
                  {local.min_signal_strength || 2}/3
                </span>
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                {[1, 2, 3].map(v => (
                  <button key={v} onClick={() => setLocal(p => ({ ...p, min_signal_strength: v }))}
                    style={{
                      flex: 1, padding: '8px', borderRadius: 8, border: 'none',
                      cursor: 'pointer', fontSize: 12, fontWeight: 700,
                      fontFamily: 'var(--font-sans)',
                      background: (local.min_signal_strength || 2) === v ? 'var(--accent)' : 'var(--bg-secondary)',
                      color: (local.min_signal_strength || 2) === v ? 'white' : 'var(--text-secondary)',
                    }}>
                    {v}/3
                  </button>
                ))}
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 6 }}>
                2/3 = Fib + Pattern OR Fib + AI must agree. 3/3 = All signals must agree.
              </div>
            </div>

            <button className="btn btn-success" onClick={save} disabled={saving}>
              {saved ? '✅ Saved!' : saving ? 'Saving...' : 'Save Risk Settings'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
