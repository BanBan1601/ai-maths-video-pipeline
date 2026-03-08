import React from 'react'
import { useNavigate } from 'react-router-dom'
import { useApi } from '../hooks/useApi'
import { getVideos } from '../api/client'

const APPROVAL_STAGES = ['IDEA_REVIEW', 'SCRIPT_REVIEW', 'FINAL_REVIEW', 'UPLOAD_REVIEW']
const STAGE_COLOR = { IDEA_REVIEW: '#ffd54f', SCRIPT_REVIEW: '#81d4fa', FINAL_REVIEW: '#a5d6a7', UPLOAD_REVIEW: '#ffcc80' }
const STAGE_DESC = {
  IDEA_REVIEW: 'Review topic idea, references, and concept plan',
  SCRIPT_REVIEW: 'Review 60-second voiceover script and scene plan',
  FINAL_REVIEW: 'Review rendered video, captions, and QA results',
  UPLOAD_REVIEW: 'Approve title, description, hashtags and platform targets',
}

export default function ApprovalsPage() {
  const navigate = useNavigate()
  const { data: allVideos, loading, error, refetch } = useApi(
    () => Promise.all(APPROVAL_STAGES.map(s => getVideos(s))).then(results => results.flat()),
    [], 10000
  )

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
          <div style={{ fontSize: 13, marginTop: 8, color: '#333' }}>Go to Dashboard to propose new ideas.</div>
        </div>
      )}

      {APPROVAL_STAGES.map(stage => {
        const items = pending.filter(v => v.stage === stage)
        if (items.length === 0) return null
        const color = STAGE_COLOR[stage]
        return (
          <div key={stage} style={{ marginBottom: 28 }}>
            <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginBottom: 12 }}>
              <div style={{ fontSize: 12, fontWeight: 700, color, letterSpacing: 1, textTransform: 'uppercase' }}>
                {stage.replace(/_/g, ' ')}
              </div>
              <div style={{ fontSize: 12, color: '#444' }}>{STAGE_DESC[stage]}</div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {items.map(v => (
                <div key={v.id} onClick={() => navigate(`/pipeline/${v.id}`)}
                  style={{ background: '#1a1a2e', border: `1px solid ${color}30`, borderLeft: `3px solid ${color}`, borderRadius: 10, padding: '16px 20px', cursor: 'pointer', display: 'flex', gap: 20, alignItems: 'center' }}
                  onMouseEnter={e => e.currentTarget.style.background = '#1e1e3a'}
                  onMouseLeave={e => e.currentTarget.style.background = '#1a1a2e'}
                >
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 15, fontWeight: 600, color: '#e0e0ff', marginBottom: 4 }}>{v.title}</div>
                    <div style={{ fontSize: 12, color: '#666' }}>{v.track?.replace(/_/g, ' ')} · {v.video_type}</div>
                  </div>
                  {v.idea_card?.hook && (
                    <div style={{ fontSize: 12, color: '#888', fontStyle: 'italic', maxWidth: 300, flex: 1 }}>"{v.idea_card.hook}"</div>
                  )}
                  <div style={{ fontSize: 12, color, fontWeight: 700, flexShrink: 0 }}>Review →</div>
                </div>
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}
