import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useApi } from '../hooks/useApi'
import { getVideos, autoApprove, bulkApprove } from '../api/client'

const APPROVAL_STAGES = ['IDEA_REVIEW', 'SCRIPT_REVIEW', 'FINAL_REVIEW', 'UPLOAD_REVIEW']
const STAGE_COLOR = { IDEA_REVIEW: '#ffd54f', SCRIPT_REVIEW: '#81d4fa', FINAL_REVIEW: '#a5d6a7', UPLOAD_REVIEW: '#ffcc80' }
const STAGE_DESC = {
  IDEA_REVIEW: 'Review topic idea, references, and concept plan',
  SCRIPT_REVIEW: 'Review 60-second voiceover script and scene plan',
  FINAL_REVIEW: 'Review rendered video, captions, and QA results',
  UPLOAD_REVIEW: 'Approve title, description, tags and platform targets',
}

function Btn({ children, onClick, color = '#4fc3f7', disabled, small }) {
  return (
    <button onClick={onClick} disabled={disabled} style={{
      background: color, color: '#0f0f1a', border: 'none', borderRadius: 6,
      padding: small ? '5px 12px' : '8px 18px', fontWeight: 700,
      cursor: disabled ? 'not-allowed' : 'pointer', opacity: disabled ? 0.5 : 1,
      fontSize: small ? 11 : 13, whiteSpace: 'nowrap',
    }}>{children}</button>
  )
}

export default function ApprovalsPage() {
  const navigate = useNavigate()
  const { data: allVideos, loading, error, refetch } = useApi(
    () => Promise.all(APPROVAL_STAGES.map(s => getVideos(s))).then(r => r.flat()),
    [], 10000
  )
  const [busy, setBusy] = useState({}) // { [id]: true } or { ['bulk_STAGE']: true }
  const [msgs, setMsgs] = useState({})

  const setMsg = (key, msg) => setMsgs(p => ({ ...p, [key]: msg }))

  const handleAutoApprove = async (e, video) => {
    e.stopPropagation()
    setBusy(p => ({ ...p, [video.id]: true }))
    try {
      await autoApprove(video.id)
      setMsg(video.id, '✓ approved')
      setTimeout(refetch, 800)
    } catch (err) {
      setMsg(video.id, 'Error: ' + (err.response?.data?.detail || err.message))
    } finally {
      setBusy(p => ({ ...p, [video.id]: false }))
    }
  }

  const handleBulkApprove = async (e, stage) => {
    e.stopPropagation()
    const key = `bulk_${stage}`
    setBusy(p => ({ ...p, [key]: true }))
    try {
      const result = await bulkApprove(stage)
      setMsg(key, `✓ ${result.count} approved`)
      setTimeout(refetch, 1000)
    } catch (err) {
      setMsg(key, 'Error: ' + (err.response?.data?.detail || err.message))
    } finally {
      setBusy(p => ({ ...p, [key]: false }))
    }
  }

  if (loading) return <div style={{ color: '#666' }}>Loading approvals...</div>
  if (error) return <div style={{ color: '#ef9a9a' }}>Error: {error}</div>

  const pending = allVideos || []

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 28 }}>
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700 }}>Approvals</h1>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <span style={{ fontSize: 13, color: '#666' }}>{pending.length} pending</span>
          <button onClick={refetch} style={{ background: 'transparent', border: '1px solid #1e1e3a', color: '#666', borderRadius: 6, padding: '6px 14px', cursor: 'pointer', fontSize: 12 }}>Refresh</button>
        </div>
      </div>

      {pending.length === 0 && (
        <div style={{ textAlign: 'center', padding: 60, color: '#444' }}>
          <div style={{ fontSize: 32, marginBottom: 12 }}>✓</div>
          <div>No items waiting for approval.</div>
        </div>
      )}

      {APPROVAL_STAGES.map(stage => {
        const items = pending.filter(v => v.stage === stage)
        if (items.length === 0) return null
        const color = STAGE_COLOR[stage]
        const bulkKey = `bulk_${stage}`
        return (
          <div key={stage} style={{ marginBottom: 32 }}>
            {/* Stage header with Approve All */}
            <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 12 }}>
              <div style={{ fontSize: 12, fontWeight: 700, color, letterSpacing: 1, textTransform: 'uppercase' }}>
                {stage.replace(/_/g, ' ')}
              </div>
              <div style={{ fontSize: 12, color: '#444', flex: 1 }}>{STAGE_DESC[stage]}</div>
              {msgs[bulkKey] && <span style={{ fontSize: 12, color: '#a5d6a7' }}>{msgs[bulkKey]}</span>}
              <Btn onClick={e => handleBulkApprove(e, stage)} disabled={busy[bulkKey]} color="#66bb6a" small>
                {busy[bulkKey] ? 'Approving...' : `Approve All (${items.length})`}
              </Btn>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {items.map(v => (
                <div key={v.id}
                  style={{ background: '#1a1a2e', border: `1px solid ${color}30`, borderLeft: `3px solid ${color}`, borderRadius: 10, padding: '14px 18px', display: 'flex', gap: 16, alignItems: 'center' }}>
                  {/* Click main area to go to detail */}
                  <div onClick={() => navigate(`/pipeline/${v.id}`)} style={{ flex: 1, cursor: 'pointer' }}>
                    <div style={{ fontSize: 14, fontWeight: 600, color: '#e0e0ff', marginBottom: 4 }}>{v.title}</div>
                    <div style={{ fontSize: 12, color: '#666' }}>{v.track?.replace(/_/g, ' ')} · {v.video_type}</div>
                    {v.idea_card?.hook && <div style={{ fontSize: 12, color: '#888', fontStyle: 'italic', marginTop: 4 }}>"{v.idea_card.hook}"</div>}
                  </div>
                  {/* Action buttons */}
                  <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexShrink: 0 }}>
                    {msgs[v.id] && <span style={{ fontSize: 11, color: '#a5d6a7' }}>{msgs[v.id]}</span>}
                    <Btn onClick={e => handleAutoApprove(e, v)} disabled={busy[v.id]} color="#4fc3f7" small>
                      {busy[v.id] ? '...' : 'Auto-approve'}
                    </Btn>
                    <Btn onClick={() => navigate(`/pipeline/${v.id}`)} color={color} small>Review →</Btn>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}
