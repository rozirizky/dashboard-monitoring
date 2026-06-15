import { Routes, Route } from 'react-router-dom'
import MainLayout from './components/layout/MainLayout'
import { DashboardPage } from './pages/DashboardPage'
import { NewsPage } from './pages/NewsPage'
import { CryptoPage, StocksPage, ForexPage } from './pages/AssetsPage'
export default function App() {
  return (
    <Routes>
      <Route element={<MainLayout />}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/news" element={<NewsPage />} />
        <Route path="/crypto" element={<CryptoPage />} />
        <Route path="/stocks" element={<StocksPage />} />
        <Route path="/forex" element={<ForexPage />} /> 
      </Route>
    </Routes>
  )
}