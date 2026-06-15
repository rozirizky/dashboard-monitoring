import { useState, useEffect, useRef, useCallback } from 'react'
import { Panel, PanelHeader, ChipGroup } from '../ui'

// ─── Types ────────────────────────────────────────────────────────────────────

interface HeatCell {
  symbol:   string
  name:     string
  change:   number
  category: 'crypto' | 'stock' | 'forex'
  // layout weight — bigger market cap / importance = bigger cell
  weight:   number
}

type Period = '24H' | '7D' | '1M'

const PERIODS: Period[] = ['24H', '7D', '1M']

// ─── Data sources ─────────────────────────────────────────────────────────────

// CoinGecko: top 15 by market cap, supports 1d / 7d / 30d change
const COIN_IDS = [
  'bitcoin', 'ethereum', 'binancecoin', 'solana', 'ripple',
  'cardano', 'avalanche-2', 'polkadot', 'chainlink', 'dogecoin',
  'shiba-inu', 'near', 'uniswap', 'litecoin', 'tron',
]

// Yahoo Finance symbols for stocks + forex
const YF_SYMBOLS = [
  // US Stocks
  'NVDA', 'AAPL', 'MSFT', 'GOOGL', 'META', 'AMZN', 'TSLA',
  // IDX
  'BBCA.JK', 'BBRI.JK', 'TLKM.JK',
  // Forex
  'EURUSD=X', 'USDJPY=X', 'GBPUSD=X', 'USDIDR=X', 'USDSGD=X',
]

// Market cap rank → weight (bigger = more visual space)
const WEIGHT_MAP: Record<string, number> = {
  bitcoin: 6, ethereum: 5, binancecoin: 3, solana: 3, ripple: 2,
  cardano: 2, avalanche: 2, NVDA: 3, AAPL: 3, MSFT: 3,
  GOOGL: 2, META: 2, AMZN: 2, TSLA: 2,
}

function coinWeight(id: string) {
  return WEIGHT_MAP[id] ?? WEIGHT_MAP[id.split('-')[0]] ?? 1
}

// ─── Color scale ──────────────────────────────────────────────────────────────
// Returns a CSS background color string based on % change value

function heatColor(pct: number): { bg: string; text: string } {
  const abs = Math.abs(pct)

  if (pct > 0) {
    if (abs >= 10) return { bg: 'rgba(16,185,129,0.55)',  text: '#6ee7b7' }
    if (abs >= 5)  return { bg: 'rgba(16,185,129,0.38)',  text: '#34d399' }
    if (abs >= 2)  return { bg: 'rgba(16,185,129,0.22)',  text: '#34d399' }
                   return { bg: 'rgba(16,185,129,0.10)',  text: '#6ee7b7' }
  } else if (pct < 0) {
    if (abs >= 10) return { bg: 'rgba(239,68,68,0.55)',   text: '#fca5a5' }
    if (abs >= 5)  return { bg: 'rgba(239,68,68,0.38)',   text: '#f87171' }
    if (abs >= 2)  return { bg: 'rgba(239,68,68,0.22)',   text: '#f87171' }
                   return { bg: 'rgba(239,68,68,0.10)',   text: '#fca5a5' }
  }
  return { bg: 'rgba(100,116,139,0.18)', text: '#64748b' }
}

// ─── Grid layout ──────────────────────────────────────────────────────────────
// Assign col/row span based on weight so bigger assets fill more space

interface CellLayout extends HeatCell {
  colSpan: number
  rowSpan: number
  bg:   string
  textColor: string
}

function buildLayout(cells: HeatCell[]): CellLayout[] {
  return cells.map(c => {
    const { bg, text } = heatColor(c.change)
    const span = c.weight >= 6 ? 2 : 1
    return {
      ...c,
      colSpan:   span,
      rowSpan:   span,
      bg,
      textColor: text,
    }
  })
}

// ─── Fetch helpers ────────────────────────────────────────────────────────────

async function fetchCryptoHeatmap(period: Period): Promise<HeatCell[]> {
  const pricePct = period === '24H' ? '24h'
                 : period === '7D'  ? '7d'
                 : '30d'

  const url = `https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids=${COIN_IDS.join(',')}&order=market_cap_desc&per_page=15&page=1&sparkline=false&price_change_percentage=${pricePct}`
  const res  = await fetch(url, { headers: { Accept: 'application/json' } })
  if (!res.ok) throw new Error(`CoinGecko ${res.status}`)
  const data: {
    id: string; symbol: string; name: string
    price_change_percentage_24h_in_currency?: number
    price_change_percentage_7d_in_currency?: number
    price_change_percentage_30d_in_currency?: number
    price_change_percentage_24h?: number
  }[] = await res.json()

  return data.map(c => ({
    symbol:   c.symbol.toUpperCase(),
    name:     c.name,
    change:   period === '24H'
                ? (c.price_change_percentage_24h_in_currency ?? c.price_change_percentage_24h ?? 0)
              : period === '7D'
                ? (c.price_change_percentage_7d_in_currency  ?? 0)
                : (c.price_change_percentage_30d_in_currency ?? 0),
    category: 'crypto' as const,
    weight:   coinWeight(c.id),
  }))
}

async function fetchYFHeatmap(): Promise<HeatCell[]> {
  const symbols = YF_SYMBOLS.join(',')
  const url = `https://query1.finance.yahoo.com/v7/finance/quote?symbols=${symbols}&lang=en-US&region=US&corsDomain=finance.yahoo.com`
  const res = await fetch(url, { headers: { Accept: 'application/json' } })
  if (!res.ok) throw new Error(`Yahoo Finance ${res.status}`)
  const data: {
    quoteResponse: {
      result: {
        symbol: string
        shortName?: string
        longName?: string
        regularMarketChangePercent: number
      }[]
    }
  } = await res.json()

  return (data.quoteResponse?.result ?? []).map(r => {
    const isForex  = r.symbol.endsWith('=X')
    const isTicker = !isForex && !r.symbol.endsWith('.JK')
    return {
      symbol:   r.symbol.replace('=X', '').replace('.JK', '').replace(/([A-Z]{3})([A-Z]{3})/, '$1/$2'),
      name:     r.shortName ?? r.longName ?? r.symbol,
      change:   r.regularMarketChangePercent ?? 0,
      category: isForex ? 'forex' as const : 'stock' as const,
      weight:   WEIGHT_MAP[r.symbol] ?? (isTicker ? 2 : 1),
    }
  })
}

// ─── Category badge ───────────────────────────────────────────────────────────

const CATEGORY_STYLE: Record<HeatCell['category'], string> = {
  crypto: 'text-violet-400/60',
  stock:  'text-blue-400/60',
  forex:  'text-amber-400/60',
}

// ─── Single heat cell ─────────────────────────────────────────────────────────

function HeatCell({ cell }: { cell: CellLayout }) {
  const isBig   = cell.colSpan > 1
  const sign    = cell.change >= 0 ? '+' : ''

  return (
    <div
      className="rounded-md flex flex-col items-center justify-center cursor-pointer transition-all hover:brightness-125 select-none overflow-hidden relative"
      style={{
        background: cell.bg,
        gridColumn: cell.colSpan > 1 ? `span ${cell.colSpan}` : undefined,
        gridRow:    cell.rowSpan > 1 ? `span ${cell.rowSpan}` : undefined,
      }}
      title={`${cell.name} — ${sign}${cell.change.toFixed(2)}%`}
    >
      {/* Category dot */}
      <span
        className={`absolute top-1.5 right-1.5 font-mono text-[7px] leading-none ${CATEGORY_STYLE[cell.category]}`}
      >
        {cell.category === 'crypto' ? '◆' : cell.category === 'stock' ? '▲' : '⬡'}
      </span>

      <span
        className="font-mono font-semibold leading-none mb-1 text-center px-1 truncate max-w-full"
        style={{
          fontSize:  isBig ? '13px' : '9px',
          color:     'rgba(255,255,255,0.55)',
        }}
      >
        {cell.symbol}
      </span>

      <span
        className="font-mono font-bold leading-none"
        style={{
          fontSize:  isBig ? '18px' : '11px',
          color:     cell.textColor,
        }}
      >
        {sign}{cell.change.toFixed(2)}%
      </span>

      {isBig && (
        <span
          className="font-mono mt-1 leading-none truncate max-w-[90%] text-center"
          style={{ fontSize: '10px', color: 'rgba(255,255,255,0.3)' }}
        >
          {cell.name}
        </span>
      )}
    </div>
  )
}

// ─── Legend ───────────────────────────────────────────────────────────────────

function Legend() {
  const steps = [
    { bg: 'rgba(239,68,68,0.55)',   label: '< -5%'  },
    { bg: 'rgba(239,68,68,0.22)',   label: '-5~-1%' },
    { bg: 'rgba(100,116,139,0.18)', label: '~0%'    },
    { bg: 'rgba(16,185,129,0.22)',  label: '+1~5%'  },
    { bg: 'rgba(16,185,129,0.55)',  label: '> +5%'  },
  ]
  return (
    <div className="flex items-center justify-center gap-3 px-4 pb-3 pt-1">
      {steps.map(s => (
        <div key={s.label} className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-sm" style={{ background: s.bg }} />
          <span className="font-mono text-[9px] text-slate-600">{s.label}</span>
        </div>
      ))}
    </div>
  )
}

function CategoryLegend() {
  return (
    <div className="flex items-center justify-center gap-4 px-4 pb-2">
      <span className="font-mono text-[9px] text-violet-400/60">◆ Crypto</span>
      <span className="font-mono text-[9px] text-blue-400/60">▲ Stock</span>
      <span className="font-mono text-[9px] text-amber-400/60">⬡ Forex</span>
    </div>
  )
}

// ─── Skeleton grid ────────────────────────────────────────────────────────────

function SkeletonGrid() {
  return (
    <div className="p-3 grid grid-cols-6 gap-1 animate-pulse" style={{ gridAutoRows: '56px' }}>
      {Array.from({ length: 24 }).map((_, i) => (
        <div
          key={i}
          className="rounded-md bg-white/[0.04]"
          style={{ gridColumn: i < 2 ? 'span 2' : undefined, gridRow: i < 2 ? 'span 2' : undefined }}
        />
      ))}
    </div>
  )
}

// ─── HeatmapPanel ─────────────────────────────────────────────────────────────

export function HeatmapPanel() {
  const [period,      setPeriod]      = useState<Period>('24H')
  const [cells,       setCells]       = useState<CellLayout[] | null>(null)
  const [loading,     setLoading]     = useState(false)
  const [error,       setError]       = useState(false)
  const [lastUpdated, setLastUpdated] = useState<string | null>(null)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const load = useCallback(async (p: Period) => {
    setLoading(true)
    setError(false)
    try {
      // Fetch crypto + stocks/forex in parallel; YF fallback silently skipped if CORS blocked
      const [cryptoCells, yfCells] = await Promise.allSettled([
        fetchCryptoHeatmap(p),
        fetchYFHeatmap(),
      ])

      const all: HeatCell[] = [
        ...(cryptoCells.status === 'fulfilled' ? cryptoCells.value : []),
        ...(yfCells.status    === 'fulfilled' ? yfCells.value    : []),
      ]

      setCells(buildLayout(all))
      setLastUpdated(
        new Date().toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' })
      )
    } catch {
      setError(true)
    } finally {
      setLoading(false)
    }
  }, [])

  // Load on mount + when period changes
  useEffect(() => {
    load(period)
  }, [period, load])

  // Auto-refresh every 90 seconds
  useEffect(() => {
    timerRef.current = setInterval(() => load(period), 90_000)
    return () => { if (timerRef.current) clearInterval(timerRef.current) }
  }, [period, load])

  return (
    <Panel>
      <PanelHeader title="Heatmap Pasar">
        <div className="flex items-center gap-2">
          {lastUpdated && (
            <span className="font-mono text-[9px] text-slate-600">{lastUpdated}</span>
          )}
          <button
            onClick={() => load(period)}
            disabled={loading}
            className="font-mono text-[10px] px-2 py-1 rounded border border-white/[0.06] text-slate-400 hover:border-white/20 bg-transparent cursor-pointer transition-all disabled:opacity-40"
          >
            <span className={loading ? 'inline-block animate-spin' : ''}>↻</span>
          </button>
          <ChipGroup
            options={PERIODS}
            value={period}
            onChange={(v) => setPeriod(v as Period)}
          />
        </div>
      </PanelHeader>

      {error ? (
        <div className="flex flex-col items-center justify-center py-10 gap-2">
          <p className="font-mono text-[11px] text-red-400/70">Gagal memuat data heatmap</p>
          <button
            onClick={() => load(period)}
            className="font-mono text-[10px] px-2.5 py-1 rounded border border-white/[0.06] text-slate-400 hover:border-white/20 bg-transparent cursor-pointer transition-all"
          >
            Coba lagi
          </button>
        </div>
      ) : !cells || loading ? (
        <SkeletonGrid />
      ) : (
        <div
          className="p-3 grid gap-1"
          style={{
            gridTemplateColumns: 'repeat(6, 1fr)',
            gridAutoRows: '56px',
          }}
        >
          {cells.map(cell => (
            <HeatCell key={`${cell.category}-${cell.symbol}`} cell={cell} />
          ))}
        </div>
      )}

      <Legend />
      <CategoryLegend />
    </Panel>
  )
}