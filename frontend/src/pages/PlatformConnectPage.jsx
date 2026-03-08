import React from 'react'
import { useApi } from '../hooks/useApi'
import { getPlatformsStatus } from '../api/client'

function StatusDot({ connected }) {
  return <span style={{ display: 'inline-block', width: 10, height: 10, borderRadius: '50%', background: connected ? '#66bb6a' : '#ef5350', marginRight: 8 }} />
}

function PlatformCard({ name, icon, connected, reason, onConnect, note }) {
  return (
    <div style={{ background: '#1a1a2e', border: `1px solid ${connected ? '#66bb6a40' : '#1e1e3a'}`, borderRadius: 14, padding: 24, marginBottom: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 16 }}>
        <div style={{ fontSize: 32 }}>{icon}</div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 16, fontWeight: 700, color: '#e0e0ff' }}>{name}</div>
          <div style={{ fontSize: 13, marginTop: 2 }}>
            <StatusDot connected={connected} />
            <span style={{ color: connected ? '#66bb6a' : '#ef9a9a' }}>{connected ? 'Connected' : 'Not connected'}</span>
          </div>
        </div>
        {!connected && onConnect && (
          <button onClick={onConnect} style={{ background: '#4fc3f7', color: '#0f0f1a', border: 'none', borderRadius: 8, padding: '10px 20px', fontWeight: 700, cursor: 'pointer', fontSize: 13 }}>
            Connect
          </button>
        )}
        {connected && <span style={{ fontSize: 12, color: '#66bb6a', border: '1px solid #66bb6a40', borderRadius: 6, padding: '4px 12px' }}>✓ Ready to upload</span>}
      </div>
      {reason && !connected && <div style={{ fontSize: 12, color: '#666', fontStyle: 'italic', marginBottom: 10 }}>{reason}</div>}
      {note && <div style={{ fontSize: 12, color: '#555', background: '#0f0f1a', borderRadius: 8, padding: '10px 14px', lineHeight: 1.7 }}>{note}</div>}
    </div>
  )
}

export default function PlatformConnectPage() {
  const { data: status, loading, refetch } = useApi(getPlatformsStatus, [], 30000)

  const yt = status?.youtube || {}
  const ig = status?.instagram || {}

  const handleYoutubeConnect = () => {
    window.location.href = 'http://localhost:8000/api/platforms/youtube/connect'
  }

  return (
    <div style={{ maxWidth: 600 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 28 }}>
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700 }}>Platform Connections</h1>
        <button onClick={refetch} style={{ background: 'transparent', border: '1px solid #1e1e3a', color: '#666', borderRadius: 6, padding: '6px 14px', cursor: 'pointer', fontSize: 12 }}>Refresh</button>
      </div>

      {loading && <div style={{ color: '#666' }}>Checking connections...</div>}

      {!loading && (
        <>
          <PlatformCard
            name="YouTube"
            icon="▶️"
            connected={yt.connected}
            reason={yt.reason}
            onConnect={handleYoutubeConnect}
            note={!yt.connected ? `To connect YouTube:
1. Go to console.cloud.google.com
2. Create a project → Enable YouTube Data API v3
3. Create OAuth 2.0 credentials (Web application)
4. Set redirect URI: http://localhost:8000/api/platforms/youtube/callback
5. Add YOUTUBE_CLIENT_ID and YOUTUBE_CLIENT_SECRET to your .env file
6. Restart Docker and click Connect above` : null}
          />

          <PlatformCard
            name="Instagram"
            icon="📷"
            connected={ig.connected}
            reason={ig.reason}
            note={!ig.connected ? `To connect Instagram:
1. Go to developers.facebook.com → Create an App
2. Add Instagram Graph API product
3. Connect your Instagram Business/Creator account
4. Generate a long-lived access token
5. Add to .env: INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_IG_USER_ID
6. Restart Docker — no OAuth redirect needed

Note: Instagram requires a Business or Creator account. Personal accounts cannot use the Graph API for video uploads.` : `Username: @${ig.username || '?'}`}
          />
        </>
      )}

      <div style={{ marginTop: 24, background: '#1a1a2e', border: '1px solid #1e1e3a', borderRadius: 12, padding: 20 }}>
        <h3 style={{ margin: '0 0 10px', fontSize: 14, color: '#4fc3f7' }}>How uploads work</h3>
        <ul style={{ margin: 0, paddingLeft: 18, fontSize: 13, color: '#666', lineHeight: 2 }}>
          <li>Videos reach <strong style={{ color: '#e0e0ff' }}>UPLOAD_REVIEW</strong> after passing QA and final approval</li>
          <li>At that stage, generate metadata (title, description, tags) and set a publish time</li>
          <li>Approve the upload — the pipeline sends the video to connected platforms</li>
          <li>YouTube: supports scheduled publishing (video is private until the set time)</li>
          <li>Instagram: publishes as a Reel (requires a public video URL for the Graph API)</li>
        </ul>
      </div>
    </div>
  )
}
