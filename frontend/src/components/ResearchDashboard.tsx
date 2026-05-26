import { useEffect, useMemo, useState } from 'react'
import {
  BookOpenCheck,
  FileText,
  GitCompare,
  Loader2,
  RefreshCw,
  Search,
  ShieldCheck,
} from 'lucide-react'
import { apiClient } from '@/api/client'
import { cn } from '../App'

type MetricValue = string | number | boolean | null

interface ResearchRun {
  run_id: string
  strategy_name: string
  strategy_version: string
  idea_id: string | null
  recorded_at: string
  manifest_path: string
  dataset_ids: string[]
  metrics: Record<string, MetricValue>
  artifact_hashes: Record<string, string>
}

interface ResearchReport {
  evidence_bundle_id: string
  workflow_run_id: string
  strategy_id: string | null
  idea_id: string | null
  report_path: string | null
  report_hash: string | null
  status: string
  promotion_eligibility: string
  review_decisions: Record<string, MetricValue>[]
  report_preview?: string | null
}

interface PromotionDecision {
  decision_id: string
  strategy_id: string | null
  evidence_bundle_id: string | null
  status: string
  source: string
  decided_at: string | null
  payload: Record<string, MetricValue | Record<string, MetricValue>>
}

interface StrategyLifecycle {
  strategy_id: string
  idea_id: string | null
  lifecycle_status: string
  promotion_status: string | null
  latest_readiness_status: string | null
}

interface RunComparison {
  left_run_id: string
  right_run_id: string
  metric: string
  left_value: number
  right_value: number
  delta: number
}

export function ResearchDashboard() {
  const [runs, setRuns] = useState<ResearchRun[]>([])
  const [reports, setReports] = useState<ResearchReport[]>([])
  const [decisions, setDecisions] = useState<PromotionDecision[]>([])
  const [lifecycle, setLifecycle] = useState<StrategyLifecycle[]>([])
  const [selectedReport, setSelectedReport] = useState<ResearchReport | null>(null)
  const [strategyFilter, setStrategyFilter] = useState('')
  const [leftRunId, setLeftRunId] = useState('')
  const [rightRunId, setRightRunId] = useState('')
  const [metric, setMetric] = useState('total_return')
  const [comparison, setComparison] = useState<RunComparison | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const refresh = () => {
    setLoading(true)
    setError(null)
    const params = strategyFilter.trim() ? { strategy_name: strategyFilter.trim() } : undefined
    Promise.all([
      apiClient.get<ResearchRun[]>('/backtests/research/runs', params ? { params } : undefined),
      apiClient.get<ResearchReport[]>('/backtests/research/reports'),
      apiClient.get<PromotionDecision[]>('/backtests/research/promotion-decisions'),
      apiClient.get<StrategyLifecycle[]>('/backtests/research/lifecycle'),
    ])
      .then(([runData, reportData, decisionData, lifecycleData]) => {
        setRuns(runData)
        setReports(reportData)
        setDecisions(decisionData)
        setLifecycle(lifecycleData)
        setLeftRunId(prev => prev || runData[0]?.run_id || '')
        setRightRunId(prev => prev || runData[1]?.run_id || runData[0]?.run_id || '')
      })
      .catch(() => setError('Unable to load research dashboard data.'))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    refresh()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    const timeout = window.setTimeout(() => refresh(), 250)
    return () => window.clearTimeout(timeout)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [strategyFilter])

  const metricOptions = useMemo(() => {
    const names = new Set<string>(['total_return', 'sharpe'])
    runs.forEach(run => Object.keys(run.metrics).forEach(name => names.add(name)))
    return Array.from(names).sort()
  }, [runs])

  const compareRuns = () => {
    if (!leftRunId || !rightRunId || !metric) return
    setComparison(null)
    apiClient.get<RunComparison>('/backtests/research/compare', {
      params: { left_run_id: leftRunId, right_run_id: rightRunId, metric },
    })
      .then(setComparison)
      .catch(() => setError('Unable to compare selected research runs.'))
  }

  const openReport = (bundleId: string) => {
    apiClient.get<ResearchReport>(`/backtests/research/reports/${bundleId}`)
      .then(setSelectedReport)
      .catch(() => setError('Unable to load research report preview.'))
  }

  return (
    <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight">Research Dashboard</h1>
          <p className="text-muted mt-1">Read-only registry, report, promotion, and comparison view.</p>
        </div>
        <div className="flex items-center gap-2">
          <label className="sr-only" htmlFor="research-strategy-filter">Strategy filter</label>
          <div className="relative">
            <Search className="w-4 h-4 text-muted absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              id="research-strategy-filter"
              aria-label="Strategy filter"
              value={strategyFilter}
              onChange={event => setStrategyFilter(event.target.value)}
              placeholder="Filter strategy"
              className="bg-slate-900 border border-slate-800 rounded-xl pl-9 pr-3 py-2 text-sm focus:outline-none focus:border-accent"
            />
          </div>
          <button onClick={refresh} className="btn-ghost border border-white/10 p-2" title="Refresh research dashboard">
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {error && <div className="p-3 bg-danger/10 border border-danger/30 rounded-xl text-sm text-danger">{error}</div>}

      <div className="grid grid-cols-1 xl:grid-cols-4 gap-4">
        <section className="card xl:col-span-2">
          <div className="flex items-center gap-2 mb-4">
            <BookOpenCheck className="w-5 h-5 text-accent" />
            <h2 className="text-base font-semibold">Research Runs</h2>
          </div>
          <div className="space-y-3 max-h-[440px] overflow-y-auto custom-scrollbar">
            {runs.length === 0 && <p className="text-sm text-muted py-8 text-center">No research runs found.</p>}
            {runs.map(run => (
              <div key={run.run_id} className="p-4 bg-slate-800/40 border border-slate-700/50 rounded-2xl">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="font-bold text-sm">{run.strategy_name}</div>
                    <div className="text-[10px] text-muted font-mono">{run.run_id}</div>
                  </div>
                  <span className="text-[10px] text-accent font-mono">{formatMetric(run.metrics.sharpe)}</span>
                </div>
                <div className="mt-3 grid grid-cols-2 gap-2 text-xs text-muted">
                  <span>Idea: {run.idea_id ?? 'unlinked'}</span>
                  <span>Return: {formatMetric(run.metrics.total_return)}</span>
                  <span>Datasets: {run.dataset_ids.join(', ') || 'none'}</span>
                  <span>{new Date(run.recorded_at).toISOString().slice(0, 10)}</span>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="card">
          <div className="flex items-center gap-2 mb-4">
            <ShieldCheck className="w-5 h-5 text-accent" />
            <h2 className="text-base font-semibold">Lifecycle</h2>
          </div>
          <div className="space-y-3">
            {lifecycle.map(item => (
              <div key={`${item.strategy_id}-${item.idea_id ?? 'none'}`} className="p-3 bg-slate-800/40 border border-slate-700/50 rounded-2xl">
                <div className="text-sm font-bold">{item.strategy_id}</div>
                <div className="text-xs text-muted mt-1">{item.lifecycle_status}</div>
                <div className="text-[11px] text-accent mt-2">
                  {item.promotion_status ?? 'no promotion'} / {item.latest_readiness_status ?? 'no readiness'}
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="card">
          <div className="flex items-center gap-2 mb-4">
            <GitCompare className="w-5 h-5 text-accent" />
            <h2 className="text-base font-semibold">Run Comparison</h2>
          </div>
          <div className="space-y-3">
            <label className="text-xs text-muted uppercase tracking-wider font-semibold block" htmlFor="research-left-run">Left run</label>
            <select id="research-left-run" aria-label="Left run" value={leftRunId} onChange={event => setLeftRunId(event.target.value)} className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-sm">
              <RunOptions runs={runs} />
            </select>
            <label className="text-xs text-muted uppercase tracking-wider font-semibold block" htmlFor="research-right-run">Right run</label>
            <select id="research-right-run" aria-label="Right run" value={rightRunId} onChange={event => setRightRunId(event.target.value)} className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-sm">
              <RunOptions runs={runs} />
            </select>
            <select aria-label="Comparison metric" value={metric} onChange={event => setMetric(event.target.value)} className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-sm">
              {metricOptions.map(name => <option key={name} value={name}>{name}</option>)}
            </select>
            <button onClick={compareRuns} className="btn-primary w-full" disabled={!leftRunId || !rightRunId}>
              Compare runs
            </button>
            {comparison && (
              <div className="p-3 bg-accent/10 border border-accent/20 rounded-2xl text-sm">
                <div>{comparison.left_run_id}: {comparison.left_value.toFixed(4)}</div>
                <div>{comparison.right_run_id}: {comparison.right_value.toFixed(4)}</div>
                <div className={cn('font-bold mt-1', comparison.delta >= 0 ? 'text-success' : 'text-danger')}>
                  Delta: {comparison.delta.toFixed(2)}
                </div>
              </div>
            )}
          </div>
        </section>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <section className="card">
          <div className="flex items-center gap-2 mb-4">
            <FileText className="w-5 h-5 text-accent" />
            <h2 className="text-base font-semibold">Reports</h2>
          </div>
          <div className="space-y-3">
            {reports.map(report => (
              <button
                key={report.evidence_bundle_id}
                aria-label={`Open report ${report.evidence_bundle_id}`}
                onClick={() => openReport(report.evidence_bundle_id)}
                className="w-full text-left p-3 bg-slate-800/40 border border-slate-700/50 rounded-2xl hover:border-accent/40 transition-colors"
              >
                <div className="font-bold text-sm">{report.evidence_bundle_id}</div>
                <div className="text-xs text-muted mt-1">{report.report_path ?? 'No report path'}</div>
                <div className="text-[11px] text-accent mt-2">{report.status}</div>
              </button>
            ))}
          </div>
          {selectedReport?.report_preview && (
            <pre className="mt-4 p-4 bg-black/30 border border-white/10 rounded-2xl text-xs whitespace-pre-wrap max-h-64 overflow-y-auto custom-scrollbar">
              {selectedReport.report_preview}
            </pre>
          )}
        </section>

        <section className="card">
          <div className="flex items-center gap-2 mb-4">
            <ShieldCheck className="w-5 h-5 text-accent" />
            <h2 className="text-base font-semibold">Promotion Decisions</h2>
          </div>
          <div className="space-y-3 max-h-80 overflow-y-auto custom-scrollbar">
            {decisions.map(decision => (
              <div key={decision.decision_id} className="p-3 bg-slate-800/40 border border-slate-700/50 rounded-2xl">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="text-sm font-bold">{decision.status}</div>
                    <div className="text-xs text-muted mt-1">{decision.strategy_id ?? 'unlinked strategy'}</div>
                  </div>
                  <span className="text-[10px] text-accent uppercase">{decision.source}</span>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}

function RunOptions({ runs }: { runs: ResearchRun[] }) {
  return (
    <>
      {runs.map(run => <option key={run.run_id} value={run.run_id}>{run.run_id}</option>)}
    </>
  )
}

function formatMetric(value: MetricValue | undefined): string {
  if (typeof value === 'number') return value.toFixed(2)
  if (value === null || value === undefined) return 'n/a'
  return String(value)
}
