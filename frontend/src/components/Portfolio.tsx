import { BarChart3, TrendingUp, DollarSign, PieChart } from 'lucide-react'
import { cn } from '../App'

export function Portfolio() {
  const positions = [
    { instrument_id: 'AAPL', quantity: 100, average_price: 182.47, unrealized_pnl: 530.00, market_value: 18800.00 },
    { instrument_id: 'GC', quantity: 5, average_price: 2340.50, unrealized_pnl: -120.00, market_value: 11702.50 },
  ]

  const totalValue = positions.reduce((acc, p) => acc + p.market_value, 0)
  const totalPnl = positions.reduce((acc, p) => acc + p.unrealized_pnl, 0)

  return (
    <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight">Portfolio</h1>
          <p className="text-muted mt-1">Real-time positions and capital exposure.</p>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card bg-gradient-to-br from-slate-900 to-slate-800 border-accent/20">
          <div className="flex items-center gap-3 text-muted mb-2">
            <BarChart3 className="w-5 h-5 text-accent" />
            <span className="font-medium">Gross Exposure</span>
          </div>
          <div className="text-xl font-bold font-mono">
            ${totalValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
        </div>
        <div className="card">
          <div className="flex items-center gap-3 text-muted mb-2">
            <TrendingUp className="w-5 h-5 text-success" />
            <span className="font-medium">Unrealized PnL</span>
          </div>
          <div className={cn("text-xl font-bold font-mono", totalPnl >= 0 ? "text-success" : "text-danger")}>
            {totalPnl >= 0 ? '+' : ''}${totalPnl.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
        </div>
        <div className="card">
          <div className="flex items-center gap-3 text-muted mb-2">
            <DollarSign className="w-5 h-5 text-warning" />
            <span className="font-medium">Positions</span>
          </div>
          <div className="text-xl font-bold font-mono text-foreground">
            {positions.length}
          </div>
        </div>
      </div>

      {/* Positions Table */}
      <div className="card overflow-hidden p-0">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <h3 className="font-bold text-lg flex items-center gap-2">
            <PieChart className="w-5 h-5 text-accent" />
            Active Positions
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800 text-muted text-xs uppercase tracking-wider bg-slate-900/50">
                <th className="p-4 font-semibold">Instrument</th>
                <th className="p-4 font-semibold text-right">Quantity</th>
                <th className="p-4 font-semibold text-right">Avg Price</th>
                <th className="p-4 font-semibold text-right">Market Value</th>
                <th className="p-4 font-semibold text-right">Unrealized PnL</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {positions.map((pos) => (
                <tr key={pos.instrument_id} className="hover:bg-slate-800/30 transition-colors group">
                  <td className="p-4 font-bold text-sm">{pos.instrument_id}</td>
                  <td className="p-4 font-mono text-sm text-right">{pos.quantity.toLocaleString()}</td>
                  <td className="p-4 font-mono text-sm text-right text-muted">
                    ${pos.average_price.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </td>
                  <td className="p-4 font-mono text-sm text-right">
                    ${pos.market_value.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </td>
                  <td className={cn(
                    "p-4 font-mono text-sm text-right font-semibold",
                    pos.unrealized_pnl >= 0 ? "text-success" : "text-danger"
                  )}>
                    {pos.unrealized_pnl >= 0 ? '+' : ''}${pos.unrealized_pnl.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
