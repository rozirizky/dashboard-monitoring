

// ─── LogoMark ────────────────────────────────────────────────────────────────
function LogoMark() {
  return (
    <div className="flex items-center gap-2.5 w-[220px] px-5 border-r border-white/[0.06] h-full flex-shrink-0">
      <div
        className="w-7 h-7 bg-emerald-400 flex-shrink-0 animate-pulse"
        style={{ clipPath: 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)' }}
      />
      <span className="font-display text-base font-extrabold tracking-tight text-slate-100">
        Quant<span className="text-emerald-400">Edge</span>
      </span>
    </div>
  )
}

// ─── Topbar ───────────────────────────────────────────────────────────────────
export function Topbar() {

  return (
    <header className="col-span-2 flex items-center h-14 border-b border-white/[0.06] bg-[#080c10]/90 backdrop-blur-xl sticky top-0 z-50">
      <LogoMark />

      {/* Ticker strip */}

      {/* Right controls */}
      <div className="flex items-center gap-2 px-5 border-l border-white/[0.06] h-full">
        {['⌕', '🔔', '⚙'].map(icon => (
          <button
            key={icon}
            className="w-8 h-8 border border-white/[0.06] rounded-md flex items-center justify-center text-slate-400 text-sm hover:border-emerald-400 hover:text-emerald-400 transition-all cursor-pointer bg-transparent"
          >
            {icon}
          </button>
        ))}
        <div className="w-8 h-8 rounded-md bg-gradient-to-br from-emerald-500 to-blue-500 flex items-center justify-center font-display text-xs font-bold text-black cursor-pointer">
          AK
        </div>
      </div>
    </header>
  )
}
