import { useState, useEffect } from 'react'
import { Plus, Building2, Trash2, Settings2, ShieldCheck, ShieldAlert, RefreshCw } from 'lucide-react'
import { apiClient } from '@/api/client'
import { AccountSnapshot } from '@/models'
import { cn } from '../App'

interface Account extends AccountSnapshot {
  name?: string
  broker_id?: string
  status?: string
}

export function AccountManagement() {
  const [accounts, setAccounts] = useState<Account[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [showConfigModal, setShowConfigModal] = useState<Account | null>(null)
  const [newAccountId, setNewAccountId] = useState('')

  const [accountIds, setAccountIds] = useState<string[]>(['paper-01'])

  const fetchAccounts = async () => {
    try {
      setLoading(true)
      const results = await Promise.allSettled(
        accountIds.map(id => apiClient.get<AccountSnapshot>(`/accounts/${id}`))
      )
      const loaded: Account[] = results
        .filter((r): r is PromiseFulfilledResult<AccountSnapshot> => r.status === 'fulfilled')
        .map(r => ({
          ...r.value,
          name: r.value.account_id,
          broker_id: 'ibkr',
          status: 'ACTIVE',
        }))
      setAccounts(loaded)
    } catch {
      setAccounts([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAccounts()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accountIds])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    setAccountIds(prev => prev.includes(newAccountId) ? prev : [...prev, newAccountId])
    setShowModal(false)
    setNewAccountId('')
  }

  const handleDelete = (accountId: string) => {
    if (!confirm(`Are you sure you want to remove account ${accountId}?`)) return
    setAccountIds(prev => prev.filter(id => id !== accountId))
  }

  const handleSync = async (accountId: string) => {
    try {
      await apiClient.get<AccountSnapshot>(`/accounts/${accountId}`)
      fetchAccounts()
    } catch {
      alert('Sync failed. Make sure the broker gateway is connected.')
    }
  }

  return (
    <div className="space-y-4 h-full flex flex-col animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-baseline gap-3">
          <h1 className="text-lg font-bold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-accent to-purple-400 drop-shadow-[0_0_10px_rgba(0,240,255,0.3)]">Account Management</h1>
          <p className="text-xs text-muted">Manage broker connections and trading accounts</p>
        </div>
        <button onClick={() => setShowModal(true)} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" />
          Add Account
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {loading && accounts.length === 0 && (
          <div className="col-span-full text-center text-muted py-12">Loading accounts…</div>
        )}
        {!loading && accounts.length === 0 && (
          <div className="col-span-full text-center text-muted py-12 italic">
            No accounts configured. Click "Add Account" to connect a broker.
          </div>
        )}
        {accounts.map((acc) => (
          <div key={acc.account_id} className="card flex flex-col group hover:border-accent/50 transition-all duration-300 relative overflow-hidden">
            <div className="absolute -inset-2 bg-gradient-to-r from-accent/0 via-accent/5 to-accent/0 opacity-0 group-hover:opacity-100 blur-xl transition-opacity duration-500 pointer-events-none" />

            <div className="flex items-start justify-between mb-4 relative z-10">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center">
                  <Building2 className={cn("w-5 h-5", acc.broker_id?.includes('ibkr') ? "text-danger" : "text-accent")} />
                </div>
                <div>
                  <h3 className="font-bold text-base text-foreground group-hover:text-accent transition-colors drop-shadow-[0_0_8px_rgba(0,240,255,0)] group-hover:drop-shadow-[0_0_8px_rgba(0,240,255,0.5)]">{acc.account_id}</h3>
                  <code className="text-[10px] text-muted font-mono">{acc.broker_id ?? 'ibkr'}</code>
                </div>
              </div>
              <StatusBadge status={acc.status ?? 'UNKNOWN'} />
            </div>

            <div className="flex-1 space-y-3 mb-4 relative z-10">
              <div className="text-xs text-muted uppercase tracking-wider font-semibold mb-2">Cash Balances</div>
              <div className="grid grid-cols-2 gap-2">
                {Object.entries(acc.cash).map(([currency, amount]) => (
                  <div key={currency} className="bg-black/40 p-2.5 rounded-xl border border-white/5">
                    <div className="text-[10px] text-muted uppercase tracking-wider mb-0.5">{currency}</div>
                    <div className="text-sm font-mono font-bold text-accent">
                      {Number(amount).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </div>
                  </div>
                ))}
                {Object.keys(acc.cash).length === 0 && (
                  <div className="col-span-2 text-xs text-muted italic">No cash balances reported</div>
                )}
              </div>
            </div>

            <div className="flex items-center gap-2 pt-3 border-t border-white/5 relative z-10">
              <button
                onClick={() => handleSync(acc.account_id)}
                className="p-2 text-muted hover:text-accent bg-white/5 hover:bg-accent/20 rounded-2xl transition-all border border-transparent hover:border-accent/30 hover:shadow-[0_0_10px_rgba(0,240,255,0.2)]"
                title="Sync from Broker"
              >
                <RefreshCw className="w-4 h-4" />
              </button>
              <button
                onClick={() => setShowConfigModal(acc)}
                className="flex-1 flex items-center justify-center gap-2 py-2 bg-white/5 hover:bg-accent/20 text-muted hover:text-accent rounded-2xl transition-all border border-transparent hover:border-accent/30 hover:shadow-[0_0_10px_rgba(0,240,255,0.2)]"
              >
                <Settings2 className="w-4 h-4" />
                <span className="text-xs font-semibold">Configure</span>
              </button>
              <button
                onClick={() => handleDelete(acc.account_id)}
                className="p-2 text-muted hover:text-danger bg-white/5 hover:bg-danger/20 rounded-2xl transition-all border border-transparent hover:border-danger/30 hover:shadow-[0_0_10px_rgba(255,0,60,0.2)]"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>
        ))}

        <button onClick={() => setShowModal(true)} className="card flex flex-col items-center justify-center gap-3 hover:border-accent/50 hover:bg-accent/5 transition-all duration-300 group border-dashed border-white/20 min-h-[200px]">
          <div className="w-12 h-12 rounded-full bg-white/5 flex items-center justify-center group-hover:scale-110 transition-transform duration-300 group-hover:shadow-[0_0_15px_rgba(0,240,255,0.4)]">
            <Plus className="w-6 h-6 text-muted group-hover:text-accent" />
          </div>
          <span className="font-semibold text-muted group-hover:text-accent">Connect New Broker</span>
        </button>
      </div>

      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="card w-full max-w-md p-6 bg-slate-900 border-accent/30 shadow-[0_0_50px_rgba(0,240,255,0.15)] animate-in zoom-in-95 duration-200">
            <h2 className="text-xl font-bold mb-6 text-transparent bg-clip-text bg-gradient-to-r from-accent to-purple-400">Connect New Broker</h2>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-muted uppercase tracking-widest mb-1.5">Account ID</label>
                <input
                  required
                  className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-sm focus:border-accent focus:outline-none transition-colors font-mono"
                  placeholder="e.g. DU123456"
                  value={newAccountId}
                  onChange={e => setNewAccountId(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-muted uppercase tracking-widest mb-1.5">Broker Type</label>
                <select className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-sm focus:border-accent focus:outline-none transition-colors">
                  <option value="ibkr">Interactive Brokers</option>
                  <option value="simulated">Paper Trading (Simulated)</option>
                </select>
              </div>
              <div className="grid grid-cols-2 gap-4 pt-4">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="py-2.5 bg-white/5 hover:bg-white/10 text-foreground font-bold rounded-xl transition-all border border-white/5"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="py-2.5 bg-accent/20 hover:bg-accent/30 text-accent font-bold rounded-xl transition-all border border-accent/30 shadow-[0_0_15px_rgba(0,240,255,0.1)]"
                >
                  Confirm Connection
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showConfigModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="card w-full max-w-lg p-8 bg-slate-900 border-accent/30 shadow-[0_0_50px_rgba(0,240,255,0.15)] animate-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between mb-8">
              <h2 className="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-accent to-purple-400">
                Broker Config: {showConfigModal.account_id}
              </h2>
              <button
                onClick={() => setShowConfigModal(null)}
                className="text-muted hover:text-white transition-colors"
              >
                <Plus className="w-6 h-6 rotate-45" />
              </button>
            </div>

            <div className="space-y-6">
              <div className="p-4 bg-accent/5 border border-accent/20 rounded-2xl flex items-center gap-4">
                <div className="w-10 h-10 rounded-full bg-accent/10 flex items-center justify-center shrink-0">
                  <ShieldCheck className="w-5 h-5 text-accent" />
                </div>
                <div>
                  <div className="text-sm font-bold text-accent uppercase tracking-wider">Gateway Active</div>
                  <p className="text-[10px] text-slate-400">Live session established with {showConfigModal.broker_id} gateway.</p>
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-[10px] font-bold text-muted uppercase tracking-widest mb-1.5 ml-1">API Endpoint</label>
                  <input
                    readOnly
                    className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-xs text-slate-500 font-mono"
                    value="http://localhost:8000"
                  />
                </div>
              </div>

              <div className="pt-6 border-t border-white/5 flex gap-3">
                <button
                  onClick={() => setShowConfigModal(null)}
                  className="flex-1 py-2.5 bg-white/5 hover:bg-white/10 text-foreground font-bold rounded-xl transition-all border border-white/5"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  const isOk = status === 'ACTIVE'

  return (
    <span className={cn(
      "px-2.5 py-1 rounded-full text-[9px] font-bold border uppercase tracking-widest flex items-center gap-1.5 shadow-sm",
      isOk
        ? "bg-success/10 text-success border-success/30 shadow-[0_0_10px_rgba(57,255,20,0.15)] drop-shadow-[0_0_2px_rgba(57,255,20,0.8)]"
        : "bg-warning/10 text-warning border-warning/30 shadow-[0_0_10px_rgba(255,234,0,0.15)] drop-shadow-[0_0_2px_rgba(255,234,0,0.8)]"
    )}>
      {isOk ? <ShieldCheck className="w-3 h-3" /> : <ShieldAlert className="w-3 h-3 animate-pulse" />}
      {status.replace('_', ' ')}
    </span>
  )
}
