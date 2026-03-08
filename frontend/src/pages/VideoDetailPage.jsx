import React, { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useApi } from '../hooks/useApi'
import {
  getVideo, getVideoSources, getVideoQA,
  approveIdea, approveScript, approveFinal, approveUpload,
  autoApprove, generateMetadata, updateMetadata, setSchedule,
  triggerUpload,
} from '../api/client'

const GATE_FOR_STAGE = {
  IDEA_REVIEW: { label: 'Idea Review', fn: approveIdea },
  SCRIPT_REVIEW: { label: 'Script Review', fn: approveScript },
  FINAL_REVIEW: { label: 'Final Review', fn: approveFinal },
  UPLOAD_REVIEW: { label: 'Upload Review', fn: approveUpload },
}

const STAGE_COLOR = {
  IDEA_REVIEW: '#ffd54f', SCRIPT_REVIEW: '#81d4fa', FINAL_REVIEW: '#a5d6a7',
  UPLOAD_REVIEW: '#ffcc80', PUBLISHED: '#4fc3f7', REJECTED: '#ef9a9a',
  MANIM_GENERATING: '#ce93d8', QA_RUNNING: '#f48fb1',
}

function Section({ title, children, action }) {
  return (
    <div style={{ background: '#1a1a2e', border: '1px solid #1e1e3a', borderRadius: 12, padding: 20, marginBottom: 20 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
        <h3 style={{ margin: 0, fontSize: 14, fontWeight: 600, color: '#4fc3f7' }}>{title}</h3>
        {action}
      </div>
      {children}
    </div>
  )
}

function Badge({ text, color }) {
  return <span style={{ background: `${color}20`, color, border: `1px solid ${color}50`, borderRadius: 6, padding: '3px 10px', fontSize: 12, fontWeight: 600 }}>{text}</span>
}

function Btn({ children, onClick, color = '#4fc3f7', disabled, outline }) {
  return (
    <button onClick={onClick} disabled={disabled} style={{
      background: outline ? 'transparent' : color, color: outline ? color : '#0f0f1a',
      border: outline ? `1px solid ${color}` : 'none', borderRadius: 8,
      padding: '9px 20px', fontWeight: 700, cursor: disabled ? 'not-allowed' : 'pointer',
      opacity: disabled ? 0.5 : 1, fontSize: 13,
    }}>{children}</button>
  )
}

export default function VideoDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { data: video, loading, error, refetch } = useApi(() => getVideo(id), [id])
  const { data: sources } = useApi(() => getVideoSources(id), [id])
  const { data: qaReports } = useApi(() => getVideoQA(id), [id])

  // Approval gate
  const [feedback, setFeedback] = useState('')
  const [actioning, setActioning] = useState(false)
  const [actionMsg, setActionMsg] = useState('')

  // Auto-approve
  const [autoApproving, setAutoApproving] = useState(false)

  // Metadata
  const [metaEditing, setMetaEditing] = useState(false)
  const [metaDraft, setMetaDraft] = useState(null)
  const [metaGenerating, setMetaGenerating] = useState(false)
  const [metaMsg, setMetaMsg] = useState('')

  // Schedule
  const [scheduleValue, setScheduleValue] = useState('')
  const [scheduleSaving, setScheduleSaving] = useState(false)
  const [scheduleMsg, setScheduleMsg] = useState('')

  // Upload
  const [uploading, setUploading] = useState(false)
  const [uploadMsg, setUploadMsg] = useState('')

  const gate = video ? GATE_FOR_STAGE[video.stage] : null
  const meta = video?.platform_metadata || {}

  const handleDecision = async (decision) => {
    if (!gate) return
    setActioning(true); setActionMsg('')
    try {
      await gate.fn(id, decision, feedback || undefined)
      setActionMsg(decision === 'approve' ? 'Approved! Advancing...' : 'Rejected.')
      setFeedback('')
      setTimeout(refetch, 1000)
    } catch (e) {
      setActionMsg('Error: ' + (e.response?.data?.detail || e.message))
    } finally { setActioning(false) }
  }

  const handleAutoApprove = async () => {
    setAutoApproving(true); setActionMsg('')
    try {
      await autoApprove(id)
      setActionMsg('Auto-approved! Advancing...')
      setTimeout(refetch, 1000)
    } catch (e) {
      setActionMsg('Error: ' + (e.response?.data?.detail || e.message))
    } finally { setAutoApproving(false) }
  }

  const handleGenerateMeta = async () => {
    setMetaGenerating(true); setMetaMsg('')
    try {
      const result = await generateMetadata(id)
      setMetaDraft(result.metadata)
      setMetaEditing(true)
      setMetaMsg('Metadata generated — review and save.')
    } catch (e) {
      setMetaMsg('Error: ' + e.message)
    } finally { setMetaGenerating(false) }
  }

  const handleSaveMeta = async () => {
    if (!metaDraft) return
    try {
      await updateMetadata(id, metaDraft)
      setMetaEditing(false)
      setMetaMsg('Saved.')
      refetch()
    } catch (e) {
      setMetaMsg('Error saving: ' + e.message)
    }
  }

  const handleSetSchedule = async () => {
    setScheduleSaving(true); setScheduleMsg('')
    try {
      await setSchedule(id, scheduleValue || null)
      setScheduleMsg(scheduleValue ? `Scheduled for ${new Date(scheduleValue).toLocaleString()}` : 'Schedule cleared.')
      refetch()
    } catch (e) {
      setScheduleMsg('Error: ' + e.message)
    } finally { setScheduleSaving(false) }
  }

  const handleUpload = async () => {
    setUploading(true); setUploadMsg('')
    try {
      await triggerUpload(id)
      setUploadMsg('Upload dispatched! Check platforms in a few minutes.')
      setTimeout(refetch, 2000)
    } catch (e) {
      setUploadMsg('Error: ' + (e.response?.data?.detail || e.message))
    } finally { setUploading(false) }
  }

  if (loading) return <div style={{ color: '#666' }}>Loading...</div>
  if (error) return <div style={{ color: '#ef9a9a' }}>Error: {error}</div>
  if (!video) return null

  const stageColor = STAGE_COLOR[video.stage] || '#666'
  const editMeta = metaEditing ? metaDraft : meta

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24, flexWrap: 'wrap' }}>
        <button onClick={() => navigate('/pipeline')} style={{ background: 'transparent', border: '1px solid #1e1e3a', color: '#666', borderRadius: 6, padding: '6px 12px', cursor: 'pointer', fontSize: 12 }}>← Back</button>
        <h1 style={{ margin: 0, fontSize: 20, fontWeight: 700, flex: 1 }}>{video.title}</h1>
        <Badge text={video.stage.replace(/_/g, ' ')} color={stageColor} />
        <button onClick={() => navigate(`/preview/${id}`)} style={{ background: '#1a1a2e', border: '1px solid #4fc3f750', color: '#4fc3f7', borderRadius: 8, padding: '7px 16px', cursor: 'pointer', fontSize: 12, fontWeight: 600 }}>
          ▶ Preview
        </button>
      </div>

      {/* Overview */}
      <Section title="Overview">
        <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap', fontSize: 13, color: '#888' }}>
          <span>Track: <b style={{ color: '#e0e0ff' }}>{video.track?.replace(/_/g, ' ')}</b></span>
          <span>Type: <b style={{ color: '#e0e0ff' }}>{video.video_type}</b></span>
          <span>Created: <b style={{ color: '#e0e0ff' }}>{new Date(video.created_at).toLocaleDateString()}</b></span>
          {video.scheduled_publish_at && (
            <span>Publish at: <b style={{ color: '#ffd54f' }}>{new Date(video.scheduled_publish_at).toLocaleString()}</b></span>
          )}
        </div>
      </Section>

      {/* Approval Gate */}
      {gate && (
        <Section title={`Gate: ${gate.label}`}>
          <textarea value={feedback} onChange={e => setFeedback(e.target.value)}
            placeholder="Optional feedback or rejection reason..."
            style={{ width: '100%', minHeight: 70, background: '#0f0f1a', border: '1px solid #1e1e3a', borderRadius: 8, color: '#e0e0ff', padding: 12, fontSize: 13, resize: 'vertical', boxSizing: 'border-box', marginBottom: 12 }} />
          <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
            <Btn onClick={() => handleDecision('approve')} disabled={actioning} color="#66bb6a">Approve</Btn>
            <Btn onClick={() => handleDecision('reject')} disabled={actioning} color="#ef5350">Reject</Btn>
            <Btn onClick={handleAutoApprove} disabled={autoApproving} color="#4fc3f7" outline>
              {autoApproving ? 'Auto-approving...' : 'Auto-approve'}
            </Btn>
            {actionMsg && <span style={{ fontSize: 13, color: '#a5d6a7' }}>{actionMsg}</span>}
          </div>
        </Section>
      )}

      {/* Upload controls — shown when in UPLOADING stage */}
      {video.stage === 'UPLOADING' && (
        <Section title="Upload to Platforms">
          <div style={{ fontSize: 13, color: '#888', marginBottom: 14 }}>
            Video is ready for upload. Make sure metadata and schedule are set, then trigger upload.
          </div>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            <Btn onClick={handleUpload} disabled={uploading} color="#66bb6a">
              {uploading ? 'Uploading...' : '⬆ Upload Now'}
            </Btn>
            {uploadMsg && <span style={{ fontSize: 13, color: '#a5d6a7' }}>{uploadMsg}</span>}
          </div>
        </Section>
      )}

      {/* Platform Metadata */}
      {(video.stage === 'UPLOAD_REVIEW' || video.stage === 'UPLOADING' || video.stage === 'PUBLISHED') && (
        <Section title="Platform Metadata" action={
          <div style={{ display: 'flex', gap: 8 }}>
            {metaMsg && <span style={{ fontSize: 12, color: '#a5d6a7' }}>{metaMsg}</span>}
            <Btn onClick={handleGenerateMeta} disabled={metaGenerating} color="#ce93d8" outline>
              {metaGenerating ? 'Generating...' : '✨ Generate'}
            </Btn>
            {metaEditing && <Btn onClick={handleSaveMeta} color="#66bb6a">Save</Btn>}
            {metaEditing && <Btn onClick={() => setMetaEditing(false)} color="#666" outline>Cancel</Btn>}
            {!metaEditing && Object.keys(meta).length > 0 && (
              <Btn onClick={() => { setMetaDraft({...meta}); setMetaEditing(true) }} color="#4fc3f7" outline>Edit</Btn>
            )}
          </div>
        }>
          {metaEditing && editMeta ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {[
                { key: 'youtube_title', label: 'YouTube Title', multiline: false },
                { key: 'youtube_description', label: 'YouTube Description', multiline: true },
                { key: 'instagram_caption', label: 'Instagram Caption', multiline: false },
              ].map(({ key, label, multiline }) => (
                <div key={key}>
                  <div style={{ fontSize: 11, color: '#666', marginBottom: 4 }}>{label}</div>
                  {multiline ? (
                    <textarea value={editMeta[key] || ''} onChange={e => setMetaDraft(p => ({ ...p, [key]: e.target.value }))}
                      style={{ width: '100%', minHeight: 80, background: '#0f0f1a', border: '1px solid #1e1e3a', borderRadius: 6, color: '#e0e0ff', padding: 10, fontSize: 13, resize: 'vertical', boxSizing: 'border-box' }} />
                  ) : (
                    <input value={editMeta[key] || ''} onChange={e => setMetaDraft(p => ({ ...p, [key]: e.target.value }))}
                      style={{ width: '100%', background: '#0f0f1a', border: '1px solid #1e1e3a', borderRadius: 6, color: '#e0e0ff', padding: 10, fontSize: 13, boxSizing: 'border-box' }} />
                  )}
                </div>
              ))}
              <div>
                <div style={{ fontSize: 11, color: '#666', marginBottom: 4 }}>Tags (comma-separated)</div>
                <input value={(editMeta.tags || []).join(', ')} onChange={e => setMetaDraft(p => ({ ...p, tags: e.target.value.split(',').map(t => t.trim()).filter(Boolean) }))}
                  style={{ width: '100%', background: '#0f0f1a', border: '1px solid #1e1e3a', borderRadius: 6, color: '#e0e0ff', padding: 10, fontSize: 13, boxSizing: 'border-box' }} />
              </div>
            </div>
          ) : Object.keys(meta).length > 0 ? (
            <div style={{ fontSize: 13, lineHeight: 1.7 }}>
              {meta.youtube_title && <div style={{ marginBottom: 8 }}><span style={{ color: '#666' }}>YouTube title: </span><b style={{ color: '#e0e0ff' }}>{meta.youtube_title}</b></div>}
              {meta.instagram_caption && <div style={{ marginBottom: 8 }}><span style={{ color: '#666' }}>Instagram: </span><span style={{ color: '#e0e0ff' }}>{meta.instagram_caption}</span></div>}
              {meta.tags?.length > 0 && (
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 8 }}>
                  {meta.tags.map(t => <span key={t} style={{ background: '#4fc3f720', color: '#4fc3f7', borderRadius: 4, padding: '2px 8px', fontSize: 11 }}>#{t}</span>)}
                </div>
              )}
              {meta.youtube_url && <div style={{ marginTop: 10, fontSize: 12 }}><a href={meta.youtube_url} target="_blank" rel="noreferrer" style={{ color: '#4fc3f7' }}>→ View on YouTube</a></div>}
            </div>
          ) : (
            <div style={{ fontSize: 13, color: '#444' }}>No metadata yet. Click "✨ Generate" to auto-generate from the script.</div>
          )}
        </Section>
      )}

      {/* Scheduled Publish */}
      {(video.stage === 'UPLOAD_REVIEW' || video.stage === 'UPLOADING') && (
        <Section title="Scheduled Publish">
          <div style={{ fontSize: 13, color: '#888', marginBottom: 12 }}>
            Set a future date/time to schedule the video. Leave empty to publish immediately.
            YouTube will keep the video private until the scheduled time.
          </div>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
            <input type="datetime-local" value={scheduleValue || (video.scheduled_publish_at ? video.scheduled_publish_at.replace(' ', 'T').slice(0, 16) : '')}
              onChange={e => setScheduleValue(e.target.value)}
              style={{ background: '#0f0f1a', border: '1px solid #1e1e3a', borderRadius: 6, color: '#e0e0ff', padding: '8px 12px', fontSize: 13 }} />
            <Btn onClick={handleSetSchedule} disabled={scheduleSaving} color="#ffd54f">
              {scheduleSaving ? 'Saving...' : 'Set Schedule'}
            </Btn>
            {scheduleValue && <Btn onClick={() => { setScheduleValue(''); setSchedule(id, null) }} color="#666" outline>Clear</Btn>}
            {scheduleMsg && <span style={{ fontSize: 13, color: '#a5d6a7' }}>{scheduleMsg}</span>}
          </div>
        </Section>
      )}

      {/* Idea card */}
      {video.idea_card && (
        <Section title="Idea Card">
          {video.idea_card.hook && <div style={{ color: '#ffd54f', fontStyle: 'italic', marginBottom: 10, fontSize: 14 }}>"{video.idea_card.hook}"</div>}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px 24px', fontSize: 13, color: '#888' }}>
            {Object.entries(video.idea_card).filter(([k]) => !['hook', 'proposed_at'].includes(k)).map(([k, v]) => (
              <div key={k}><span>{k.replace(/_/g, ' ')}: </span><b style={{ color: '#e0e0ff' }}>{String(v)}</b></div>
            ))}
          </div>
        </Section>
      )}

      {/* Script */}
      {video.script_data && (
        <Section title="Script">
          {video.script_data.hook && <div style={{ color: '#ffd54f', fontStyle: 'italic', marginBottom: 12, fontSize: 14 }}>Hook: "{video.script_data.hook}"</div>}
          {video.script_data.scenes?.map(s => (
            <div key={s.scene_id} style={{ background: '#0f0f1a', borderRadius: 8, padding: '12px 16px', marginBottom: 8 }}>
              <div style={{ fontSize: 11, color: '#4fc3f7', fontWeight: 700, marginBottom: 6 }}>SCENE {s.scene_id} — {s.timing}</div>
              <div style={{ color: '#e0e0ff', fontSize: 13, marginBottom: 4 }}>{s.narration}</div>
              {s.visual_goal && <div style={{ fontSize: 11, color: '#666' }}>Visual: {s.visual_goal}</div>}
            </div>
          ))}
          {video.script_data.word_count && (
            <div style={{ marginTop: 8, fontSize: 12, color: '#555' }}>
              Word count: {video.script_data.word_count} · Generated by: {video.script_data.generated_by}
            </div>
          )}
        </Section>
      )}

      {/* Sources */}
      {sources?.length > 0 && (
        <Section title={`Sources (${sources.length})`}>
          {sources.map(s => (
            <div key={s.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', padding: '10px 0', borderBottom: '1px solid #1e1e3a' }}>
              <div>
                <div style={{ fontSize: 13, color: '#e0e0ff', fontWeight: 600 }}>{s.title}</div>
                <div style={{ fontSize: 11, color: '#666', marginTop: 2 }}>{(s.authors || []).join(', ')} · {s.source_type}</div>
              </div>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexShrink: 0, marginLeft: 12 }}>
                <Badge text={`Trust ${s.trust_score}`} color={s.trust_score >= 90 ? '#a5d6a7' : s.trust_score >= 75 ? '#ffd54f' : '#ef9a9a'} />
                {s.url && <a href={s.url} target="_blank" rel="noreferrer" style={{ fontSize: 11, color: '#4fc3f7' }}>→</a>}
              </div>
            </div>
          ))}
        </Section>
      )}

      {/* QA */}
      {qaReports?.length > 0 && (
        <Section title="QA Reports">
          {qaReports.map((r, i) => (
            <div key={i} style={{ marginBottom: 12 }}>
              <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginBottom: 6 }}>
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
            </div>
          ))}
        </Section>
      )}

      {/* Approval history */}
      {video.approvals?.length > 0 && (
        <Section title="Approval History">
          {video.approvals.map((a, i) => (
            <div key={i} style={{ display: 'flex', gap: 10, alignItems: 'center', padding: '8px 0', borderBottom: '1px solid #1e1e3a', fontSize: 13 }}>
              <Badge text={a.gate} color="#ce93d8" />
              <Badge text={a.decision.toUpperCase()} color={a.decision === 'approve' ? '#a5d6a7' : '#ef9a9a'} />
              {a.feedback && <span style={{ color: '#888', fontStyle: 'italic', fontSize: 12 }}>{a.feedback}</span>}
              <span style={{ color: '#444', fontSize: 11, marginLeft: 'auto' }}>{new Date(a.created_at).toLocaleString()}</span>
            </div>
          ))}
        </Section>
      )}
    </div>
  )
}
