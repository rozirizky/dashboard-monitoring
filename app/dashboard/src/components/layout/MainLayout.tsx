// layouts/MainLayout.tsx

import { Outlet } from 'react-router-dom'
import { Topbar } from './Topbar'
import { Sidebar } from './Sidebar'


export default function MainLayout() {
  return (
    <div
      className="grid h-screen overflow-hidden"
      style={{
        gridTemplateColumns: '220px 1fr',
        gridTemplateRows: '56px 1fr'
      }}
    >
      <Topbar />
      <Sidebar />

      <div className="overflow-auto">
        <Outlet />
      </div>
    </div>
  )
}