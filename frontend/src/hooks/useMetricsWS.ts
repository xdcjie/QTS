import { useEffect, useRef, useState, useCallback } from 'react'

export interface MetricSample {
  name: string
  value: number
  labels: Record<string, string>
  count: number
  sum: number
  sampled_at_utc: string
}

export interface MetricsState {
  latest: MetricSample[]
  history: MetricSample[][]
  connected: boolean
  error: string | null
}

const MAX_HISTORY = 60
const WS_URL = `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws/events`

export function useMetricsWS(): MetricsState {
  const [state, setState] = useState<MetricsState>({
    latest: [],
    history: [],
    connected: false,
    error: null,
  })
  const wsRef = useRef<WebSocket | null>(null)
  const retryRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const retryCount = useRef(0)

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    try {
      const ws = new WebSocket(WS_URL)
      wsRef.current = ws

      ws.onopen = () => {
        retryCount.current = 0
        setState(s => ({ ...s, connected: true, error: null }))
      }

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data)
          if (msg.type === 'snapshot') {
            setState(s => ({
              ...s,
              latest: msg.data,
              history: [...s.history.slice(-(MAX_HISTORY - 1)), msg.data],
            }))
          }
        } catch {
          // ignore non-JSON messages (e.g. system.synthetic)
        }
      }

      ws.onerror = () => {
        setState(s => ({ ...s, connected: false, error: 'WebSocket error' }))
      }

      ws.onclose = () => {
        setState(s => ({ ...s, connected: false }))
        const delay = Math.min(1000 * Math.pow(2, retryCount.current), 30000)
        retryCount.current += 1
        retryRef.current = setTimeout(connect, delay)
      }
    } catch (err) {
      setState(s => ({ ...s, error: String(err) }))
    }
  }, [])

  useEffect(() => {
    connect()
    const hb = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send('ping')
      }
    }, 20000)

    return () => {
      clearInterval(hb)
      if (retryRef.current) clearTimeout(retryRef.current)
      wsRef.current?.close()
    }
  }, [connect])

  return state
}
