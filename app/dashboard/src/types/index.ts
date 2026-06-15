export type MarketType = 'crypto' | 'forex' | 'stock' | 'commodity'
export type SignalType = 'BUY' | 'SELL' | 'HOLD'
export type ChangeDirection = 'up' | 'dn'

export interface NavItem {
  label: string
  icon: string
  badge?: string
  active?: boolean
  path: string
}
