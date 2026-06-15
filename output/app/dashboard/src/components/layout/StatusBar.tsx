import { useCountdown, useNow, useLatency } from '@/hooks/useTrending'

// ─── Types ────────────────────────────────────────────────────────────────────

interface StatusPill {
  dot?:        'live' | 'warn' | 'error' | 'none'
  label:       string
  value?:      string
  valueColor?: string
}

// ─── Latency pill helpers ─────────────────────────────────────────────────────

function latencyColor(ms: number | null, slowThreshold = 200): string {
  if (ms == null) return 'text-red-400'
  if (ms > slowThreshold) return 'text-amber-400'
  return 'text-emerald-400'
}

function latencyDot(ms: number | null): StatusPill['dot'] {
  if (ms == null) return 'error'
  if (ms > 200)   return 'warn'
  return 'live'
}

function latencyLabel(ms: number | null): string {
  return ms != null ? `${ms}ms` : 'N/A'
}

// ─── Individual pill ──────────────────────────────────────────────────────────

function Pill({ pill }: { pill: StatusPill }) {
  return (
    <div className="flex items-center gap-1.5 flex-shrink-0">
      {pill.dot && pill.dot !== 'none' && (
        <span
          className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${
            pill.dot === 'live'  ? 'bg-emerald-400 animate-pulse' :
            pill.dot === 'warn'  ? 'bg-amber-400' :
            pill.dot === 'error' ? 'bg-red-400'   : 'bg-slate-600'
          }`}
        />
      )}
      <span className="text-slate-600">{pill.label}</span>
      {pill.value && (
        <span className={pill.valueColor ?? 'text-slate-400'}>{pill.value}</span>
      )}
    </div>
  )
}

const Divider = () => <div className="h-3 w-px bg-white/[0.06] flex-shrink-0" />

// ─── StatusBar ────────────────────────────────────────────────────────────────

export function StatusBar() {
  const now       = useNow()
  const countdown = useCountdown(30)

  // Ping real public endpoints — no API key needed
  // CoinGecko ping (crypto data source)
  const coingecko = useLatency('https://api.coingecko.com/api/v3/ping', 30_000)
  // Yahoo Finance (stocks + forex source)
  const yahoo     = useLatency('https://query1.finance.yahoo.com', 30_000)
  // ExchangeRate API (forex fallback)
  const exrate    = useLatency('https://open.er-api.com/v6/latest/USD', 60_000)

  const timeStr = now.toLocaleTimeString('id-ID', {
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  })
  const dateStr = now.toLocaleDateString('id-ID', {
    weekday: 'long', day: 'numeric', month: 'short', year: 'numeric',
  })

  // Overall connection health
  const allOk    = coingecko.status === 'ok' && yahoo.status === 'ok'
  const anyError = coingecko.status === 'error' || yahoo.status === 'error'

  const pills: StatusPill[] = [
    // Overall data status
    {
      dot:        anyError ? 'error' : allOk ? 'live' : 'warn',
      label:      anyError ? 'Koneksi terputus' : allOk ? 'Live data' : 'Koneksi parsial',
      valueColor: anyError ? 'text-red-400' : allOk ? 'text-emerald-400' : 'text-amber-400',
    },
    // CoinGecko latency
    {
      dot:        latencyDot(coingecko.ms),
      label:      'CoinGecko:',
      value:      latencyLabel(coingecko.ms),
      valueColor: latencyColor(coingecko.ms),
    },
    // Yahoo Finance latency
    {
      dot:        latencyDot(yahoo.ms),
      label:      'Yahoo Finance:',
      value:      latencyLabel(yahoo.ms),
      valueColor: latencyColor(yahoo.ms),
    },
    // ExchangeRate fallback latency
    {
      dot:        latencyDot(exrate.ms),
      label:      'ExRate API:',
      value:      latencyLabel(exrate.ms),
      valueColor: latencyColor(exrate.ms, 300),
    },
    // Refresh countdown
    {
      label:      'Refresh:',
      value:      `00:${countdown}`,
      valueColor: 'text-slate-300',
    },
  ]

  return (
    <div className="flex items-center gap-4 px-4 py-2.5 bg-[#0d1117] border border-white/[0.06] rounded-lg font-mono text-[10px] overflow-x-auto scrollbar-none">
      {/* Date / time */}
      <span className="text-slate-500 flex-shrink-0">
        {dateStr} · {timeStr} WIB
      </span>

      <Divider />

      {pills.map((pill, i) => (
        <div key={i} className="contents">
          <Pill pill={pill} />
          {i < pills.length - 1 && <Divider />}
        </div>
      ))}
    </div>
  )
}