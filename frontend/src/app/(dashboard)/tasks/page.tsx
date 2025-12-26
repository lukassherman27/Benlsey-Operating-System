'use client'

import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import {
  CheckCircle2,
  Clock,
  AlertTriangle,
  RefreshCw,
  ListTodo,
  AlertCircle,
  Plus,
  FolderOpen,
} from 'lucide-react'
import { useState } from 'react'
import { cn } from '@/lib/utils'
import { ds } from '@/lib/design-system'
import { api } from '@/lib/api'
import { TaskEditModal } from '@/components/tasks/task-edit-modal'
import { TaskMiniKanban } from '@/components/tasks/task-mini-kanban'
import Link from 'next/link'

interface Task {
  task_id: number
  title: string
  description: string | null
  task_type: string
  priority: string
  status: string
  due_date: string | null
  project_code: string | null
  proposal_id: number | null
  source_suggestion_id: number | null
  source_email_id: number | null
  source_transcript_id: number | null
  source_meeting_id: number | null
  assignee: string | null
  created_at: string
  completed_at: string | null
  parent_task_id: number | null
  category: string | null
  assigned_staff_id: number | null
  deliverable_id: number | null
}

export default function TasksPage() {
  const queryClient = useQueryClient()
  const [modalOpen, setModalOpen] = useState(false)
  const [modalMode, setModalMode] = useState<'create' | 'edit'>('create')
  const [selectedTask, setSelectedTask] = useState<Task | null>(null)

  // Fetch tasks
  const { data, isLoading, error } = useQuery({
    queryKey: ['tasks'],
    queryFn: () => api.getTasks({ limit: 500 }),
  })

  // Open create modal
  const handleCreateTask = () => {
    setSelectedTask(null)
    setModalMode('create')
    setModalOpen(true)
  }

  const tasks = data?.tasks || []

  // Calculate stats
  const today = new Date().toISOString().split('T')[0]
  const stats = {
    total: tasks.length,
    pending: tasks.filter((t) => t.status === 'pending' || t.status === 'in_progress').length,
    overdue: tasks.filter((t) =>
      t.due_date && t.due_date < today && t.status !== 'completed' && t.status !== 'cancelled'
    ).length,
    completed: tasks.filter((t) => t.status === 'completed').length,
  }

  // Group tasks by project
  const projectGroups = tasks.reduce((acc, task) => {
    const code = task.project_code || 'No Project'
    if (!acc[code]) acc[code] = []
    acc[code].push(task)
    return acc
  }, {} as Record<string, Task[]>)

  // Sort projects by number of pending tasks (most active first)
  const sortedProjects = Object.entries(projectGroups)
    .map(([code, tasks]) => ({
      code,
      tasks,
      pending: tasks.filter(t => t.status === 'pending' || t.status === 'in_progress').length,
      overdue: tasks.filter(t => t.due_date && t.due_date < today && t.status !== 'completed').length,
    }))
    .sort((a, b) => {
      // Overdue first, then by pending count
      if (a.overdue > 0 && b.overdue === 0) return -1
      if (b.overdue > 0 && a.overdue === 0) return 1
      return b.pending - a.pending
    })

  // Loading skeleton
  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <Skeleton className="h-8 w-48 mb-2" />
            <Skeleton className="h-4 w-96" />
          </div>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <Card key={i}><CardContent className="pt-6"><Skeleton className="h-16 w-full" /></CardContent></Card>
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-64 w-full" />
          ))}
        </div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="space-y-6">
        <Card className={cn(ds.borderRadius.card, "border-red-200 bg-red-50")}>
          <CardContent className="py-12 text-center">
            <AlertCircle className="mx-auto h-12 w-12 text-red-400 mb-4" />
            <p className={cn(ds.typography.heading3, "text-red-700 mb-2")}>
              Failed to load tasks
            </p>
            <p className={cn(ds.typography.body, "text-red-600 mb-4")}>
              The tasks API may not be available yet.
            </p>
            <Button
              onClick={() => queryClient.invalidateQueries({ queryKey: ['tasks'] })}
              variant="outline"
              className="border-red-200 text-red-700 hover:bg-red-100"
            >
              Try Again
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6 w-full max-w-full overflow-x-hidden">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className={cn(ds.typography.heading1, ds.textColors.primary)}>
            Tasks Overview
          </h1>
          <p className={cn(ds.typography.body, ds.textColors.secondary, "mt-1")}>
            All tasks grouped by project
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => queryClient.invalidateQueries({ queryKey: ['tasks'] })}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button
            size="sm"
            onClick={handleCreateTask}
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Task
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-slate-100">
                <ListTodo className="h-5 w-5 text-slate-700" />
              </div>
              <div>
                <p className={cn(ds.typography.caption, ds.textColors.tertiary)}>Total</p>
                <p className={cn(ds.typography.heading2, ds.textColors.primary)}>
                  {stats.total}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className={cn(ds.borderRadius.card, "border-blue-200 bg-blue-50/30")}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-100">
                <Clock className="h-5 w-5 text-blue-700" />
              </div>
              <div>
                <p className={cn(ds.typography.caption, "text-blue-700")}>Pending</p>
                <p className={cn(ds.typography.heading2, "text-blue-800")}>
                  {stats.pending}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className={cn(ds.borderRadius.card, "border-red-200 bg-red-50/30")}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-red-100">
                <AlertTriangle className="h-5 w-5 text-red-700" />
              </div>
              <div>
                <p className={cn(ds.typography.caption, "text-red-700")}>Overdue</p>
                <p className={cn(ds.typography.heading2, "text-red-800")}>
                  {stats.overdue}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className={cn(ds.borderRadius.card, "border-emerald-200 bg-emerald-50/30")}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-emerald-100">
                <CheckCircle2 className="h-5 w-5 text-emerald-700" />
              </div>
              <div>
                <p className={cn(ds.typography.caption, "text-emerald-700")}>Completed</p>
                <p className={cn(ds.typography.heading2, "text-emerald-800")}>
                  {stats.completed}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Projects Summary */}
      <div className="flex items-center gap-2 text-sm text-slate-600">
        <FolderOpen className="h-4 w-4" />
        <span>{sortedProjects.length} projects with tasks</span>
      </div>

      {/* Tasks by Project */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {sortedProjects.map(({ code, pending, overdue }) => (
          <div key={code} className="relative">
            {overdue > 0 && (
              <Badge className="absolute -top-2 -right-2 z-10 bg-red-500">
                {overdue} overdue
              </Badge>
            )}
            {code !== 'No Project' ? (
              <Link href={`/proposals/${encodeURIComponent(code)}`}>
                <TaskMiniKanban
                  projectCode={code}
                  title={code}
                />
              </Link>
            ) : (
              <TaskMiniKanban
                projectCode=""
                title="Unassigned Tasks"
              />
            )}
          </div>
        ))}
      </div>

      {sortedProjects.length === 0 && (
        <Card className="border-dashed">
          <CardContent className="py-12 text-center">
            <ListTodo className="mx-auto h-12 w-12 text-slate-300 mb-4" />
            <p className={cn(ds.typography.heading3, ds.textColors.secondary)}>
              No tasks yet
            </p>
            <p className={cn(ds.typography.body, ds.textColors.tertiary, "mt-2")}>
              Create a task to get started
            </p>
            <Button className="mt-4" onClick={handleCreateTask}>
              <Plus className="h-4 w-4 mr-2" />
              Add Task
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Task Edit Modal */}
      <TaskEditModal
        open={modalOpen}
        onOpenChange={setModalOpen}
        task={selectedTask}
        mode={modalMode}
      />
    </div>
  )
}
