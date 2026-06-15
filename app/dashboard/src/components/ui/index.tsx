import { useState } from 'react'

// ─── Panel ────────────────────────────────────────────────────────────────────
export function Panel({
  children, className = '',
}: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`bg-[#0d1117] border border-white/[0.06] rounded-xl overflow-hidden ${className}`}>
      {children}
    </div>
  )
}

// ─── PanelHeader ─────────────────────────────────────────────────────────────
export function PanelHeader({
  title, live = false, children,
}: { title: string; live?: boolean; children?: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between px-4 py-3.5 border-b border-white/[0.06]">
      <div className="flex items-center gap-2 font-display text-[13px] font-semibold text-slate-100">
        {live && <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />}
        {title}
      </div>
      {children && <div className="flex items-center gap-1.5">{children}</div>}
    </div>
  )
}

// ─── Chip ─────────────────────────────────────────────────────────────────────
export function Chip({
  label, active = false, onClick,
}: { label: string; active?: boolean; onClick?: () => void }) {
  return (
    <button
      onClick={onClick}
      className={`font-mono text-[10px] px-2 py-1 rounded border cursor-pointer transition-all ${
        active
          ? 'border-emerald-400/50 text-emerald-400 bg-emerald-400/6'
          : 'border-white/[0.06] text-slate-400 bg-transparent hover:text-slate-200 hover:border-white/[0.12]'
      }`}
    >
      {label}
    </button>
  )
}

// ─── ChipGroup ────────────────────────────────────────────────────────────────
export function ChipGroup({
  options, value, onChange,
}: { options: string[]; value: string; onChange: (v: string) => void }) {
  return (
    <div className="flex items-center gap-1">
      {options.map(opt => (
        <Chip key={opt} label={opt} active={opt === value} onClick={() => onChange(opt)} />
      ))}
    </div>
  )
}

// ─── TimeframeTabs ────────────────────────────────────────────────────────────
export function TimeframeTabs({
  options, value, onChange,
}: { options: string[]; value: string; onChange: (v: string) => void }) {
  return (
    <div className="flex gap-0.5 bg-[#111820] border border-white/[0.06] rounded-lg p-[3px]">
      {options.map(opt => (
        <button
          key={opt}
          onClick={() => onChange(opt)}
          className={`font-mono text-[11px] px-2.5 py-1 rounded-[5px] cursor-pointer transition-all border-none ${
            opt === value
              ? 'bg-emerald-400 text-black font-medium'
              : 'text-slate-400 bg-transparent hover:text-slate-200'
          }`}
        >
          {opt}
        </button>
      ))}
    </div>
  )
}

// ─── SignalBadge ─────────────────────────────────────────────────────────────
export function SignalBadge({ signal }: { signal: 'BUY' | 'SELL' | 'HOLD' }) {
  const styles = {
    BUY: 'bg-emerald-400/12 text-emerald-400 border-emerald-400/20',
    SELL: 'bg-red-500/12 text-red-400 border-red-500/20',
    HOLD: 'bg-amber-400/10 text-amber-400 border-amber-400/20',
  }
  return (
    <span className={`font-mono text-[10px] px-2 py-0.5 rounded border font-medium ${styles[signal]}`}>
      {signal}
    </span>
  )
}

// ─── StrengthBar ─────────────────────────────────────────────────────────────
export function StrengthBar({ value, max = 5, signal }: { value: number; max?: number; signal: 'BUY' | 'SELL' | 'HOLD' }) {
  const colors = { BUY: 'bg-emerald-400', SELL: 'bg-red-400', HOLD: 'bg-amber-400' }
  return (
    <div className="flex gap-0.5 items-center">
      {Array.from({ length: max }).map((_, i) => (
        <div
          key={i}
          className={`w-[5px] h-3.5 rounded-[2px] ${i < value ? colors[signal] : 'bg-[#16202a]'}`}
        />
      ))}
    </div>
  )
}

// ─── PrimaryButton ────────────────────────────────────────────────────────────
export function PrimaryButton({
  children, onClick,
}: { children: React.ReactNode; onClick?: () => void }) {
  return (
    <button
      onClick={onClick}
      className="bg-emerald-400 text-black border-none rounded-lg px-3.5 py-1.5 font-display text-[12px] font-semibold cursor-pointer hover:bg-emerald-300 active:scale-95 transition-all flex items-center gap-1.5"
    >
      {children}
    </button>
  )
}
