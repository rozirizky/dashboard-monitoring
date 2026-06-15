// ─────────────────────────────────────────────────────────────────────────────
//  ASSET DETAIL PAGES
//  CryptoPage  → /crypto
//  StocksPage  → /stocks
//  ForexPage   → /forex
//
//  Masing-masing page mengambil data dari backend (via trendingService),
//  menampilkan tabel detail + mini stat bar + filter/sort.
// ─────────────────────────────────────────────────────────────────────────────

import { useState, useEffect, useCallback, useRef } from 'react'
import {
  fetchAllCryptoDetail,
  fetchAllStocksDetail,
  fetchAllForexDetail,
  type CryptoDetailItem,
  type StockDetailItem,
  type ForexDetailItem,
} from '@/service/AssetsService'

// ─── Shared UI ────────────────────────────────────────────────────────────────

function PageShell({
  title,
  subtitle,
  accent,
  actions,
  children,
}: {
  title:    string
  subtitle: string
  accent:   string
  actions?: React.ReactNode
  children: React.ReactNode
}) {
  return (
    <main className="overflow-y-auto p-6 flex flex-col gap-5 min-h-0">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h1 className={`font-display text-[22px] font-bold tracking-tight text-slate-100 leading-none`}>
            {title.split(' ')[0]}{' '}
            <span className={accent}>{title.split(' ').slice(1).join(' ')}</span>
          </h1>
          <p className="font-mono text-[11px] text-slate-500 mt-1">{subtitle}</p>
        </div>
        {actions && <div className="flex items-center gap-2">{actions}</div>}
      </div>
      {children}
    </main>
  )
}

function StatCard({
  label, value, sub, accent,
}: {
  label: string; value: string; sub?: string; accent?: string
}) {
  return (
    <div className="rounded-lg border border-white/[0.06] bg-white/[0.02] px-4 py-3">
      <p className="font-mono text-[9px] text-slate-600 uppercase tracking-widest mb-1">{label}</p>
      <p className={`font-mono text-[15px] font-semibold ${accent ?? 'text-slate-100'}`}>{value}</p>
      {sub && <p className="font-mono text-[10px] text-slate-600 mt-0.5">{sub}</p>}
    </div>
  )
}

function SortHeader({
  label, field, active, dir, onSort,
}: {
  label: string
  field: string
  active: string
  dir: 'asc' | 'desc'
  onSort: (f: string) => void
}) {
  const isActive = active === field
  return (
    <button
      onClick={() => onSort(field)}
      className="flex items-center gap-1 font-mono text-[9px] uppercase tracking-widest text-slate-600 hover:text-slate-300 cursor-pointer transition-colors whitespace-nowrap"
    >
      {label}
      <span className={`text-[8px] ${isActive ? 'text-emerald-400' : 'text-slate-700'}`}>
        {isActive ? (dir === 'asc' ? '▲' : '▼') : '↕'}
      </span>
    </button>
  )
}

function ChangeChip({ pct }: { pct: number | null }) {
  if (pct == null) return <span className="font-mono text-[11px] text-slate-600">—</span>
  const up   = pct >= 0
  const sign = up ? '+' : ''
  const cls  = pct >= 5 ? 'text-emerald-300 font-semibold'
             : pct > 0  ? 'text-emerald-400'
             : pct > -5 ? 'text-red-400'
             :             'text-red-300 font-semibold'
  return <span className={`font-mono text-[11px] ${cls}`}>{sign}{pct.toFixed(2)}%</span>
}

function MiniBar({ pct }: { pct: number | null }) {
  const up  = (pct ?? 0) >= 0
  const abs = Math.min(Math.abs(pct ?? 0) / 10, 1)   // cap at 10%
  return (
    <div className="w-10 h-1 rounded-full bg-white/[0.06] overflow-hidden">
      <div
        className={`h-full rounded-full transition-all duration-500 ${up ? 'bg-emerald-400/60' : 'bg-red-400/60'}`}
        style={{ width: `${abs * 100}%` }}
      />
    </div>
  )
}

function SearchInput({ value, onChange, placeholder }: {
  value: string; onChange: (v: string) => void; placeholder: string
}) {
  return (
    <div className="relative">
      <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-600 text-[11px]">⌕</span>
      <input
        type="text"
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        className="font-mono text-[11px] bg-white/[0.03] border border-white/[0.07] rounded-lg pl-7 pr-3 py-1.5 text-slate-300 placeholder:text-slate-700 focus:outline-none focus:border-white/20 w-52 transition-colors"
      />
    </div>
  )
}

function RefreshBtn({ loading, onClick }: { loading: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      disabled={loading}
      className="font-mono text-[10px] px-3 py-1.5 rounded-lg border border-white/[0.06] text-slate-400 hover:border-white/20 bg-transparent cursor-pointer transition-all disabled:opacity-40 flex items-center gap-1.5"
    >
      <span className={loading ? 'inline-block animate-spin' : ''}>↻</span>
      {loading ? 'Memuat…' : 'Refresh'}
    </button>
  )
}

function TableShell({ headers, children }: { headers: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-white/[0.06] overflow-hidden">
      <table className="w-full border-collapse">
        <thead>
          <tr className="border-b border-white/[0.06] bg-white/[0.02]">
            {headers}
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  )
}

function Th({ children, align = 'left' }: { children: React.ReactNode; align?: 'left' | 'right' }) {
  return (
    <th className={`px-4 py-2.5 text-${align}`}>{children}</th>
  )
}

function Td({ children, align = 'left', cls = '' }: {
  children: React.ReactNode; align?: 'left' | 'right'; cls?: string
}) {
  return (
    <td className={`px-4 py-2.5 border-b border-white/[0.03] text-${align} ${cls}`}>
      {children}
    </td>
  )
}

function EmptyState({ message }: { message: string }) {
  return (
    <tr>
      <td colSpan={99} className="px-4 py-12 text-center">
        <p className="font-mono text-[11px] text-slate-600">{message}</p>
      </td>
    </tr>
  )
}

function SkeletonTableRows({ cols, n = 8 }: { cols: number; n?: number }) {
  return (
    <>
      {Array.from({ length: n }).map((_, i) => (
        <tr key={i} className="border-b border-white/[0.03] animate-pulse">
          {Array.from({ length: cols }).map((__, j) => (
            <td key={j} className="px-4 py-3">
              <div className="h-2.5 rounded bg-white/[0.04]" style={{ width: `${40 + (j * 17) % 40}%` }} />
            </td>
          ))}
        </tr>
      ))}
    </>
  )
}

function fmtPrice(n: number | null, decimals = 2): string {
  if (n == null) return '—'
  if (n < 0.0001) return `$${n.toFixed(8)}`
  if (n < 0.01)   return `$${n.toFixed(6)}`
  if (n < 1)      return `$${n.toFixed(4)}`
  return `$${n.toLocaleString('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}`
}

function fmtLargeNum(n: number | null): string {
  if (n == null) return '—'
  if (n >= 1e12) return `$${(n / 1e12).toFixed(2)}T`
  if (n >= 1e9)  return `$${(n / 1e9).toFixed(2)}B`
  if (n >= 1e6)  return `$${(n / 1e6).toFixed(2)}M`
  if (n >= 1e3)  return `$${(n / 1e3).toFixed(2)}K`
  return `$${n.toFixed(2)}`
}

function useSort<T>(items: T[], defaultField: keyof T) {
  const [field, setField] = useState<keyof T>(defaultField)
  const [dir,   setDir]   = useState<'asc' | 'desc'>('desc')

  const toggle = useCallback((f: string) => {
    const k = f as keyof T
    if (field === k) setDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setField(k); setDir('desc') }
  }, [field])

  const sorted = [...items].sort((a, b) => {
    const av = a[field] as number | string | null
    const bv = b[field] as number | string | null
    if (av == null && bv == null) return 0
    if (av == null) return 1
    if (bv == null) return -1
    const cmp = av < bv ? -1 : av > bv ? 1 : 0
    return dir === 'asc' ? cmp : -cmp
  })

  return { sorted, sortField: String(field), sortDir: dir, onSort: toggle }
}

// ─────────────────────────────────────────────────────────────────────────────
//  CRYPTO PAGE
// ─────────────────────────────────────────────────────────────────────────────

export function CryptoPage() {
  const [raw,     setRaw]     = useState<CryptoDetailItem[]>([])
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState(false)
  const [search,  setSearch]  = useState('')
  const [view,    setView]    = useState<'all' | 'gainers' | 'losers'>('all')
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const load = useCallback(async () => {
    setLoading(true); setError(false)
    try   { setRaw(await fetchAllCryptoDetail()) }
    catch { setError(true) }
    finally { setLoading(false) }
  }, [])

  useEffect(() => {
    load()
    timerRef.current = setInterval(load, 60_000)
    return () => { if (timerRef.current) clearInterval(timerRef.current) }
  }, [load])

  // Filter
  const filtered = raw.filter(c => {
    if (search && !c.symbol.toLowerCase().includes(search.toLowerCase()) &&
        !c.name.toLowerCase().includes(search.toLowerCase())) return false
    if (view === 'gainers') return (c.change24h ?? 0) > 0
    if (view === 'losers')  return (c.change24h ?? 0) < 0
    return true
  })

  const { sorted, sortField, sortDir, onSort } = useSort(filtered, 'marketCap' as keyof CryptoDetailItem)

  // Stats
  const valid     = raw.filter(c => c.change24h != null)
  const bullCount = valid.filter(c => (c.change24h ?? 0) > 0).length
  const totalMCap = raw.reduce((s, c) => s + (c.marketCap ?? 0), 0)
  const totalVol  = raw.reduce((s, c) => s + (c.volume24h ?? 0), 0)
  const avgChange = valid.length
    ? valid.reduce((s, c) => s + (c.change24h ?? 0), 0) / valid.length
    : null

  const VIEWS = [
    { id: 'all',     label: 'Semua' },
    { id: 'gainers', label: '▲ Naik' },
    { id: 'losers',  label: '▼ Turun' },
  ] as const

  return (
    <PageShell
      title="Crypto Market"
      subtitle="Data diperbarui tiap 15 menit via CoinGecko · Top 100 by market cap"
      accent="text-violet-400"
      actions={
        <>
          <SearchInput value={search} onChange={setSearch} placeholder="Cari symbol / nama…" />
          <RefreshBtn loading={loading} onClick={load} />
        </>
      }
    >
      {/* Stat cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <StatCard label="Total Market Cap" value={fmtLargeNum(totalMCap)} />
        <StatCard label="Volume 24h" value={fmtLargeNum(totalVol)} />
        <StatCard
          label="Avg. Perubahan 24h"
          value={avgChange != null ? `${avgChange >= 0 ? '+' : ''}${avgChange.toFixed(2)}%` : '—'}
          accent={avgChange != null ? (avgChange >= 0 ? 'text-emerald-400' : 'text-red-400') : undefined}
        />
        <StatCard
          label="Bullish / Total"
          value={`${bullCount} / ${valid.length}`}
          sub={valid.length ? `${((bullCount / valid.length) * 100).toFixed(0)}% pasar naik` : undefined}
          accent="text-emerald-400"
        />
      </div>

      {/* View toggle */}
      <div className="flex items-center gap-1">
        {VIEWS.map(v => (
          <button
            key={v.id}
            onClick={() => setView(v.id)}
            className={`font-mono text-[10px] px-3 py-1.5 rounded-lg cursor-pointer transition-all
              ${view === v.id
                ? 'bg-violet-400/10 border border-violet-400/30 text-violet-400'
                : 'border border-white/[0.06] text-slate-500 hover:text-slate-300 bg-transparent'
              }`}
          >
            {v.label}
          </button>
        ))}
        <span className="ml-2 font-mono text-[10px] text-slate-600">
          {sorted.length} aset
        </span>
      </div>

      {/* Table */}
      {error ? (
        <div className="flex flex-col items-center justify-center py-16 gap-2">
          <p className="font-mono text-[11px] text-red-400/70">Gagal memuat data</p>
          <button onClick={load} className="font-mono text-[10px] px-3 py-1 rounded border border-white/[0.06] text-slate-400 hover:border-white/20 bg-transparent cursor-pointer">
            Coba lagi
          </button>
        </div>
      ) : (
        <TableShell
          headers={
            <>
              <Th><SortHeader label="#"         field="rank"       active={sortField} dir={sortDir} onSort={onSort} /></Th>
              <Th><SortHeader label="Nama"      field="name"       active={sortField} dir={sortDir} onSort={onSort} /></Th>
              <Th align="right"><SortHeader label="Harga"     field="price"      active={sortField} dir={sortDir} onSort={onSort} /></Th>
              <Th align="right"><SortHeader label="24h"       field="change24h"  active={sortField} dir={sortDir} onSort={onSort} /></Th>
              <Th align="right"><SortHeader label="7d"        field="change7d"   active={sortField} dir={sortDir} onSort={onSort} /></Th>
              <Th align="right"><SortHeader label="Mkt Cap"   field="marketCap"  active={sortField} dir={sortDir} onSort={onSort} /></Th>
              <Th align="right"><SortHeader label="Volume 24h" field="volume24h" active={sortField} dir={sortDir} onSort={onSort} /></Th>
              <Th align="right">Trend</Th>
            </>
          }
        >
          {loading && !raw.length ? (
            <SkeletonTableRows cols={8} />
          ) : sorted.length === 0 ? (
            <EmptyState message="Tidak ada aset yang cocok" />
          ) : sorted.map((c, i) => (
            <tr
              key={c.symbol}
              className="hover:bg-white/[0.02] transition-colors cursor-pointer group"
            >
              <Td cls="font-mono text-[11px] text-slate-600">{c.rank ?? i + 1}</Td>
              <Td>
                <div className="flex items-center gap-2.5">
                  {c.thumb
                    ? <img src={c.thumb} alt={c.symbol} className="w-6 h-6 rounded-full flex-shrink-0" />
                    : <div className="w-6 h-6 rounded-full bg-white/[0.05] flex items-center justify-center flex-shrink-0">
                        <span className="font-mono text-[8px] text-slate-500">{c.symbol.slice(0, 2)}</span>
                      </div>
                  }
                  <div>
                    <p className="font-mono text-[12px] font-semibold text-slate-100">{c.symbol}</p>
                    <p className="font-mono text-[10px] text-slate-600">{c.name}</p>
                  </div>
                </div>
              </Td>
              <Td align="right" cls="font-mono text-[12px] text-slate-100">{fmtPrice(c.price)}</Td>
              <Td align="right"><ChangeChip pct={c.change24h} /></Td>
              <Td align="right"><ChangeChip pct={c.change7d} /></Td>
              <Td align="right" cls="font-mono text-[11px] text-slate-400">{fmtLargeNum(c.marketCap)}</Td>
              <Td align="right" cls="font-mono text-[11px] text-slate-400">{fmtLargeNum(c.volume24h)}</Td>
              <Td align="right"><MiniBar pct={c.change24h} /></Td>
            </tr>
          ))}
        </TableShell>
      )}
    </PageShell>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
//  STOCKS PAGE
// ─────────────────────────────────────────────────────────────────────────────

export function StocksPage() {
  const [raw,        setRaw]        = useState<StockDetailItem[]>([])
  const [loading,    setLoading]    = useState(false)
  const [error,      setError]      = useState(false)
  const [search,     setSearch]     = useState('')
  const [activeGroup, setGroup]     = useState<string>('All')
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const load = useCallback(async () => {
    setLoading(true); setError(false)
    try   { setRaw(await fetchAllStocksDetail()) }
    catch { setError(true) }
    finally { setLoading(false) }
  }, [])

  useEffect(() => {
    load()
    timerRef.current = setInterval(load, 60_000)
    return () => { if (timerRef.current) clearInterval(timerRef.current) }
  }, [load])

  const groups = ['All', ...Array.from(new Set(raw.map(s => s.group)))]

  const filtered = raw.filter(s => {
    if (activeGroup !== 'All' && s.group !== activeGroup) return false
    if (search && !s.ticker.toLowerCase().includes(search.toLowerCase()) &&
        !(s.shortName ?? '').toLowerCase().includes(search.toLowerCase())) return false
    return true
  })

  const { sorted, sortField, sortDir, onSort } = useSort(filtered, 'change' as keyof StockDetailItem)

  const valid     = raw.filter(s => s.change != null)
  const upCount   = valid.filter(s => (s.change ?? 0) > 0).length
  const best      = valid.reduce<StockDetailItem | null>((a, b) => (b.change! > (a?.change ?? -Infinity) ? b : a), null)
  const worst     = valid.reduce<StockDetailItem | null>((a, b) => (b.change! < (a?.change ??  Infinity) ? b : a), null)

  return (
    <PageShell
      title="Stocks Market"
      subtitle="US Tech · US Index · Indonesia (IDX) · Data via Yahoo Finance"
      accent="text-blue-400"
      actions={
        <>
          <SearchInput value={search} onChange={setSearch} placeholder="Cari ticker / nama…" />
          <RefreshBtn loading={loading} onClick={load} />
        </>
      }
    >
      {/* Stat cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <StatCard label="Total Aset" value={String(raw.length)} sub="saham dipantau" />
        <StatCard
          label="Naik / Turun"
          value={`${upCount} / ${valid.length - upCount}`}
          accent={upCount > valid.length / 2 ? 'text-emerald-400' : 'text-red-400'}
        />
        {best && (
          <StatCard
            label="Terbaik Hari Ini"
            value={best.ticker}
            sub={`+${best.change!.toFixed(2)}%`}
            accent="text-emerald-400"
          />
        )}
        {worst && (
          <StatCard
            label="Terburuk Hari Ini"
            value={worst.ticker}
            sub={`${worst.change!.toFixed(2)}%`}
            accent="text-red-400"
          />
        )}
      </div>

      {/* Group filter */}
      <div className="flex items-center gap-1 flex-wrap">
        {groups.map(g => (
          <button
            key={g}
            onClick={() => setGroup(g)}
            className={`font-mono text-[10px] px-3 py-1.5 rounded-lg cursor-pointer transition-all
              ${activeGroup === g
                ? 'bg-blue-400/10 border border-blue-400/30 text-blue-400'
                : 'border border-white/[0.06] text-slate-500 hover:text-slate-300 bg-transparent'
              }`}
          >
            {g}
          </button>
        ))}
        <span className="ml-2 font-mono text-[10px] text-slate-600">{sorted.length} aset</span>
      </div>

      {error ? (
        <div className="flex flex-col items-center justify-center py-16 gap-2">
          <p className="font-mono text-[11px] text-red-400/70">Gagal memuat data</p>
          <button onClick={load} className="font-mono text-[10px] px-3 py-1 rounded border border-white/[0.06] text-slate-400 hover:border-white/20 bg-transparent cursor-pointer">Coba lagi</button>
        </div>
      ) : (
        <TableShell
          headers={
            <>
              <Th><SortHeader label="Ticker"    field="ticker"    active={sortField} dir={sortDir} onSort={onSort} /></Th>
              <Th><SortHeader label="Nama"      field="shortName" active={sortField} dir={sortDir} onSort={onSort} /></Th>
              <Th><SortHeader label="Grup"      field="group"     active={sortField} dir={sortDir} onSort={onSort} /></Th>
              <Th align="right"><SortHeader label="Harga"    field="price"     active={sortField} dir={sortDir} onSort={onSort} /></Th>
              <Th align="right"><SortHeader label="Prev Close" field="prevClose" active={sortField} dir={sortDir} onSort={onSort} /></Th>
              <Th align="right"><SortHeader label="Perubahan" field="change"   active={sortField} dir={sortDir} onSort={onSort} /></Th>
              <Th align="right"><SortHeader label="Volume"   field="volume"    active={sortField} dir={sortDir} onSort={onSort} /></Th>
              <Th align="right">Trend</Th>
            </>
          }
        >
          {loading && !raw.length ? (
            <SkeletonTableRows cols={8} />
          ) : sorted.length === 0 ? (
            <EmptyState message="Tidak ada saham yang cocok" />
          ) : sorted.map(s => (
            <tr key={s.ticker} className="hover:bg-white/[0.02] transition-colors cursor-pointer">
              <Td>
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-md bg-white/[0.04] border border-white/[0.05] flex items-center justify-center">
                    <span className="font-mono text-[8px] font-bold text-slate-400">
                      {s.ticker.replace('.JK', '').replace('^', '').slice(0, 4)}
                    </span>
                  </div>
                  <span className="font-mono text-[12px] font-semibold text-slate-100">{s.ticker}</span>
                </div>
              </Td>
              <Td cls="font-mono text-[11px] text-slate-400">{s.shortName ?? '—'}</Td>
              <Td>
                <span className="font-mono text-[10px] px-2 py-0.5 rounded border border-blue-400/20 text-blue-400/80 bg-blue-400/[0.05]">
                  {s.group}
                </span>
              </Td>
              <Td align="right" cls="font-mono text-[12px] text-slate-100">
                {s.price != null
                  ? `$${s.price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                  : '—'}
              </Td>
              <Td align="right" cls="font-mono text-[11px] text-slate-600">
                {s.prevClose != null
                  ? `$${s.prevClose.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                  : '—'}
              </Td>
              <Td align="right"><ChangeChip pct={s.change} /></Td>
              <Td align="right" cls="font-mono text-[11px] text-slate-400">{fmtLargeNum(s.volume)}</Td>
              <Td align="right"><MiniBar pct={s.change} /></Td>
            </tr>
          ))}
        </TableShell>
      )}
    </PageShell>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
//  FOREX PAGE
// ─────────────────────────────────────────────────────────────────────────────

const FOREX_REGION_MAP: Record<string, string[]> = {
  Major:     ['EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CHF'],
  Commodity: ['AUD/USD', 'NZD/USD', 'USD/CAD'],
  Asia:      ['USD/IDR', 'USD/SGD', 'USD/CNY'],
}

function getRegion(pair: string): string {
  return Object.entries(FOREX_REGION_MAP).find(([, pairs]) => pairs.includes(pair))?.[0] ?? 'Other'
}

export function ForexPage() {
  const [raw,     setRaw]     = useState<ForexDetailItem[]>([])
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState(false)
  const [region,  setRegion]  = useState('All')
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const load = useCallback(async () => {
    setLoading(true); setError(false)
    try   { setRaw(await fetchAllForexDetail()) }
    catch { setError(true) }
    finally { setLoading(false) }
  }, [])

  useEffect(() => {
    load()
    timerRef.current = setInterval(load, 30_000)   // forex refresh lebih sering
    return () => { if (timerRef.current) clearInterval(timerRef.current) }
  }, [load])

  const withRegion = raw.map(f => ({ ...f, region: getRegion(f.pair) }))
  const regions    = ['All', ...Object.keys(FOREX_REGION_MAP)]

  const filtered = withRegion.filter(f =>
    region === 'All' || f.region === region
  )

  const { sorted, sortField, sortDir, onSort } = useSort(filtered, 'pair' as keyof typeof filtered[0])

  const idr       = raw.find(f => f.pair === 'USD/IDR')
  const valid     = raw.filter(f => f.change != null)
  const strongest = valid.reduce<ForexDetailItem | null>((a, b) => (b.change! > (a?.change ?? -Infinity) ? b : a), null)
  const weakest   = valid.reduce<ForexDetailItem | null>((a, b) => (b.change! < (a?.change ??  Infinity) ? b : a), null)

  return (
    <PageShell
      title="Forex Market"
      subtitle="10 pasangan mata uang utama · Yahoo Finance + ExchangeRate-API"
      accent="text-amber-400"
      actions={<RefreshBtn loading={loading} onClick={load} />}
    >
      {/* Stat cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {idr && (
          <StatCard
            label="USD / IDR"
            value={idr.rate.toLocaleString('id-ID', { maximumFractionDigits: 0 })}
            sub={idr.change != null ? `${idr.change >= 0 ? '+' : ''}${idr.change.toFixed(3)}% hari ini` : undefined}
            accent="text-amber-400"
          />
        )}
        <StatCard label="Pasangan Dipantau" value={String(raw.length)} />
        {strongest && strongest.pair !== 'USD/IDR' && (
          <StatCard
            label="Terkuat"
            value={strongest.pair}
            sub={`+${strongest.change!.toFixed(3)}%`}
            accent="text-emerald-400"
          />
        )}
        {weakest && weakest.pair !== strongest?.pair && (
          <StatCard
            label="Terlemah"
            value={weakest.pair}
            sub={`${weakest.change!.toFixed(3)}%`}
            accent="text-red-400"
          />
        )}
      </div>

      {/* Region filter */}
      <div className="flex items-center gap-1">
        {regions.map(r => (
          <button
            key={r}
            onClick={() => setRegion(r)}
            className={`font-mono text-[10px] px-3 py-1.5 rounded-lg cursor-pointer transition-all
              ${region === r
                ? 'bg-amber-400/10 border border-amber-400/30 text-amber-400'
                : 'border border-white/[0.06] text-slate-500 hover:text-slate-300 bg-transparent'
              }`}
          >
            {r}
          </button>
        ))}
        <span className="ml-2 font-mono text-[10px] text-slate-600">{sorted.length} pasangan</span>
      </div>

      {error ? (
        <div className="flex flex-col items-center justify-center py-16 gap-2">
          <p className="font-mono text-[11px] text-red-400/70">Gagal memuat data</p>
          <button onClick={load} className="font-mono text-[10px] px-3 py-1 rounded border border-white/[0.06] text-slate-400 hover:border-white/20 bg-transparent cursor-pointer">Coba lagi</button>
        </div>
      ) : (
        <TableShell
          headers={
            <>
              <Th><SortHeader label="Pasangan"  field="pair"   active={sortField} dir={sortDir} onSort={onSort} /></Th>
              <Th><SortHeader label="Region"    field="region" active={sortField} dir={sortDir} onSort={onSort} /></Th>
              <Th align="right"><SortHeader label="Rate"     field="rate"   active={sortField} dir={sortDir} onSort={onSort} /></Th>
              <Th align="right"><SortHeader label="Perubahan" field="change" active={sortField} dir={sortDir} onSort={onSort} /></Th>
              <Th align="right">Sumber</Th>
              <Th align="right">Trend</Th>
            </>
          }
        >
          {loading && !raw.length ? (
            <SkeletonTableRows cols={6} />
          ) : sorted.length === 0 ? (
            <EmptyState message="Tidak ada pasangan forex" />
          ) : sorted.map(f => {
            const [base, quote] = f.pair.split('/')
            const isIDR  = f.pair.includes('IDR')
            const isJPY  = f.pair.includes('JPY')
            const dec    = isIDR ? 0 : isJPY ? 3 : 5
            return (
              <tr key={f.pair} className={`hover:bg-white/[0.02] transition-colors cursor-pointer ${isIDR ? 'bg-amber-400/[0.015]' : ''}`}>
                <Td>
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-lg bg-white/[0.04] border border-white/[0.05] flex flex-col items-center justify-center flex-shrink-0 gap-px">
                      <span className="font-mono text-[7px] font-bold text-slate-300 leading-none">{base}</span>
                      <div className="w-4 h-px bg-white/20" />
                      <span className={`font-mono text-[7px] font-bold leading-none ${isIDR ? 'text-amber-400/70' : 'text-slate-500'}`}>{quote}</span>
                    </div>
                    <span className={`font-mono text-[13px] font-semibold ${isIDR ? 'text-amber-400' : 'text-slate-100'}`}>{f.pair}</span>
                  </div>
                </Td>
                <Td>
                  <span className="font-mono text-[10px] px-2 py-0.5 rounded border border-amber-400/20 text-amber-400/70 bg-amber-400/[0.04]">
                    {f.region}
                  </span>
                </Td>
                <Td align="right" cls="font-mono text-[13px] font-medium text-slate-100">
                  {f.rate.toLocaleString('en-US', { minimumFractionDigits: dec, maximumFractionDigits: dec })}
                </Td>
                <Td align="right"><ChangeChip pct={f.change} /></Td>
                <Td align="right">
                  <span className={`font-mono text-[10px] ${f.source === 'yahoo' ? 'text-slate-600' : 'text-amber-400/50'}`}>
                    {f.source}
                  </span>
                </Td>
                <Td align="right"><MiniBar pct={f.change} /></Td>
              </tr>
            )
          })}
        </TableShell>
      )}
    </PageShell>
  )
}