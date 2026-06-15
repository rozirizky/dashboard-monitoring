import { useEffect, useRef, useState, useCallback, createContext, useContext } from 'react'
import { Panel, PanelHeader } from '../ui'
import {
  fetchTrendingData,
  type TrendingCoin,
  type CoinGainerLoser,
  type StockItem,
  type ForexPair,
  type TrendingData,
  STOCK_WATCHLIST,
} from '@/service/TrendingService'

// ─────────────────────────────────────────────────────────────────────────────
//  SHARED DATA CONTEXT
//  Semua panel share satu fetch — tidak ada duplikasi request ke backend.
// ─────────────────────────────────────────────────────────────────────────────

interface TrendingCtx {
  data:        TrendingData | null
  loading:     boolean
  error:       boolean
  lastUpdated: string | null
  refresh:     () => void
}

const TrendingContext = createContext<TrendingCtx>({
  data: null, loading: false, error: false, lastUpdated: null, refresh: () => {},
})

export function TrendingDataProvider({ children, refreshInterval = 60_000 }: {
  children: React.ReactNode
  refreshInterval?: number
}) {
  const [data,        setData]        = useState<TrendingData | null>(null)
  const [loading,     setLoading]     = useState(false)
  const [error,       setError]       = useState(false)
  const [lastUpdated, setLastUpdated] = useState<string | null>(null)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(false)
    try {
      const result = await fetchTrendingData()
      setData(result)
      setLastUpdated(
        result.lastUpdated.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' })
      )
    } catch (e) {
      console.error('[TrendingData] fetch error:', e)
      setError(true)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
    timerRef.current = setInterval(load, refreshInterval)
    return () => { if (timerRef.current) clearInterval(timerRef.current) }
  }, [load, refreshInterval])

  return (
    <TrendingContext.Provider value={{ data, loading, error, lastUpdated, refresh: load }}>
      {children}
    </TrendingContext.Provider>
  )
}

function useTrending() {
  return useContext(TrendingContext)
}

// ─────────────────────────────────────────────────────────────────────────────
//  SHARED UI HELPERS
// ─────────────────────────────────────────────────────────────────────────────

function fmtPrice(n: number | null): string {
  if (n == null) return '—'
  if (n < 0.01)  return `$${n.toFixed(6)}`
  if (n < 1)     return `$${n.toFixed(4)}`
  return `$${n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

function fmtVolume(n: number | null): string {
  if (n == null) return '—'
  if (n >= 1e9)  return `$${(n / 1e9).toFixed(1)}B`
  if (n >= 1e6)  return `$${(n / 1e6).toFixed(1)}M`
  if (n >= 1e3)  return `$${(n / 1e3).toFixed(1)}K`
  return `$${n.toFixed(2)}`
}

function ChangeLabel({ pct }: { pct: number | null }) {
  if (pct == null) return <span className="font-mono text-[10px] text-slate-600">—</span>
  const sign = pct >= 0 ? '+' : ''
  const cls  = pct >= 0 ? 'text-emerald-400' : 'text-red-400'
  return <span className={`font-mono text-[10px] ${cls}`}>{sign}{pct.toFixed(2)}%</span>
}

function SparkBars({ pct }: { pct: number | null }) {
  const up = (pct ?? 0) >= 0
  const h  = [3, 6, 4, 8, 5, 7, up ? 10 : 2]
  return (
    <div className="flex items-end gap-px h-3 flex-shrink-0">
      {h.map((v, i) => (
        <div
          key={i}
          className={`w-[3px] rounded-sm ${up ? 'bg-emerald-400/40' : 'bg-red-400/40'}`}
          style={{ height: `${v}px` }}
        />
      ))}
    </div>
  )
}

function SkeletonRows({ n = 6 }: { n?: number }) {
  return (
    <>
      {Array.from({ length: n }).map((_, i) => (
        <div key={i} className="flex items-center gap-3 px-4 py-2.5 border-b border-white/[0.03] animate-pulse">
          <div className="w-8 h-8 rounded-lg bg-white/[0.04] flex-shrink-0" />
          <div className="flex-1 space-y-1.5">
            <div className="h-2.5 w-20 bg-white/[0.04] rounded" />
            <div className="h-2 w-14 bg-white/[0.03] rounded" />
          </div>
          <div className="space-y-1.5 text-right">
            <div className="h-2.5 w-16 bg-white/[0.04] rounded ml-auto" />
            <div className="h-2 w-10 bg-white/[0.03] rounded ml-auto" />
          </div>
        </div>
      ))}
    </>
  )
}

function ErrorState({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-8 gap-2">
      <p className="font-mono text-[11px] text-red-400/70">Gagal memuat data</p>
      <button
        onClick={onRetry}
        className="font-mono text-[10px] px-2.5 py-1 rounded border border-white/[0.06] text-slate-400 hover:border-white/20 bg-transparent cursor-pointer transition-all"
      >
        Coba lagi
      </button>
    </div>
  )
}

function DataAge({ fetchedAt }: { fetchedAt: string | null | undefined }) {
  // Tampilkan seberapa lama data dari DB (bukan waktu fetch frontend)
  if (!fetchedAt) return null
  const diff = Math.floor((Date.now() - new Date(fetchedAt).getTime()) / 1000)
  const label = diff < 60
    ? `${diff}d lalu`
    : `${Math.floor(diff / 60)}m lalu`
  const cls = diff > 600 ? 'text-amber-400/60' : 'text-slate-700'
  return <span className={`font-mono text-[9px] ${cls}`}>{label}</span>
}

function RefreshBtn({ loading, onClick, lastUpdated }: {
  loading: boolean
  onClick: () => void
  lastUpdated: string | null
}) {
  return (
    <div className="flex items-center gap-2">
      {lastUpdated && (
        <span className="font-mono text-[9px] text-slate-600">{lastUpdated}</span>
      )}
      <button
        onClick={onClick}
        disabled={loading}
        className="font-mono text-[10px] px-2 py-1 rounded border border-white/[0.06] text-slate-400 hover:border-white/20 bg-transparent cursor-pointer transition-all disabled:opacity-40 disabled:cursor-not-allowed"
      >
        <span className={loading ? 'inline-block animate-spin' : ''}>↻</span>
      </button>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
//  1. CRYPTO TRENDING PANEL
// ─────────────────────────────────────────────────────────────────────────────

type CryptoView = 'trending' | 'gainers' | 'losers'

function CryptoSummaryBar({ trending, gainers, losers }: {
  trending: TrendingCoin[]
  gainers:  CoinGainerLoser[]
  losers:   CoinGainerLoser[]
}) {
  const bullCount = trending.filter(c => (c.change24h ?? 0) >= 0).length
  const top  = gainers[0]
  const bot  = losers[0]
  return (
    <div className="flex items-center gap-5 px-4 py-2 border-b border-white/[0.05] bg-white/[0.01]">
      {top && (
        <div>
          <p className="font-mono text-[9px] text-slate-600 uppercase tracking-widest">Top Gainer</p>
          <p className="font-mono text-[11px] text-emerald-400 font-medium">
            {top.symbol} +{top.change24h.toFixed(1)}%
          </p>
        </div>
      )}
      {bot && (
        <div>
          <p className="font-mono text-[9px] text-slate-600 uppercase tracking-widest">Top Loser</p>
          <p className="font-mono text-[11px] text-red-400 font-medium">
            {bot.symbol} {bot.change24h.toFixed(1)}%
          </p>
        </div>
      )}
      <div className="ml-auto flex items-center gap-2">
        <p className="font-mono text-[9px] text-slate-600 uppercase tracking-widest">Bullish</p>
        <div className="flex items-center gap-1.5">
          <div className="h-1 w-14 rounded-full bg-white/[0.06] overflow-hidden">
            <div
              className="h-full bg-emerald-400/50 rounded-full transition-all duration-700"
              style={{ width: `${(bullCount / Math.max(trending.length, 1)) * 100}%` }}
            />
          </div>
          <span className="font-mono text-[10px] text-slate-500">{bullCount}/{trending.length}</span>
        </div>
      </div>
    </div>
  )
}

function TrendingCoinRow({ coin }: { coin: TrendingCoin }) {
  return (

    <div className="flex items-center gap-3 px-4 py-2.5 border-b border-white/[0.03] hover:bg-white/[0.02] cursor-pointer transition-all">
      <div className="relative w-8 h-8 rounded-lg bg-white/[0.04] border border-white/[0.05] flex items-center justify-center flex-shrink-0 overflow-hidden">
        {coin.thumb
          ? <img src={coin.thumb} alt={coin.symbol} className="w-5 h-5 object-contain" />
          : <span className="font-mono text-[9px] font-bold text-slate-500">{coin.symbol.slice(0, 2)}</span>
        }
        <span className="absolute bottom-0 right-0 bg-slate-950/80 font-mono text-[7px] text-slate-500 px-0.5 leading-none">
          #{coin.rank}
        </span>
      </div>
      <div className="flex-1 min-w-0">
        <div className="font-display text-[12px] font-semibold text-slate-100">{coin.symbol}</div>
        <div className="font-mono text-[10px] text-slate-600 truncate">{coin.name}</div>
      </div>
      <SparkBars pct={coin.change24h} />
      <div className="text-right min-w-[70px]">
        <div className="font-mono text-[12px] text-slate-100">{fmtPrice(coin.price)}</div>
        <ChangeLabel pct={coin.change24h} />
      </div>
      <div className="text-right min-w-[48px] hidden lg:block">
        <div className="font-mono text-[10px] text-slate-600">{fmtVolume(coin.volume24h)}</div>
        <div className="font-mono text-[9px] text-slate-700">vol</div>
      </div>
    </div>
  )
}

function GainerLoserRow({ coin, type }: { coin: CoinGainerLoser; type: 'gainer' | 'loser' }) {
  const isUp   = type === 'gainer'
  const accent = isUp ? 'text-emerald-400' : 'text-red-400'
  const bar    = isUp ? 'bg-emerald-400/[0.04]' : 'bg-red-400/[0.04]'
  const border = isUp ? 'border-l-emerald-400/30' : 'border-l-red-400/30'
  return (
    <div className={`flex items-center gap-3 px-4 py-2.5 border-b border-white/[0.03] border-l-2 ${border} ${bar} hover:brightness-110 cursor-pointer transition-all`}>
      <div className="w-8 h-8 rounded-lg bg-white/[0.04] border border-white/[0.05] flex items-center justify-center flex-shrink-0">
        <span className="font-mono text-[9px] font-bold text-slate-400">{coin.symbol.slice(0, 3)}</span>
      </div>
      <div className="flex-1 min-w-0">
        <div className="font-display text-[12px] font-semibold text-slate-100">{coin.symbol}</div>
        <div className="font-mono text-[10px] text-slate-600 truncate">{coin.name}</div>
      </div>
      <div className="text-right">
        <div className="font-mono text-[12px] text-slate-100">{fmtPrice(coin.price)}</div>
        <span className={`font-mono text-[10px] font-semibold ${accent}`}>
          {coin.change24h >= 0 ? '+' : ''}{coin.change24h.toFixed(2)}%
        </span>
      </div>
      <div className="text-right hidden lg:block min-w-[48px]">
        <div className="font-mono text-[10px] text-slate-600">{fmtVolume(coin.volume)}</div>
        <div className="font-mono text-[9px] text-slate-700">vol</div>
      </div>
    </div>
  )
}

export function CryptoTrendingPanel() {
  const { data, loading, error, lastUpdated, refresh } = useTrending()
  const [view, setView] = useState<CryptoView>('trending')

  const VIEW_LABELS: Record<CryptoView, string> = {
    trending: 'Trending', gainers: 'Gainers', losers: 'Losers',
  }

  const crypto = data?.crypto

  return (
    <Panel> 
      <PanelHeader title="Crypto" >
        <div className="flex items-center gap-2 overflow-y-auto height-[500px]" >
          <DataAge fetchedAt={data?.fetchedAt?.coingecko_trending} />
          <RefreshBtn loading={loading} onClick={refresh} lastUpdated={lastUpdated} />
        </div>
      </PanelHeader>

      {/* Sub-nav */}
      <div className="flex items-center gap-px px-4 py-2 border-b border-white/[0.04]">
        {(['trending', 'gainers', 'losers'] as CryptoView[]).map(v => (
          <button
            key={v}
            onClick={() => setView(v)}
            className={`font-mono text-[10px] px-2.5 py-1 rounded cursor-pointer transition-all
              ${view === v
                ? 'text-emerald-400 bg-emerald-400/[0.08]'
                : 'text-slate-600 hover:text-slate-400'
              }`}
          >
            {VIEW_LABELS[v]}
          </button>
        ))}
      </div>

      {error ? (
        <ErrorState onRetry={refresh} />
      ) : !crypto ? (
        <SkeletonRows n={8} />
      ) : (
        <div className="overflow-y-auto h-[350px]">
          <CryptoSummaryBar
            trending={crypto.trending}
            gainers={crypto.gainers}
            losers={crypto.losers}
          />
          {view === 'trending' && crypto.trending.map(c => (
            <TrendingCoinRow key={c.symbol} coin={c} />
          ))}
          {view === 'gainers' && crypto.gainers.map(c => (
            <GainerLoserRow key={c.symbol} coin={c} type="gainer" />
          ))}
          {view === 'losers' && crypto.losers.map(c => (
            <GainerLoserRow key={c.symbol} coin={c} type="loser" />
          ))}
        </div>
      )}
    </Panel>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
//  2. STOCKS TRENDING PANEL
// ─────────────────────────────────────────────────────────────────────────────

function StocksSummaryBar({ data }: { data: StockItem[] }) {
  const valid   = data.filter(s => s.change != null)
  if (!valid.length) return null
  const top     = valid.reduce((a, b) => (b.change! > (a.change ?? -Infinity) ? b : a), valid[0])
  const bot     = valid.reduce((a, b) => (b.change! < (a.change ?? Infinity)  ? b : a), valid[0])
  const upCount = valid.filter(s => (s.change ?? 0) >= 0).length

  return (
    <div className="flex items-center gap-5 px-4 py-2 border-b border-white/[0.05] bg-white/[0.01]">
      {top && (
        <div>
          <p className="font-mono text-[9px] text-slate-600 uppercase tracking-widest">Best</p>
          <p className="font-mono text-[11px] text-emerald-400 font-medium">
            {top.ticker} {top.change! >= 0 ? '+' : ''}{top.change!.toFixed(2)}%
          </p>
        </div>
      )}
      {bot && bot.ticker !== top?.ticker && (
        <div>
          <p className="font-mono text-[9px] text-slate-600 uppercase tracking-widest">Worst</p>
          <p className="font-mono text-[11px] text-red-400 font-medium">
            {bot.ticker} {bot.change!.toFixed(2)}%
          </p>
        </div>
      )}
      <div className="ml-auto text-right">
        <p className="font-mono text-[9px] text-slate-600 uppercase tracking-widest">Up / Total</p>
        <p className="font-mono text-[11px] text-slate-300 font-medium">{upCount}/{valid.length}</p>
      </div>
    </div>
  )
}

function StockRow({ item }: { item: StockItem }) {
  const displayTicker = item.ticker.replace('.JK', '').replace('^', '')
  return (
    <div className="flex items-center gap-3 px-4 py-2.5 border-b border-white/[0.03] hover:bg-white/[0.02] cursor-pointer transition-all">
      <div className="w-8 h-8 rounded-lg bg-white/[0.04] border border-white/[0.05] flex items-center justify-center flex-shrink-0">
        <span className="font-mono text-[8px] font-bold text-slate-400 leading-tight text-center px-0.5">
          {displayTicker.slice(0, 4)}
        </span>
      </div>
      <div className="flex-1 min-w-0">
        <div className="font-display text-[12px] font-semibold text-slate-100">{item.ticker}</div>
        <div className="font-mono text-[10px] text-slate-600">
          {item.shortName ?? item.group}
        </div>
      </div>
      <SparkBars pct={item.change} />
      <div className="text-right min-w-[80px]">
        <div className="font-mono text-[12px] text-slate-100">
          {item.price != null
            ? `$${item.price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
            : '—'}
        </div>
        <ChangeLabel pct={item.change} />
      </div>
    </div>
  )
}

export function StocksTrendingPanel() {
  const { data, loading, error, lastUpdated, refresh } = useTrending()
  const [activeGroup, setActiveGroup] = useState<string>('All')

  const groups   = ['All', ...Object.keys(STOCK_WATCHLIST)]
  const stocks   = data?.stocks ?? null
  const filtered = stocks
    ? activeGroup === 'All' ? stocks : stocks.filter(s => s.group === activeGroup)
    : null

  return (
    <Panel>
      <PanelHeader title="Stocks">
        <div className="flex items-center gap-2">
          <DataAge fetchedAt={data?.fetchedAt?.yfinance_stocks} />
          <RefreshBtn loading={loading} onClick={refresh} lastUpdated={lastUpdated} />
        </div>
      </PanelHeader>

      {/* Group filter */}
      <div className="flex items-center gap-px px-4 py-2 border-b border-white/[0.04] overflow-x-auto scrollbar-none">
        {groups.map(g => (
          <button
            key={g}
            onClick={() => setActiveGroup(g)}
            className={`font-mono text-[10px] px-2.5 py-1 rounded cursor-pointer transition-all whitespace-nowrap flex-shrink-0
              ${activeGroup === g
                ? 'text-blue-400 bg-blue-400/[0.08]'
                : 'text-slate-600 hover:text-slate-400'
              }`}
          >
            {g}
          </button>
        ))}
      </div>

      {error ? (
        <ErrorState onRetry={refresh} />
      ) : !filtered ? (
        <SkeletonRows n={8} />
      ) : (
        <div className="overflow-y-auto h-[350px]">
          <StocksSummaryBar data={filtered} />
          {filtered.map(item => <StockRow key={item.ticker} item={item} />)}
        </div>
      )}
    </Panel>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
//  3. FOREX TRENDING PANEL
// ─────────────────────────────────────────────────────────────────────────────

const FOREX_GROUPS: Record<string, string[]> = {
  'Major':     ['EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CHF'],
  'Commodity': ['AUD/USD', 'NZD/USD', 'USD/CAD'],
  'Asia':      ['USD/IDR', 'USD/SGD', 'USD/CNY'],
}

function ForexSummaryBar({ data }: { data: ForexPair[] }) {
  const idr   = data.find(f => f.pair === 'USD/IDR')
  const valid = data.filter(f => f.change != null)
  const topUp = valid.reduce<ForexPair | null>((a, b) => (b.change! > (a?.change ?? -Infinity) ? b : a), null)
  const topDn = valid.reduce<ForexPair | null>((a, b) => (b.change! < (a?.change ??  Infinity) ? b : a), null)

  return (
    <div className="flex items-center gap-5 px-4 py-2 border-b border-white/[0.05] bg-white/[0.01]">
      {idr && (
        <div>
          <p className="font-mono text-[9px] text-slate-600 uppercase tracking-widest">USD/IDR</p>
          <p className="font-mono text-[11px] text-amber-400 font-medium">
            {idr.rate.toLocaleString('id-ID', { maximumFractionDigits: 0 })}
          </p>
        </div>
      )}
      {topUp && topUp.pair !== 'USD/IDR' && (
        <div>
          <p className="font-mono text-[9px] text-slate-600 uppercase tracking-widest">Strongest</p>
          <p className="font-mono text-[11px] text-emerald-400 font-medium">
            {topUp.pair} +{topUp.change!.toFixed(2)}%
          </p>
        </div>
      )}
      {topDn && topDn.pair !== topUp?.pair && (
        <div>
          <p className="font-mono text-[9px] text-slate-600 uppercase tracking-widest">Weakest</p>
          <p className="font-mono text-[11px] text-red-400 font-medium">
            {topDn.pair} {topDn.change!.toFixed(2)}%
          </p>
        </div>
      )}
    </div>
  )
}

function ForexRow({ pair }: { pair: ForexPair }) {
  const isIDR    = pair.pair.includes('IDR')
  const isJPY    = pair.pair.includes('JPY')
  const decimals = isIDR ? 0 : isJPY ? 3 : 5
  const [base, quote] = pair.pair.split('/')

  return (
    <div className={`flex items-center gap-3 px-4 py-2.5 border-b border-white/[0.03] hover:bg-white/[0.02] cursor-pointer transition-all
      ${isIDR ? 'bg-amber-400/[0.02]' : ''}`}
    >
      <div className="w-8 h-8 rounded-lg bg-white/[0.04] border border-white/[0.05] flex flex-col items-center justify-center flex-shrink-0 gap-px">
        <span className="font-mono text-[7px] font-bold text-slate-300 leading-none">{base}</span>
        <div className="w-4 h-px bg-white/20" />
        <span className={`font-mono text-[7px] font-bold leading-none ${isIDR ? 'text-amber-400/70' : 'text-slate-500'}`}>{quote}</span>
      </div>
      <div className="flex-1 min-w-0">
        <div className="font-display text-[12px] font-semibold text-slate-100">{pair.pair}</div>
        <div className="font-mono text-[9px] mt-px">
          {isIDR
            ? <span className="text-amber-400/50">Rupiah</span>
            : <span className="text-slate-700">{pair.source}</span>
          }
        </div>
      </div>
      <SparkBars pct={pair.change} />
      <div className="text-right min-w-[90px]">
        <div className="font-mono text-[12px] text-slate-100">
          {pair.rate.toLocaleString('en-US', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals,
          })}
        </div>
        <ChangeLabel pct={pair.change} />
      </div>
    </div>
  )
}

export function ForexTrendingPanel() {
  const { data, loading, error, lastUpdated, refresh } = useTrending()
  const [activeGroup, setActiveGroup] = useState<string>('All')

  const groups = ['All', ...Object.keys(FOREX_GROUPS)]
  const forex  = data?.forex ?? null
  const filtered = forex
    ? activeGroup === 'All'
      ? forex
      : forex.filter(f => FOREX_GROUPS[activeGroup]?.includes(f.pair))
    : null

  return (
    <Panel>
      <PanelHeader title="Forex">
        <div className="flex items-center gap-2">
          <DataAge fetchedAt={data?.fetchedAt?.forex} />
          <RefreshBtn loading={loading} onClick={refresh} lastUpdated={lastUpdated} />
        </div>
      </PanelHeader>

      {/* Region filter */}
      <div className="flex items-center gap-px px-4 py-2 border-b border-white/[0.04]">
        {groups.map(g => (
          <button
            key={g}
            onClick={() => setActiveGroup(g)}
            className={`font-mono text-[10px] px-2.5 py-1 rounded cursor-pointer transition-all
              ${activeGroup === g
                ? 'text-amber-400 bg-amber-400/[0.08]'
                : 'text-slate-600 hover:text-slate-400'
              }`}
          >
            {g}
          </button>
        ))}
      </div>

      {error ? (
        <ErrorState onRetry={refresh} />
      ) : !filtered ? (
        <SkeletonRows n={8} />
      ) : (
  
       <div className="overflow-y-auto h-[350px]">
          <ForexSummaryBar data={forex!} />
          {filtered.map(pair => <ForexRow key={pair.pair} pair={pair} />)}
  
        </div>
      )}
    </Panel>
  )
}