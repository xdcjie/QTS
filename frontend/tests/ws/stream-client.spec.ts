import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { StreamClient, type StreamEvent } from '@/ws/stream-client'

type Listener = (event: MessageEvent<string>) => void

const WS_OPEN = 1
const WS_CONNECTING = 0

class FakeWebSocket {
  public readyState = WS_CONNECTING
  public sent: string[] = []
  public onopen: (() => void) | null = null
  public onmessage: Listener | null = null
  public onclose: (() => void) | null = null
  public onerror: ((error: Event) => void) | null = null

  constructor(public readonly url: string) {}

  public open(): void {
    this.readyState = WS_OPEN
    this.onopen?.()
  }

  public close(): void {
    this.readyState = 3
    this.onclose?.()
  }

  public send(payload: string): void {
    this.sent.push(payload)
  }

  public receive(payload: StreamEvent | { type: string }) {
    this.onmessage?.(new MessageEvent('message', { data: JSON.stringify(payload) }))
  }
}

describe('StreamClient', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  it('replays missed sequences and emits gap notifications', () => {
    const onMessage = vi.fn()
    const onSequenceGap = vi.fn()

    let socket: FakeWebSocket | null = null
    const socketFactory = vi.fn(() => {
      const created = new FakeWebSocket('ws://localhost/ws/events')
      socket = created
      return created as unknown as WebSocket
    })

    const client = new StreamClient('ws://localhost/ws/events', {
      heartbeatMs: 60_000,
      onMessage,
      onSequenceGap,
      onError: vi.fn(),
      onConnected: vi.fn(),
      websocketFactory: socketFactory,
    })

    client.connect()
    socket?.open()

    expect(socket?.sent).toEqual([JSON.stringify({ type: 'replay', from_sequence: 0 })])

    socket?.receive({ event_type: 'snapshot', sequence_number: 1, event_time_utc: '2026-01-01T00:00:00Z', payload: { samples: [] } })
    socket?.receive({ event_type: 'runtime_state_changed', sequence_number: 3, event_time_utc: '2026-01-01T00:00:01Z', payload: {} })

    expect(onMessage).toHaveBeenCalledTimes(1)
    expect(onSequenceGap).toHaveBeenCalledWith(1, 3)
    expect(socket?.sent[socket.sent.length - 1]).toBe(JSON.stringify({ type: 'replay', from_sequence: 1 }))

    socket?.receive({
      event_type: 'runtime_state_changed',
      sequence_number: 2,
      event_time_utc: '2026-01-01T00:00:02Z',
      payload: {},
      replayed: true,
    })
    socket?.receive({
      event_type: 'runtime_state_changed',
      sequence_number: 4,
      event_time_utc: '2026-01-01T00:00:03Z',
      payload: {},
      replayed: true,
    })

    expect(onMessage).toHaveBeenCalledTimes(4)
  })
})
