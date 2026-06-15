import type {
   NavItem
} from '../types'


export const NAV_ITEMS: NavItem[] = [
  { path: '/dashboard', label: 'Dashboard', icon: '▦', active: true },
  { path: '/news', label: 'News', icon: '◈', badge: 'Live' },
  { path: '/portfolio', label: 'Portfolio', icon: '◉' },
  { path: '/signals', label: 'Signals', icon: '⊞' },
  { path: '/analysis', label: 'Analysis', icon: '⋯' },
  { path: '/screener', label: 'Screener', icon: '≋' },
]

export const MARKET_NAV: NavItem[] = [
  { path: '/forex', label: 'Forex', icon: '♦' },
  { path: '/crypto', label: 'Crypto', icon: '◆' },
  { path: '/stocks', label: 'Stocks', icon: '◇' },
  { path: '/news', label: 'News', icon: '○' },
]

export const TIMEFRAMES = ['1H', '4H', '1D', '1W', '1M']
