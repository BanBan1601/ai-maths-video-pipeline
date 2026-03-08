import React from 'react'
import { useApi } from '../hooks/useApi'
import { getPipeline } from '../api/client'
import { useNavigate } from 'react-router-dom'

const STAGE_ORDER = [
  'IDEA_REVIEW', 'IDEA_APPROVED', 'SCRIPT_REVIEW', 'SCRIPT_APPROVED',
  'MANIM_GENERATING', 'QA_RUNNING', 'FINAL_REVIEW', 'FINAL_APPROVED',
  'UPLOAD_REVIEW', 'UPLOADING', 'PUBLISHED', 'REJECTED'
]

const STAGE_COLOR = {
  IDEA_REVIEW: '#ffd54f', IDEA_APPROVED: '#ffe082',
  SCRIPT_REVIEW: '#81d4fa', SCRIPT_APPROVED: '#4fc3f7',
  MANIM_GENERATING: '#ce93d8', QA_RUNNING: '#f48fb1',
  FINAL_REVIEW: '#a5d6a7', FINAL_APPROVED: '#66bb6a',
  UPLOAD_REVIEW: '#ffcc80', UPLOADING: '#ffa726',
  PUBLISHED: '#26c6da', REJECTED: '#ef9a9a',
}

export default function PipelinePage() {
  const { data, loading, error, refetch } = useApi(getPipeline, [], 8000)
  const navigate = useNavigate()

  if (loading) return <div style={{ color: '#666' }}>Loading pipeline...</div>
  if (error) return <div style={{ color: '#ef9a9a' }}>Error: {error}</div>

  const visibleStages = STAGE_ORDER.filter(s => (data?.[s] || []).length > 0 || ['IDEA_REVIEW', 'SCRIPT_REVIEW', 'FINAL_REVIEW'].includes(s))

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 28 }}>
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700 }}>Pipeline Board</h1>
        <button onClick={refetch} style={{ background: 'transparent', border: '1px solid #1e1e3a', color: '#666', borderRadius: 6, padding: '6px 14px', cursor: 'pointer', fontSize: 12 }}>Refresh</button>
      </div>
      <div style={{ display: 'flex', gap: 16, overflowX: 'auto', paddingBottom: 16, alignItems: 'flex-start' }}>
        {visibleStages.map(stage => {
          const cards = data?.[stage] || []
          const color = STAGE_COLOR[stage] || '#e0e0ff'
          return (
            <div key={stage} style={{ minWidth: 220, maxWidth: 260, flexShrink: 0 }}>
              <div style={{ fontSize: 11, fontWeight: 700, color, marginBottom: 10, letterSpacing: 1, textTransform: 'uppercase' }}>
                {stage.replace(/_/g, ' ')} {cards.length > 0 && <span style={{ background: color, color: '#0f0f1a', borderRadius: 10, padding: '1px 7px', fontSize: 10 }}>{cards.length}</span>}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {cards.map(card => (
                  <div key={card.id} onClick={() => navigate(`/pipeline/${card.id}`)}
                    style={{ background: '#1a1a2e', border: `1px solid ${color}30`, borderLeft: `3px solid ${color}`, borderRadius: 8, padding: '12px 14px', cursor: 'pointer', transition: 'all 0.15s' }}
                    onMouseEnter={e => e.currentTarget.style.background = '#1e1e3a'}
                    onMouseLeave={e => e.currentTarget.style.background = '#1a1a2e'}
                  >
                    <div style={{ fontSize: 13, fontWeight: 600, color: '#e0e0ff', lineHeight: 1.3, marginBottom: 6 }}>{card.title}</div>
                    <div style={{ fontSize: 11, color: '#666' }}>{card.track?.replace(/_/g, ' ')} · {card.video_type}</div>
                    <div style={{ fontSize: 10, color: '#444', marginTop: 6 }}>{new Date(card.updated_at).toLocaleString()}</div>
                  </div>
                ))}
                {cards.length === 0 && (
                  <div style={{ fontSize: 12, color: '#333', padding: '12px 14px', border: '1px dashed #1e1e3a', borderRadius: 8, textAlign: 'center' }}>empty</div>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
