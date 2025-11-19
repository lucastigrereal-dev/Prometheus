'use client'

interface ResultsProps {
  results: any[]
  loading: boolean
}

export default function Results({ results, loading }: ResultsProps) {
  if (loading) {
    return (
      <div className="max-w-4xl mx-auto text-center py-12">
        <div className="inline-block w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="mt-4 text-gray-400">Buscando no Knowledge Brain...</p>
      </div>
    )
  }

  if (results.length === 0) {
    return (
      <div className="max-w-4xl mx-auto text-center py-12">
        <p className="text-gray-500 text-lg">
          Faça uma busca para explorar o conhecimento
        </p>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto space-y-4">
      <h2 className="text-2xl font-bold mb-4 text-white">
        {results.length} Resultados Encontrados
      </h2>
      {results.map((result, index) => (
        <div
          key={index}
          className="bg-gray-800/50 border border-gray-700 rounded-xl p-6 hover:border-blue-500 transition-colors"
        >
          <div className="flex justify-between items-start mb-3">
            <div>
              <span className="px-3 py-1 bg-blue-600/20 text-blue-400 text-sm rounded-full">
                {result.source_type || 'claude'}
              </span>
              <span className="ml-3 text-gray-500 text-sm">
                Relevância: {(result.similarity * 100).toFixed(1)}%
              </span>
            </div>
            <span className="text-gray-500 text-sm">
              {new Date(result.created_at).toLocaleDateString('pt-BR')}
            </span>
          </div>
          <p className="text-gray-300 leading-relaxed whitespace-pre-wrap">
            {result.content}
          </p>
          <div className="mt-4 text-sm text-gray-500">
            {result.tokens} tokens
          </div>
        </div>
      ))}
    </div>
  )
}
