import React from 'react'

export default function StageCard({ title, items }) {
  return (
    <div style={{ border: '1px solid #ddd', borderRadius: 12, padding: 16, minWidth: 220 }}>
      <h3>{title}</h3>
      <p>{items} items</p>
    </div>
  )
}
