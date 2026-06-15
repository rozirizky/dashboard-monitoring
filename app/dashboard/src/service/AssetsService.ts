// src/service/assetDetailService.ts
// ─────────────────────────────────────────────────────────────────────────────
//  Asset Detail Service — fetch data per-halaman detail aset
//  Endpoint: /api/trending/crypto, /api/trending/stocks, /api/trending/forex
// ─────────────────────────────────────────────────────────────────────────────

const API_BASE = 'http://localhost:8000'

async function apiFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { headers: { Accept: 'application/json' } })
  if (!res.ok) throw new Error(`API ${res.status}: ${path}`)
  return res.json() as Promise<T>
}

// ─── Types ────────────────────────────────────────────────────────────────────

export interface CryptoDetailItem {
  rank:          number | null
  symbol:        string
  name:          string
  marketCapRank: number | null
  price:         number | null
  change24h:     number | null
  change7d:      number | null
  change30d:     number | null
  volume24h:     number | null
  marketCap:     number | null
  thumb:         string | null
}

export interface StockDetailItem {
  ticker:    string
  group:     string
  price:     number | null
  prevClose: number | null
  change:    number | null
  volume:    number | null
  shortName: string | null
}

export interface ForexDetailItem {
  pair:   string
  rate:   number
  change: number | null
  source: string
  region?: string
}

// ─── Fetchers ─────────────────────────────────────────────────────────────────

export async function fetchAllCryptoDetail(): Promise<CryptoDetailItem[]> {
  // Pakai endpoint /heatmap untuk dapat change 7d & 30d juga
  const data = await apiFetch<{
    cells: {
      symbol: string; name: string; change: number
      category: string; weight: number
    }[]
    period: string
  }>('/trending/heatmap?period=24h')

  // Merge dengan market data
  const market = await apiFetch<{
    trending: { rank: number; symbol: string; name: string; marketCapRank: number | null; price: number | null; change24h: number | null; volume24h: number | null; thumb: string | null }[]
    gainers:  { symbol: string; name: string; price: number; change24h: number; volume: number | null }[]
    losers:   { symbol: string; name: string; price: number; change24h: number; volume: number | null }[]
  }>('/trending/crypto')

  // Build map dari gainers+losers untuk price/volume
  const priceMap = new Map<string, { price: number; volume: number | null; change: number }>()
  ;[...market.gainers, ...market.losers].forEach(c => {
    priceMap.set(c.symbol, { price: c.price, volume: c.volume, change: c.change24h })
  })

  // Cells hanya ada crypto
  const cryptoCells = data.cells.filter(c => c.category === 'crypto')

  return cryptoCells.map((c, i) => {
    const trending = market.trending.find(t => t.symbol === c.symbol)
    const pm       = priceMap.get(c.symbol)
    return {
      rank:          trending?.rank ?? null,
      symbol:        c.symbol,
      name:          c.name,
      marketCapRank: trending?.marketCapRank ?? null,
      price:         trending?.price ?? pm?.price ?? null,
      change24h:     c.change,
      change7d:      null,    // akan ada jika endpoint heatmap?period=7d di-merge
      change30d:     null,
      volume24h:     trending?.volume24h ?? pm?.volume ?? null,
      marketCap:     null,    // tidak tersedia di endpoint saat ini
      thumb:         trending?.thumb ?? null,
    }
  })
}

export async function fetchAllStocksDetail(): Promise<StockDetailItem[]> {
  const data = await apiFetch<{
    stocks: StockDetailItem[]
    lastUpdated: string
  }>('/trending/stocks')
  return data.stocks
}

export async function fetchAllForexDetail(): Promise<ForexDetailItem[]> {
  const data = await apiFetch<{
    forex: ForexDetailItem[]
    lastUpdated: string
  }>('/trending/forex')
  return data.forex
}