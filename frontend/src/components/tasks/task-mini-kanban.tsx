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
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  CheckSquare,
  Plus,
  Calendar,
  ChevronRight,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { api } from '@/lib/api'
import { toast } from 'sonner'
import { TaskEditModal } from '@/components/tasks/task-edit-modal'
import Link from 'next/link'

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
  assignee?: string | null
  assigned_to?: string | null
  created_at: string
  completed_at: string | null
  category?: string | null
  source_suggestion_id?: number | null
  source_email_id?: number | null
  source_transcript_id?: number | null
  source_meeting_id?: number | null
}

interface TaskMiniKanbanProps {
  projectCode: string
  title?: string
}

type TaskStatus = 'pending' | 'in_progress' | 'completed'

const COLUMNS: { id: string; title: string; status: TaskStatus; color: string }[] = [
  { id: 'pending', title: 'To Do', status: 'pending', color: 'slate' },
  { id: 'in_progress', title: 'In Progress', status: 'in_progress', color: 'blue' },
  { id: 'completed', title: 'Done', status: 'completed', color: 'emerald' },
]

const priorityColors: Record<string, string> = {
  low: 'bg-slate-100 text-slate-600',
  medium: 'bg-blue-100 text-blue-600',
  high: 'bg-amber-100 text-amber-600',
  critical: 'bg-red-100 text-red-600',
}

// Mini task card for embedded Kanban
function MiniTaskCard({
  task,
  onClick,
  isDragging = false,
}: {
  task: Task
  onClick: () => void
  isDragging?: boolean
}) {
  const today = new Date().toISOString().split('T')[0]
  const isOverdue = task.due_date && task.due_date < today && task.status !== 'completed'

  return (
    <div
      className={cn(
        "bg-white border rounded p-2 cursor-pointer hover:shadow-sm transition-shadow text-xs",
        isDragging && "shadow-md ring-1 ring-blue-400",
        isOverdue && "border-red-300 bg-red-50/50"
      )}
      onClick={onClick}
    >
      <p className="font-medium line-clamp-2 text-slate-700">{task.title}</p>
      <div className="flex items-center gap-1 mt-1">
        <Badge className={cn("text-[10px] px-1 py-0", priorityColors[task.priority])}>
          {task.priority}
        </Badge>
        {task.due_date && (
          <span className={cn(
            "text-[10px] flex items-center gap-0.5",
            isOverdue ? "text-red-600" : "text-slate-400"
          )}>
            <Calendar className="h-2.5 w-2.5" />
            {task.due_date.slice(5)}
          </span>
        )}
      </div>
    </div>
  )
}

// Sortable wrapper
function SortableMiniCard({
  task,
  onClick,
}: {
  task: Task
  onClick: () => void
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
      <MiniTaskCard task={task} onClick={onClick} isDragging={isDragging} />
    </div>
  )
}

export function TaskMiniKanban({ projectCode, title = "Tasks" }: TaskMiniKanbanProps) {
  const queryClient = useQueryClient()
  const [activeTask, setActiveTask] = useState<Task | null>(null)
  const [selectedTask, setSelectedTask] = useState<Task | null>(null)
  const [modalOpen, setModalOpen] = useState(false)
  const [modalMode, setModalMode] = useState<'create' | 'edit'>('create')

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } })
  )

  // Fetch tasks for this project
  const { data, isLoading } = useQuery({
    queryKey: ['project-tasks', projectCode],
    queryFn: () => api.getProjectTasks(projectCode, false),
    enabled: !!projectCode,
  })

  const tasks = data?.tasks || []

  // Update task status
  const updateStatus = useMutation({
    mutationFn: async ({ taskId, status }: { taskId: number; status: string }) => {
      const response = await fetch(`http://localhost:8000/api/tasks/${taskId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status }),
      })
      if (!response.ok) throw new Error('Failed to update')
      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['project-tasks', projectCode] })
    },
    onError: () => {
      toast.error('Failed to update task')
    },
  })

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

    // Find target column
    const overTask = tasks.find(t => t.task_id === over.id)
    let targetStatus: TaskStatus | undefined

    if (overTask) {
      targetStatus = overTask.status as TaskStatus
    } else {
      const column = COLUMNS.find(c => c.id === over.id)
      if (column) targetStatus = column.status
    }

    if (targetStatus && task.status !== targetStatus) {
      updateStatus.mutate({ taskId, status: targetStatus })
      toast.success(`Moved to ${COLUMNS.find(c => c.status === targetStatus)?.title}`)
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

  const getTasksForColumn = (status: TaskStatus) =>
    tasks.filter(t => t.status === status)

  if (isLoading) {
    return (
      <Card className="border-amber-200 bg-gradient-to-br from-amber-50/50 to-orange-50/30">
        <CardHeader className="pb-2">
          <CardTitle className="text-base text-amber-800 flex items-center gap-2">
            <CheckSquare className="h-4 w-4" />
            {title}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-32 flex items-center justify-center text-sm text-muted-foreground">
            Loading...
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="border-amber-200 bg-gradient-to-br from-amber-50/50 to-orange-50/30">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center justify-between text-base">
          <div className="flex items-center gap-2 text-amber-800">
            <CheckSquare className="h-4 w-4" />
            <span>{title} ({tasks.length})</span>
          </div>
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleOpenCreate}
              className="text-amber-700 hover:text-amber-900 hover:bg-amber-100 h-7 w-7 p-0"
            >
              <Plus className="h-4 w-4" />
            </Button>
            <Link href="/tasks">
              <Button variant="ghost" size="sm" className="text-xs text-amber-700 hover:text-amber-900">
                View All <ChevronRight className="h-3 w-3 ml-1" />
              </Button>
            </Link>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <DndContext
          sensors={sensors}
          collisionDetection={closestCorners}
          onDragStart={handleDragStart}
          onDragEnd={handleDragEnd}
        >
          <div className="grid grid-cols-3 gap-2">
            {COLUMNS.map(column => {
              const columnTasks = getTasksForColumn(column.status)
              return (
                <div key={column.id} className="min-h-[120px]">
                  <div className={cn(
                    "text-[10px] font-medium mb-1.5 px-1",
                    column.color === 'slate' && "text-slate-500",
                    column.color === 'blue' && "text-blue-600",
                    column.color === 'emerald' && "text-emerald-600"
                  )}>
                    {column.title} ({columnTasks.length})
                  </div>
                  <SortableContext
                    id={column.id}
                    items={columnTasks.map(t => t.task_id)}
                    strategy={verticalListSortingStrategy}
                  >
                    <div className={cn(
                      "space-y-1.5 p-1.5 rounded min-h-[100px]",
                      column.color === 'slate' && "bg-slate-50",
                      column.color === 'blue' && "bg-blue-50",
                      column.color === 'emerald' && "bg-emerald-50"
                    )}>
                      {columnTasks.slice(0, 4).map(task => (
                        <SortableMiniCard
                          key={task.task_id}
                          task={task}
                          onClick={() => handleOpenEdit(task)}
                        />
                      ))}
                      {columnTasks.length > 4 && (
                        <p className="text-[10px] text-center text-muted-foreground">
                          +{columnTasks.length - 4} more
                        </p>
                      )}
                      {columnTasks.length === 0 && (
                        <p className="text-[10px] text-center text-muted-foreground py-4">
                          No tasks
                        </p>
                      )}
                    </div>
                  </SortableContext>
                </div>
              )
            })}
          </div>

          <DragOverlay>
            {activeTask ? (
              <MiniTaskCard task={activeTask} onClick={() => {}} isDragging />
            ) : null}
          </DragOverlay>
        </DndContext>
      </CardContent>

      <TaskEditModal
        open={modalOpen}
        onOpenChange={setModalOpen}
        task={selectedTask as Parameters<typeof TaskEditModal>[0]['task']}
        defaultProjectCode={projectCode}
        mode={modalMode}
      />
    </Card>
  )
}
