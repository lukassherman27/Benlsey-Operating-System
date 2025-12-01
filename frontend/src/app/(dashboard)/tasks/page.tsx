'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Skeleton } from '@/components/ui/skeleton'
import {
  CheckCircle2,
  Clock,
  AlertTriangle,
  ChevronRight,
  RefreshCw,
  ListTodo,
  AlertCircle,
  ExternalLink,
  Calendar,
  CheckSquare,
  Bell,
} from 'lucide-react'
import { useState } from 'react'
import { cn } from '@/lib/utils'
import { ds } from '@/lib/design-system'
import Link from 'next/link'

// Task type matching database schema
interface Task {
  task_id: number
  title: string
  description: string | null
  task_type: 'follow_up' | 'action_item' | 'deadline' | 'reminder'
  priority: 'low' | 'medium' | 'high' | 'critical'
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled'
  due_date: string | null
  project_code: string | null
  proposal_id: number | null
  source_suggestion_id: number | null
  source_email_id: number | null
  created_at: string
  completed_at: string | null
}

interface TasksResponse {
  success: boolean
  tasks: Task[]
  count: number
}

// API placeholder - will be connected when backend API is created
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

async function fetchTasks(): Promise<TasksResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/tasks`)
    if (!response.ok) {
      throw new Error('API not available')
    }
    return response.json()
  } catch {
    // Return empty data when API doesn't exist yet
    return { success: true, tasks: [], count: 0 }
  }
}

async function updateTaskStatus(taskId: number, status: string): Promise<{ success: boolean }> {
  const response = await fetch(`${API_BASE_URL}/api/tasks/${taskId}/status`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status }),
  })
  return response.json()
}

async function snoozeTask(taskId: number, newDueDate: string): Promise<{ success: boolean }> {
  const response = await fetch(`${API_BASE_URL}/api/tasks/${taskId}/snooze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ due_date: newDueDate }),
  })
  return response.json()
}

export default function TasksPage() {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState('all')

  // Fetch tasks
  const { data, isLoading, error } = useQuery({
    queryKey: ['tasks'],
    queryFn: fetchTasks,
  })

  // Mark complete mutation
  const completeTask = useMutation({
    mutationFn: (taskId: number) => updateTaskStatus(taskId, 'completed'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
    },
  })

  // Snooze task mutation
  const snoozeTaskMutation = useMutation({
    mutationFn: ({ taskId, newDueDate }: { taskId: number; newDueDate: string }) =>
      snoozeTask(taskId, newDueDate),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
    },
  })

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

  // Filter tasks based on tab
  const filteredTasks = tasks.filter((task) => {
    switch (activeTab) {
      case 'pending':
        return task.status === 'pending' || task.status === 'in_progress'
      case 'overdue':
        return task.due_date && task.due_date < today && task.status !== 'completed' && task.status !== 'cancelled'
      case 'completed':
        return task.status === 'completed'
      default:
        return true
    }
  })

  // Priority colors
  const priorityColors: Record<string, string> = {
    low: 'bg-slate-100 text-slate-700 border-slate-200',
    medium: 'bg-blue-100 text-blue-700 border-blue-200',
    high: 'bg-amber-100 text-amber-700 border-amber-200',
    critical: 'bg-red-100 text-red-700 border-red-200',
  }

  // Status colors
  const statusColors: Record<string, string> = {
    pending: 'bg-slate-100 text-slate-700 border-slate-200',
    in_progress: 'bg-blue-100 text-blue-700 border-blue-200',
    completed: 'bg-emerald-100 text-emerald-700 border-emerald-200',
    cancelled: 'bg-slate-100 text-slate-500 border-slate-200',
  }

  // Handle snooze (add 7 days)
  const handleSnooze = (task: Task) => {
    const currentDue = task.due_date ? new Date(task.due_date) : new Date()
    currentDue.setDate(currentDue.getDate() + 7)
    const newDueDate = currentDue.toISOString().split('T')[0]
    snoozeTaskMutation.mutate({ taskId: task.task_id, newDueDate })
  }

  // Check if overdue
  const isOverdue = (dueDate: string | null) => {
    if (!dueDate) return false
    return dueDate < today
  }

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
        <Card><CardContent className="py-8"><Skeleton className="h-48 w-full" /></CardContent></Card>
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
            Tasks
          </h1>
          <p className={cn(ds.typography.body, ds.textColors.secondary, "mt-1")}>
            Follow-ups and action items from AI suggestions
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => queryClient.invalidateQueries({ queryKey: ['tasks'] })}
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
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

      {/* Filter Tabs & Task List */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="all">All</TabsTrigger>
          <TabsTrigger value="pending">Pending</TabsTrigger>
          <TabsTrigger value="overdue">
            <AlertTriangle className="h-4 w-4 mr-1" />
            Overdue
          </TabsTrigger>
          <TabsTrigger value="completed">Completed</TabsTrigger>
        </TabsList>

        <TabsContent value={activeTab} className="space-y-4">
          <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
            <CardHeader>
              <CardTitle className={ds.typography.heading3}>
                {activeTab === 'all' ? 'All Tasks' :
                 activeTab === 'pending' ? 'Pending Tasks' :
                 activeTab === 'overdue' ? 'Overdue Tasks' : 'Completed Tasks'}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {filteredTasks.length === 0 ? (
                <div className="text-center py-12">
                  <ListTodo className="mx-auto h-12 w-12 text-slate-300 mb-4" />
                  <p className={cn(ds.typography.heading3, ds.textColors.primary, "mb-2")}>
                    {stats.total === 0 ? 'No tasks yet' : 'No tasks in this category'}
                  </p>
                  <p className={cn(ds.typography.body, ds.textColors.tertiary, "max-w-md mx-auto")}>
                    {stats.total === 0
                      ? 'Tasks are created when you approve follow_up_needed suggestions from AI.'
                      : 'Try switching to a different tab to see other tasks.'}
                  </p>
                </div>
              ) : (
                <div className="space-y-2 max-h-[600px] overflow-y-auto">
                  {filteredTasks.map((task) => (
                    <div
                      key={task.task_id}
                      className="flex items-center justify-between p-4 border rounded-lg hover:bg-slate-50 transition-colors group"
                    >
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <p className={cn(ds.typography.bodyBold, ds.textColors.primary, "truncate")}>
                            {task.title}
                          </p>
                        </div>
                        <div className="flex items-center gap-2 mt-1 flex-wrap">
                          {task.project_code && (
                            <Link
                              href={`/projects/${encodeURIComponent(task.project_code)}`}
                              className={cn(ds.typography.caption, "text-teal-600 font-medium hover:underline")}
                            >
                              {task.project_code}
                            </Link>
                          )}
                          {task.due_date && (
                            <>
                              {task.project_code && <span className={ds.textColors.tertiary}>•</span>}
                              <span className={cn(
                                ds.typography.caption,
                                isOverdue(task.due_date) ? "text-red-600 font-medium" : ds.textColors.tertiary
                              )}>
                                <Calendar className="h-3 w-3 inline mr-1" />
                                {isOverdue(task.due_date) ? 'Overdue: ' : 'Due: '}
                                {task.due_date}
                              </span>
                            </>
                          )}
                          {task.source_suggestion_id && (
                            <>
                              <span className={ds.textColors.tertiary}>•</span>
                              <Link
                                href={`/admin/suggestions`}
                                className={cn(ds.typography.caption, ds.textColors.tertiary, "hover:text-teal-600 flex items-center gap-1")}
                              >
                                <ExternalLink className="h-3 w-3" />
                                Suggestion #{task.source_suggestion_id}
                              </Link>
                            </>
                          )}
                          {task.source_email_id && (
                            <>
                              <span className={ds.textColors.tertiary}>•</span>
                              <span className={cn(ds.typography.caption, ds.textColors.tertiary, "flex items-center gap-1")}>
                                <ExternalLink className="h-3 w-3" />
                                Email #{task.source_email_id}
                              </span>
                            </>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-2 ml-4">
                        <Badge
                          variant="outline"
                          className={priorityColors[task.priority] || 'bg-slate-100 text-slate-600'}
                        >
                          {task.priority}
                        </Badge>
                        <Badge
                          variant="outline"
                          className={statusColors[task.status] || 'bg-slate-100 text-slate-600'}
                        >
                          {task.status.replace('_', ' ')}
                        </Badge>
                        {isOverdue(task.due_date) && task.status !== 'completed' && (
                          <Badge variant="destructive">Overdue</Badge>
                        )}

                        {/* Actions - only show for non-completed tasks */}
                        {task.status !== 'completed' && task.status !== 'cancelled' && (
                          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => completeTask.mutate(task.task_id)}
                              disabled={completeTask.isPending}
                              className="h-8 px-2 text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50"
                              title="Mark complete"
                            >
                              <CheckSquare className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleSnooze(task)}
                              disabled={snoozeTaskMutation.isPending}
                              className="h-8 px-2 text-amber-600 hover:text-amber-700 hover:bg-amber-50"
                              title="Snooze 7 days"
                            >
                              <Bell className="h-4 w-4" />
                            </Button>
                          </div>
                        )}
                        <ChevronRight className="h-4 w-4 text-slate-400" />
                      </div>
                    </div>
                  ))}
                </div>
              )}
              {filteredTasks.length > 0 && (
                <div className="mt-4 pt-4 border-t">
                  <p className={cn(ds.typography.caption, ds.textColors.tertiary, "text-center")}>
                    Showing {filteredTasks.length} of {stats.total} tasks
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
