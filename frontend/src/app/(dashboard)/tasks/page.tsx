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
  ChevronDown,
  RefreshCw,
  ListTodo,
  AlertCircle,
  ExternalLink,
  Calendar,
  CheckSquare,
  Bell,
  Plus,
  User,
  Pencil,
  FolderTree,
  Filter,
  Tag,
} from 'lucide-react'
import React, { useState } from 'react'
import { cn } from '@/lib/utils'
import { ds } from '@/lib/design-system'
import Link from 'next/link'
import { api } from '@/lib/api'
import { TaskEditModal } from '@/components/tasks/task-edit-modal'

// Task type matching database schema
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

// Task categories as defined in database
const TASK_CATEGORIES = [
  'Proposal', 'Project', 'Finance', 'Legal', 'Operations',
  'Marketing', 'Personal', 'HR', 'Admin', 'Other'
] as const

// Category badge colors
const categoryColors: Record<string, string> = {
  'Proposal': 'bg-teal-100 text-teal-700 border-teal-200',
  'Project': 'bg-blue-100 text-blue-700 border-blue-200',
  'Finance': 'bg-emerald-100 text-emerald-700 border-emerald-200',
  'Legal': 'bg-purple-100 text-purple-700 border-purple-200',
  'Operations': 'bg-orange-100 text-orange-700 border-orange-200',
  'Marketing': 'bg-pink-100 text-pink-700 border-pink-200',
  'Personal': 'bg-indigo-100 text-indigo-700 border-indigo-200',
  'HR': 'bg-amber-100 text-amber-700 border-amber-200',
  'Admin': 'bg-slate-100 text-slate-700 border-slate-200',
  'Other': 'bg-gray-100 text-gray-600 border-gray-200',
}

export default function TasksPage() {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState('all')
  const [categoryFilter, setCategoryFilter] = useState<string | null>(null)
  const [showHierarchy, setShowHierarchy] = useState(false)
  const [expandedTasks, setExpandedTasks] = useState<Set<number>>(new Set())
  const [modalOpen, setModalOpen] = useState(false)
  const [modalMode, setModalMode] = useState<'create' | 'edit'>('create')
  const [selectedTask, setSelectedTask] = useState<Task | null>(null)

  // Fetch tasks
  const { data, isLoading, error } = useQuery({
    queryKey: ['tasks'],
    queryFn: () => api.getTasks({ limit: 500 }),
  })

  // Fetch staff for displaying assignee names
  const { data: staffData } = useQuery({
    queryKey: ['staff'],
    queryFn: () => api.getStaff(),
  })

  // Mark complete mutation
  const completeTask = useMutation({
    mutationFn: (taskId: number) => api.completeTask(taskId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
    },
  })

  // Snooze task mutation
  const snoozeTaskMutation = useMutation({
    mutationFn: ({ taskId, newDueDate }: { taskId: number; newDueDate: string }) =>
      api.snoozeTask(taskId, newDueDate),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
    },
  })

  // Open create modal
  const handleCreateTask = () => {
    setSelectedTask(null)
    setModalMode('create')
    setModalOpen(true)
  }

  // Open edit modal
  const handleEditTask = (task: Task) => {
    setSelectedTask(task)
    setModalMode('edit')
    setModalOpen(true)
  }

  // Get assignee name from ID
  const getAssigneeName = (assigneeId: string | null) => {
    if (!assigneeId) return null
    const assignee = staffData?.assignees?.find(a => a.id === assigneeId)
    return assignee?.name || assigneeId
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
    fromMeetings: tasks.filter((t) => t.source_transcript_id || t.source_meeting_id).length,
  }

  // Filter tasks based on tab and category
  const filteredTasks = tasks.filter((task) => {
    // First apply category filter
    if (categoryFilter && (task.category || 'Other') !== categoryFilter) {
      return false
    }

    // Then apply tab filter
    switch (activeTab) {
      case 'pending':
        return task.status === 'pending' || task.status === 'in_progress'
      case 'overdue':
        return task.due_date && task.due_date < today && task.status !== 'completed' && task.status !== 'cancelled'
      case 'completed':
        return task.status === 'completed'
      case 'from_meetings':
        return task.source_transcript_id || task.source_meeting_id
      default:
        return true
    }
  })

  // Organize tasks for hierarchy view
  const getChildTasks = (parentId: number) =>
    filteredTasks.filter(t => t.parent_task_id === parentId)

  const hasChildren = (taskId: number) =>
    tasks.some(t => t.parent_task_id === taskId)

  const toggleExpanded = (taskId: number) => {
    setExpandedTasks(prev => {
      const newSet = new Set(prev)
      if (newSet.has(taskId)) {
        newSet.delete(taskId)
      } else {
        newSet.add(taskId)
      }
      return newSet
    })
  }

  // Get root tasks (no parent) for hierarchy view, or all tasks for flat view
  const displayTasks = showHierarchy
    ? filteredTasks.filter(t => !t.parent_task_id)
    : filteredTasks

  // Count tasks by category
  const categoryCounts = tasks.reduce((acc, task) => {
    const cat = task.category || 'Other'
    acc[cat] = (acc[cat] || 0) + 1
    return acc
  }, {} as Record<string, number>)

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
            Follow-ups and action items from meetings and proposals
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

      {/* Category Filter + Hierarchy Toggle */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2">
          <Tag className="h-4 w-4 text-slate-500" />
          <span className={cn(ds.typography.caption, ds.textColors.tertiary)}>Category:</span>
        </div>
        <div className="flex flex-wrap gap-1.5">
          <Button
            variant={categoryFilter === null ? "default" : "outline"}
            size="sm"
            onClick={() => setCategoryFilter(null)}
            className="h-7 px-2.5 text-xs"
          >
            All ({stats.total})
          </Button>
          {TASK_CATEGORIES.filter(cat => categoryCounts[cat] > 0).map(cat => (
            <Button
              key={cat}
              variant={categoryFilter === cat ? "default" : "outline"}
              size="sm"
              onClick={() => setCategoryFilter(categoryFilter === cat ? null : cat)}
              className={cn(
                "h-7 px-2.5 text-xs",
                categoryFilter !== cat && categoryColors[cat]
              )}
            >
              {cat} ({categoryCounts[cat] || 0})
            </Button>
          ))}
        </div>
        <div className="ml-auto">
          <Button
            variant={showHierarchy ? "default" : "outline"}
            size="sm"
            onClick={() => setShowHierarchy(!showHierarchy)}
            className="h-7"
          >
            <FolderTree className="h-3.5 w-3.5 mr-1.5" />
            Hierarchy
          </Button>
        </div>
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
          <TabsTrigger value="from_meetings">
            <Calendar className="h-4 w-4 mr-1" />
            From Meetings
          </TabsTrigger>
          <TabsTrigger value="completed">Completed</TabsTrigger>
        </TabsList>

        <TabsContent value={activeTab} className="space-y-4">
          <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
            <CardHeader>
              <CardTitle className={ds.typography.heading3}>
                {activeTab === 'all' ? 'All Tasks' :
                 activeTab === 'pending' ? 'Pending Tasks' :
                 activeTab === 'overdue' ? 'Overdue Tasks' :
                 activeTab === 'from_meetings' ? 'Tasks from Meetings' : 'Completed Tasks'}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {displayTasks.length === 0 ? (
                <div className="text-center py-12">
                  <ListTodo className="mx-auto h-12 w-12 text-slate-300 mb-4" />
                  <p className={cn(ds.typography.heading3, ds.textColors.primary, "mb-2")}>
                    {stats.total === 0 ? 'No tasks yet' : 'No tasks in this category'}
                  </p>
                  <p className={cn(ds.typography.body, ds.textColors.tertiary, "max-w-md mx-auto")}>
                    {stats.total === 0
                      ? 'Tasks are created when you approve follow_up_needed suggestions from AI.'
                      : 'Try switching to a different tab or clearing the category filter.'}
                  </p>
                </div>
              ) : (
                <div className="space-y-2 max-h-[600px] overflow-y-auto">
                  {displayTasks.map((task) => (
                    <React.Fragment key={task.task_id}>
                    <div
                      className="flex items-center justify-between p-4 border rounded-lg hover:bg-slate-50 transition-colors group cursor-pointer"
                      onClick={() => handleEditTask(task)}
                    >
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          {/* Hierarchy expand button */}
                          {showHierarchy && hasChildren(task.task_id) && (
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-6 w-6 p-0 shrink-0"
                              onClick={(e) => { e.stopPropagation(); toggleExpanded(task.task_id) }}
                            >
                              {expandedTasks.has(task.task_id) ? (
                                <ChevronDown className="h-4 w-4" />
                              ) : (
                                <ChevronRight className="h-4 w-4" />
                              )}
                            </Button>
                          )}
                          <p className={cn(ds.typography.bodyBold, ds.textColors.primary, "truncate")}>
                            {task.title}
                          </p>
                          {task.category && task.category !== 'Other' && (
                            <Badge
                              variant="outline"
                              className={cn("text-xs", categoryColors[task.category] || categoryColors['Other'])}
                            >
                              {task.category}
                            </Badge>
                          )}
                          {task.assignee && task.assignee !== 'us' && (
                            <Badge variant="secondary" className="text-xs flex items-center gap-1">
                              <User className="h-3 w-3" />
                              {getAssigneeName(task.assignee)}
                            </Badge>
                          )}
                        </div>
                        <div className="flex items-center gap-2 mt-1 flex-wrap">
                          {task.project_code && (
                            <Link
                              href={`/proposals/${encodeURIComponent(task.project_code)}`}
                              className={cn(ds.typography.caption, "text-teal-600 font-medium hover:underline")}
                              onClick={(e) => e.stopPropagation()}
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
                          {task.source_transcript_id && (
                            <>
                              <span className={ds.textColors.tertiary}>•</span>
                              <span className={cn(ds.typography.caption, "text-purple-600 font-medium flex items-center gap-1")}>
                                <Calendar className="h-3 w-3" />
                                From Meeting
                              </span>
                            </>
                          )}
                          {task.source_suggestion_id && !task.source_transcript_id && (
                            <>
                              <span className={ds.textColors.tertiary}>•</span>
                              <span className={cn(ds.typography.caption, ds.textColors.tertiary, "flex items-center gap-1")}>
                                AI Suggestion
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
                              onClick={(e) => { e.stopPropagation(); completeTask.mutate(task.task_id) }}
                              disabled={completeTask.isPending}
                              className="h-8 px-2 text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50"
                              title="Mark complete"
                            >
                              <CheckSquare className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={(e) => { e.stopPropagation(); handleSnooze(task) }}
                              disabled={snoozeTaskMutation.isPending}
                              className="h-8 px-2 text-amber-600 hover:text-amber-700 hover:bg-amber-50"
                              title="Snooze 7 days"
                            >
                              <Bell className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={(e) => { e.stopPropagation(); handleEditTask(task) }}
                              className="h-8 px-2 text-slate-600 hover:text-slate-700 hover:bg-slate-100"
                              title="Edit task"
                            >
                              <Pencil className="h-4 w-4" />
                            </Button>
                          </div>
                        )}
                        <ChevronRight className="h-4 w-4 text-slate-400" />
                      </div>
                    </div>
                    {/* Child tasks (hierarchy view) */}
                    {showHierarchy && expandedTasks.has(task.task_id) && (
                      <div className="ml-8 border-l-2 border-slate-200 space-y-2 pl-4">
                        {getChildTasks(task.task_id).map(childTask => (
                          <div
                            key={childTask.task_id}
                            className="flex items-center justify-between p-3 border rounded-lg hover:bg-slate-50 transition-colors cursor-pointer bg-slate-50/50"
                            onClick={() => handleEditTask(childTask)}
                          >
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2">
                                <p className={cn(ds.typography.body, ds.textColors.primary, "truncate")}>
                                  {childTask.title}
                                </p>
                                {childTask.category && childTask.category !== 'Other' && (
                                  <Badge
                                    variant="outline"
                                    className={cn("text-xs", categoryColors[childTask.category] || categoryColors['Other'])}
                                  >
                                    {childTask.category}
                                  </Badge>
                                )}
                              </div>
                            </div>
                            <div className="flex items-center gap-2 ml-4">
                              <Badge variant="outline" className={priorityColors[childTask.priority] || 'bg-slate-100 text-slate-600'}>
                                {childTask.priority}
                              </Badge>
                              <Badge variant="outline" className={statusColors[childTask.status] || 'bg-slate-100 text-slate-600'}>
                                {childTask.status.replace('_', ' ')}
                              </Badge>
                              {childTask.status !== 'completed' && childTask.status !== 'cancelled' && (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={(e) => { e.stopPropagation(); completeTask.mutate(childTask.task_id) }}
                                  disabled={completeTask.isPending}
                                  className="h-6 px-1.5 text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50"
                                >
                                  <CheckSquare className="h-3.5 w-3.5" />
                                </Button>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </React.Fragment>
                  ))}
                </div>
              )}
              {displayTasks.length > 0 && (
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
