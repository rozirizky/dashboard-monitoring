import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// ─────────────────────────────────────────────────────────────────────────────
//  QuantEdge — Vite Config
// ─────────────────────────────────────────────────────────────────────────────
//
//  Alias   : @/ → src/
//  Proxy   : /api  → FastAPI backend  (localhost:8000)  — trending + news
//            /cg   → CoinGecko        (fallback dev, sekarang tidak dipakai
//                                      karena semua lewat backend)
//            /yf   → Yahoo Finance    (idem)
//            /er   → ExchangeRate API (idem)
//
//  Catatan : Proxy /cg, /yf, /er dipertahankan untuk kemudahan debugging
//            langsung ke sumber — tapi normalnya frontend hanya hit /api.
// ─────────────────────────────────────────────────────────────────────────────

export default defineConfig({
  plugins: [react()],

  // ── Path alias ──────────────────────────────────────────────────────────────
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },

  // ── Dev server ──────────────────────────────────────────────────────────────
  server: {
    port: 3000,
    proxy: {

      // ── FastAPI backend — semua /api/** (trending, news, dll) ───────────────
      '/api': {
        target:       'http://localhost:8000',
        changeOrigin: true,
        // Tidak perlu rewrite — FastAPI sudah mount di /api
      },

      // ── CoinGecko (debug / fallback) ────────────────────────────────────────
      '/cg': {
        target:       'https://api.coingecko.com/api/v3',
        changeOrigin: true,
        rewrite:      (p) => p.replace(/^\/cg/, ''),
      },

      // ── Yahoo Finance (debug / fallback) ────────────────────────────────────
      '/yf': {
        target:       'https://query1.finance.yahoo.com',
        changeOrigin: true,
        rewrite:      (p) => p.replace(/^\/yf/, ''),
        headers: {
          'User-Agent': 'Mozilla/5.0 (compatible; QuantEdge/1.0)',
        },
      },

      // ── ExchangeRate API (debug / fallback) ─────────────────────────────────
      '/er': {
        target:       'https://open.er-api.com',
        changeOrigin: true,
        rewrite:      (p) => p.replace(/^\/er/, ''),
      },
    },
  },

  // ── Build ───────────────────────────────────────────────────────────────────
  build: {
    outDir:   'dist',
    sourcemap: true,
  },
})