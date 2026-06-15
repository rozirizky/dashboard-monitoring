// src/components/panels/NewsPanel.tsx
import { Panel, PanelHeader } from '../ui'
import { useNews } from '../../hooks/useNews'
import type { Article } from '@/service/newsApi'
import type { NewsFilter } from '../../hooks/useNews'
import { normalizeTags } from '@/service/newsApi'
// ─── Helpers ──────────────────────────────────────────────────────────────────
function timeAgo(isoString: string): string {
  const diff = Math.floor((Date.now() - new Date(isoString).getTime()) / 1000)
  if (diff < 60) return `${diff} dtk lalu`
  if (diff < 3600) return `${Math.floor(diff / 60)} mnt lalu`
  if (diff < 86400) return `${Math.floor(diff / 3600)} jam lalu`
  return `${Math.floor(diff / 86400)} hr lalu`
}


// ─── Style maps ───────────────────────────────────────────────────────────────
const CATEGORY_STYLE: Record<string, string> = {
  stocks: 'bg-violet-400/10 text-violet-400 border-violet-400/20',
  crypto: 'bg-amber-400/10  text-amber-400  border-amber-400/20',
  forex: 'bg-blue-400/10   text-blue-400   border-blue-400/20',
  commodities: 'bg-orange-400/10 text-orange-400 border-orange-400/20',
  macro: 'bg-emerald-400/10 text-emerald-400 border-emerald-400/20',
}

const SENTIMENT_STYLE = {
  positive: { dot: 'bg-emerald-400', label: 'BULLISH', text: 'text-emerald-400' },
  negative: { dot: 'bg-red-400', label: 'BEARISH', text: 'text-red-400' },
  neutral: { dot: 'bg-slate-500', label: 'NETRAL', text: 'text-slate-500' },
} as const

// Category filter tabs — sesuaikan dengan kategori yang ada di API
const CATEGORY_TABS: { label: string; filter: NewsFilter }[] = [
  { label: 'Semua', filter: { type: 'all' } },
  { label: 'Stocks', filter: { type: 'category', value: 'stocks' } },
  { label: 'Crypto', filter: { type: 'category', value: 'crypto' } },
  { label: 'Forex', filter: { type: 'category', value: 'forex' } },
]

// Sentiment filter tabs
const SENTIMENT_TABS: { label: string; value: string }[] = [
  { label: '▲ Bullish', value: 'positive' },
  { label: '─ Netral', value: 'neutral' },
  { label: '▼ Bearish', value: 'negative' },
]

// ─── NewsRow ──────────────────────────────────────────────────────────────────
function NewsRow({ item }: { item: Article }) {
  const cat = (item.category ?? '').toLowerCase()
  const catStyle = CATEGORY_STYLE[cat] ?? 'bg-white/[0.04] text-slate-400 border-white/10'

  // ✅ Safe access: fallback ke 'neutral' jika analysis undefined
  const sentimentKey = item.analysis?.sentiment ?? 'neutral'
  const sentiment = SENTIMENT_STYLE[sentimentKey] ?? SENTIMENT_STYLE.neutral
  const confidence = Math.round((item.analysis?.confidence ?? 0) * 100)

  return (<a

    href={item.url}
    target="_blank"
    rel="noopener noreferrer"
    className="flex flex-col gap-1.5 px-4 py-3 border-b border-white/[0.03] cursor-pointer hover:bg-white/[0.02] transition-all no-underline"
  >
    <div className="flex items-center gap-1.5">
      <span className={`font-mono text-[9px] font-semibold px-1.5 py-px rounded-sm border tracking-widest ${catStyle}`}>
        {cat.toUpperCase()}
      </span>
      <span className="font-mono text-[9px] px-1.5 py-px rounded-sm bg-white/[0.04] text-slate-600">
        {item.source?.name ?? '—'}
      </span>
      <span className="font-mono text-[9px] text-slate-700 ml-auto">
        {timeAgo(item.published_date)}
      </span>
    </div>

    <p className="font-display text-[11px] font-semibold text-slate-300 leading-[1.45] m-0">
      {item.title}
    </p>

    {/* Summary hanya tampil jika ada dan beda dari title */}
    {item.analysis?.summary && item.analysis.summary !== item.title && (
      <p className="font-mono text-[9px] text-slate-600 leading-relaxed m-0">
        {item.analysis.summary}
      </p>
    )}

    {item.tags?.length > 0 && (
      <div className="flex items-center gap-1 flex-wrap">
        {normalizeTags(item.tags).slice(0, 5).map(tag => (
          <span
            key={tag}
            className="font-mono text-[8px] px-1 py-px rounded-sm bg-white/[0.03] text-slate-700"
          >
            #{tag}
          </span>
        ))}
      </div>
    )}

    <div className="flex items-center gap-2 mt-0.5">
      <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${sentiment.dot}`} />
      <span className={`font-mono text-[9px] tracking-widest ${sentiment.text}`}>
        {sentiment.label}
      </span>

      {/* Confidence bar — hanya tampil jika analysis ada */}
      {item.analysis && (
        <div className="flex items-center gap-1.5 ml-auto">
          <span className="font-mono text-[8px] text-slate-700">conf.</span>
          <div className="w-16 h-0.5 bg-white/[0.06] rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full ${confidence >= 70 ? 'bg-emerald-400/60' :
                confidence >= 45 ? 'bg-amber-400/60' : 'bg-slate-600'
                }`}
              style={{ width: `${confidence}%` }}
            />
          </div>
          <span className="font-mono text-[8px] text-slate-600">{confidence}%</span>
        </div>
      )}
    </div>
  </a>
  )
}

// ─── Skeleton ─────────────────────────────────────────────────────────────────
function NewsSkeleton() {
  return (
    <>
      {[...Array(4)].map((_, i) => (
        <div key={i} className="flex flex-col gap-2 px-4 py-3 border-b border-white/[0.03]">
          <div className="flex gap-2">
            <div className="h-3 w-14 rounded-sm bg-white/[0.04] animate-pulse" />
            <div className="h-3 w-20 rounded-sm bg-white/[0.03] animate-pulse" />
          </div>
          <div className="h-3 w-full rounded-sm bg-white/[0.04] animate-pulse" />
          <div className="h-3 w-4/5 rounded-sm bg-white/[0.03] animate-pulse" />
          <div className="flex gap-1">
            {[...Array(4)].map((_, j) => (
              <div key={j} className="h-2 w-10 rounded-sm bg-white/[0.03] animate-pulse" />
            ))}
          </div>
        </div>
      ))}
    </>
  )
}

// ─── NewsPanel ────────────────────────────────────────────────────────────────
export function NewsPanel() {
  const { articles, loading, error, filter, setFilter, refresh } = useNews()

  const isActiveTab = (f: NewsFilter) => JSON.stringify(f) === JSON.stringify(filter)

  return (
    <Panel>
      <PanelHeader title="Market News">
        <div className="flex items-center gap-2">
          <button
            onClick={refresh}
            title="Refresh"
            className="font-mono text-[11px] w-6 h-6 flex items-center justify-center rounded border border-white/[0.06] text-slate-500 hover:border-white/20 hover:text-slate-300 transition-all bg-transparent cursor-pointer"
          >
            ↻
          </button>
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.5)]" />
            <span className="font-mono text-[9px] font-semibold tracking-widest text-emerald-400 border border-emerald-400/20 bg-emerald-400/10 px-1.5 py-px rounded-sm">
              LIVE
            </span>
          </div>
        </div>
      </PanelHeader>

      {/* Category tabs */}
      <div className="flex items-center gap-1.5 px-4 py-2 border-b border-white/[0.04]">
        {CATEGORY_TABS.map(({ label, filter: f }) => (
          <button
            key={label}
            onClick={() => setFilter(f)}
            className={`font-mono text-[9px] px-2 py-1 rounded-sm border transition-all cursor-pointer ${isActiveTab(f)
              ? 'border-emerald-400/30 text-emerald-400 bg-emerald-400/[0.06]'
              : 'border-white/[0.06] text-slate-600 bg-transparent hover:border-white/20 hover:text-slate-400'
              }`}
          >
            {label}
          </button>
        ))}

        {/* Divider */}
        <div className="w-px h-3 bg-white/[0.06] mx-1" />

        {/* Sentiment filters */}
        {SENTIMENT_TABS.map(({ label, value }) => {
          const isActive = filter.type === 'sentiment' && filter.value === value
          return (
            <button
              key={value}
              onClick={() => setFilter({ type: 'sentiment', value })}
              className={`font-mono text-[9px] px-2 py-1 rounded-sm border transition-all cursor-pointer ${isActive
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
          )
        })}
      </div>

      {/* Content */}
      {loading && <NewsSkeleton />}

      {error && (
        <div className="px-4 py-6 text-center">
          <p className="font-mono text-[10px] text-red-400/80 mb-2">{error}</p>
          <button
            onClick={refresh}
            className="font-mono text-[9px] text-slate-500 hover:text-slate-300 transition-all bg-transparent border-none cursor-pointer"
          >
            Coba lagi →
          </button>
        </div>
      )}

      {!loading && !error && articles.length === 0 && (
        <div className="px-4 py-8 text-center font-mono text-[10px] text-slate-700">
          Tidak ada berita tersedia.
        </div>
      )}
      <div className='h-[710px] overflow-y-auto'>
        {!loading && !error && articles.map(item => (
          <NewsRow key={item.id} item={item} />
        ))}
      </div>
      {/* Footer count */}
      {!loading && !error && articles.length > 0 && (
        <div className="flex items-center justify-between px-4 py-2 border-t border-white/[0.04]">
          <span className="font-mono text-[9px] text-slate-700">
            {articles.length} artikel
          </span>
          <button className="font-mono text-[9px] text-slate-700 hover:text-slate-500 transition-all bg-transparent border-none cursor-pointer tracking-widest">
            Lihat semua →
          </button>
        </div>
      )}
    </Panel>
  )
}