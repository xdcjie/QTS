import { useState, useEffect, useRef } from 'react'
import { Activity, Search, RefreshCw } from 'lucide-react'
import { createChart, ColorType, IChartApi } from 'lightweight-charts'
import { cn } from '../App'

interface Subscription {
  key: string
  ref_count: number
  subscribers: string[]
}

export function MarketData() {
  const [activeTab, setActiveTab] = useState<'chart' | 'subscriptions'>('chart')
  const [resolution, setResolution] = useState('5m')
  const [symbol, setSymbol] = useState('AAPL')
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)

  const [subscriptions] = useState<Subscription[]>([])

  useEffect(() => {
    if (activeTab === 'chart' && chartContainerRef.current) {
      const chart = createChart(chartContainerRef.current, {
        layout: {
          background: { type: ColorType.Solid, color: 'transparent' },
          textColor: 'rgba(255, 255, 255, 0.5)',
        },
        grid: {
          vertLines: { color: 'rgba(255, 255, 255, 0.05)' },
          horzLines: { color: 'rgba(255, 255, 255, 0.05)' },
        },
        width: chartContainerRef.current.clientWidth,
        height: chartContainerRef.current.clientHeight,
        timeScale: {
          borderColor: 'rgba(255, 255, 255, 0.1)',
        },
      })

      const candlestickSeries = chart.addCandlestickSeries({
        upColor: '#39ff14',
        downColor: '#ff003c',
        borderVisible: false,
        wickUpColor: '#39ff14',
        wickDownColor: '#ff003c',
      })

      candlestickSeries.setData(MOCK_CANDLE_DATA)
      chart.timeScale().fitContent()
      chartRef.current = chart

      const handleResize = () => {
        if (chartContainerRef.current) {
          chart.applyOptions({
            width: chartContainerRef.current.clientWidth,
            height: chartContainerRef.current.clientHeight,
          })
        }
      }

      window.addEventListener('resize', handleResize)
      return () => {
        window.removeEventListener('resize', handleResize)
        chart.remove()
      }
    }
  }, [activeTab])

  return (
    <div className="space-y-4 h-full flex flex-col animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-baseline gap-3">
          <h1 className="text-lg font-bold tracking-tight">Market Data</h1>
          <p className="text-xs text-muted">Real-time streams and aggregation status</p>
        </div>
        <div className="flex items-center gap-2 bg-slate-900 p-1 rounded-full border border-slate-800">
          <button
            onClick={() => setActiveTab('chart')}
            className={cn("px-3 py-1 rounded-full text-xs font-medium transition-all", activeTab === 'chart' ? "bg-accent text-white" : "text-muted hover:text-foreground")}
          >
            Live Chart
          </button>
          <button
            onClick={() => setActiveTab('subscriptions')}
            className={cn("px-3 py-1 rounded-full text-xs font-medium transition-all", activeTab === 'subscriptions' ? "bg-accent text-white" : "text-muted hover:text-foreground")}
          >
            Subscriptions
          </button>
        </div>
      </div>

      {activeTab === 'chart' && (
        <div className="card flex-1 flex flex-col min-h-0 p-3">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-4">
              <div className="relative">
                <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
                <input
                  type="text"
                  placeholder="Search instrument..."
                  className="bg-slate-900 border border-slate-800 rounded-full pl-9 pr-4 py-2 text-sm focus:outline-none focus:border-accent w-64 transition-colors"
                  value={symbol}
                  onChange={e => setSymbol(e.target.value.toUpperCase())}
                />
              </div>
              <div className="flex gap-1">
                {['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w'].map(res => (
                  <button
                    key={res}
                    onClick={() => setResolution(res)}
                    className={cn(
                      "px-3 py-1.5 text-xs rounded-full font-medium transition-colors",
                      res === resolution ? "bg-slate-800 text-foreground border border-white/10" : "text-muted hover:bg-slate-800/50"
                    )}
                  >
                    {res}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex items-center gap-2 text-success text-sm font-medium">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-success opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-success"></span>
              </span>
              Live Feed: {symbol}
            </div>
          </div>
          <div className="flex-1 bg-black/20 rounded-2xl border border-slate-800/50 relative overflow-hidden">
            <div ref={chartContainerRef} className="absolute inset-0" />
          </div>
        </div>
      )}

      {activeTab === 'subscriptions' && (
        <div className="card flex-1 overflow-y-auto custom-scrollbar">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-lg flex items-center gap-2">
              <Activity className="w-5 h-5 text-accent" />
              Active Aggregation Streams
            </h3>
            <button className="btn-ghost flex items-center gap-2 text-sm">
              <RefreshCw className="w-4 h-4" /> Refresh
            </button>
          </div>

          <div className="space-y-3">
            {subscriptions.length === 0 && (
              <p className="text-center text-muted text-sm py-8 italic">
                No active subscriptions. Start a strategy to see live data streams.
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

const MOCK_CANDLE_DATA = [
  { time: '2025-04-29', open: 180.50, high: 182.80, low: 179.20, close: 182.47 },
  { time: '2025-04-30', open: 182.47, high: 184.20, low: 181.50, close: 183.10 },
  { time: '2025-05-01', open: 183.10, high: 183.50, low: 180.20, close: 181.20 },
  { time: '2025-05-02', open: 181.20, high: 182.90, low: 180.80, close: 182.10 },
  { time: '2025-05-03', open: 182.10, high: 185.00, low: 182.00, close: 184.50 },
  { time: '2025-05-04', open: 184.50, high: 186.20, low: 184.00, close: 185.80 },
  { time: '2025-05-05', open: 185.80, high: 187.50, low: 185.20, close: 186.90 },
]
