import { useState } from 'react'
import { Pause, Play, ShieldAlert } from 'lucide-react'
import { apiClient } from '@/api/client'

type RuntimeCommandResponse = {
  state: string
}

type KillSwitchResponse = {
  scope: string
  scope_id: string | null
  active: boolean
  reason: string
}

export function Operations() {
  const [runtimeState, setRuntimeState] = useState('running')
  const [killSwitch, setKillSwitch] = useState<KillSwitchResponse | null>(null)

  const pauseRuntime = async () => {
    const response = await apiClient.post<RuntimeCommandResponse>(
      '/operations/runtime/pause',
      undefined,
      { headers: { 'Idempotency-Key': 'console-pause', 'X-QTS-Operator': 'console' } }
    )
    setRuntimeState(response.state)
  }

  const resumeRuntime = async () => {
    const response = await apiClient.post<RuntimeCommandResponse>(
      '/operations/runtime/resume',
      undefined,
      { headers: { 'Idempotency-Key': 'console-resume', 'X-QTS-Operator': 'console' } }
    )
    setRuntimeState(response.state)
  }

  const haltGlobal = async () => {
    const response = await apiClient.post<KillSwitchResponse>(
      '/operations/kill-switches',
      { scope: 'global', scope_id: null, reason: 'console operator halt' },
      { headers: { 'X-QTS-Operator': 'console' } }
    )
    setKillSwitch(response)
  }

  return (
    <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight">Operations</h1>
          <p className="text-muted mt-1">Runtime controls and live-beta safety state.</p>
        </div>
        <div className="font-mono text-xs uppercase text-accent border border-accent/20 rounded-full px-3 py-1 bg-accent/10">
          {runtimeState}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <button onClick={pauseRuntime} className="card flex items-center gap-3 text-left hover:border-warning/40">
          <Pause className="w-5 h-5 text-warning" />
          <span className="font-bold">Pause Runtime</span>
        </button>
        <button onClick={resumeRuntime} className="card flex items-center gap-3 text-left hover:border-success/40">
          <Play className="w-5 h-5 text-success" />
          <span className="font-bold">Resume Runtime</span>
        </button>
        <button onClick={haltGlobal} className="card flex items-center gap-3 text-left hover:border-danger/40">
          <ShieldAlert className="w-5 h-5 text-danger" />
          <span className="font-bold">Global Halt</span>
        </button>
      </div>

      <div className="card">
        <h3 className="font-semibold text-lg mb-4 border-b border-slate-800 pb-4">Kill Switch</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <div className="text-muted text-xs uppercase">Scope</div>
            <div className="font-mono">{killSwitch?.scope ?? 'none'}</div>
          </div>
          <div>
            <div className="text-muted text-xs uppercase">Scope ID</div>
            <div className="font-mono">{killSwitch?.scope_id ?? '-'}</div>
          </div>
          <div>
            <div className="text-muted text-xs uppercase">Active</div>
            <div className="font-mono">{killSwitch?.active ? 'true' : 'false'}</div>
          </div>
          <div>
            <div className="text-muted text-xs uppercase">Reason</div>
            <div className="font-mono">{killSwitch?.reason ?? '-'}</div>
          </div>
        </div>
      </div>
    </div>
  )
}
