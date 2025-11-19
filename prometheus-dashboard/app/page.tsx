'use client'

import { useState } from 'react'
import SearchBar from '@/components/SearchBar'
import Results from '@/components/Results'
import Stats from '@/components/Stats'

export default function Home() {
  const [results, setResults] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  const handleSearch = async (query: string) => {
    if (!query.trim()) return

    setLoading(true)
    try {
      const response = await fetch('/api/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, limit: 10 })
      })

      const data = await response.json()
      setResults(data.results || [])
    } catch (error) {
      console.error('Search error:', error)
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <header className="mb-12 text-center">
          <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            Prometheus Command Center
          </h1>
          <p className="text-gray-400 text-lg">
            Busca Semântica no Knowledge Brain
          </p>
        </header>

        {/* Stats Dashboard */}
        <div className="mb-8">
          <Stats />
        </div>

        {/* Search Section */}
        <div className="mb-8">
          <SearchBar onSearch={handleSearch} loading={loading} />
        </div>

        {/* Results Section */}
        <div>
          <Results results={results} loading={loading} />
        </div>
      </div>
    </div>
  )
}
