'use client'

import { useState } from 'react'
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
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  CheckSquare,
  Bell,
  Calendar,
  GripVertical,
  User,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { ds } from '@/lib/design-system'
import { api } from '@/lib/api'
import { toast } from 'sonner'

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

interface TaskKanbanBoardProps {
  tasks: Task[]
  categoryFilter: string | null
  onEditTask: (task: Task) => void
}

// Column configuration
type TaskStatus = 'pending' | 'in_progress' | 'completed'
type ColumnColor = 'slate' | 'blue' | 'emerald'

interface Column {
  id: string
  title: string
  statuses: TaskStatus[]
  color: ColumnColor
}

const COLUMNS: Column[] = [
  { id: 'pending', title: 'To Do', statuses: ['pending'], color: 'slate' },
  { id: 'in_progress', title: 'In Progress', statuses: ['in_progress'], color: 'blue' },
  { id: 'completed', title: 'Done', statuses: ['completed'], color: 'emerald' },
]

// Priority colors
const priorityColors: Record<string, string> = {
  low: 'bg-slate-100 text-slate-700 border-slate-200',
  medium: 'bg-blue-100 text-blue-700 border-blue-200',
  high: 'bg-amber-100 text-amber-700 border-amber-200',
  critical: 'bg-red-100 text-red-700 border-red-200',
}

// Category colors
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

// Draggable Task Card
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
        "bg-white border rounded-lg p-3 cursor-pointer hover:shadow-md transition-shadow",
        isDragging && "shadow-lg ring-2 ring-blue-400",
        isOverdue && "border-red-300 bg-red-50/30"
      )}
      onClick={onEdit}
    >
      <div className="flex items-start gap-2">
        <GripVertical className="h-4 w-4 text-slate-300 mt-0.5 shrink-0 cursor-grab" />
        <div className="flex-1 min-w-0">
          <p className={cn(ds.typography.bodyBold, ds.textColors.primary, "line-clamp-2 text-sm")}>
            {task.title}
          </p>

          {/* Badges row */}
          <div className="flex flex-wrap items-center gap-1 mt-2">
            <Badge
              variant="outline"
              className={cn("text-[10px] px-1.5 py-0", priorityColors[task.priority])}
            >
              {task.priority}
            </Badge>
            {task.category && task.category !== 'Other' && (
              <Badge
                variant="outline"
                className={cn("text-[10px] px-1.5 py-0", categoryColors[task.category])}
              >
                {task.category}
              </Badge>
            )}
          </div>

          {/* Meta info */}
          <div className="flex items-center gap-2 mt-2 text-xs text-slate-500">
            {task.project_code && (
              <span className="font-medium text-teal-600 truncate max-w-[100px]">
                {task.project_code}
              </span>
            )}
            {task.due_date && (
              <span className={cn(
                "flex items-center gap-1",
                isOverdue && "text-red-600 font-medium"
              )}>
                <Calendar className="h-3 w-3" />
                {task.due_date}
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
            <div className="flex items-center gap-1 mt-2 pt-2 border-t">
              <Button
                variant="ghost"
                size="sm"
                onClick={(e) => { e.stopPropagation(); onComplete(); }}
                className="h-6 px-2 text-xs text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50"
              >
                <CheckSquare className="h-3 w-3 mr-1" />
                Done
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={(e) => { e.stopPropagation(); onSnooze(); }}
                className="h-6 px-2 text-xs text-amber-600 hover:text-amber-700 hover:bg-amber-50"
              >
                <Bell className="h-3 w-3 mr-1" />
                +7d
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// Sortable wrapper for task card
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

// Kanban column
function KanbanColumn({
  column,
  tasks,
  onEditTask,
  onCompleteTask,
  onSnoozeTask,
}: {
  column: Column
  tasks: Task[]
  onEditTask: (task: Task) => void
  onCompleteTask: (taskId: number) => void
  onSnoozeTask: (task: Task) => void
}) {
  const columnColors = {
    slate: 'bg-slate-50 border-slate-200',
    blue: 'bg-blue-50 border-blue-200',
    emerald: 'bg-emerald-50 border-emerald-200',
  }

  const headerColors = {
    slate: 'text-slate-700',
    blue: 'text-blue-700',
    emerald: 'text-emerald-700',
  }

  return (
    <div className={cn("flex-1 min-w-[280px] max-w-[350px] rounded-lg border p-3", columnColors[column.color])}>
      <div className="flex items-center justify-between mb-3">
        <h3 className={cn(ds.typography.heading3, headerColors[column.color])}>
          {column.title}
        </h3>
        <Badge variant="secondary" className="text-xs">
          {tasks.length}
        </Badge>
      </div>

      <SortableContext
        items={tasks.map(t => t.task_id)}
        strategy={verticalListSortingStrategy}
      >
        <div className="space-y-2 min-h-[200px]">
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
            <div className="text-center py-8 text-slate-400 text-sm">
              No tasks
            </div>
          )}
        </div>
      </SortableContext>
    </div>
  )
}

export function TaskKanbanBoard({ tasks, categoryFilter, onEditTask }: TaskKanbanBoardProps) {
  const queryClient = useQueryClient()
  const [activeTask, setActiveTask] = useState<Task | null>(null)

  // Sensors for drag detection
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8, // 8px movement before drag starts
      },
    })
  )

  // Update task status mutation
  const updateTaskStatus = useMutation({
    mutationFn: async ({ taskId, status }: { taskId: number; status: string }) => {
      const response = await fetch(`http://localhost:8000/api/tasks/${taskId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status }),
      })
      if (!response.ok) throw new Error('Failed to update task')
      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
    },
    onError: () => {
      toast.error('Failed to update task status')
    },
  })

  // Complete task mutation
  const completeTask = useMutation({
    mutationFn: (taskId: number) => api.completeTask(taskId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
      toast.success('Task completed')
    },
    onError: () => {
      toast.error('Failed to complete task')
    },
  })

  // Snooze task mutation
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

  // Handle snooze
  const handleSnooze = (task: Task) => {
    const currentDue = task.due_date ? new Date(task.due_date) : new Date()
    currentDue.setDate(currentDue.getDate() + 7)
    const newDueDate = currentDue.toISOString().split('T')[0]
    snoozeTask.mutate({ taskId: task.task_id, newDueDate })
  }

  // Filter tasks by category
  const filteredTasks = categoryFilter
    ? tasks.filter(t => (t.category || 'Other') === categoryFilter)
    : tasks

  // Group tasks by column
  const getTasksForColumn = (column: Column) => {
    return filteredTasks.filter(task => column.statuses.includes(task.status as TaskStatus))
  }

  // Handle drag start
  const handleDragStart = (event: DragStartEvent) => {
    const task = filteredTasks.find(t => t.task_id === event.active.id)
    if (task) setActiveTask(task)
  }

  // Handle drag end
  const handleDragEnd = (event: DragEndEvent) => {
    setActiveTask(null)

    const { active, over } = event
    if (!over) return

    const taskId = active.id as number
    const task = filteredTasks.find(t => t.task_id === taskId)
    if (!task) return

    // Find which column the task was dropped on
    // The 'over' could be another task or the column itself
    let targetColumn: Column | undefined

    // Check if dropped on a task
    const overTask = filteredTasks.find(t => t.task_id === over.id)
    if (overTask) {
      // Find which column contains this task
      targetColumn = COLUMNS.find(col => col.statuses.includes(overTask.status as TaskStatus))
    }

    // If still no target, check if dropped directly on column
    if (!targetColumn) {
      // Check if 'over.id' matches a column id
      targetColumn = COLUMNS.find(col => col.id === over.id)
    }

    if (!targetColumn) return

    // Get the new status from the target column
    const newStatus = targetColumn.statuses[0]
    if (task.status !== newStatus) {
      updateTaskStatus.mutate({ taskId, status: newStatus })
      toast.success(`Task moved to ${targetColumn.title}`)
    }
  }

  return (
    <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
      <CardHeader className="pb-3">
        <CardTitle className={ds.typography.heading3}>Task Board</CardTitle>
      </CardHeader>
      <CardContent>
        <DndContext
          sensors={sensors}
          collisionDetection={closestCorners}
          onDragStart={handleDragStart}
          onDragEnd={handleDragEnd}
        >
          <div className="flex gap-4 overflow-x-auto pb-4">
            {COLUMNS.map(column => (
              <KanbanColumn
                key={column.id}
                column={column}
                tasks={getTasksForColumn(column)}
                onEditTask={onEditTask}
                onCompleteTask={(id) => completeTask.mutate(id)}
                onSnoozeTask={handleSnooze}
              />
            ))}
          </div>

          {/* Drag overlay for smooth dragging */}
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
      </CardContent>
    </Card>
  )
}
