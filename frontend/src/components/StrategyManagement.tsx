import { useState, useEffect } from 'react'
import { Play, Square, Settings2 } from 'lucide-react'
import { apiClient } from '@/api/client'
import { StrategyStatusEntry } from '@/models'

export function StrategyManagement() {
  const [strategies, setStrategies] = useState<StrategyStatusEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [newStrategy, setNewStrategy] = useState({
    strategy_id: '',
    strategy_name: 'EMA Cross',
    class_path: 'qts.user_strategies.ema_cross.strategy.EMAStrategy',
    parameters: { fast: 10, slow: 20 }
  })

  const fetchStrategies = async () => {
    try {
      setLoading(true)
      const data = await apiClient.get<StrategyStatusEntry[]>('/strategies')
      setStrategies(data)
    } catch {
      setStrategies([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStrategies()
  }, [])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await apiClient.post('/strategies/', newStrategy)
      setShowModal(false)
      fetchStrategies()
    } catch (error) {
      console.error('Create failed', error)
    }
  }

  const handleStart = async (id: string) => {
    try {
      await apiClient.post(`/strategies/${id}/start`)
      fetchStrategies()
    } catch (error) {
      console.error('Start failed', error)
    }
  }

  const handleStop = async (id: string) => {
    try {
      await apiClient.post(`/strategies/${id}/stop`)
      fetchStrategies()
    } catch (error) {
      console.error('Stop failed', error)
    }
  }

  const isActive = (status: string) => status.toUpperCase() === 'ACTIVE'

  return (
    <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight">Strategies</h1>
          <p className="text-muted mt-1">Manage and monitor your automated trading algorithms.</p>
        </div>
        <button onClick={() => setShowModal(true)} className="btn-primary">New Strategy Instance</button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {loading && strategies.length === 0 && (
          <div className="col-span-full text-center text-muted py-12">Loading strategies…</div>
        )}
        {!loading && strategies.length === 0 && (
          <div className="col-span-full text-center text-muted py-12 italic">
            No strategies deployed. Click "New Strategy Instance" to get started.
          </div>
        )}
        {strategies.map((strat) => (
          <div key={strat.strategy_id} className="card flex flex-col group hover:border-accent transition-all duration-300">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="font-bold text-lg">{strat.strategy_id}</h3>
                <code className="text-[10px] text-muted font-mono">{strat.strategy_id}</code>
              </div>
              <StatusBadge status={strat.status} />
            </div>

            <div className="flex-1 mb-4">
              <div className="text-xs text-muted uppercase tracking-wider font-semibold">Current State</div>
              <div className="mt-2 bg-slate-800/50 p-2.5 rounded-xl border border-slate-700/50">
                <div className="text-sm font-mono font-medium">{strat.status}</div>
              </div>
            </div>

            <div className="flex items-center gap-2 pt-4 border-t border-slate-800">
              {isActive(strat.status) ? (
                <button
                  onClick={() => handleStop(strat.strategy_id)}
                  className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-danger/10 text-danger hover:bg-danger/20 rounded-2xl transition-colors"
                >
                  <Square className="w-4 h-4 fill-current" />
                  <span className="text-sm font-semibold">Stop</span>
                </button>
              ) : (
                <button
                  onClick={() => handleStart(strat.strategy_id)}
                  className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-success/10 text-success hover:bg-success/20 rounded-2xl transition-colors"
                >
                  <Play className="w-4 h-4 fill-current" />
                  <span className="text-sm font-semibold">Start</span>
                </button>
              )}
              <button
                className="p-2.5 text-muted hover:text-foreground hover:bg-slate-800 rounded-2xl transition-all"
              >
                <Settings2 className="w-5 h-5" />
              </button>
            </div>
          </div>
        ))}
      </div>

      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="card w-full max-w-md p-6 bg-slate-900 border-accent/30 shadow-[0_0_50px_rgba(0,240,255,0.15)] animate-in zoom-in-95 duration-200">
            <h2 className="text-xl font-bold mb-6 text-transparent bg-clip-text bg-gradient-to-r from-accent to-purple-400">Deploy New Strategy</h2>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-muted uppercase tracking-widest mb-1.5">Instance ID</label>
                <input
                  required
                  className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-sm focus:border-accent focus:outline-none transition-colors font-mono"
                  placeholder="e.g. ema-cross-live-01"
                  value={newStrategy.strategy_id}
                  onChange={e => setNewStrategy({...newStrategy, strategy_id: e.target.value})}
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-muted uppercase tracking-widest mb-1.5">Strategy Template</label>
                <select
                  className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-sm focus:border-accent focus:outline-none transition-colors"
                  value={newStrategy.strategy_id}
                  onChange={() => {}}
                >
                  <option value="ema_cross">EMA Cross (v1.0.0)</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-bold text-muted uppercase tracking-widest mb-1.5">Parameters (JSON)</label>
                <textarea
                  className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-sm focus:border-accent focus:outline-none transition-colors font-mono min-h-[100px]"
                  value={JSON.stringify(newStrategy.parameters, null, 2)}
                  onChange={e => {
                    try {
                      setNewStrategy({...newStrategy, parameters: JSON.parse(e.target.value)})
                    } catch {
                      // ignore parse errors while typing
                    }
                  }}
                />
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
                  Deploy Instance
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  const normalizedStatus = status.toUpperCase()
  const styles: Record<string, string> = {
    ACTIVE: "bg-success/10 text-success border-success/20",
    PAUSED: "bg-warning/10 text-warning border-warning/20",
    FAILED: "bg-danger/10 text-danger border-danger/20",
    WARMING_UP: "bg-accent/10 text-accent border-accent/20 animate-pulse",
    STOPPED: "bg-slate-800 text-muted border-slate-700",
    CREATED: "bg-slate-800 text-muted border-slate-700",
  }

  return (
    <span className={`px-3 py-1.5 rounded-full text-[10px] font-bold border uppercase tracking-tighter ${styles[normalizedStatus] ?? "bg-slate-800 text-muted border-slate-700"}`}>
      {status.replace('_', ' ')}
    </span>
  )
}
