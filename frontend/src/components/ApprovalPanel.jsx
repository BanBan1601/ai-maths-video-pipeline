import React from 'react'

export default function ApprovalPanel() {
  return (
    <div style={{ border: '1px solid #ddd', borderRadius: 12, padding: 16 }}>
      <h3>Approval Queue</h3>
      <p>Idea review, script review, final review, upload review.</p>
      <button>Approve</button>
      <button style={{ marginLeft: 8 }}>Reject</button>
    </div>
  )
}
