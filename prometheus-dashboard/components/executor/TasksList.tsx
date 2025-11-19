'use client'

interface TasksListProps {
  tasks: any[]
  onRefresh: () => void
}

export default function TasksList({ tasks, onRefresh }: TasksListProps) {
  const getStatusColor = (status: string) => {
    const colors: any = {
      pending: 'text-yellow-400 bg-yellow-400/20',
      running: 'text-blue-400 bg-blue-400/20',
      completed: 'text-green-400 bg-green-400/20',
      failed: 'text-red-400 bg-red-400/20',
      cancelled: 'text-gray-400 bg-gray-400/20'
    }
    return colors[status] || colors.pending
  }

  const getStatusIcon = (status: string) => {
    const icons: any = {
      pending: '⏳',
      running: '⚡',
      completed: '✅',
      failed: '❌',
      cancelled: '🚫'
    }
    return icons[status] || '❓'
  }

  const executeTask = async (taskId: string) => {
    try {
      await fetch(`/api/executor/task/${taskId}/execute`, { method: 'POST' })
      onRefresh()
    } catch (error) {
      console.error('Error executing task:', error)
      alert('Erro ao executar tarefa')
    }
  }

  const cancelTask = async (taskId: string) => {
    try {
      await fetch(`/api/executor/task/${taskId}`, { method: 'DELETE' })
      onRefresh()
    } catch (error) {
      console.error('Error cancelling task:', error)
      alert('Erro ao cancelar tarefa')
    }
  }

  if (tasks.length === 0) {
    return (
      <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-12 text-center">
        <p className="text-gray-500 text-lg">Nenhuma tarefa ainda</p>
        <p className="text-gray-600 text-sm mt-2">Use as ações rápidas acima para começar</p>
      </div>
    )
  }

  return (
    <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold text-white">Tarefas ({tasks.length})</h2>
        <button
          onClick={onRefresh}
          className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-white transition-colors"
        >
          🔄 Atualizar
        </button>
      </div>

      <div className="space-y-3">
        {tasks.map((task) => (
          <div
            key={task.id}
            className="bg-gray-900/50 border border-gray-700 rounded-lg p-4 hover:border-purple-500 transition-colors"
          >
            <div className="flex justify-between items-start mb-2">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-2xl">{getStatusIcon(task.status)}</span>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(task.status)}`}>
                    {task.status}
                  </span>
                  <span className="text-gray-500 text-sm">#{task.id}</span>
                </div>
                <p className="text-white font-medium">{task.description}</p>
                <p className="text-gray-400 text-sm mt-1">Ação: {task.action}</p>
              </div>

              <div className="flex gap-2">
                {task.status === 'pending' && (
                  <>
                    <button
                      onClick={() => executeTask(task.id)}
                      className="px-3 py-1 bg-green-600 hover:bg-green-700 rounded text-white text-sm"
                    >
                      ▶️ Executar
                    </button>
                    <button
                      onClick={() => cancelTask(task.id)}
                      className="px-3 py-1 bg-red-600 hover:bg-red-700 rounded text-white text-sm"
                    >
                      ❌ Cancelar
                    </button>
                  </>
                )}
              </div>
            </div>

            {/* Logs */}
            {task.logs && task.logs.length > 0 && (
              <div className="mt-3 pt-3 border-t border-gray-700">
                <p className="text-gray-400 text-xs font-medium mb-2">LOGS:</p>
                <div className="space-y-1">
                  {task.logs.map((log: any, index: number) => (
                    <div key={index} className="text-xs text-gray-500">
                      <span className="text-gray-600">{new Date(log.timestamp).toLocaleTimeString()}</span>
                      {' '}- <span className={log.level === 'error' ? 'text-red-400' : log.level === 'success' ? 'text-green-400' : ''}>{log.message}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Result (para completed) */}
            {task.status === 'completed' && task.result && (
              <div className="mt-3 pt-3 border-t border-gray-700">
                <p className="text-gray-400 text-xs font-medium mb-2">RESULTADO:</p>
                <pre className="text-xs text-gray-300 bg-gray-950 p-2 rounded overflow-auto max-h-40">
                  {JSON.stringify(task.result, null, 2)}
                </pre>
              </div>
            )}

            {/* Error (para failed) */}
            {task.status === 'failed' && task.error && (
              <div className="mt-3 pt-3 border-t border-gray-700">
                <p className="text-red-400 text-xs font-medium mb-2">ERRO:</p>
                <p className="text-xs text-red-300">{task.error}</p>
              </div>
            )}

            {/* Timestamps */}
            <div className="mt-3 text-xs text-gray-600">
              <span>Criado: {new Date(task.created_at).toLocaleString()}</span>
              {task.completed_at && (
                <span className="ml-4">Concluído: {new Date(task.completed_at).toLocaleString()}</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
