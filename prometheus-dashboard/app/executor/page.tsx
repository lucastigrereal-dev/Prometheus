'use client'

import { useState, useEffect } from 'react'
import ActionButtons from '@/components/executor/ActionButtons'
import TasksList from '@/components/executor/TasksList'
import ExecutorStats from '@/components/executor/ExecutorStats'

export default function ExecutorPage() {
  const [tasks, setTasks] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [stats, setStats] = useState<any>(null)

  const fetchTasks = async () => {
    try {
      const response = await fetch('/api/executor/tasks')
      const data = await response.json()
      setTasks(data.tasks || [])
    } catch (error) {
      console.error('Error fetching tasks:', error)
    }
  }

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/executor/stats')
      const data = await response.json()
      setStats(data)
    } catch (error) {
      console.error('Error fetching stats:', error)
    }
  }

  useEffect(() => {
    fetchTasks()
    fetchStats()

    // Auto-refresh a cada 5 segundos
    const interval = setInterval(() => {
      fetchTasks()
      fetchStats()
    }, 5000)

    return () => clearInterval(interval)
  }, [])

  const handleTaskCreated = () => {
    fetchTasks()
    fetchStats()
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <header className="mb-12">
          <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
            Executor Local
          </h1>
          <p className="text-gray-400 text-lg">
            Execute ações no sistema local de forma segura e auditada
          </p>
        </header>

        {/* Stats */}
        {stats && (
          <div className="mb-8">
            <ExecutorStats stats={stats} />
          </div>
        )}

        {/* Action Buttons */}
        <div className="mb-8">
          <ActionButtons onTaskCreated={handleTaskCreated} />
        </div>

        {/* Tasks List */}
        <div>
          <TasksList tasks={tasks} onRefresh={fetchTasks} />
        </div>
      </div>
    </div>
  )
}
