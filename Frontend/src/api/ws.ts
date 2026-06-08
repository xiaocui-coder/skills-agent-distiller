import type { WSEvent } from './types'

export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'reconnecting'

type OnEvent = (event: WSEvent) => void
type OnStatus = (status: ConnectionStatus) => void

export class WebSocketManager {
  private ws: WebSocket | null = null
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private backoff = 1000
  private failCount = 0
  private _status: ConnectionStatus = 'disconnected'
  private messageQueue: string[] = []

  constructor(
    private url: string,
    private onEvent: OnEvent,
    private onStatus: OnStatus,
  ) {}

  connect() {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return
    }
    this._setStatus('connecting')
    try {
      this.ws = new WebSocket(this.url)
      this.ws.onopen = () => {
        this.backoff = 1000
        this.failCount = 0
        this._setStatus('connected')
        while (this.messageQueue.length > 0) {
          this.ws?.send(this.messageQueue.shift()!)
        }
      }
      this.ws.onmessage = (e) => {
        try {
          const event = JSON.parse(e.data as string) as WSEvent
          this.onEvent(event)
        } catch {
          // skip non-JSON
        }
      }
      this.ws.onclose = () => {
        if (this._status !== 'disconnected') {
          this._scheduleReconnect()
        }
      }
      this.ws.onerror = () => {
        // onclose will fire after onerror
      }
    } catch {
      this._scheduleReconnect()
    }
  }

  disconnect() {
    this._status = 'disconnected'
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    this.messageQueue = []
    if (this.ws) {
      this.ws.onclose = null
      this.ws.close()
      this.ws = null
    }
  }

  send(data: { type: string; content: string; thread_id?: string }) {
    const msg = JSON.stringify(data)
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(msg)
    } else {
      this.messageQueue.push(msg)
    }
  }

  private _scheduleReconnect() {
    if (this.failCount >= 5) {
      this._setStatus('disconnected')
      return
    }
    this.failCount++
    this._setStatus('reconnecting')
    this.reconnectTimer = setTimeout(() => {
      this.connect()
    }, this.backoff)
    this.backoff = Math.min(this.backoff * 2, 30000)
  }

  private _setStatus(s: ConnectionStatus) {
    this._status = s
    this.onStatus(s)
  }

  get status() { return this._status }

  reconnect() {
    this.failCount = 0
    this.backoff = 1000
    if (this.ws) {
      this.ws.onclose = null
      this.ws.close()
      this.ws = null
    }
    this.connect()
  }
}
