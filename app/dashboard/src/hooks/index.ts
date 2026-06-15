import { useState, useEffect, useCallback, useRef } from 'react'
// ─── useCountdown ───────────────────────────────────────────────────────────
export function useCountdown(initialSeconds: number = 29) {
  const [seconds, setSeconds] = useState(initialSeconds)

  useEffect(() => {
    const timer = setInterval(() => {
      setSeconds(s => (s <= 0 ? initialSeconds : s - 1))
    }, 1000)
    return () => clearInterval(timer)
  }, [initialSeconds])

  return String(seconds).padStart(2, '0')
}

// ─── useLiveTicker ───────────────
// ─── useActiveTab ────────────────────────────────────────────────────────────
export function useActiveTab<T extends string>(initial: T) {
  const [active, setActive] = useState<T>(initial)
  return { active, setActive }
}

// ─── useFlicker ──────────────────────────────────────────────────────────────
export function useFlicker(intervalMs: number = 900) {
  const [flickering, setFlickering] = useState<Set<number>>(new Set())

  useEffect(() => {
    const interval = setInterval(() => {
      const indices = new Set<number>()
      for (let i = 0; i < 3; i++) {
        if (Math.random() > 0.6) indices.add(Math.floor(Math.random() * 10))
      }
      setFlickering(indices)
      setTimeout(() => setFlickering(new Set()), 150)
    }, intervalMs)
    return () => clearInterval(interval)
  }, [intervalMs])

  return flickering
}

// ─── useNow ──────────────────────────────────────────────────────────────────
export function useNow() {
  const [now, setNow] = useState(new Date())
  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(t)
  }, [])
  return now
}

// ─── useTickerScroll ─────────────────────────────────────────────────────────
export function useTickerScroll() {
  const ref = useRef<HTMLDivElement>(null)
  const posRef = useRef(0)
  const rafRef = useRef<number>(0)

  const animate = useCallback(() => {
    const el = ref.current
    if (!el) return
    posRef.current -= 0.5
    const half = el.scrollWidth / 2
    if (Math.abs(posRef.current) >= half) posRef.current = 0
    el.style.transform = `translateX(${posRef.current}px)`
    rafRef.current = requestAnimationFrame(animate)
  }, [])

  useEffect(() => {
    rafRef.current = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(rafRef.current)
  }, [animate])

  return ref
}
