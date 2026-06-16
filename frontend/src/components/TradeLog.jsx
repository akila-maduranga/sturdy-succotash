import React, { useState } from 'react'
import { History, X, TrendingUp, TrendingDown } from 'lucide-react'
import { useTrades } from '../hooks/useTrades.js'

function TradeRow({ trade, onClose }) {
  const isPnlPos = (trade.pnl || 0) >= 0
  const isOpen = trade.status === 'open'

  return (
    <tr>
      <td>
        <div style={{ fontWeight: 600, fontSize: 13 }}>{trade.symbol}</div>
        <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
          {new Date(trade.opened_at).toLocaleString()}
        </div>
      </td>
      <td>
        <span className={`badge badge-${trade.side}`}>{trade.side.toUpperCase()}</span>
      </td>
      <td>
        <span className={`badge badge-${trade.status}`}>{trade.status.toUpperCase()}</span>
      </td>
      <td className="mono" style={{ fontSize: 12 }}>
        ${(trade.entry_price || 0).toLocaleString('en-US', { maximumFractionDigits: 4 })}
      </td>
      <td className="mono" style={{ fontSize: 12 }}>
        {trade.exit_price
          ? `$${trade.exit_price.toLocaleString('en-US', { maximumFractionDigits: 4 })}`
          : <span style={{ color: 'var(--text-muted)' }}>—</span>
        }
      </td>
      <td className="mono" style={{ fontSize: 12 }}>
        {trade.quantity.toFixed(5)}
      </td>
      <td>
        {trade.pnl !== null && trade.pnl !== undefined ? (
          <div>
            <div className="mono" style={{ color: isPnlPos ? 'var(--green)' : 'var(--red)', fontWeight: 600 }}>
              {isPnlPos ? '+' : ''}${trade.pnl.toFixed(4)}
            </div>
            <div style={{ fontSize: 10, color: isPnlPos ? 'var(--green)' : 'var(--red)' }}>
              {isPnlPos ? '+' : ''}{((trade.pnl_percent || 0) * 100).toFixed(2)}%
            </div>
          </div>
        ) : (
          <span style={{ color: 'var(--text-muted)' }}>—</span>
        )}
      </td>
      <td>
        <div style={{ display: 'flex', gap: 6 }}>
          {trade.ai_confidence && (
            <div style={{
              padding: '3px 8px', borderRadius: 6,
              background: 'var(--accent-dim)', fontSize: 11,
              color: 'var(--accent-light)', fontWeight: 600
            }}>
              AI {(trade.ai_confidence * 100).toFixed(0)}%
            </div>
          )}
          {trade.signal_strength > 0 && (
            <div style={{
              padding: '3px 8px', borderRadius: 6,
              background: 'rgba(168,85,247,0.15)', fontSize: 11,
              color: 'var(--purple)', fontWeight: 600
            }}>
              {trade.signal_strength}/3
            </div>
          )}
        </div>
      </td>
      <td>
        {isOpen && (
          <button
            onClick={() => onClose(trade.id)}
            className="btn btn-danger"
            style={{ padding: '4px 10px', fontSize: 11 }}
          >
            <X size={12} /> Close
          </button>
        )}
      </td>
    </tr>
  )
}

export default function TradeLog() {
  const { trades, stats, loading, closeTrade } = useTrades()
  const [filter, setFilter] = useState('all')

  const filtered = filter === 'all' ? trades : trades.filter(t => t.status === filter)

  return (
    <div className="fade-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 800 }}>Trade Log</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 4 }}>All executed and open trades</p>
        </div>
        {stats && (
          <div style={{ display: 'flex', gap: 12 }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--accent)' }}>{stats.total}</div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Total</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--green)' }}>{stats.open}</div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Open</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-secondary)' }}>{stats.closed}</div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Closed</div>
            </div>
          </div>
        )}
      </div>

      {/* Filter */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        {['all', 'open', 'closed'].map(f => (
          <button key={f} onClick={() => setFilter(f)}
            style={{
              padding: '6px 14px', borderRadius: 8, border: 'none',
              cursor: 'pointer', fontSize: 12, fontWeight: 600, fontFamily: 'var(--font-sans)',
              background: filter === f ? 'var(--accent)' : 'var(--bg-card)',
              color: filter === f ? 'white' : 'var(--text-secondary)',
              transition: 'all 0.2s'
            }}>
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        {loading ? (
          <div style={{ padding: 40, display: 'flex', justifyContent: 'center' }}>
            <div className="spinner" />
          </div>
        ) : filtered.length === 0 ? (
          <div style={{ padding: 60, textAlign: 'center', color: 'var(--text-muted)' }}>
            <History size={40} style={{ opacity: 0.2, marginBottom: 12 }} />
            <div style={{ fontSize: 15 }}>No trades yet</div>
            <div style={{ fontSize: 12, marginTop: 6 }}>
              {filter === 'open' ? 'No open positions' : 'Trade history will appear here'}
            </div>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Symbol / Time</th>
                  <th>Side</th>
                  <th>Status</th>
                  <th>Entry</th>
                  <th>Exit</th>
                  <th>Quantity</th>
                  <th>P&L</th>
                  <th>Signals</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map(t => (
                  <TradeRow key={t.id} trade={t} onClose={closeTrade} />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
