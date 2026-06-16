import React, { useState, useEffect } from 'react'
import { Settings, Key, Bot, AlertTriangle, CheckCircle, ExternalLink } from 'lucide-react'
import axios from 'axios'

const API = '/api'

export default function SettingsPage({ setBotEnabled }) {
  const [settings, setSettings] = useState(null)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')
  const [local, setLocal] = useState({})
  const [health, setHealth] = useState(null)

  useEffect(() => {
    Promise.all([
      axios.get(`${API}/settings`),
      axios.get(`${API}/health`)
    ]).then(([s, h]) => {
      setSettings(s.data)
      setHealth(h.data)
      setLocal({
        bot_enabled: s.data.bot_enabled,
        trading_pairs: s.data.trading_pairs,
        ai_model: s.data.ai_model,
      })
    }).catch(console.error)
  }, [])

  const save = async () => {
    setSaving(true)
    setError('')
    try {
      const { data } = await axios.patch(`${API}/settings`, local)
      setSettings(data)
      setBotEnabled(data.bot_enabled)
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to save settings')
    }
    setSaving(false)
  }

  const AI_MODELS = [
    { value: 'google/gemini-flash-1.5', label: 'Gemini Flash 1.5 (Fast, Cheap)' },
    { value: 'anthropic/claude-3.5-haiku', label: 'Claude 3.5 Haiku (Best Analysis)' },
    { value: 'openai/gpt-4o-mini', label: 'GPT-4o Mini (Balanced)' },
    { value: 'meta-llama/llama-3.1-8b-instruct:free', label: 'Llama 3.1 8B (Free)' },
  ]

  if (!settings) return (
    <div style={{ display: 'flex', justifyContent: 'center', padding: 60 }}>
      <div className="spinner" />
    </div>
  )

  return (
    <div className="fade-in">
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 800, display: 'flex', alignItems: 'center', gap: 10 }}>
          <Settings size={24} color="var(--accent)" />
          Settings
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 4 }}>
          Bot configuration and API settings
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        {/* System Status */}
        <div className="card">
          <div className="section-title">
            <Bot size={16} color="var(--green)" />
            System Status
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {[
              { label: 'Exchange', value: health?.exchange || 'Binance', icon: '🏦', ok: true },
              { label: 'API Mode', value: settings.read_only_mode ? '🔒 Read Only' : '⚡ Trading', icon: '🔑', ok: !settings.read_only_mode },
              { label: 'Bot Status', value: settings.bot_enabled ? 'Running' : 'Stopped', icon: '🤖', ok: settings.bot_enabled },
              { label: 'OpenRouter AI', value: 'Check .env', icon: '🧠', ok: false },
            ].map(item => (
              <div key={item.label} style={{
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                padding: '10px 12px', borderRadius: 8, background: 'var(--bg-secondary)'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span>{item.icon}</span>
                  <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{item.label}</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span style={{ fontSize: 12, fontWeight: 600, color: item.ok ? 'var(--green)' : 'var(--yellow)' }}>
                    {item.value}
                  </span>
                  {item.ok
                    ? <CheckCircle size={14} color="var(--green)" />
                    : <AlertTriangle size={14} color="var(--yellow)" />
                  }
                </div>
              </div>
            ))}
          </div>

          {/* Bot Toggle */}
          <div style={{ marginTop: 20, padding: 16, borderRadius: 10, background: 'var(--bg-secondary)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
              <div>
                <div style={{ fontWeight: 700, fontSize: 14 }}>Auto Trading</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                  {settings.read_only_mode ? 'Requires trading API key' : 'Enable to auto-execute signals'}
                </div>
              </div>
              <label className="toggle">
                <input type="checkbox"
                  checked={local.bot_enabled || false}
                  disabled={settings.read_only_mode}
                  onChange={e => setLocal(p => ({ ...p, bot_enabled: e.target.checked }))}
                />
                <span className="toggle-slider" />
              </label>
            </div>
            {settings.read_only_mode && (
              <div style={{ fontSize: 11, color: 'var(--yellow)', padding: '8px 10px', borderRadius: 6, background: 'var(--yellow-dim)' }}>
                ⚠️ Add EXCHANGE_API_SECRET and set READ_ONLY=false in .env to enable live trading
              </div>
            )}
          </div>
        </div>

        {/* Bot Config */}
        <div className="card">
          <div className="section-title">
            <Settings size={16} color="var(--accent)" />
            Bot Configuration
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {/* Trading Pairs */}
            <div>
              <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: 6 }}>
                Trading Pairs (comma-separated)
              </label>
              <input className="input"
                value={local.trading_pairs || ''}
                onChange={e => setLocal(p => ({ ...p, trading_pairs: e.target.value }))}
                placeholder="BTC/USDT,ETH/USDT,SOL/USDT"
              />
            </div>

            {/* AI Model */}
            <div>
              <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: 6 }}>
                OpenRouter AI Model
              </label>
              <select className="input"
                value={local.ai_model || ''}
                onChange={e => setLocal(p => ({ ...p, ai_model: e.target.value }))}
                style={{ cursor: 'pointer' }}>
                {AI_MODELS.map(m => (
                  <option key={m.value} value={m.value}>{m.label}</option>
                ))}
              </select>
            </div>

            {error && (
              <div style={{ padding: '10px 12px', borderRadius: 8, background: 'var(--red-dim)', color: 'var(--red)', fontSize: 12 }}>
                ❌ {error}
              </div>
            )}

            <button className="btn btn-primary" onClick={save} disabled={saving}>
              {saved ? '✅ Saved!' : saving ? 'Saving...' : 'Save Configuration'}
            </button>
          </div>
        </div>

        {/* Setup Guide */}
        <div className="card" style={{ gridColumn: '1 / -1' }}>
          <div className="section-title">
            <Key size={16} color="var(--yellow)" />
            Setup Guide
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
            {[
              {
                step: '1',
                title: 'Add OpenRouter API Key',
                desc: 'Get an API key from openrouter.ai and add OPENROUTER_API_KEY to your .env file',
                color: 'var(--accent)',
                link: 'https://openrouter.ai'
              },
              {
                step: '2',
                title: 'Enable Trading API',
                desc: 'Create a Binance API key with Spot trading enabled, add secret to .env, set READ_ONLY=false',
                color: 'var(--yellow)',
                link: 'https://www.binance.com/en/my/settings/api-management'
              },
              {
                step: '3',
                title: 'Enable the Bot',
                desc: 'Once keys are configured, toggle "Auto Trading" above. Bot checks signals every 5 minutes.',
                color: 'var(--green)',
                link: null
              }
            ].map(s => (
              <div key={s.step} style={{ padding: 16, borderRadius: 10, background: 'var(--bg-secondary)', border: `1px solid ${s.color}25` }}>
                <div style={{ width: 28, height: 28, borderRadius: 8, background: `${s.color}20`, color: s.color, fontWeight: 800, fontSize: 14, display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 10 }}>
                  {s.step}
                </div>
                <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 8 }}>{s.title}</div>
                <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.6 }}>{s.desc}</div>
                {s.link && (
                  <a href={s.link} target="_blank" rel="noopener noreferrer"
                    style={{ display: 'inline-flex', alignItems: 'center', gap: 4, marginTop: 10, fontSize: 11, color: s.color, textDecoration: 'none', fontWeight: 600 }}>
                    Open <ExternalLink size={11} />
                  </a>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
