'use client'

import { useEffect, useState } from 'react'

interface StatsData {
  total_documents: number
  total_chunks: number
  claude_count: number
  gpt_count: number
}

export default function Stats() {
  const [stats, setStats] = useState<StatsData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/stats')
      .then(res => res.json())
      .then(data => {
        setStats(data)
        setLoading(false)
      })
      .catch(err => {
        console.error('Stats error:', err)
        setLoading(false)
      })
  }, [])

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 max-w-4xl mx-auto">
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="bg-gray-800/30 rounded-xl p-6 animate-pulse">
            <div className="h-4 bg-gray-700 rounded w-20 mb-2"></div>
            <div className="h-8 bg-gray-700 rounded w-16"></div>
          </div>
        ))}
      </div>
    )
  }

  if (!stats) return null

  const statItems = [
    { label: 'Documentos', value: stats.total_documents, color: 'text-blue-400' },
    { label: 'Chunks', value: stats.total_chunks, color: 'text-purple-400' },
    { label: 'Claude', value: stats.claude_count, color: 'text-green-400' },
    { label: 'GPT', value: stats.gpt_count, color: 'text-yellow-400' },
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 max-w-4xl mx-auto">
      {statItems.map((item, index) => (
        <div key={index} className="bg-gray-800/50 border border-gray-700 rounded-xl p-6 text-center">
          <div className="text-gray-400 text-sm mb-1">{item.label}</div>
          <div className={`text-3xl font-bold ${item.color}`}>
            {item.value.toLocaleString()}
          </div>
        </div>
      ))}
    </div>
  )
}
