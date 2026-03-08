import React, { useState } from 'react'
import { useApi } from '../hooks/useApi'
import { getDashboard, proposeIdeas } from '../api/client'

const STAGE_COLORS = {
  IDEA_REVIEW: '#ffd54f', SCRIPT_REVIEW: '#81d4fa', QA_RUNNING: '#f48fb1',
  FINAL_REVIEW: '#a5d6a7', UPLOAD_REVIEW: '#ce93d8', PUBLISHED: '#4fc3f7',
  REJECTED: '#ef9a9a',
}

function StatCard({ label, value, color }) {
  return (
    <div style={{ background: '#1a1a2e', border: `1px solid ${color || '#1e1e3a'}`, borderRadius: 12, padding: '20px 24px', minWidth: 140 }}>
      <div style={{ fontSize: 28, fontWeight: 700, color: color || '#e0e0ff' }}>{value ?? '—'}</div>
      <div style={{ fontSize: 13, color: '#666', marginTop: 4 }}>{label}</div>
    </div>
  )
}

export default function DashboardPage() {
  const { data, loading, error, refetch } = useApi(getDashboard, [], 10000)
  const [proposing, setProposing] = useState(false)
  const [proposeMsg, setProposeMsg] = useState('')

  const handlePropose = async () => {
    setProposing(true)
    setProposeMsg('')
    try {
      const result = await proposeIdeas(3)
      setProposeMsg(`${result.queued} idea generation tasks dispatched`)
      setTimeout(refetch, 3000)
    } catch (e) {
      setProposeMsg('Failed: ' + e.message)
    } finally {
      setProposing(false)
    }
  }

  if (loading) return <div style={{ color: '#666' }}>Loading dashboard...</div>
  if (error) return (
    <div>
      <div style={{ color: '#ef9a9a', marginBottom: 16 }}>Backend not reachable: {error}</div>
      <div style={{ color: '#666', fontSize: 13 }}>Make sure <code>docker compose up</code> is running.</div>
    </div>
  )

  const stageCounts = data?.stage_counts || {}

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 28 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700 }}>Dashboard</h1>
          <div style={{ fontSize: 13, color: '#666', marginTop: 4 }}>
            Status: <span style={{ color: '#4fc3f7' }}>{data?.system_status}</span>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          {proposeMsg && <span style={{ fontSize: 13, color: '#a5d6a7' }}>{proposeMsg}</span>}
          <button onClick={handlePropose} disabled={proposing}
            style={{ background: '#4fc3f7', color: '#0f0f1a', border: 'none', borderRadius: 8, padding: '10px 20px', fontWeight: 700, cursor: proposing ? 'not-allowed' : 'pointer', opacity: proposing ? 0.6 : 1 }}>
            {proposing ? 'Proposing...' : '+ Propose Ideas'}
          </button>
        </div>
      </div>

      {/* Stat cards */}
      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 32 }}>
        <StatCard label="Total Videos" value={data?.total_videos} color="#4fc3f7" />
        <StatCard label="Published" value={data?.published} color="#a5d6a7" />
        <StatCard label="Pending Approval" value={data?.pending_approvals} color="#ffd54f" />
      </div>

      {/* Stage breakdown */}
      <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Pipeline stages</h2>
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 32 }}>
        {Object.entries(stageCounts).map(([stage, count]) => (
          <div key={stage} style={{
            background: '#1a1a2e', border: `1px solid ${STAGE_COLORS[stage] || '#1e1e3a'}`,
            borderRadius: 8, padding: '10px 16px', fontSize: 13, display: 'flex', gap: 10, alignItems: 'center'
          }}>
            <span style={{ fontWeight: 700, color: STAGE_COLORS[stage] || '#e0e0ff', fontSize: 18 }}>{count}</span>
            <span style={{ color: '#888' }}>{stage.replace(/_/g, ' ')}</span>
          </div>
        ))}
      </div>

      {/* Workers */}
      <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>Workers</h2>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        {(data?.workers || []).map(w => (
          <div key={w} style={{ background: '#1a1a2e', border: '1px solid #1e1e3a', borderRadius: 6, padding: '6px 14px', fontSize: 12, color: '#4fc3f7' }}>
            {w}
          </div>
        ))}
      </div>
    </div>
  )
}
