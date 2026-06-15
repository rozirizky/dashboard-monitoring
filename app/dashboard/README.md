# QuantEdge — Finance Analytics Dashboard

Dashboard analytics real-time untuk Forex, Saham, dan Crypto.  
Dibangun dengan **React 18 + TypeScript + Tailwind CSS**.

## Tech Stack

| Layer | Library |
|---|---|
| Framework | React 18 + TypeScript |
| Styling | Tailwind CSS v3 |
| Build | Vite 5 |
| Charts | Recharts (siap diganti Lightweight Charts) |
| State | Zustand |
| Fetching | TanStack Query (React Query) |
| HTTP | Axios |

## Struktur Komponen

```
src/
├── types/
│   └── index.ts              ← semua TypeScript interfaces
│
├── utils/
│   └── mockData.ts           ← data statis / mock
│
├── hooks/
│   └── index.ts              ← useCountdown, useLiveTicker, useTickerScroll, useNow, useFlicker
│
├── components/
│   ├── layout/
│   │   ├── Topbar.tsx        ← logo + ticker berjalan + kontrol kanan
│   │   ├── Sidebar.tsx       ← navigasi + watchlist
│   │   └── StatusBar.tsx     ← status koneksi, latensi, countdown
│   │
│   ├── charts/
│   │   └── ChartPanel.tsx    ← area chart + candle + volume
│   │
│   ├── panels/
│   │   ├── KPIRow.tsx        ← 4 kartu KPI dengan sparkline
│   │   ├── OrderBookPanel.tsx ← ask/bid dengan depth bar
│   │   ├── SignalsPanel.tsx  ← tabel sinyal ML (buy/sell/hold)
│   │   ├── PortfolioPanel.tsx ← daftar aset + P&L + alokasi
│   │   └── HeatmapPanel.tsx ← heatmap pasar multi-aset
│   │
│   └── ui/
│       └── index.tsx         ← Panel, Chip, TimeframeTabs, SignalBadge, dll.
│
├── pages/
│   └── DashboardPage.tsx     ← layout utama halaman
│
├── App.tsx                   ← root grid layout
├── main.tsx                  ← entry point
└── index.css                 ← Tailwind + custom tokens
```

## Cara Menjalankan

```bash
# Install dependencies
npm install

# Development server (port 3000)
npm run dev

# Build production
npm run build

# Type check
npm run type-check
```

## Integrasi Backend

Edit `vite.config.ts` untuk proxy ke backend FastAPI:

```ts
proxy: {
  '/api': { target: 'http://localhost:8000', changeOrigin: true },
  '/ws':  { target: 'ws://localhost:8000', ws: true },
}
```

Lalu di komponen ganti mock data dengan React Query:

```ts
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'

function useMetrics() {
  return useQuery({
    queryKey: ['metrics'],
    queryFn: () => axios.get('/api/metrics').then(r => r.data),
    refetchInterval: 5000,
  })
}
```

## WebSocket Live Feed

```ts
// hooks/useWebSocket.ts
import { useEffect, useRef } from 'react'

export function useWebSocket(url: string, onMessage: (data: any) => void) {
  const ws = useRef<WebSocket | null>(null)

  useEffect(() => {
    ws.current = new WebSocket(url)
    ws.current.onmessage = e => onMessage(JSON.parse(e.data))
    return () => ws.current?.close()
  }, [url])
}
```

## Catatan Desain

- **Font**: Syne (display) + DM Mono (angka/kode) + DM Sans (body)
- **Warna**: Dark `#080c10` base, emerald `#00e5a0` accent, red `#ff4d6a` negatif
- **Grid**: 40×40px subtle pattern overlay
- **Animasi**: ticker scroll RAF, pulse status, flicker harga live
