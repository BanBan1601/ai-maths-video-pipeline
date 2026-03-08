import React, { useRef, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useApi } from '../hooks/useApi'
import { getVideo, getPreviewUrl } from '../api/client'

export default function VideoPreviewPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const videoRef = useRef(null)
  const [playing, setPlaying] = useState(false)

  const { data: video } = useApi(() => getVideo(id), [id])
  const { data: previewData } = useApi(() => getPreviewUrl(id), [id])

  const videoUrl = previewData?.video_url
  const hasVideo = previewData?.has_video

  const togglePlay = () => {
    if (!videoRef.current) return
    if (playing) { videoRef.current.pause(); setPlaying(false) }
    else { videoRef.current.play(); setPlaying(true) }
  }

  return (
    <div style={{ maxWidth: 520, margin: '0 auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
        <button onClick={() => navigate(-1)} style={{ background: 'transparent', border: '1px solid #1e1e3a', color: '#666', borderRadius: 6, padding: '6px 12px', cursor: 'pointer', fontSize: 12 }}>← Back</button>
        <h1 style={{ margin: 0, fontSize: 18, fontWeight: 700, flex: 1 }}>{video?.title || 'Preview'}</h1>
        {video?.stage && (
          <span style={{ fontSize: 12, color: '#4fc3f7', border: '1px solid #4fc3f740', borderRadius: 6, padding: '3px 10px' }}>
            {video.stage.replace(/_/g, ' ')}
          </span>
        )}
      </div>

      {/* Portrait video container */}
      <div style={{ background: '#000', borderRadius: 16, overflow: 'hidden', position: 'relative', aspectRatio: '9/16', maxHeight: 700, border: '1px solid #1e1e3a' }}>
        {hasVideo && videoUrl ? (
          <>
            <video
              ref={videoRef}
              src={videoUrl}
              style={{ width: '100%', height: '100%', objectFit: 'contain' }}
              onEnded={() => setPlaying(false)}
              controls
              playsInline
            />
          </>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#444', gap: 16 }}>
            <div style={{ fontSize: 48 }}>🎬</div>
            <div style={{ fontSize: 14, color: '#555', textAlign: 'center', padding: '0 24px' }}>
              {video?.stage === 'MANIM_GENERATING' || video?.stage === 'QA_RUNNING'
                ? 'Video is being rendered...'
                : video?.stage === 'IDEA_REVIEW' || video?.stage === 'SCRIPT_REVIEW'
                ? 'Video will be generated after script approval'
                : 'No video available yet'}
            </div>
            <div style={{ fontSize: 11, color: '#333' }}>Stage: {video?.stage?.replace(/_/g, ' ')}</div>
          </div>
        )}
      </div>

      {/* Script scenes below player */}
      {video?.script_data?.scenes && (
        <div style={{ marginTop: 24 }}>
          <h3 style={{ fontSize: 13, fontWeight: 600, color: '#4fc3f7', marginBottom: 12 }}>Script Breakdown</h3>
          {video.script_data.scenes.map(s => (
            <div key={s.scene_id} style={{ background: '#1a1a2e', border: '1px solid #1e1e3a', borderRadius: 8, padding: '10px 14px', marginBottom: 8 }}>
              <div style={{ fontSize: 11, color: '#4fc3f7', fontWeight: 700, marginBottom: 4 }}>SCENE {s.scene_id} · {s.timing}</div>
              <div style={{ fontSize: 13, color: '#e0e0ff', lineHeight: 1.6 }}>{s.narration}</div>
              {s.visual_goal && <div style={{ fontSize: 11, color: '#555', marginTop: 4 }}>Visual: {s.visual_goal}</div>}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
