// src/pages/NewsPage.tsx
import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  newsApi,
  normalizeTags,
  getSentiment,
  getConfidence,
  getSummary,
  getSourceName,
} from '@/service/newsApi'
import type { Article, ArticleDetail } from '@/service/newsApi'

// ─── Constants ────────────────────────────────────────────────────────────────
const CATEGORY_STYLE: Record<string, string> = {
  stocks:      'bg-violet-400/10 text-violet-400 border-violet-400/20',
  crypto:      'bg-amber-400/10  text-amber-400  border-amber-400/20',
  forex:       'bg-blue-400/10   text-blue-400   border-blue-400/20',
  commodities: 'bg-orange-400/10 text-orange-400 border-orange-400/20',
}

const SENTIMENT_STYLE = {
  positive: { dot: 'bg-emerald-400', label: 'BULLISH', text: 'text-emerald-400', bar: 'bg-emerald-400/60' },
  negative: { dot: 'bg-red-400',     label: 'BEARISH', text: 'text-red-400',     bar: 'bg-red-400/60'     },
  neutral:  { dot: 'bg-slate-500',   label: 'NETRAL',  text: 'text-slate-500',   bar: 'bg-slate-500/60'   },
} as const

const CATEGORY_TABS = ['Semua', 'Stocks', 'Crypto', 'Forex']
const SENTIMENT_TABS = [
  { label: '▲ Bullish', value: 'positive' },
  { label: '─ Netral',  value: 'neutral'  },
  { label: '▼ Bearish', value: 'negative' },
]

// ─── Helpers ──────────────────────────────────────────────────────────────────
function timeAgo(iso: string) {
  const s = Math.floor((Date.now() - new Date(iso).getTime()) / 1000)
  if (s < 60)    return `${s} dtk lalu`
  if (s < 3600)  return `${Math.floor(s / 60)} mnt lalu`
  if (s < 86400) return `${Math.floor(s / 3600)} jam lalu`
  return new Date(iso).toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' })
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('id-ID', {
    weekday: 'long', day: 'numeric', month: 'long', year: 'numeric',
    hour: '2-digit', minute: '2-digit', timeZoneName: 'short'
  })
}

// ─── Skeleton ─────────────────────────────────────────────────────────────────
function CardSkeleton() {
  return (
    <div className="flex flex-col gap-2.5 p-4 rounded-lg border border-white/[0.06] bg-white/[0.01]">
      <div className="flex gap-2">
        <div className="h-4 w-16 rounded bg-white/[0.04] animate-pulse" />
        <div className="h-4 w-24 rounded bg-white/[0.03] animate-pulse" />
      </div>
      <div className="h-4 w-full rounded bg-white/[0.05] animate-pulse" />
      <div className="h-4 w-4/5 rounded bg-white/[0.04] animate-pulse" />
      <div className="flex gap-1.5 mt-1">
        {[...Array(5)].map((_, i) => <div key={i} className="h-3 w-12 rounded bg-white/[0.03] animate-pulse" />)}
      </div>
    </div>
  )
}

// ─── Article Card (grid item) ─────────────────────────────────────────────────
function ArticleCard({ item, onClick }: { item: Article; onClick: () => void }) {
  const cat       = item.category.toLowerCase()
  const catStyle  = CATEGORY_STYLE[cat] ?? 'bg-white/[0.04] text-slate-400 border-white/10'
  const sentiment = SENTIMENT_STYLE[getSentiment(item)]
  const confidence = Math.round(getConfidence(item) * 100)
  const summary    = getSummary(item)
  const tags       = normalizeTags(item.tags)

  return (
    <div
      onClick={onClick}
      className="flex flex-col gap-2.5 p-4 rounded-lg border border-white/[0.06] bg-white/[0.01] cursor-pointer hover:bg-white/[0.03] hover:border-white/[0.10] transition-all group"
    >
      {/* Meta */}
      <div className="flex items-center gap-1.5 flex-wrap">
        <span className={`font-mono text-[9px] font-semibold px-1.5 py-px rounded-sm border tracking-widest ${catStyle}`}>
          {cat.toUpperCase()}
        </span>
        <span className="font-mono text-[9px] px-1.5 py-px rounded-sm bg-white/[0.04] text-slate-600">
          {getSourceName(item.source)}
        </span>
        <span className="font-mono text-[9px] text-slate-700 ml-auto">{timeAgo(item.published_date)}</span>
      </div>

      {/* Title */}
      <p className="font-display text-[12px] font-semibold text-slate-200 leading-[1.5] group-hover:text-white transition-colors m-0">
        {item.title}
      </p>

      {/* Summary */}
      {summary && summary !== item.title && (
        <p className="font-mono text-[10px] text-slate-600 leading-relaxed line-clamp-2 m-0">
          {summary}
        </p>
      )}

      {/* Tags */}
      {tags.length > 0 && (
        <div className="flex items-center gap-1 flex-wrap mt-auto pt-1">
          {tags.slice(0, 5).map(t => (
            <span key={t} className="font-mono text-[8px] px-1.5 py-px rounded-sm bg-white/[0.03] text-slate-700">
              #{t}
            </span>
          ))}
        </div>
      )}

      {/* Footer: sentiment + confidence */}

    </div>
  )
}

// ─── Article Detail Modal ─────────────────────────────────────────────────────
function ArticleDetailModal({ id, onClose }: { id: number; onClose: () => void }) {
  const [article, setArticle] = useState<ArticleDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    newsApi.getById(id)
      .then(setArticle)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [id])

  const sentiment  = article ? SENTIMENT_STYLE[getSentiment(article)] : null
  const confidence = article ? Math.round(getConfidence(article) * 100) : 0
  const tags       = article ? normalizeTags(article.tags) : []
  const cat        = article?.category.toLowerCase() ?? ''
  const catStyle   = CATEGORY_STYLE[cat] ?? 'bg-white/[0.04] text-slate-400 border-white/10'

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center bg-black/70 backdrop-blur-sm p-4 pt-16 overflow-y-auto"
      onClick={e => { if (e.target === e.currentTarget) onClose() }}
    >
      <div className="w-full max-w-2xl rounded-xl border border-white/[0.08] bg-[#0d1117] shadow-2xl">
        {/* Modal header */}
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-white/[0.06]">
          <span className="font-display text-[11px] font-semibold text-slate-400 tracking-widest uppercase">
            Detail Artikel
          </span>
          <button
            onClick={onClose}
            className="font-mono text-[11px] w-7 h-7 flex items-center justify-center rounded border border-white/[0.06] text-slate-500 hover:border-white/20 hover:text-slate-300 transition-all bg-transparent cursor-pointer"
          >
            ✕
          </button>
        </div>

        {loading && (
          <div className="p-6 flex flex-col gap-3">
            <div className="h-5 w-3/4 rounded bg-white/[0.04] animate-pulse" />
            <div className="h-4 w-1/2 rounded bg-white/[0.03] animate-pulse" />
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-3 w-full rounded bg-white/[0.03] animate-pulse" />
            ))}
          </div>
        )}

        {error && (
          <div className="p-6 text-center font-mono text-[10px] text-red-400">{error}</div>
        )}

        {!loading && !error && article && (
          <div className="flex flex-col gap-0">
            {/* Article meta */}
            <div className="px-5 pt-5 pb-4 flex flex-col gap-3">
              <div className="flex items-center gap-1.5 flex-wrap">
                <span className={`font-mono text-[9px] font-semibold px-1.5 py-px rounded-sm border tracking-widest ${catStyle}`}>
                  {cat.toUpperCase()}
                </span>
                <span className="font-mono text-[9px] px-1.5 py-px rounded-sm bg-white/[0.04] text-slate-600">
                  {getSourceName(article.source)}
                </span>
                {article.author && (
                  <span className="font-mono text-[9px] text-slate-600">by {article.author}</span>
                )}
                <span className="font-mono text-[9px] text-slate-700 ml-auto">
                  {timeAgo(article.published_date)}
                </span>
              </div>

              {/* Title */}
              <h1 className="font-display text-[15px] font-semibold text-slate-100 leading-[1.5] m-0">
                {article.title}
              </h1>

              {/* Date */}
              <p className="font-mono text-[9px] text-slate-700 m-0">
                {formatDate(article.published_date)}
              </p>

            
            </div>

            {/* Divider */}
            <div className="h-px bg-white/[0.05] mx-5" />

            {/* Content */}
            <div className="px-5 py-4 max-h-72 overflow-y-auto">
              <p className="font-mono text-[10px] text-slate-500 leading-relaxed m-0 whitespace-pre-wrap">
                {article.content}
              </p>
            </div>

            {/* Tags */}
            {tags.length > 0 && (
              <>
                <div className="h-px bg-white/[0.05] mx-5" />
                <div className="px-5 py-3 flex items-center gap-1.5 flex-wrap">
                  {tags.map(t => (
                    <span key={t} className="font-mono text-[8px] px-1.5 py-px rounded-sm bg-white/[0.04] text-slate-600 border border-white/[0.04]">
                      #{t}
                    </span>
                  ))}
                </div>
              </>
            )}

            {/* Footer: open URL */}
            <div className="h-px bg-white/[0.05] mx-5" />
            <div className="px-5 py-3 flex items-center justify-between">
              <span className="font-mono text-[9px] text-slate-700">
                {getSourceName(article.source)} · {article.language?.toUpperCase()}
              </span>
              <a
                href={article.url}
                target="_blank"
                rel="noopener noreferrer"
                className="font-mono text-[9px] px-3 py-1.5 rounded border border-emerald-400/20 text-emerald-400 bg-emerald-400/[0.06] hover:bg-emerald-400/10 transition-all no-underline"
              >
                Baca artikel asli →
              </a>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// ─── NewsPage ─────────────────────────────────────────────────────────────────
export function NewsPage() {
  const navigate = useNavigate()

  const [articles, setArticles]         = useState<Article[]>([])
  const [loading, setLoading]           = useState(true)
  const [error, setError]               = useState<string | null>(null)
  const [activeCategory, setActiveCategory] = useState('Semua')
  const [activeSentiment, setActiveSentiment] = useState<string | null>(null)
  const [selectedId, setSelectedId]     = useState<number | null>(null)
  const [search, setSearch]             = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      let data: Article[]
      if (activeSentiment)
        data = await newsApi.getBySentiment(activeSentiment)
      else if (activeCategory !== 'Semua')
        data = await newsApi.getByCategory(activeCategory.toLowerCase())
      else
        data = await newsApi.getAll()
      setArticles(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Gagal memuat berita')
    } finally {
      setLoading(false)
    }
  }, [activeCategory, activeSentiment])

  useEffect(() => { load() }, [load])

  // Client-side search filter
  const filtered = search.trim()
    ? articles.filter(a =>
        a.title.toLowerCase().includes(search.toLowerCase()) ||
        normalizeTags(a.tags).some(t => t.toLowerCase().includes(search.toLowerCase()))
      )
    : articles

  function handleCategoryClick(label: string) {
    setActiveCategory(label)
    setActiveSentiment(null)
  }

  function handleSentimentClick(value: string) {
    setActiveSentiment(prev => prev === value ? null : value)
    setActiveCategory('Semua')
  }

  return (
    <div className="min-h-screen bg-[#060b12] text-slate-100">
      {/* ── Header bar ── */}
      <div className="sticky top-0 z-40 border-b border-white/[0.06] bg-[#060b12]/90 backdrop-blur-sm">
        <div className="max-w-6xl mx-auto px-6 py-3 flex items-center gap-4">
          {/* Back */}
          <button
            onClick={() => navigate(-1)}
            className="font-mono text-[10px] px-2.5 py-1.5 rounded border border-white/[0.06] text-slate-500 hover:border-white/20 hover:text-slate-300 transition-all bg-transparent cursor-pointer flex items-center gap-1.5"
          >
            ← Dashboard
          </button>

          <div className="flex items-center gap-2">
            <h1 className="font-display text-[14px] font-semibold text-slate-100">Market News</h1>
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.5)]" />
            <span className="font-mono text-[9px] font-semibold tracking-widest text-emerald-400 border border-emerald-400/20 bg-emerald-400/10 px-1.5 py-px rounded-sm">
              LIVE
            </span>
          </div>

          {/* Count */}
          {!loading && (
            <span className="font-mono text-[9px] text-slate-700 ml-auto">
              {filtered.length} artikel
            </span>
          )}

          {/* Refresh */}
          <button
            onClick={load}
            className="font-mono text-[11px] w-7 h-7 flex items-center justify-center rounded border border-white/[0.06] text-slate-500 hover:border-white/20 hover:text-slate-300 transition-all bg-transparent cursor-pointer"
          >
            ↻
          </button>
        </div>

        {/* ── Filter row ── */}
        <div className="max-w-6xl mx-auto px-6 py-2 flex items-center gap-2 flex-wrap border-t border-white/[0.04]">
          {/* Search */}
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Cari judul atau tag..."
            className="font-mono text-[10px] px-3 py-1.5 rounded border border-white/[0.06] bg-white/[0.02] text-slate-300 placeholder-slate-700 outline-none focus:border-white/20 transition-all w-48"
          />

          <div className="w-px h-4 bg-white/[0.08]" />

          {/* Category tabs */}
          {CATEGORY_TABS.map(label => (
            <button
              key={label}
              onClick={() => handleCategoryClick(label)}
              className={`font-mono text-[9px] px-2.5 py-1.5 rounded-sm border transition-all cursor-pointer ${
                activeCategory === label && !activeSentiment
                  ? 'border-emerald-400/30 text-emerald-400 bg-emerald-400/[0.06]'
                  : 'border-white/[0.06] text-slate-600 bg-transparent hover:border-white/20 hover:text-slate-400'
              }`}
            >
              {label}
            </button>
          ))}

          <div className="w-px h-4 bg-white/[0.08]" />

          {/* Sentiment tabs */}
          {SENTIMENT_TABS.map(({ label, value }) => (
            <button
              key={value}
              onClick={() => handleSentimentClick(value)}
              className={`font-mono text-[9px] px-2.5 py-1.5 rounded-sm border transition-all cursor-pointer ${
                activeSentiment === value
                  ? value === 'positive'
                    ? 'border-emerald-400/30 text-emerald-400 bg-emerald-400/[0.06]'
                    : value === 'negative'
                    ? 'border-red-400/30 text-red-400 bg-red-400/[0.06]'
                    : 'border-slate-500/30 text-slate-400 bg-slate-500/[0.06]'
                  : 'border-white/[0.06] text-slate-600 bg-transparent hover:border-white/20 hover:text-slate-400'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* ── Content ── */}
      <div className="max-w-6xl mx-auto px-6 py-6">
        {error && (
          <div className="text-center py-12">
            <p className="font-mono text-[11px] text-red-400/80 mb-3">{error}</p>
            <button onClick={load} className="font-mono text-[10px] text-slate-500 hover:text-slate-300 bg-transparent border-none cursor-pointer">
              Coba lagi →
            </button>
          </div>
        )}

        {loading && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {[...Array(9)].map((_, i) => <CardSkeleton key={i} />)}
          </div>
        )}

        {!loading && !error && filtered.length === 0 && (
          <div className="text-center py-16 font-mono text-[11px] text-slate-700">
            Tidak ada artikel ditemukan.
          </div>
        )}

        {!loading && !error && filtered.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {filtered.map(item => (
              <ArticleCard
                key={item.id}
                item={item}
                onClick={() => setSelectedId(item.id)}
              />
            ))}
          </div>
        )}
      </div>

      {/* ── Detail modal ── */}
      {selectedId !== null && (
        <ArticleDetailModal
          id={selectedId}
          onClose={() => setSelectedId(null)}
        />
      )}
    </div>
  )
}