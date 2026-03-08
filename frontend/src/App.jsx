import React from 'react'
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import DashboardPage from './pages/DashboardPage'
import PipelinePage from './pages/PipelinePage'
import VideoDetailPage from './pages/VideoDetailPage'
import ApprovalsPage from './pages/ApprovalsPage'

const NAV = [
  { to: '/', label: '⬡ Dashboard', end: true },
  { to: '/pipeline', label: '⬡ Pipeline' },
  { to: '/approvals', label: '⬡ Approvals' },
]

const navStyle = (active) => ({
  display: 'block', padding: '10px 18px', borderRadius: 8,
  color: active ? '#4fc3f7' : '#a0aec0', background: active ? 'rgba(79,195,247,0.1)' : 'transparent',
  textDecoration: 'none', fontSize: 14, fontWeight: active ? 600 : 400,
  transition: 'all 0.15s',
})

export default function App() {
  return (
    <BrowserRouter>
      <div style={{ display: 'flex', minHeight: '100vh', background: '#0f0f1a', color: '#e0e0ff', fontFamily: 'system-ui, sans-serif' }}>
        {/* Sidebar */}
        <aside style={{ width: 220, background: '#13131f', borderRight: '1px solid #1e1e3a', padding: '24px 12px', display: 'flex', flexDirection: 'column', gap: 4, flexShrink: 0 }}>
          <div style={{ padding: '8px 10px 20px', borderBottom: '1px solid #1e1e3a', marginBottom: 12 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: '#4fc3f7', letterSpacing: 1 }}>AI MATHS</div>
            <div style={{ fontSize: 11, color: '#666', marginTop: 2 }}>Video Factory</div>
          </div>
          {NAV.map(({ to, label, end }) => (
            <NavLink key={to} to={to} end={end} style={({ isActive }) => navStyle(isActive)}>
              {label}
            </NavLink>
          ))}
        </aside>

        {/* Main */}
        <main style={{ flex: 1, overflow: 'auto', padding: 32 }}>
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/pipeline" element={<PipelinePage />} />
            <Route path="/pipeline/:id" element={<VideoDetailPage />} />
            <Route path="/approvals" element={<ApprovalsPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
