import { useState } from 'react'
import { NAV_ITEMS, MARKET_NAV } from '../../utils/mockData'
import { useNavigate } from 'react-router-dom'
// ─── NavSection ──────────────────────────────────────────────────────────────
function NavSection({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="px-3 mb-5">
      <p className="font-mono text-[9px] tracking-[0.12em] text-slate-600 uppercase px-2 mb-1.5">{label}</p>
      {children}
    </div>
  )
}

// ─── NavItem ─────────────────────────────────────────────────────────────────
function NavItem({
  icon, label, badge, active, onClick,
}: { icon: string; label: string; badge?: string; active?: boolean; onClick?: () => void }) {
  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg cursor-pointer transition-all mb-0.5 text-[12.5px] text-left border ${
        active
          ? 'bg-emerald-400/8 text-emerald-400 border-emerald-400/15'
          : 'text-slate-400 border-transparent hover:bg-white/[0.04] hover:text-slate-100'
      }`}
    >
      <span className="w-4 text-center text-[13px]">{icon}</span>
      <span className="flex-1">{label}</span>
      {badge && (
        <span className="font-mono text-[9px] px-1.5 py-px rounded-full bg-emerald-400/15 text-emerald-400">
          {badge}
        </span>
      )}
    </button>
  )
}

// ─── Sidebar ─────────────────────────────────────────────────────────────────
export function Sidebar() {
  const [activeNav, setActiveNav] = useState('Dashboard')
  const navigate = useNavigate()

  const handleNavigation = (item: any) => {
    setActiveNav(item.label)
    navigate(item.path)
  }

  return (
    <aside className="bg-[#0d1117] border-r border-white/[0.06] py-4 overflow-y-auto flex-shrink-0">
      <NavSection label="Menu">
          {NAV_ITEMS.map(item => (
          <NavItem
            key={item.label}
            {...item}
            active={item.label === activeNav}
            onClick={() => handleNavigation(item)}
          />
        ))}
      </NavSection>

      <div className="h-px bg-white/[0.06] mx-4 my-4" />

      <NavSection label="Markets">
       {MARKET_NAV.map(item => (
          <NavItem
            key={item.label}
            {...item}
            onClick={() => navigate(item.path)}
          />
        ))}
      </NavSection>

      <div className="h-px bg-white/[0.06] mx-4 my-4" />


    </aside>
  )
}
