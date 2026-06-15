import { useState, useEffect, useRef } from 'react'

// ─── useNow ───────────────────────────────────────────────────────────────────
// Returns a Date that ticks every second

export function useNow(intervalMs = 1000): Date {
  const [now, setNow] = useState(() => new Date())

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), intervalMs)
    return () => clearInterval(id)
  }, [intervalMs])

  return now
}

// ─── useCountdown ─────────────────────────────────────────────────────────────
// Counts down from `seconds` to 0 then resets, returns zero-padded string "29" → "00"
// Also calls optional onReset callback each time it wraps

export function useCountdown(seconds: number, onReset?: () => void): string {
  const [remaining, setRemaining] = useState(seconds)
  const onResetRef = useRef(onReset)
  onResetRef.current = onReset

  useEffect(() => {
    const id = setInterval(() => {
      setRemaining(prev => {
        if (prev <= 1) {
          onResetRef.current?.()
          return seconds
        }
        return prev - 1
      })
    }, 1000)
    return () => clearInterval(id)
  }, [seconds])

  return String(remaining).padStart(2, '0')
}

// ─── useLatency ───────────────────────────────────────────────────────────────
// Pings an endpoint and returns round-trip latency in ms
// Falls back to null if fetch fails (CORS / offline)

export interface LatencyResult {
  ms:     number | null
  status: 'ok' | 'slow' | 'error'
}

function classify(ms: number | null): LatencyResult['status'] {
  if (ms == null)  return 'error'
  if (ms > 300)    return 'slow'
  return 'ok'
}

export function useLatency(url: string, intervalMs = 30_000): LatencyResult {
  const [result, setResult] = useState<LatencyResult>({ ms: null, status: 'ok' })

  const ping = useCallback(async () => {
    const t0 = performance.now()
    try {
      // HEAD is lighter; no-cache so we actually hit the server
      await fetch(url, { method: 'HEAD', cache: 'no-store', mode: 'no-cors' })
      const ms = Math.round(performance.now() - t0)
      setResult({ ms, status: classify(ms) })
    } catch {
      setResult({ ms: null, status: 'error' })
    }
  }, [url])

  useEffect(() => {
    ping()
    const id = setInterval(ping, intervalMs)
    return () => clearInterval(id)
  }, [ping, intervalMs])

  return result
}

// ─── useWebSocket ─────────────────────────────────────────────────────────────
// Lightweight WS connection status tracker

export type WsStatus = 'connecting' | 'open' | 'closed' | 'error'

export function useWebSocketStatus(url: string): WsStatus {
  const [status, setStatus] = useState<WsStatus>('connecting')
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    let alive = true

    function connect() {
      try {
        const ws = new WebSocket(url)
        wsRef.current = ws
        ws.onopen  = () => { if (alive) setStatus('open') }
        ws.onclose = () => { if (alive) { setStatus('closed'); setTimeout(connect, 5000) } }
        ws.onerror = () => { if (alive) setStatus('error') }
      } catch {
        setStatus('error')
      }
    }

    connect()
    return () => {
      alive = false
      wsRef.current?.close()
    }
  }, [url])

  return status
}

// re-export useCallback so consumers don't need a separate import
import { useCallback } from 'react'
export { useCallback }