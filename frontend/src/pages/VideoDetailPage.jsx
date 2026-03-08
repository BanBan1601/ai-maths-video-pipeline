import React, { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useApi } from '../hooks/useApi'
import { getVideo, getVideoSources, getVideoQA, approveIdea, approveScript, approveFinal, approveUpload } from '../api/client'

const GATE_FOR_STAGE = {
  IDEA_REVIEW: { label: 'Idea Review', fn: approveIdea },
  SCRIPT_REVIEW: { label: 'Script Review', fn: approveScript },
  FINAL_REVIEW: { label: 'Final Review', fn: approveFinal },
  UPLOAD_REVIEW: { label: 'Upload Review', fn: approveUpload },
}

function Section({ title, children }) {
  return (
    <div style={{ background: '#1a1a2e', border: '1px solid #1e1e3a', borderRadius: 12, padding: 20, marginBottom: 20 }}>
      <h3 style={{ margin: '0 0 14px', fontSize: 14, fontWeight: 600, color: '#4fc3f7' }}>{title}</h3>
      {children}
    </div>
  )
}

function Badge({ text, color }) {
  return <span style={{ background: `${color}20`, color, border: `1px solid ${color}50`, borderRadius: 6, padding: '3px 10px', fontSize: 12, fontWeight: 600 }}>{text}</span>
}

export default function VideoDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { data: video, loading, error, refetch } = useApi(() => getVideo(id), [id])
  const { data: sources } = useApi(() => getVideoSources(id), [id])
  const { data: qaReports } = useApi(() => getVideoQA(id), [id])

  const [feedback, setFeedback] = useState('')
  const [actioning, setActioning] = useState(false)
  const [actionMsg, setActionMsg] = useState('')

  const gate = video ? GATE_FOR_STAGE[video.stage] : null

  const handleDecision = async (decision) => {
    if (!gate) return
    setActioning(true)
    setActionMsg('')
    try {
      await gate.fn(id, decision, feedback || undefined)
      setActionMsg(decision === 'approve' ? 'Approved! Pipeline advancing...' : 'Rejected.')
      setFeedback('')
      setTimeout(refetch, 1000)
    } catch (e) {
      setActionMsg('Error: ' + (e.response?.data?.detail || e.message))
    } finally {
      setActioning(false)
    }
  }

  if (loading) return <div style={{ color: '#666' }}>Loading...</div>
  if (error) return <div style={{ color: '#ef9a9a' }}>Error: {error}</div>
  if (!video) return null

  const stageColor = { IDEA_REVIEW: '#ffd54f', SCRIPT_REVIEW: '#81d4fa', FINAL_REVIEW: '#a5d6a7', UPLOAD_REVIEW: '#ffcc80', PUBLISHED: '#4fc3f7', REJECTED: '#ef9a9a' }[video.stage] || '#666'

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
        <button onClick={() => navigate('/pipeline')} style={{ background: 'transparent', border: '1px solid #1e1e3a', color: '#666', borderRadius: 6, padding: '6px 12px', cursor: 'pointer', fontSize: 12 }}>← Back</button>
        <h1 style={{ margin: 0, fontSize: 20, fontWeight: 700, flex: 1 }}>{video.title}</h1>
        <Badge text={video.stage.replace(/_/g, ' ')} color={stageColor} />
      </div>

      {/* Meta */}
      <Section title="Overview">
        <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap', fontSize: 13, color: '#888' }}>
          <span>Track: <b style={{ color: '#e0e0ff' }}>{video.track?.replace(/_/g, ' ')}</b></span>
          <span>Type: <b style={{ color: '#e0e0ff' }}>{video.video_type}</b></span>
          <span>Created: <b style={{ color: '#e0e0ff' }}>{new Date(video.created_at).toLocaleDateString()}</b></span>
        </div>
      </Section>

      {/* Approval gate */}
      {gate && (
        <Section title={`Gate: ${gate.label}`}>
          <div style={{ marginBottom: 14 }}>
            <textarea value={feedback} onChange={e => setFeedback(e.target.value)}
              placeholder="Optional feedback (rejection reason, revision notes...)"
              style={{ width: '100%', minHeight: 80, background: '#0f0f1a', border: '1px solid #1e1e3a', borderRadius: 8, color: '#e0e0ff', padding: 12, fontSize: 13, resize: 'vertical', boxSizing: 'border-box' }} />
          </div>
          <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
            <button onClick={() => handleDecision('approve')} disabled={actioning}
              style={{ background: '#66bb6a', color: '#0f0f1a', border: 'none', borderRadius: 8, padding: '10px 24px', fontWeight: 700, cursor: actioning ? 'not-allowed' : 'pointer', opacity: actioning ? 0.6 : 1 }}>
              Approve
            </button>
            <button onClick={() => handleDecision('reject')} disabled={actioning}
              style={{ background: '#ef5350', color: '#fff', border: 'none', borderRadius: 8, padding: '10px 24px', fontWeight: 700, cursor: actioning ? 'not-allowed' : 'pointer', opacity: actioning ? 0.6 : 1 }}>
              Reject
            </button>
            {actionMsg && <span style={{ fontSize: 13, color: '#a5d6a7' }}>{actionMsg}</span>}
          </div>
        </Section>
      )}

      {/* Idea card */}
      {video.idea_card && (
        <Section title="Idea Card">
          <div style={{ fontSize: 13, lineHeight: 1.7 }}>
            {video.idea_card.hook && <div style={{ color: '#ffd54f', fontStyle: 'italic', marginBottom: 10, fontSize: 14 }}>"{video.idea_card.hook}"</div>}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px 24px', color: '#888' }}>
              {Object.entries(video.idea_card).filter(([k]) => !['hook', 'proposed_at'].includes(k)).map(([k, v]) => (
                <div key={k}><span>{k.replace(/_/g, ' ')}: </span><b style={{ color: '#e0e0ff' }}>{String(v)}</b></div>
              ))}
            </div>
          </div>
        </Section>
      )}

      {/* Script */}
      {video.script_data && (
        <Section title="Script">
          <div style={{ fontSize: 13, lineHeight: 1.8 }}>
            {video.script_data.hook && <div style={{ color: '#ffd54f', fontStyle: 'italic', marginBottom: 12, fontSize: 14 }}>Hook: "{video.script_data.hook}"</div>}
            {video.script_data.scenes?.map(s => (
              <div key={s.scene_id} style={{ background: '#0f0f1a', borderRadius: 8, padding: '12px 16px', marginBottom: 8 }}>
                <div style={{ fontSize: 11, color: '#4fc3f7', fontWeight: 700, marginBottom: 6 }}>SCENE {s.scene_id} — {s.timing}</div>
                <div style={{ color: '#e0e0ff', marginBottom: 4 }}>{s.narration}</div>
                {s.visual_goal && <div style={{ fontSize: 11, color: '#666' }}>Visual: {s.visual_goal}</div>}
              </div>
            ))}
            {video.script_data.full_voiceover && (
              <div style={{ marginTop: 12, padding: 12, background: '#0f0f1a', borderRadius: 8, fontSize: 12, color: '#888', fontStyle: 'italic' }}>
                Word count: {video.script_data.word_count} | Generator: {video.script_data.generated_by}
              </div>
            )}
          </div>
        </Section>
      )}

      {/* Sources */}
      {sources && sources.length > 0 && (
        <Section title={`Sources (${sources.length})`}>
          {sources.map(s => (
            <div key={s.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', padding: '10px 0', borderBottom: '1px solid #1e1e3a' }}>
              <div>
                <div style={{ fontSize: 13, color: '#e0e0ff', fontWeight: 600 }}>{s.title}</div>
                <div style={{ fontSize: 11, color: '#666', marginTop: 2 }}>{(s.authors || []).join(', ')} · {s.source_type}</div>
              </div>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexShrink: 0, marginLeft: 12 }}>
                <Badge text={`Trust ${s.trust_score}`} color={s.trust_score >= 90 ? '#a5d6a7' : s.trust_score >= 75 ? '#ffd54f' : '#ef9a9a'} />
                {s.url && <a href={s.url} target="_blank" rel="noreferrer" style={{ fontSize: 11, color: '#4fc3f7' }}>→ link</a>}
              </div>
            </div>
          ))}
        </Section>
      )}

      {/* QA Reports */}
      {qaReports && qaReports.length > 0 && (
        <Section title="QA Reports">
          {qaReports.map((r, i) => (
            <div key={i} style={{ marginBottom: 12 }}>
              <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 8 }}>
                <Badge text={r.qa_type} color="#ce93d8" />
                <Badge text={r.passed ? 'PASSED' : 'FAILED'} color={r.passed ? '#a5d6a7' : '#ef9a9a'} />
              </div>
              {r.issues?.length > 0 && (
                <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12, color: '#888' }}>
                  {r.issues.map((issue, j) => (
                    <li key={j} style={{ marginBottom: 4, color: issue.severity === 'error' ? '#ef9a9a' : '#ffd54f' }}>
                      [{issue.severity?.toUpperCase()}] {issue.message}
                    </li>
                  ))}
                </ul>
              )}
              {r.repair_actions?.length > 0 && (
                <div style={{ marginTop: 8, fontSize: 12, color: '#a5d6a7' }}>
                  Repair: {r.repair_actions.join(' | ')}
                </div>
              )}
            </div>
          ))}
        </Section>
      )}

      {/* Approvals history */}
      {video.approvals?.length > 0 && (
        <Section title="Approval History">
          {video.approvals.map((a, i) => (
            <div key={i} style={{ display: 'flex', gap: 12, alignItems: 'center', padding: '8px 0', borderBottom: '1px solid #1e1e3a', fontSize: 13 }}>
              <Badge text={a.gate} color="#ce93d8" />
              <Badge text={a.decision.toUpperCase()} color={a.decision === 'approve' ? '#a5d6a7' : '#ef9a9a'} />
              {a.feedback && <span style={{ color: '#888', fontStyle: 'italic' }}>{a.feedback}</span>}
              <span style={{ color: '#444', fontSize: 11, marginLeft: 'auto' }}>{new Date(a.created_at).toLocaleString()}</span>
            </div>
          ))}
        </Section>
      )}
    </div>
  )
}
