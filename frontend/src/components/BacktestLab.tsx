import { useState, useEffect } from 'react'
import { History, Play, Settings, ChevronRight, Loader2, BarChart2, RefreshCw } from 'lucide-react'
import { apiClient } from '@/api/client'
import { BacktestRun } from '@/models'
import { cn } from '../App'

const STRATEGY_OPTIONS = [
  { label: 'EMA Cross', class_path: 'qts.user_strategies.ema_cross.strategy.EMAStrategy' },
  { label: 'Mean Reversion', class_path: 'qts.user_strategies.mean_reversion.strategy.MeanReversionStrategy' },
]

interface BacktestRunExt extends BacktestRun {
  _strategy?: string
  _date?: string
}

export function BacktestLab() {
  const [isRunning, setIsRunning] = useState(false)
  const [results, setResults] = useState<BacktestRunExt[]>([])
  const [strategyIdx, setStrategyIdx] = useState(0)
  const [error, setError] = useState<string | null>(null)

  const fetchResults = () => {
    apiClient.get<BacktestRun[]>('/backtests')
      .then(data => setResults([...data].reverse()))
      .catch(() => {})
  }

  useEffect(() => { fetchResults() }, [])

  const handleRun = async () => {
    setIsRunning(true)
    setError(null)
    const strategy = STRATEGY_OPTIONS[strategyIdx]
    try {
      const result = await apiClient.post<BacktestRun>('/backtests', {
        strategy_name: strategy.label,
      })
      const ext: BacktestRunExt = { ...result, _strategy: strategy.label, _date: 'Just now' }
      setResults(prev => [ext, ...prev])
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Backtest failed. Check backend logs.'
      setError(msg)
    } finally {
      setIsRunning(false)
    }
  }

  return (
    <div className="space-y-4 h-full flex flex-col animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight">Backtest Lab</h1>
          <p className="text-muted mt-1">Design, run, and analyze historical simulations.</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={fetchResults} className="btn-ghost border border-white/10 p-2" title="Refresh results">
            <RefreshCw className="w-4 h-4" />
          </button>
          <button
            onClick={handleRun}
            disabled={isRunning}
            className="btn-primary flex items-center gap-2 disabled:opacity-50"
          >
            {isRunning ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4 fill-current" />}
            {isRunning ? 'Running Simulation…' : 'Run Simulation'}
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-danger/10 border border-danger/30 rounded-xl text-sm text-danger">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 flex-1 min-h-0">
        {/* Left Column: Config */}
        <div className="card flex flex-col overflow-y-auto custom-scrollbar">
          <div className="flex items-center gap-2 mb-4 text-base font-semibold">
            <Settings className="w-5 h-5 text-accent" />
            Configuration
          </div>

          <div className="space-y-5 flex-1">
            <div>
              <label className="text-xs text-muted uppercase tracking-wider font-semibold block mb-2">Strategy</label>
              <select
                value={strategyIdx}
                onChange={e => setStrategyIdx(Number(e.target.value))}
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-accent"
              >
                {STRATEGY_OPTIONS.map((s, i) => (
                  <option key={i} value={i}>{s.label}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Right Column: History & Results */}
        <div className="lg:col-span-2 flex flex-col gap-4 min-h-0 overflow-y-auto custom-scrollbar">
          <div className="card flex-1">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-lg flex items-center gap-2">
                <History className="w-5 h-5 text-accent" />
                Recent Runs
              </h3>
            </div>

            <div className="space-y-3">
              {results.length === 0 && (
                <p className="text-center text-muted text-sm py-8 italic">No backtest runs yet. Configure and click Run Simulation.</p>
              )}
              {results.map((run) => {
                const statusColor = run.status === 'completed' ? 'text-success' : run.status === 'failed' ? 'text-danger' : 'text-warning'
                return (
                  <div key={run.run_id} className="p-4 bg-slate-800/40 border border-slate-700/50 rounded-2xl hover:border-accent/30 transition-all group cursor-pointer">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-accent/10 flex items-center justify-center">
                          <BarChart2 className="w-4 h-4 text-accent" />
                        </div>
                        <div>
                          <div className="font-bold text-sm">{run._strategy ?? run.strategy_name}</div>
                          <div className="text-[10px] text-muted font-mono">
                            {run.run_id} {run._date ? `• ${run._date}` : ''}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <div className={cn("text-[10px] font-bold uppercase", statusColor)}>{run.status}</div>
                        </div>
                        <ChevronRight className="w-4 h-4 text-slate-600 group-hover:text-accent transition-colors" />
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
