import { useState, useEffect } from 'react'
import { ClipboardList, Search, RefreshCw } from 'lucide-react'
import { apiClient } from '@/api/client'
import { OrderStatusEntry } from '@/models'

export function Orders() {
  const [orders, setOrders] = useState<OrderStatusEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [searchId, setSearchId] = useState('')

  const fetchOrder = async (orderId: string) => {
    if (!orderId.trim()) return
    try {
      const data = await apiClient.get<OrderStatusEntry>(`/orders/${orderId}`)
      setOrders(prev => {
        if (prev.find(o => o.order_id === data.order_id)) {
          return prev.map(o => o.order_id === data.order_id ? data : o)
        }
        return [data, ...prev]
      })
    } catch {
      // order not found or API unavailable
    }
  }

  useEffect(() => {
    setLoading(false)
  }, [])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    fetchOrder(searchId)
    setSearchId('')
  }

  return (
    <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight">Orders</h1>
          <p className="text-muted mt-1">Track order lifecycle and fills.</p>
        </div>
        <form onSubmit={handleSearch} className="flex items-center gap-2">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
            <input
              type="text"
              placeholder="Order ID..."
              className="bg-slate-900 border border-slate-800 rounded-full pl-9 pr-4 py-2 text-sm focus:outline-none focus:border-accent w-56 transition-colors font-mono"
              value={searchId}
              onChange={e => setSearchId(e.target.value)}
            />
          </div>
          <button type="submit" className="btn-primary text-sm">Lookup</button>
        </form>
      </div>

      {loading && (
        <div className="text-center text-muted py-12">Loading…</div>
      )}

      {!loading && orders.length === 0 && (
        <div className="card text-center py-12">
          <ClipboardList className="w-12 h-12 text-slate-700 mx-auto mb-3" />
          <p className="text-muted text-sm">No orders to display. Use the search bar to look up an order by ID.</p>
        </div>
      )}

      {orders.length > 0 && (
        <div className="card overflow-hidden p-0">
          <div className="p-4 border-b border-slate-800 flex items-center justify-between">
            <h3 className="font-bold text-lg flex items-center gap-2">
              <ClipboardList className="w-5 h-5 text-accent" />
              Order Status
            </h3>
            <button onClick={() => setOrders([])} className="btn-ghost text-xs flex items-center gap-1">
              <RefreshCw className="w-3 h-3" /> Clear
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-muted text-xs uppercase tracking-wider bg-slate-900/50">
                  <th className="p-4 font-semibold">Order ID</th>
                  <th className="p-4 font-semibold text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {orders.map((order) => (
                  <tr key={order.order_id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="p-4 font-mono text-sm font-medium">{order.order_id}</td>
                    <td className="p-4 text-right">
                      <OrderStatusBadge status={order.status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

function OrderStatusBadge({ status }: { status: string }) {
  const normalizedStatus = status.toUpperCase()
  const styles: Record<string, string> = {
    CREATED: "bg-slate-800 text-muted border-slate-700",
    SENT: "bg-accent/10 text-accent border-accent/20",
    PARTIALLY_FILLED: "bg-warning/10 text-warning border-warning/20",
    FILLED: "bg-success/10 text-success border-success/20",
    CANCELED: "bg-slate-800 text-muted border-slate-700",
    REJECTED: "bg-danger/10 text-danger border-danger/20",
  }

  return (
    <span className={`px-3 py-1 rounded-full text-[10px] font-bold border uppercase tracking-tighter ${styles[normalizedStatus] ?? "bg-slate-800 text-muted border-slate-700"}`}>
      {status.replace('_', ' ')}
    </span>
  )
}
