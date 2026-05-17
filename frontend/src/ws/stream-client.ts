import { useEffect } from 'react'

export interface StreamEvent<TPayload = Record<string, unknown>> {
  event_type: string
  sequence_number: number
  event_time_utc: string
  payload: TPayload
  replayed?: boolean
  correlation_id?: string | null
}

export interface StreamClientOptions {
  url: string
  heartbeatMs?: number
  reconnectBaseDelayMs?: number
  reconnectMaxDelayMs?: number
  onSequenceGap?: (fromSequence: number, receivedSequence: number) => void
  onMessage: (event: StreamEvent) => void
  onError?: (error: Error) => void
  onConnected?: () => void
  websocketFactory?: (url: string) => WebSocket
}

type ReplayRequest = {
  type: 'replay'
  from_sequence: number
}

export class StreamClient {
  private readonly websocketFactory: (url: string) => WebSocket
  private readonly heartbeatMs: number
  private readonly reconnectBaseDelayMs: number
  private readonly reconnectMaxDelayMs: number
  private readonly onMessage: (event: StreamEvent) => void
  private readonly onConnected?: () => void
  private readonly onError?: (error: Error) => void
  private readonly onSequenceGap?: (fromSequence: number, receivedSequence: number) => void

  private readonly url: string
  private reconnectAttempts = 0
  private socket: WebSocket | null = null
  private heartbeatHandle: number | null = null
  private lastSequence: number | null = null
  private pendingEvents: Map<number, StreamEvent> = new Map()
  private closedByUser = false

  public constructor(url: string, options: Omit<StreamClientOptions, 'url'>) {
    this.url = url
    this.websocketFactory = options.websocketFactory ?? ((socketUrl: string) => new WebSocket(socketUrl))
    this.heartbeatMs = options.heartbeatMs ?? 20_000
    this.reconnectBaseDelayMs = options.reconnectBaseDelayMs ?? 1000
    this.reconnectMaxDelayMs = options.reconnectMaxDelayMs ?? 30_000
    this.onMessage = options.onMessage
    this.onConnected = options.onConnected
    this.onError = options.onError
    this.onSequenceGap = options.onSequenceGap
  }

  public connect(): void {
    if (this.closedByUser) {
      return
    }

    const socket = this.websocketFactory(this.url)
    this.socket = socket

    socket.onopen = () => {
      this.reconnectAttempts = 0
      this.onConnected?.()
      this._startHeartbeat()
      this._requestReplay()
    }

    socket.onmessage = (event) => {
      this._handleMessage(event.data as string)
    }

    socket.onclose = () => {
      this._stopHeartbeat()
      if (this.closedByUser) {
        return
      }
      const delay = this._reconnectDelay()
      this.reconnectAttempts += 1
      window.setTimeout(() => this.connect(), delay)
    }

    socket.onerror = (error) => {
      this.onError?.(new Error(`WebSocket error: ${String(error)}`))
      socket.close()
    }
  }

  public close(): void {
    this.closedByUser = true
    this._stopHeartbeat()
    if (this.socket?.readyState === WebSocket.OPEN || this.socket?.readyState === WebSocket.CONNECTING) {
      this.socket.close()
    }
    this.socket = null
  }

  public setLastSequence(sequence: number): void {
    this.lastSequence = sequence
    this._flushPending()
  }

  private _reconnectDelay(): number {
    const delay = this.reconnectBaseDelayMs * 2 ** this.reconnectAttempts
    return Math.min(delay, this.reconnectMaxDelayMs)
  }

  private _startHeartbeat(): void {
    this._stopHeartbeat()
    this.heartbeatHandle = window.setInterval(() => {
      if (this.socket?.readyState === WebSocket.OPEN) {
        this.socket.send(JSON.stringify({ type: 'ping' }))
      }
    }, this.heartbeatMs)
  }

  private _stopHeartbeat(): void {
    if (this.heartbeatHandle !== null) {
      window.clearInterval(this.heartbeatHandle)
      this.heartbeatHandle = null
    }
  }

  private _requestReplay(): void {
    const socket = this.socket
    if (socket?.readyState !== WebSocket.OPEN) {
      return
    }

    const fromSequence = this.lastSequence ?? 0
      const payload: ReplayRequest = { type: 'replay', from_sequence: fromSequence }
    socket.send(JSON.stringify(payload))
  }

  private _handleMessage(raw: string): void {
    let parsed: unknown

    try {
      parsed = JSON.parse(raw)
    } catch {
      return
    }

    if (typeof parsed !== 'object' || parsed === null) {
      return
    }

    const event = parsed as Record<string, unknown>
    const eventType = event['event_type']
    const sequence = event['sequence_number']
    const payload = event['payload']

    if (typeof eventType !== 'string' || typeof sequence !== 'number' || typeof payload !== 'object' || payload === null) {
      return
    }

    const envelope: StreamEvent = {
      event_type: eventType,
      sequence_number: sequence,
      event_time_utc: typeof event['event_time_utc'] === 'string' ? event['event_time_utc'] : '',
      payload: payload as Record<string, unknown>,
      replayed: event['replayed'] === true,
      correlation_id: event['correlation_id'] as string | null | undefined,
    }

    if (eventType === 'stream.resync_required') {
      this.lastSequence = null
      this.pendingEvents.clear()
      this.onSequenceGap?.(0, sequence)
      return
    }

    if (this.lastSequence !== null) {
      const expected = this.lastSequence + 1
      if (!envelope.replayed && sequence < expected) {
        return
      }
      if (!envelope.replayed && sequence > expected) {
        this.pendingEvents.set(sequence, envelope)
        this.onSequenceGap?.(this.lastSequence, sequence)
        this._requestReplay()
        return
      }
    }

    this._applyAndFlush(envelope)
  }

  private _applyAndFlush(event: StreamEvent): void {
    this.lastSequence = event.sequence_number
    this.pendingEvents.delete(event.sequence_number)
    this.onMessage(event)

    if (event.replayed) {
      this._flushPending()
    }
  }

  private _flushPending(): void {
    while (this.lastSequence !== null) {
      const next = this.lastSequence + 1
      const event = this.pendingEvents.get(next)
      if (event === undefined) {
        break
      }
      this.pendingEvents.delete(next)
      this._applyAndFlush(event)
    }
  }
}

export const useStreamClientLifecycle = ({
  client,
  onCleanup,
}: {
  client: StreamClient | null
  onCleanup?: () => void
}): void => {
  useEffect(() => {
    return () => {
      client?.close()
      onCleanup?.()
    }
  }, [client, onCleanup])
}
