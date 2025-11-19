'use client'

import { useState } from 'react'

interface ActionButtonsProps {
  onTaskCreated: () => void
}

export default function ActionButtons({ onTaskCreated }: ActionButtonsProps) {
  const [loading, setLoading] = useState(false)

  const quickActions = [
    {
      name: 'System Info',
      action: 'get_system_info',
      params: {},
      description: 'Ver informações do sistema',
      icon: '💻',
      color: 'blue'
    },
    {
      name: 'List Downloads',
      action: 'list_files',
      params: { path: 'C:/Users/lucas/Downloads', max_files: 20 },
      description: 'Listar arquivos em Downloads',
      icon: '📁',
      color: 'green'
    },
    {
      name: 'Organize Downloads (Dry Run)',
      action: 'organize_downloads',
      params: { dry_run: true },
      description: 'Simular organização de Downloads',
      icon: '🗂️',
      color: 'yellow'
    }
  ]

  const executeQuickAction = async (action: string, params: any, description: string) => {
    setLoading(true)
    try {
      // Criar tarefa
      const response = await fetch('/api/executor/task/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, params, description })
      })

      const data = await response.json()
      const taskId = data.task_id

      // Executar imediatamente
      await fetch(`/api/executor/task/${taskId}/execute`, { method: 'POST' })

      onTaskCreated()
    } catch (error) {
      console.error('Error executing action:', error)
      alert('Erro ao executar ação')
    } finally {
      setLoading(false)
    }
  }

  const getColorClasses = (color: string) => {
    const colors: any = {
      blue: 'bg-blue-600 hover:bg-blue-700 border-blue-500',
      green: 'bg-green-600 hover:bg-green-700 border-green-500',
      yellow: 'bg-yellow-600 hover:bg-yellow-700 border-yellow-500',
      purple: 'bg-purple-600 hover:bg-purple-700 border-purple-500',
      red: 'bg-red-600 hover:bg-red-700 border-red-500'
    }
    return colors[color] || colors.blue
  }

  return (
    <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-6">
      <h2 className="text-2xl font-bold mb-4 text-white">Ações Rápidas</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {quickActions.map((qa, index) => (
          <button
            key={index}
            onClick={() => executeQuickAction(qa.action, qa.params, qa.description)}
            disabled={loading}
            className={`${getColorClasses(qa.color)} disabled:opacity-50 disabled:cursor-not-allowed border-2 rounded-lg p-4 transition-all text-left`}
          >
            <div className="text-3xl mb-2">{qa.icon}</div>
            <div className="font-bold text-white">{qa.name}</div>
            <div className="text-sm text-gray-300 mt-1">{qa.description}</div>
          </button>
        ))}
      </div>
    </div>
  )
}
