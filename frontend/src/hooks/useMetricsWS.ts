import { useEffect, useState } from 'react'

import { StreamClient } from '@/ws/stream-client'

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

  useEffect(() => {
    const client = new StreamClient(WS_URL, {
      heartbeatMs: 20000,
      onConnected: () => {
        setState(s => ({ ...s, connected: true, error: null }))
      },
      onMessage: (event) => {
        if (event.event_type !== 'snapshot') {
          return
        }

        const payload = event.payload
        const samples = Array.isArray(payload?.samples) ? payload.samples : []
        const normalized = samples.map((raw): MetricSample => ({
          name: typeof (raw as Record<string, unknown>).name === 'string' ? String((raw as Record<string, unknown>).name) : '',
          value: typeof (raw as Record<string, unknown>).value === 'number'
            ? Number((raw as Record<string, unknown>).value)
            : 0,
          labels: (raw as Record<string, unknown>).labels && typeof (raw as Record<string, unknown>).labels === 'object'
            ? { ...(raw as Record<string, unknown>).labels as Record<string, string> }
            : {},
          count: typeof (raw as Record<string, unknown>).count === 'number'
            ? Number((raw as Record<string, unknown>).count)
            : 0,
          sum: typeof (raw as Record<string, unknown>).sum === 'number'
            ? Number((raw as Record<string, unknown>).sum)
            : 0,
          sampled_at_utc:
            typeof (raw as Record<string, unknown>).sampled_at_utc === 'string'
              ? String((raw as Record<string, unknown>).sampled_at_utc)
              : event.event_time_utc,
        }))

        setState((s) => ({
          ...s,
          latest: normalized,
          history: [...s.history.slice(-(MAX_HISTORY - 1)), normalized],
        }))
      },
      onSequenceGap: (fromSequence, receivedSequence) => {
        setState((s) => ({
          ...s,
          error: `Event stream gap detected (${fromSequence} → ${receivedSequence})`,
        }))
      },
      onError: (error) => {
        setState(s => ({ ...s, connected: false, error: error.message }))
      },
    })

    client.connect()

    return () => {
      client.close()
    }
  }, [])

  return state
}
