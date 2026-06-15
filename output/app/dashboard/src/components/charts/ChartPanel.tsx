import { useState } from 'react'
import { Panel, PanelHeader, ChipGroup } from '../ui'

const CHART_TYPES = ['Candlestick', 'Line', 'Heikin Ashi']

// ─── ChartSVG ────────────────────────────────────────────────────────────────
function ChartSVG() {
  return (
    <svg
      width="100%"
      height="260"
      viewBox="0 0 600 260"
      preserveAspectRatio="none"
      className="block"
    >
      <defs>
        <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#00e5a0" stopOpacity="0.15" />
          <stop offset="100%" stopColor="#00e5a0" stopOpacity="0" />
        </linearGradient>
      </defs>

      {/* Grid lines */}
      {[52, 104, 156, 208].map(y => (
        <line key={y} x1="0" y1={y} x2="600" y2={y} stroke="rgba(255,255,255,0.04)" strokeWidth="1" />
      ))}

      {/* Area fill */}
      <path
        d="M0,200 C30,185 60,175 90,160 C120,145 150,155 180,140 C210,125 240,130 270,110 C300,90 330,100 360,80 C390,60 420,70 450,50 C480,30 510,40 540,30 C560,24 580,20 600,15 L600,260 L0,260 Z"
        fill="url(#areaGrad)"
      />

      {/* Price line */}
      <path
        d="M0,200 C30,185 60,175 90,160 C120,145 150,155 180,140 C210,125 240,130 270,110 C300,90 330,100 360,80 C390,60 420,70 450,50 C480,30 510,40 540,30 C560,24 580,20 600,15"
        fill="none"
        stroke="#00e5a0"
        strokeWidth="2"
        strokeLinecap="round"
      />

      {/* Candles */}
      {[
        { x: 20, wickT: 190, wickB: 215, bodyY: 196, bodyH: 12, bull: false },
        { x: 50, wickT: 178, wickB: 200, bodyY: 178, bodyH: 14, bull: true },
        { x: 80, wickT: 162, wickB: 185, bodyY: 162, bodyH: 16, bull: true },
        { x: 110, wickT: 148, wickB: 170, bodyY: 152, bodyH: 10, bull: false },
        { x: 140, wickT: 138, wickB: 162, bodyY: 138, bodyH: 18, bull: true },
        { x: 170, wickT: 122, wickB: 145, bodyY: 124, bodyH: 14, bull: true },
      ].map(c => (
        <g key={c.x}>
          <line x1={c.x} y1={c.wickT} x2={c.x} y2={c.wickB} stroke={c.bull ? '#00e5a0' : '#ff4d6a'} strokeWidth="1" />
          <rect x={c.x - 4} y={c.bodyY} width={8} height={c.bodyH} fill={c.bull ? '#00e5a0' : '#ff4d6a'} rx="1" />
        </g>
      ))}

      {/* Current price dashed line */}
      <line x1="0" y1="15" x2="600" y2="15" stroke="#00e5a0" strokeWidth="0.5" strokeDasharray="4 4" />

      {/* Volume bars */}
      {[
        { x: 8, h: 18, bull: false }, { x: 38, h: 25, bull: true },
        { x: 68, h: 21, bull: true }, { x: 98, h: 15, bull: false },
        { x: 128, h: 28, bull: true }, { x: 158, h: 23, bull: true },
        { x: 188, h: 13, bull: false }, { x: 218, h: 31, bull: true },
      ].map(v => (
        <rect key={v.x} x={v.x} y={253 - v.h} width={10} height={v.h} fill={v.bull ? '#00e5a0' : '#ff4d6a'} rx="1" opacity="0.3" />
      ))}

      {/* Y-axis labels */}
      {[['70k', 50], ['68k', 102], ['66k', 154], ['64k', 206]].map(([label, y]) => (
        <text key={label} x={4} y={y as number} fill="#3a4a5a" fontSize="9" fontFamily="DM Mono">{label}</text>
      ))}
    </svg>
  )
}

// ─── ChartPanel ──────────────────────────────────────────────────────────────
export function ChartPanel() {
  const [chartType, setChartType] = useState('Candlestick')

  return (
    <Panel>
      <PanelHeader title="BTC/USD · Live Chart" live>
        <ChipGroup options={CHART_TYPES} value={chartType} onChange={setChartType} />
        <button className="font-mono text-[10px] px-2 py-1 rounded border border-white/[0.06] text-slate-400 hover:border-white/20 transition-all bg-transparent cursor-pointer">
          Indicators
        </button>
      </PanelHeader>

      <div className="p-4 relative">
        {/* Price overlay */}
        <div className="absolute top-4 right-4 text-right pointer-events-none z-10">
          <p className="font-mono text-xl font-medium text-emerald-400">$67,412</p>
          <p className="font-mono text-xs text-emerald-400">+2.41% ▲</p>
        </div>

        <ChartSVG />
      </div>
    </Panel>
  )
}
