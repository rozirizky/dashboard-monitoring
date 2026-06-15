/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['Syne', 'sans-serif'],
        mono: ['DM Mono', 'monospace'],
        sans: ['DM Sans', 'sans-serif'],
      },
      colors: {
        // Brand
        accent: {
          DEFAULT: '#00e5a0',
          dark: '#00b87a',
        },
        // Dark surfaces
        surface: {
          base: '#080c10',
          card: '#0d1117',
          elevated: '#111820',
          high: '#16202a',
        },
      },
      animation: {
        'fade-in-up': 'fadeInUp 0.4s ease both',
        'pulse-slow': 'pulse 3s ease-in-out infinite',
      },
      keyframes: {
        fadeInUp: {
          from: { opacity: '0', transform: 'translateY(8px)' },
          to:   { opacity: '1', transform: 'translateY(0)' },
        },
      },
      backgroundImage: {
        'grid-pattern':
          'linear-gradient(rgba(0,229,160,0.015) 1px, transparent 1px), linear-gradient(90deg, rgba(0,229,160,0.015) 1px, transparent 1px)',
      },
      backgroundSize: {
        grid: '40px 40px',
      },
    },
  },
  plugins: [],
}
