import { useState } from 'react'
import { ShieldCheck, ShieldX } from 'lucide-react'
import { cn } from '../App'

export function RiskControl() {
  const [systemProtected, setSystemProtected] = useState(true)
  const [activeRules, setActiveRules] = useState([
    { id: 1, name: 'MaxNotionalRule', desc: 'Prevents single order notional from exceeding configured limit.', enabled: true },
    { id: 2, name: 'MaxOrderQtyRule', desc: 'Rejects orders exceeding maximum quantity per instrument.', enabled: true },
    { id: 3, name: 'TradingSessionRule', desc: 'Allows trading only during exchange sessions.', enabled: true },
    { id: 4, name: 'InstrumentWhitelistRule', desc: 'Allows trading only on pre-approved instruments.', enabled: false },
  ])

  const toggleRule = (id: number) => {
    setActiveRules(prev => prev.map(r => r.id === id ? { ...r, enabled: !r.enabled } : r))
  }

  const toggleSystem = () => {
    if (systemProtected && !confirm('WARNING: Disabling system protection will bypass all pre-trade risk checks. Are you sure?')) return
    setSystemProtected(!systemProtected)
  }

  return (
    <div className="space-y-4 h-full flex flex-col animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight">Risk Control</h1>
          <p className="text-muted mt-1">Pre-trade limits and portfolio guardrails.</p>
        </div>
        <button
          onClick={toggleSystem}
          className={cn(
            "flex items-center gap-2 px-4 py-2 rounded-full border transition-all duration-300 shadow-[0_0_15px_rgba(0,0,0,0.2)]",
            systemProtected
              ? "bg-success/10 text-success border-success/20 hover:bg-success/20"
              : "bg-danger/10 text-danger border-danger/20 hover:bg-danger/20 animate-pulse"
          )}
        >
          {systemProtected ? <ShieldCheck className="w-5 h-5" /> : <ShieldX className="w-5 h-5" />}
          <span className="text-sm font-bold">{systemProtected ? 'System Protected' : 'Protection Disabled'}</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 min-h-0 overflow-y-auto custom-scrollbar">
        {/* Active Rules */}
        <div className="lg:col-span-2 card">
          <h3 className="font-semibold text-lg mb-4 border-b border-slate-800 pb-4">Active Guardrails</h3>
          <div className="space-y-4">
            {activeRules.map((rule) => (
              <div
                key={rule.id}
                className={cn(
                  "p-4 rounded-2xl border transition-all duration-300 flex items-start gap-4",
                  rule.enabled ? "bg-slate-900/50 border-slate-800/80" : "bg-slate-900/20 border-slate-800/30 opacity-60"
                )}
              >
                <div className={cn(
                  "p-2 rounded-full mt-1 transition-colors",
                  rule.enabled ? "bg-accent/10 text-accent" : "bg-slate-800 text-slate-600"
                )}>
                  {rule.enabled ? <ShieldCheck className="w-4 h-4" /> : <ShieldX className="w-4 h-4" />}
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className={cn("font-bold text-sm", rule.enabled ? "text-foreground" : "text-muted")}>{rule.name}</span>
                    <button
                      onClick={() => toggleRule(rule.id)}
                      className={cn(
                        "text-[10px] uppercase font-bold px-2 py-0.5 rounded-full border transition-colors",
                        rule.enabled
                          ? "text-success bg-success/10 border-success/20 hover:bg-success/20"
                          : "text-muted bg-slate-800 border-slate-700 hover:text-foreground"
                      )}
                    >
                      {rule.enabled ? 'Enabled' : 'Disabled'}
                    </button>
                  </div>
                  <p className="text-xs text-muted leading-relaxed">{rule.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Risk Events Log */}
        <div className="card flex flex-col min-h-0">
          <h3 className="font-semibold text-lg mb-4 border-b border-slate-800 pb-4 flex items-center justify-between">
            Recent Interventions
            <span className="text-xs font-normal text-muted bg-slate-800 px-2 py-1 rounded-full">
              Last 24h
            </span>
          </h3>

          <div className="flex-1 space-y-4 overflow-y-auto pr-2 custom-scrollbar">
            <div className="text-center text-muted text-sm py-8 italic">
              No risk interventions recorded.
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
