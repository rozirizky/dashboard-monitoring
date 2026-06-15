import { useState } from 'react'
import { NewsPanel } from '@/components/panels/TopNews'
import {
  CryptoTrendingPanel,
  StocksTrendingPanel,
  ForexTrendingPanel,
  TrendingDataProvider,
} from '@/components/panels/TrendingPanel'
import { HeatmapPanel } from '../components/panels/HeatmapPanel'
import { StatusBar } from '../components/layout/StatusBar'
import { TimeframeTabs, PrimaryButton } from '../components/ui'
import { TIMEFRAMES } from '../utils/mockData'
import { useNow } from '../hooks'

// ─── Session badge ────────────────────────────────────────────────────────────

function SessionBadge() {
  const now   = useNow()
  const hour  = now.getUTCHours() + 7   // WIB = UTC+7
  const wrapH = ((h: number) => ((h % 24) + 24) % 24)

  const sessions = [
    { name: 'Sydney',   open: 22, close: 7  },
    { name: 'Tokyo',    open: 0,  close: 9  },
    { name: 'London',   open: 8,  close: 17 },
    { name: 'New York', open: 13, close: 22 },
  ]

  const active = sessions.filter(s => {
    const h = wrapH(hour)
    return s.open <= s.close
      ? h >= s.open && h < s.close
      : h >= s.open || h < s.close
  })

  if (!active.length) return (
    <span className="font-mono text-[10px] text-slate-600 px-2 py-0.5 rounded border border-white/[0.05]">
      Pasar tutup
    </span>
  )

  return (
    <div className="flex items-center gap-1">
      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse flex-shrink-0" />
      <span className="font-mono text-[10px] text-emerald-400/80">
        {active.map(s => s.name).join(' · ')}
      </span>
    </div>
  )
}

// ─── PageHeader ───────────────────────────────────────────────────────────────

function PageHeader({
  timeframe,
  onTimeframe,
}: {
  timeframe: string
  onTimeframe: (t: string) => void
}) {
  const now     = useNow()
  const dateStr = now.toLocaleDateString('id-ID', {
    weekday: 'long', day: 'numeric', month: 'long', year: 'numeric',
  })
  const timeStr = now.toLocaleTimeString('id-ID', {
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  })

  return (
    <div className="flex items-end justify-between gap-4 flex-wrap">
      <div className="space-y-1">
        <h1 className="font-display text-[22px] font-bold tracking-tight text-slate-100 leading-none">
          Market <span className="text-emerald-400">Overview</span>
        </h1>
        <div className="flex items-center gap-3">
          <p className="font-mono text-[11px] text-slate-500">
            {dateStr} · {timeStr} WIB
          </p>
          <span className="text-slate-700">·</span>
          <SessionBadge />
        </div>
      </div>

      <div className="flex items-center gap-2 flex-shrink-0">
        <TimeframeTabs options={TIMEFRAMES} value={timeframe} onChange={onTimeframe} />
        <PrimaryButton>+ Tambah Aset</PrimaryButton>
      </div>
    </div>
  )
}

// ─── Section label ────────────────────────────────────────────────────────────

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-3 mb-2">
      <span className="font-mono text-[9px] uppercase tracking-[0.15em] text-slate-600">
        {children}
      </span>
      <div className="flex-1 h-px bg-white/[0.04]" />
    </div>
  )
}

// ─── DashboardPage ────────────────────────────────────────────────────────────

export function DashboardPage() {
  const [timeframe, setTimeframe] = useState('1D')

  return (
    <TrendingDataProvider refreshInterval={60_000}>
      <main className=" p-6 flex flex-col gap-6 ">

        {/* ── Header ── */}
        <PageHeader timeframe={timeframe} onTimeframe={setTimeframe} />

        {/* ── Main grid: left content + right news sidebar ── */}
        <div className="grid grid-cols-[1fr_320px] gap-5 ">

          {/* Left column */}
          <div className="flex flex-col gap-5 min-w-0">

            {/* Heatmap — full width left */}
            <section>
              <SectionLabel>Heatmap Pasar</SectionLabel>
              <HeatmapPanel />
            </section>

            {/* Three trending panels — equal thirds */}
            <section>
              <SectionLabel>Trending Aset</SectionLabel>
              <div className="grid grid-cols-3 gap-4 mb-5">
                <CryptoTrendingPanel />
            
                <StocksTrendingPanel />
               
            
                  <ForexTrendingPanel />
             
              </div>
                 <StatusBar />
            </section>

          </div>

          {/* Right sidebar — news, full height */}
          <div className="flex flex-col min-h-0">
            <SectionLabel>Berita Terkini</SectionLabel>
            <div className="flex-1 min-h-0">
              <NewsPanel />
            </div>
          </div>
        </div>

      </main>
    </TrendingDataProvider>
  )
}