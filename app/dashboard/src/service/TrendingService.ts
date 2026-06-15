// ─────────────────────────────────────────────────────────────────────────────
//  TRENDING SERVICE  —  v2 (DB-backed)
//  Semua data diambil dari backend lokal (FastAPI → SQLite).
//  Python fetcher + scheduler yang handle request ke CoinGecko / yFinance.
//  Frontend cukup satu request ke /api/trending/all.
// ─────────────────────────────────────────────────────────────────────────────

// ─── Types ────────────────────────────────────────────────────────────────────

export interface TrendingCoin {
  rank:          number
  symbol:        string
  name:          string
  marketCapRank: number | null
  price:         number | null
  change24h:     number | null
  volume24h:     number | null
  thumb:         string | null
}

export interface CoinGainerLoser {
  symbol:    string
  name:      string
  price:     number
  change24h: number
  volume:    number | null
}

export interface CryptoData {
  trending: TrendingCoin[]
  gainers:  CoinGainerLoser[]
  losers:   CoinGainerLoser[]
}

export interface StockItem {
  ticker:    string
  group:     string
  price:     number | null
  prevClose: number | null
  change:    number | null
  volume:    number | null
  shortName: string | null
}

export interface ForexPair {
  pair:   string
  rate:   number
  change: number | null
  source: string
}

export interface HeatCell {
  symbol:   string
  name:     string
  change:   number
  category: 'crypto' | 'stock' | 'forex'
  weight:   number
}

export interface TrendingData {
  crypto:      CryptoData
  stocks:      StockItem[]
  forex:       ForexPair[]
  fetchedAt:   Record<string, string | null>
  lastUpdated: Date
}

export interface HeatmapData {
  cells:       HeatCell[]
  period:      string
  lastUpdated: Date
}

// ─── Config ───────────────────────────────────────────────────────────────────

const API_BASE =  'http://localhost:8000'

// ─── Helper ───────────────────────────────────────────────────────────────────

async function apiFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { Accept: 'application/json' },
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`API ${res.status}: ${path} — ${text}`)
  }
  return res.json() as Promise<T>
}

// ─── API response shapes ──────────────────────────────────────────────────────

interface AllResponse {
  crypto: {
    trending: TrendingCoin[]
    gainers:  CoinGainerLoser[]
    losers:   CoinGainerLoser[]
  }
  stocks:      StockItem[]
  forex:       ForexPair[]
  fetchedAt:   Record<string, string | null>
  lastUpdated: string
}

interface HeatmapResponse {
  cells:       HeatCell[]
  period:      string
  lastUpdated: string
}

// ─── Public API ───────────────────────────────────────────────────────────────

/** Satu request untuk semua panel — data sudah di-aggregate dari DB. */
export async function fetchTrendingData(): Promise<TrendingData> {
  const data = await apiFetch<AllResponse>('/trending/all')
  return {
    crypto:      data.crypto,
    stocks:      data.stocks,
    forex:       data.forex,
    fetchedAt:   data.fetchedAt,
    lastUpdated: new Date(data.lastUpdated),
  }
}

/** Untuk HeatmapPanel — pilih period 24h / 7d / 30d. */
export async function fetchHeatmapData(period: '24h' | '7d' | '30d' = '24h'): Promise<HeatmapData> {
  const data = await apiFetch<HeatmapResponse>(`/trending/heatmap?period=${period}`)
  return {
    cells:       data.cells,
    period:      data.period,
    lastUpdated: new Date(data.lastUpdated),
  }
}

/** Status fetch terakhir — untuk StatusBar. */
export async function fetchTrendingStatus(): Promise<{
  status:    string
  fetchedAt: Record<string, string | null>
  recentLogs: {
    source: string; success: boolean; rows: number
    durationMs: number; error: string | null; at: string
  }[]
}> {
  return apiFetch('/trending/status')
}

// ─── Re-exports (panel components tidak perlu refactor) ───────────────────────

export const STOCK_WATCHLIST: Record<string, string[]> = {
  'US Tech':   ['NVDA', 'AAPL', 'MSFT', 'GOOGL', 'META', 'AMZN', 'TSLA'],
  'US Index':  ['^GSPC', '^IXIC', '^DJI'],
  'Indonesia': ['BBCA.JK', 'BBRI.JK', 'TLKM.JK', 'ASII.JK', 'GOTO.JK', 'BMRI.JK'],
}

export const FOREX_PAIRS = [
  'EURUSD=X', 'GBPUSD=X', 'USDJPY=X', 'AUDUSD=X',
  'USDCAD=X', 'USDCHF=X', 'NZDUSD=X', 'USDIDR=X',
  'USDSGD=X', 'USDCNY=X',
]