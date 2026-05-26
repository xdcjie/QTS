import { useState } from 'react'
import {
  LayoutDashboard,
  PlayCircle,
  Wallet,
  BarChart3,
  ShieldCheck,
  History,
  Settings,
  Activity,
  Globe,
  Bell,
  X,
  ClipboardList,
  SlidersHorizontal,
  FlaskConical,
} from 'lucide-react'
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'
import { StrategyManagement } from './components/StrategyManagement'
import { AccountManagement } from './components/AccountManagement'
import { Portfolio } from './components/Portfolio'
import { MarketData } from './components/MarketData'
import { BacktestLab } from './components/BacktestLab'
import { ResearchDashboard } from './components/ResearchDashboard'
import { RiskControl } from './components/RiskControl'
import { Orders } from './components/Orders'
import { Operations } from './components/Operations'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

const MOCK_LOGS = [
  '[08:00:01] SYSTEM: Actor system initialization complete.',
  '[08:00:05] DATA: Connected to IBKR Gateway (Paper Trading).',
  '[08:00:10] RISK: Loaded 4 active guardrails.',
  '[08:05:22] STRATEGY: EMA-Cross-01 signal: BUY AAPL @ 182.45',
  '[08:05:23] ORDER: Submitted BUY 100 AAPL (MKT)',
  '[08:05:23] ORDER: Filled BUY 100 AAPL @ 182.47',
  '[08:15:00] SYSTEM: Health check passed - All services green.',
  '[08:30:45] STRATEGY: Trend-Follower-02 warming up (55/100 bars).',
  '[09:45:12] RISK: MaxOrderValueRule REJECTED order for 1500 AAPL.',
  '[10:00:00] PORTFOLIO: Snapshot taken. Equity: $1,240,500.00',
]

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard')
  const [showNotifications, setShowNotifications] = useState(false)
  const [showLogsModal, setShowLogsModal] = useState(false)

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'accounts', label: 'Accounts', icon: Wallet },
    { id: 'strategies', label: 'Strategies', icon: PlayCircle },
    { id: 'portfolio', label: 'Portfolio', icon: BarChart3 },
    { id: 'orders', label: 'Orders', icon: ClipboardList },
    { id: 'market', label: 'Market Data', icon: Activity },
    { id: 'backtest', label: 'Backtest Lab', icon: History },
    { id: 'research', label: 'Research', icon: FlaskConical },
    { id: 'risk', label: 'Risk Control', icon: ShieldCheck },
    { id: 'operations', label: 'Operations', icon: SlidersHorizontal },
  ]

  return (
    <div className="flex h-screen bg-transparent overflow-hidden text-foreground">
      {/* Sidebar */}
      <aside className="w-64 border-r border-white/5 flex flex-col bg-black/40 backdrop-blur-3xl">
        <div className="p-4 flex items-center gap-3">
          <div className="w-10 h-10 bg-accent/10 border border-accent/30 rounded-2xl flex items-center justify-center shadow-[0_0_15px_rgba(0,240,255,0.2)]">
            <Activity className="text-accent w-6 h-6" />
          </div>
          <span className="font-bold text-xl tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-accent to-purple-400">QTS Core</span>
        </div>

        <nav className="flex-1 px-4 space-y-1">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={cn(
                "w-full flex items-center gap-3 px-3 py-2 rounded-2xl transition-all duration-300 group relative overflow-hidden",
                activeTab === item.id
                  ? "text-accent bg-accent/10 border border-accent/20 shadow-[inset_0_0_15px_rgba(0,240,255,0.1)]"
                  : "text-muted hover:bg-white/5 hover:text-foreground border border-transparent"
              )}
            >
              <item.icon className={cn(
                "w-5 h-5 relative z-10",
                activeTab === item.id ? "text-accent drop-shadow-[0_0_8px_rgba(0,240,255,0.8)]" : "text-muted group-hover:text-foreground"
              )} />
              <span className="font-medium relative z-10">{item.label}</span>
            </button>
          ))}
        </nav>

        <div className="p-4 border-t border-white/5">
          <button
            onClick={() => setActiveTab('settings')}
            className={cn(
              "w-full flex items-center gap-3 px-3 py-2 rounded-2xl transition-all",
              activeTab === 'settings'
                ? "text-accent bg-accent/10 border border-accent/20"
                : "text-muted hover:bg-white/5 hover:text-foreground border border-transparent hover:border-white/10"
            )}
          >
            <Settings className="w-5 h-5" />
            <span className="font-medium">Settings</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden relative">
        {/* Header */}
        <header className="h-16 border-b border-white/5 bg-black/20 backdrop-blur-2xl flex items-center justify-between px-8 z-20">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2 px-3 py-1 bg-success/10 border border-success/30 rounded-full shadow-[0_0_10px_rgba(57,255,20,0.15)]">
              <span className="status-dot bg-success animate-pulse" />
              <span className="text-xs font-bold text-success uppercase tracking-wider drop-shadow-[0_0_5px_rgba(57,255,20,0.8)]">Live System</span>
            </div>
            <div className="flex items-center gap-4 text-sm text-muted font-mono">
              <div className="flex items-center gap-1.5">
                <Globe className="w-4 h-4 text-accent opacity-70" />
                <span>UTC {new Date().toISOString().slice(0, 19).replace('T', ' ')}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="relative">
              <button
                onClick={() => setShowNotifications(!showNotifications)}
                className={cn(
                  "relative p-2 transition-colors rounded-full hover:bg-white/5",
                  showNotifications ? "text-accent" : "text-muted hover:text-accent"
                )}
              >
                <Bell className="w-5 h-5" />
                <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-danger rounded-full shadow-[0_0_8px_rgba(255,0,60,0.8)] border border-black" />
              </button>

              {showNotifications && (
                <div className="absolute right-0 mt-2 w-80 bg-slate-900 border border-white/10 rounded-2xl shadow-2xl p-4 z-50 animate-in fade-in zoom-in-95 duration-200">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-bold text-sm">Notifications</h3>
                    <button onClick={() => setShowNotifications(false)} className="text-muted hover:text-foreground">
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                  <div className="space-y-3">
                    {[
                      { title: 'Order Filled', desc: 'BUY 100 AAPL @ 182.47', time: '2m ago', type: 'success' },
                      { title: 'Risk Alert', desc: 'MaxOrderValueRule triggered', time: '15m ago', type: 'warn' },
                      { title: 'System', desc: 'Actor system health check passed', time: '1h ago', type: 'info' },
                    ].map((n, i) => (
                      <div key={i} className="p-3 bg-white/5 rounded-xl border border-white/5 hover:border-white/10 transition-colors cursor-pointer">
                        <div className="flex justify-between items-start mb-1">
                          <span className="text-xs font-bold">{n.title}</span>
                          <span className="text-[10px] text-muted">{n.time}</span>
                        </div>
                        <p className="text-[11px] text-muted line-clamp-1">{n.desc}</p>
                      </div>
                    ))}
                  </div>
                  <button className="w-full mt-4 py-2 text-[11px] font-bold text-accent hover:bg-accent/10 rounded-lg transition-colors">
                    View All Activity
                  </button>
                </div>
              )}
            </div>

            <div className="h-8 w-px bg-white/10 mx-2" />
            <div className="flex items-center gap-3">
              <div className="text-right">
                <div className="text-sm font-semibold text-foreground">Trader</div>
                <div className="text-xs text-accent font-mono opacity-80">qts-local-01</div>
              </div>
              <div className="w-9 h-9 rounded-full border border-accent/50 bg-gradient-to-tr from-accent/20 to-purple-500/20 shadow-[0_0_10px_rgba(0,240,255,0.2)]" />
            </div>
          </div>
        </header>

        {/* Content Scroll Area */}
        <section className="flex-1 overflow-y-auto p-8 custom-scrollbar relative z-10">
          {activeTab === 'dashboard' && (
            <DashboardPlaceholder
              onDeploy={() => setActiveTab('strategies')}
              onViewLogs={() => setShowLogsModal(true)}
            />
          )}
          {activeTab === 'accounts' && <AccountManagement />}
          {activeTab === 'strategies' && <StrategyManagement />}
          {activeTab === 'portfolio' && <Portfolio />}
          {activeTab === 'orders' && <Orders />}
          {activeTab === 'market' && <MarketData />}
          {activeTab === 'backtest' && <BacktestLab />}
          {activeTab === 'research' && <ResearchDashboard />}
          {activeTab === 'risk' && <RiskControl />}
          {activeTab === 'operations' && <Operations />}
          {activeTab === 'settings' && <SettingsView />}
        </section>

        {/* Logs Modal */}
        {showLogsModal && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="bg-slate-900 border border-white/10 w-full max-w-2xl h-[500px] rounded-3xl shadow-2xl flex flex-col overflow-hidden animate-in zoom-in-95 duration-200">
              <div className="p-6 border-b border-white/5 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Activity className="w-5 h-5 text-accent" />
                  <h2 className="text-lg font-bold">System Logs</h2>
                </div>
                <button onClick={() => setShowLogsModal(false)} className="p-2 hover:bg-white/5 rounded-full transition-colors">
                  <X className="w-5 h-5" />
                </button>
              </div>
              <div className="flex-1 overflow-y-auto p-6 font-mono text-xs space-y-2 bg-black/40 custom-scrollbar">
                {MOCK_LOGS.map((log, i) => (
                  <div key={i} className="flex gap-4">
                    <span className="text-slate-500 whitespace-nowrap">{log.split('] ')[0]}]</span>
                    <span className={cn(
                      log.includes('SYSTEM') && "text-purple-400",
                      log.includes('DATA') && "text-blue-400",
                      log.includes('RISK') && "text-warning",
                      log.includes('STRATEGY') && "text-accent",
                      log.includes('ORDER') && "text-success",
                      !log.match(/SYSTEM|DATA|RISK|STRATEGY|ORDER/) && "text-foreground"
                    )}>
                      {log.split('] ')[1]}
                    </span>
                  </div>
                ))}
              </div>
              <div className="p-4 bg-black/20 border-t border-white/5 flex justify-end">
                <button
                  onClick={() => setShowLogsModal(false)}
                  className="px-6 py-2 bg-white/5 hover:bg-white/10 rounded-xl font-bold transition-all"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

function DashboardPlaceholder({ onDeploy, onViewLogs }: { onDeploy: () => void, onViewLogs: () => void }) {
  return (
    <div className="space-y-5 animate-in fade-in duration-500">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight">Overview</h1>
          <p className="text-muted mt-1">Real-time performance and system health.</p>
        </div>
        <div className="flex gap-3">
          <button onClick={onDeploy} className="btn-primary">Deploy Strategy</button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Total Equity', value: '$1,240,500.00', change: '+2.4%', up: true },
          { label: 'Daily PnL', value: '+$14,230.15', change: '+1.2%', up: true },
          { label: 'Active Strategies', value: '—', change: '0', up: true },
          { label: 'Risk Exposure', value: '24.5%', change: '-5.1%', up: false },
        ].map((stat, i) => (
          <div key={i} className="card group hover:border-accent/50 transition-colors">
            <div className="text-sm font-medium text-muted">{stat.label}</div>
            <div className="flex items-end justify-between mt-2">
              <div className="text-base font-bold font-mono">{stat.value}</div>
              <div className={cn(
                "text-xs font-bold px-2 py-1 rounded-full",
                stat.up ? "bg-success/10 text-success" : "bg-danger/10 text-danger"
              )}>
                {stat.change}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Performance Chart */}
        <div className="lg:col-span-2 card h-96 flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-lg">Portfolio Performance</h3>
          </div>
          <div className="flex-1 min-h-0 flex items-center justify-center text-muted text-sm">
            Connect strategies to see performance data
          </div>
        </div>

        {/* System Health */}
        <div className="card flex flex-col">
          <h3 className="font-semibold text-lg mb-4">System Health</h3>
          <div className="space-y-4 flex-1">
            {[
              { name: 'Event Bus', status: 'Healthy', load: '12%' },
              { name: 'Data Stream', status: 'Healthy', load: '45%' },
              { name: 'IBKR Gateway', status: 'Connected', load: 'Latency 24ms' },
              { name: 'Actor System', status: 'Healthy', load: '98% uptime' },
            ].map((s, i) => (
              <div key={i} className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full bg-success shadow-[0_0_8px_rgba(57,255,20,0.8)]" />
                  <span className="text-sm font-medium">{s.name}</span>
                </div>
                <div className="text-xs text-accent/70 font-mono">{s.load}</div>
              </div>
            ))}
          </div>
          <div className="mt-6 pt-6 border-t border-white/5">
            <div className="text-xs text-muted flex items-center justify-between font-mono">
              <span>Uptime: —</span>
              <span
                onClick={onViewLogs}
                className="text-accent hover:text-white cursor-pointer drop-shadow-[0_0_5px_rgba(0,240,255,0.5)] transition-all"
              >
                View Logs
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function SettingsView() {
  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <h1 className="text-2xl font-bold">Settings</h1>

      <div className="grid gap-6">
        <div className="card">
          <h3 className="font-bold text-lg mb-4 flex items-center gap-2">
            <Globe className="w-5 h-5 text-accent" />
            API Connections
          </h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-white/5 rounded-2xl border border-white/5">
              <div>
                <div className="font-bold">Interactive Brokers (TWS/Gateway)</div>
                <div className="text-xs text-muted">127.0.0.1:7497 - Client ID: 1</div>
              </div>
              <div className="text-success text-xs font-bold uppercase tracking-widest bg-success/10 px-3 py-1 rounded-full">Connected</div>
            </div>
            <div className="flex items-center justify-between p-4 bg-white/5 rounded-2xl border border-white/5">
              <div>
                <div className="font-bold">Simulated Broker</div>
                <div className="text-xs text-muted">Paper trading adapter</div>
              </div>
              <div className="text-success text-xs font-bold uppercase tracking-widest bg-success/10 px-3 py-1 rounded-full">Active</div>
            </div>
          </div>
        </div>

        <div className="card">
          <h3 className="font-bold text-lg mb-4 flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-accent" />
            System Preferences
          </h3>
          <div className="space-y-4">
            {[
              { label: 'Paper Trading Mode', desc: 'Use simulated execution for all orders.', active: true },
              { label: 'Auto-Deleverage', desc: 'Automatically close positions if margin exceeds 90%.', active: false },
              { label: 'Event Sourcing', desc: 'Persist all events for state recovery and audit trail.', active: true },
            ].map((pref, i) => (
              <div key={i} className="flex items-center justify-between">
                <div>
                  <div className="font-bold text-sm">{pref.label}</div>
                  <div className="text-xs text-muted">{pref.desc}</div>
                </div>
                <button className={cn(
                  "w-12 h-6 rounded-full transition-colors relative",
                  pref.active ? "bg-accent" : "bg-slate-700"
                )}>
                  <span className={cn(
                    "absolute top-1 w-4 h-4 bg-white rounded-full transition-all",
                    pref.active ? "right-1" : "left-1"
                  )} />
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
