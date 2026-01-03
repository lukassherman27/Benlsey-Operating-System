'use client'

import { useState, useMemo, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  DndContext,
  DragEndEvent,
  DragOverlay,
  DragStartEvent,
  PointerSensor,
  useSensor,
  useSensors,
  closestCorners,
} from '@dnd-kit/core'
import {
  SortableContext,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable'
import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  CheckSquare,
  AlertTriangle,
  ListTodo,
  Kanban,
  Plus,
  Search,
  Filter,
  Calendar,
  User,
  GripVertical,
  Bell,
  MoreHorizontal,
  CheckCircle2,
  Circle,
  PlayCircle,
  XCircle,
  ArrowUpDown,
  SlidersHorizontal,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { ds } from '@/lib/design-system'
import { api } from '@/lib/api'
import { toast } from 'sonner'
import { TaskEditModal } from '@/components/tasks/task-edit-modal'

// Types
interface Task {
  task_id: number
  title: string
  description: string | null
  task_type: string | null
  priority: string
  status: string
  due_date: string | null
  project_code: string | null
  proposal_id: number | null
  assignee: string | null
  assigned_staff_id: number | null
  source_suggestion_id: number | null
  source_email_id: number | null
  source_transcript_id: number | null
  source_meeting_id: number | null
  created_at: string
  completed_at: string | null
  category: string | null
  parent_task_id: number | null
  deliverable_id: number | null
}

interface TaskStats {
  total: number
  pending: number
  in_progress: number
  completed: number
  cancelled: number
  overdue: number
  active: number
  by_priority: Record<string, number>
  by_type: Record<string, number>
}

type ViewMode = 'kanban' | 'list'
type TaskStatus = 'pending' | 'in_progress' | 'completed'

// Column configuration for Kanban
const COLUMNS = [
  { id: 'pending', title: 'To Do', status: 'pending' as TaskStatus, color: 'slate', icon: Circle },
  { id: 'in_progress', title: 'In Progress', status: 'in_progress' as TaskStatus, color: 'blue', icon: PlayCircle },
  { id: 'completed', title: 'Done', status: 'completed' as TaskStatus, color: 'emerald', icon: CheckCircle2 },
]

// Priority configuration
const PRIORITIES = [
  { value: 'critical', label: 'Critical', color: 'bg-red-100 text-red-700 border-red-200' },
  { value: 'high', label: 'High', color: 'bg-amber-100 text-amber-700 border-amber-200' },
  { value: 'medium', label: 'Medium', color: 'bg-blue-100 text-blue-700 border-blue-200' },
  { value: 'low', label: 'Low', color: 'bg-slate-100 text-slate-700 border-slate-200' },
]

const priorityColors: Record<string, string> = {
  critical: 'bg-red-100 text-red-700 border-red-200',
  high: 'bg-amber-100 text-amber-700 border-amber-200',
  medium: 'bg-blue-100 text-blue-700 border-blue-200',
  low: 'bg-slate-100 text-slate-700 border-slate-200',
}

// ============================================================================
// TASK CARD COMPONENT
// ============================================================================

function TaskCard({
  task,
  onEdit,
  onComplete,
  onSnooze,
  isDragging = false,
}: {
  task: Task
  onEdit: () => void
  onComplete: () => void
  onSnooze: () => void
  isDragging?: boolean
}) {
  const today = new Date().toISOString().split('T')[0]
  const isOverdue = task.due_date && task.due_date < today && task.status !== 'completed'

  return (
    <div
      className={cn(
        "bg-white border rounded-lg p-3 cursor-pointer hover:shadow-md transition-all group",
        isDragging && "shadow-lg ring-2 ring-blue-400 rotate-2",
        isOverdue && "border-red-300 bg-red-50/30"
      )}
      onClick={onEdit}
    >
      <div className="flex items-start gap-2">
        <GripVertical className="h-4 w-4 text-slate-300 mt-0.5 shrink-0 cursor-grab opacity-0 group-hover:opacity-100 transition-opacity" />
        <div className="flex-1 min-w-0">
          <p className={cn("font-medium line-clamp-2 text-sm text-slate-800")}>
            {task.title}
          </p>

          {/* Badges row */}
          <div className="flex flex-wrap items-center gap-1.5 mt-2">
            <Badge
              variant="outline"
              className={cn("text-[10px] px-1.5 py-0 font-medium", priorityColors[task.priority])}
            >
              {task.priority}
            </Badge>
            {task.category && task.category !== 'Other' && (
              <Badge variant="outline" className="text-[10px] px-1.5 py-0 bg-slate-50">
                {task.category}
              </Badge>
            )}
          </div>

          {/* Meta info */}
          <div className="flex items-center gap-3 mt-2 text-xs text-slate-500">
            {task.project_code && (
              <span className="font-medium text-teal-600 truncate max-w-[120px]">
                {task.project_code}
              </span>
            )}
            {task.due_date && (
              <span className={cn(
                "flex items-center gap-1",
                isOverdue && "text-red-600 font-semibold"
              )}>
                <Calendar className="h-3 w-3" />
                {new Date(task.due_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
              </span>
            )}
            {task.assignee && task.assignee !== 'us' && (
              <span className="flex items-center gap-1">
                <User className="h-3 w-3" />
                {task.assignee}
              </span>
            )}
          </div>

          {/* Quick actions */}
          {task.status !== 'completed' && task.status !== 'cancelled' && (
            <div className="flex items-center gap-1 mt-3 pt-2 border-t opacity-0 group-hover:opacity-100 transition-opacity">
              <Button
                variant="ghost"
                size="sm"
                onClick={(e) => { e.stopPropagation(); onComplete(); }}
                className="h-7 px-2 text-xs text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50"
              >
                <CheckSquare className="h-3.5 w-3.5 mr-1" />
                Done
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={(e) => { e.stopPropagation(); onSnooze(); }}
                className="h-7 px-2 text-xs text-amber-600 hover:text-amber-700 hover:bg-amber-50"
              >
                <Bell className="h-3.5 w-3.5 mr-1" />
                +7d
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// Sortable wrapper for drag and drop
function SortableTaskCard({
  task,
  onEdit,
  onComplete,
  onSnooze,
}: {
  task: Task
  onEdit: () => void
  onComplete: () => void
  onSnooze: () => void
}) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: task.task_id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  }

  return (
    <div ref={setNodeRef} style={style} {...attributes} {...listeners}>
      <TaskCard
        task={task}
        onEdit={onEdit}
        onComplete={onComplete}
        onSnooze={onSnooze}
        isDragging={isDragging}
      />
    </div>
  )
}

// ============================================================================
// KANBAN COLUMN
// ============================================================================

function KanbanColumn({
  column,
  tasks,
  onEditTask,
  onCompleteTask,
  onSnoozeTask,
}: {
  column: typeof COLUMNS[0]
  tasks: Task[]
  onEditTask: (task: Task) => void
  onCompleteTask: (taskId: number) => void
  onSnoozeTask: (task: Task) => void
}) {
  const Icon = column.icon
  const colorClasses = {
    slate: { bg: 'bg-slate-50', border: 'border-slate-200', text: 'text-slate-600', header: 'text-slate-700' },
    blue: { bg: 'bg-blue-50', border: 'border-blue-200', text: 'text-blue-600', header: 'text-blue-700' },
    emerald: { bg: 'bg-emerald-50', border: 'border-emerald-200', text: 'text-emerald-600', header: 'text-emerald-700' },
  }
  const colors = colorClasses[column.color as keyof typeof colorClasses]

  return (
    <div className={cn("flex-1 min-w-[300px] max-w-[380px] rounded-xl border-2 p-4", colors.bg, colors.border)}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Icon className={cn("h-5 w-5", colors.text)} />
          <h3 className={cn("font-semibold", colors.header)}>
            {column.title}
          </h3>
        </div>
        <Badge variant="secondary" className="text-xs font-medium">
          {tasks.length}
        </Badge>
      </div>

      <SortableContext
        items={tasks.map(t => t.task_id)}
        strategy={verticalListSortingStrategy}
      >
        <div className="space-y-3 min-h-[400px]">
          {tasks.map(task => (
            <SortableTaskCard
              key={task.task_id}
              task={task}
              onEdit={() => onEditTask(task)}
              onComplete={() => onCompleteTask(task.task_id)}
              onSnooze={() => onSnoozeTask(task)}
            />
          ))}
          {tasks.length === 0 && (
            <div className="flex flex-col items-center justify-center py-12 text-slate-400">
              <CheckSquare className="h-8 w-8 mb-2 opacity-50" />
              <p className="text-sm">No tasks</p>
            </div>
          )}
        </div>
      </SortableContext>
    </div>
  )
}

// ============================================================================
// LIST VIEW ROW
// ============================================================================

function TaskListRow({
  task,
  onEdit,
  onComplete,
  onSnooze,
}: {
  task: Task
  onEdit: () => void
  onComplete: () => void
  onSnooze: () => void
}) {
  const today = new Date().toISOString().split('T')[0]
  const isOverdue = task.due_date && task.due_date < today && task.status !== 'completed'

  const statusIcons = {
    pending: Circle,
    in_progress: PlayCircle,
    completed: CheckCircle2,
    cancelled: XCircle,
  }
  const StatusIcon = statusIcons[task.status as keyof typeof statusIcons] || Circle

  return (
    <div
      className={cn(
        "flex items-center gap-4 px-4 py-3 border-b hover:bg-slate-50 cursor-pointer transition-colors group",
        isOverdue && "bg-red-50/50 hover:bg-red-50"
      )}
      onClick={onEdit}
    >
      {/* Status icon */}
      <StatusIcon className={cn(
        "h-5 w-5 shrink-0",
        task.status === 'pending' && "text-slate-400",
        task.status === 'in_progress' && "text-blue-500",
        task.status === 'completed' && "text-emerald-500",
        task.status === 'cancelled' && "text-slate-300",
      )} />

      {/* Title and description */}
      <div className="flex-1 min-w-0">
        <p className={cn(
          "font-medium text-sm text-slate-800 truncate",
          task.status === 'completed' && "line-through text-slate-500"
        )}>
          {task.title}
        </p>
        {task.project_code && (
          <p className="text-xs text-teal-600 mt-0.5">{task.project_code}</p>
        )}
      </div>

      {/* Priority badge */}
      <Badge
        variant="outline"
        className={cn("text-[10px] px-2 py-0.5 font-medium shrink-0", priorityColors[task.priority])}
      >
        {task.priority}
      </Badge>

      {/* Due date */}
      <div className={cn(
        "text-xs shrink-0 w-24 text-right",
        isOverdue ? "text-red-600 font-semibold" : "text-slate-500"
      )}>
        {task.due_date ? (
          <span className="flex items-center justify-end gap-1">
            <Calendar className="h-3 w-3" />
            {new Date(task.due_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
          </span>
        ) : (
          <span className="text-slate-300">No date</span>
        )}
      </div>

      {/* Assignee */}
      <div className="text-xs text-slate-500 shrink-0 w-24 truncate">
        {task.assignee && task.assignee !== 'us' ? task.assignee : '—'}
      </div>

      {/* Actions */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
          >
            <MoreHorizontal className="h-4 w-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          {task.status !== 'completed' && (
            <DropdownMenuItem onClick={(e) => { e.stopPropagation(); onComplete(); }}>
              <CheckCircle2 className="h-4 w-4 mr-2 text-emerald-600" />
              Mark Complete
            </DropdownMenuItem>
          )}
          {task.status !== 'completed' && (
            <DropdownMenuItem onClick={(e) => { e.stopPropagation(); onSnooze(); }}>
              <Bell className="h-4 w-4 mr-2 text-amber-600" />
              Snooze 7 days
            </DropdownMenuItem>
          )}
          <DropdownMenuItem onClick={(e) => { e.stopPropagation(); onEdit(); }}>
            <SlidersHorizontal className="h-4 w-4 mr-2" />
            Edit Task
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  )
}

// ============================================================================
// MAIN PAGE COMPONENT
// ============================================================================

function TasksPageContent() {
  const queryClient = useQueryClient()
  const searchParams = useSearchParams()

  // State
  const [viewMode, setViewMode] = useState<ViewMode>('kanban')
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>(searchParams.get('filter') === 'overdue' ? 'overdue' : 'all')
  const [priorityFilter, setPriorityFilter] = useState<string>('all')
  const [activeTask, setActiveTask] = useState<Task | null>(null)
  const [selectedTask, setSelectedTask] = useState<Task | null>(null)
  const [modalOpen, setModalOpen] = useState(false)
  const [modalMode, setModalMode] = useState<'create' | 'edit'>('create')

  // Sensors for drag detection
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 8 },
    })
  )

  // Fetch tasks
  const { data: tasksData, isLoading: tasksLoading } = useQuery({
    queryKey: ['tasks'],
    queryFn: () => api.getTasks({ limit: 500 }),
  })

  // Fetch stats
  const { data: statsData } = useQuery({
    queryKey: ['tasks', 'stats'],
    queryFn: async () => {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'}/api/tasks/stats`)
      return res.json() as Promise<TaskStats>
    },
  })

  const tasks = tasksData?.tasks || []
  const stats = statsData

  // Filter tasks
  const filteredTasks = useMemo(() => {
    let result = [...tasks]
    const today = new Date().toISOString().split('T')[0]

    // Apply search
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      result = result.filter(t =>
        t.title.toLowerCase().includes(query) ||
        t.project_code?.toLowerCase().includes(query) ||
        t.description?.toLowerCase().includes(query)
      )
    }

    // Apply status filter
    if (statusFilter === 'overdue') {
      result = result.filter(t =>
        t.due_date && t.due_date < today && t.status !== 'completed' && t.status !== 'cancelled'
      )
    } else if (statusFilter !== 'all') {
      result = result.filter(t => t.status === statusFilter)
    }

    // Apply priority filter
    if (priorityFilter !== 'all') {
      result = result.filter(t => t.priority === priorityFilter)
    }

    // Exclude cancelled and completed for Kanban view (unless specifically filtered)
    if (viewMode === 'kanban' && statusFilter === 'all') {
      result = result.filter(t => t.status !== 'cancelled')
    }

    return result
  }, [tasks, searchQuery, statusFilter, priorityFilter, viewMode])

  // Get tasks for each Kanban column
  const getTasksForColumn = (status: TaskStatus) => {
    return filteredTasks.filter(t => t.status === status)
  }

  // Mutations
  const updateTaskStatus = useMutation({
    mutationFn: ({ taskId, status }: { taskId: number; status: string }) =>
      api.updateTask(taskId, { status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
    },
    onError: () => {
      toast.error('Failed to update task status')
    },
  })

  const completeTask = useMutation({
    mutationFn: (taskId: number) => api.completeTask(taskId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
      toast.success('Task completed!')
    },
    onError: () => {
      toast.error('Failed to complete task')
    },
  })

  const snoozeTask = useMutation({
    mutationFn: ({ taskId, newDueDate }: { taskId: number; newDueDate: string }) =>
      api.snoozeTask(taskId, newDueDate),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
      toast.success('Task snoozed by 7 days')
    },
    onError: () => {
      toast.error('Failed to snooze task')
    },
  })

  // Handlers
  const handleSnooze = (task: Task) => {
    const currentDue = task.due_date ? new Date(task.due_date) : new Date()
    currentDue.setDate(currentDue.getDate() + 7)
    const newDueDate = currentDue.toISOString().split('T')[0]
    snoozeTask.mutate({ taskId: task.task_id, newDueDate })
  }

  const handleDragStart = (event: DragStartEvent) => {
    const task = tasks.find(t => t.task_id === event.active.id)
    if (task) setActiveTask(task)
  }

  const handleDragEnd = (event: DragEndEvent) => {
    setActiveTask(null)
    const { active, over } = event
    if (!over) return

    const taskId = active.id as number
    const task = tasks.find(t => t.task_id === taskId)
    if (!task) return

    let targetColumn: typeof COLUMNS[0] | undefined
    const overTask = tasks.find(t => t.task_id === over.id)

    if (overTask) {
      targetColumn = COLUMNS.find(col => col.status === overTask.status)
    } else {
      targetColumn = COLUMNS.find(col => col.id === over.id)
    }

    if (!targetColumn) return

    if (task.status !== targetColumn.status) {
      updateTaskStatus.mutate({ taskId, status: targetColumn.status })
      toast.success(`Moved to ${targetColumn.title}`)
    }
  }

  const handleOpenCreate = () => {
    setSelectedTask(null)
    setModalMode('create')
    setModalOpen(true)
  }

  const handleOpenEdit = (task: Task) => {
    setSelectedTask(task)
    setModalMode('edit')
    setModalOpen(true)
  }

  // Loading state
  if (tasksLoading) {
    return (
      <div className="space-y-6 p-6">
        <div className="flex items-center justify-between">
          <Skeleton className="h-10 w-48" />
          <Skeleton className="h-10 w-32" />
        </div>
        <div className="grid grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
        <div className="flex gap-4">
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-[500px] flex-1" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className={cn(ds.typography.heading1, "text-slate-900")}>Tasks</h1>
          <p className="text-slate-500 mt-1">Manage and track all your tasks</p>
        </div>
        <Button onClick={handleOpenCreate} className="gap-2">
          <Plus className="h-4 w-4" />
          New Task
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card
          className={cn(
            "cursor-pointer transition-all hover:shadow-md",
            statusFilter === 'overdue' && "ring-2 ring-red-500"
          )}
          onClick={() => setStatusFilter(statusFilter === 'overdue' ? 'all' : 'overdue')}
        >
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-red-100">
                <AlertTriangle className="h-5 w-5 text-red-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-red-600">{stats?.overdue || 0}</p>
                <p className="text-xs text-slate-500">Overdue</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card
          className={cn(
            "cursor-pointer transition-all hover:shadow-md",
            statusFilter === 'pending' && "ring-2 ring-slate-500"
          )}
          onClick={() => setStatusFilter(statusFilter === 'pending' ? 'all' : 'pending')}
        >
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-slate-100">
                <Circle className="h-5 w-5 text-slate-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-slate-700">{stats?.pending || 0}</p>
                <p className="text-xs text-slate-500">To Do</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card
          className={cn(
            "cursor-pointer transition-all hover:shadow-md",
            statusFilter === 'in_progress' && "ring-2 ring-blue-500"
          )}
          onClick={() => setStatusFilter(statusFilter === 'in_progress' ? 'all' : 'in_progress')}
        >
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-100">
                <PlayCircle className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-blue-600">{stats?.in_progress || 0}</p>
                <p className="text-xs text-slate-500">In Progress</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card
          className={cn(
            "cursor-pointer transition-all hover:shadow-md",
            statusFilter === 'completed' && "ring-2 ring-emerald-500"
          )}
          onClick={() => setStatusFilter(statusFilter === 'completed' ? 'all' : 'completed')}
        >
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-emerald-100">
                <CheckCircle2 className="h-5 w-5 text-emerald-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-emerald-600">{stats?.completed || 0}</p>
                <p className="text-xs text-slate-500">Completed</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-3 bg-white p-4 rounded-xl border shadow-sm">
        {/* Search */}
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <Input
            placeholder="Search tasks..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>

        {/* Status Filter */}
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[140px]">
            <Filter className="h-4 w-4 mr-2 text-slate-400" />
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="overdue">Overdue</SelectItem>
            <SelectItem value="pending">To Do</SelectItem>
            <SelectItem value="in_progress">In Progress</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
          </SelectContent>
        </Select>

        {/* Priority Filter */}
        <Select value={priorityFilter} onValueChange={setPriorityFilter}>
          <SelectTrigger className="w-[140px]">
            <ArrowUpDown className="h-4 w-4 mr-2 text-slate-400" />
            <SelectValue placeholder="Priority" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Priority</SelectItem>
            {PRIORITIES.map(p => (
              <SelectItem key={p.value} value={p.value}>{p.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <div className="flex-1" />

        {/* View Toggle */}
        <div className="flex items-center border rounded-lg p-1 bg-slate-50">
          <Button
            variant={viewMode === 'kanban' ? 'default' : 'ghost'}
            size="sm"
            onClick={() => setViewMode('kanban')}
            className="gap-2"
          >
            <Kanban className="h-4 w-4" />
            Kanban
          </Button>
          <Button
            variant={viewMode === 'list' ? 'default' : 'ghost'}
            size="sm"
            onClick={() => setViewMode('list')}
            className="gap-2"
          >
            <ListTodo className="h-4 w-4" />
            List
          </Button>
        </div>
      </div>

      {/* Active filter indicator */}
      {statusFilter !== 'all' && (
        <div className="flex items-center gap-2">
          <span className="text-sm text-slate-500">Showing:</span>
          <Badge variant="secondary" className="gap-1">
            {statusFilter === 'overdue' ? 'Overdue tasks' : statusFilter.replace('_', ' ')} ({filteredTasks.length})
            <button
              onClick={() => setStatusFilter('all')}
              className="ml-1 hover:text-red-500"
            >
              ×
            </button>
          </Badge>
        </div>
      )}

      {/* Content */}
      {viewMode === 'kanban' ? (
        <DndContext
          sensors={sensors}
          collisionDetection={closestCorners}
          onDragStart={handleDragStart}
          onDragEnd={handleDragEnd}
        >
          <div className="flex gap-6 overflow-x-auto pb-4">
            {COLUMNS.map(column => (
              <KanbanColumn
                key={column.id}
                column={column}
                tasks={getTasksForColumn(column.status)}
                onEditTask={handleOpenEdit}
                onCompleteTask={(id) => completeTask.mutate(id)}
                onSnoozeTask={handleSnooze}
              />
            ))}
          </div>

          <DragOverlay>
            {activeTask ? (
              <TaskCard
                task={activeTask}
                onEdit={() => {}}
                onComplete={() => {}}
                onSnooze={() => {}}
                isDragging
              />
            ) : null}
          </DragOverlay>
        </DndContext>
      ) : (
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-medium">
                {filteredTasks.length} {filteredTasks.length === 1 ? 'task' : 'tasks'}
              </CardTitle>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {/* List header */}
            <div className="flex items-center gap-4 px-4 py-2 border-b bg-slate-50 text-xs font-medium text-slate-500">
              <div className="w-5"></div>
              <div className="flex-1">Task</div>
              <div className="w-20 text-center">Priority</div>
              <div className="w-24 text-right">Due Date</div>
              <div className="w-24">Assignee</div>
              <div className="w-8"></div>
            </div>

            {/* List rows */}
            <div className="divide-y">
              {filteredTasks.map(task => (
                <TaskListRow
                  key={task.task_id}
                  task={task}
                  onEdit={() => handleOpenEdit(task)}
                  onComplete={() => completeTask.mutate(task.task_id)}
                  onSnooze={() => handleSnooze(task)}
                />
              ))}
              {filteredTasks.length === 0 && (
                <div className="flex flex-col items-center justify-center py-16 text-slate-400">
                  <CheckSquare className="h-12 w-12 mb-3 opacity-50" />
                  <p className="text-lg font-medium">No tasks found</p>
                  <p className="text-sm mt-1">Try adjusting your filters or create a new task</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Task Edit Modal */}
      <TaskEditModal
        open={modalOpen}
        onOpenChange={setModalOpen}
        task={selectedTask as Parameters<typeof TaskEditModal>[0]['task']}
        mode={modalMode}
      />
    </div>
  )
}

// Page loading skeleton
function TasksPageSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-10 w-32" />
      </div>
      <div className="grid grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <Skeleton key={i} className="h-24" />
        ))}
      </div>
      <div className="flex gap-4">
        {[...Array(3)].map((_, i) => (
          <Skeleton key={i} className="h-[500px] flex-1" />
        ))}
      </div>
    </div>
  )
}

// Export with Suspense boundary for useSearchParams
export default function TasksPage() {
  return (
    <Suspense fallback={<TasksPageSkeleton />}>
      <TasksPageContent />
    </Suspense>
  )
}
