'use client'

interface ExecutorStatsProps {
  stats: {
    task_stats: {
      total: number
      pending: number
      running: number
      completed: number
      failed: number
      cancelled: number
      critical_pending: number
    }
  }
}

export default function ExecutorStats({ stats }: ExecutorStatsProps) {
  const { task_stats } = stats

  const statItems = [
    { label: 'Total', value: task_stats.total, color: 'text-white', bg: 'bg-gray-700' },
    { label: 'Pendentes', value: task_stats.pending, color: 'text-yellow-400', bg: 'bg-yellow-900/30' },
    { label: 'Executando', value: task_stats.running, color: 'text-blue-400', bg: 'bg-blue-900/30' },
    { label: 'Completas', value: task_stats.completed, color: 'text-green-400', bg: 'bg-green-900/30' },
    { label: 'Falhas', value: task_stats.failed, color: 'text-red-400', bg: 'bg-red-900/30' },
    { label: 'Canceladas', value: task_stats.cancelled, color: 'text-gray-400', bg: 'bg-gray-800' },
  ]

  return (
    <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
      {statItems.map((item, index) => (
        <div key={index} className={`${item.bg} border border-gray-700 rounded-lg p-4 text-center`}>
          <div className="text-gray-400 text-xs uppercase mb-1">{item.label}</div>
          <div className={`text-3xl font-bold ${item.color}`}>
            {item.value}
          </div>
        </div>
      ))}
    </div>
  )
}
