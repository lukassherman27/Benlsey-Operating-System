'use client'

import { useMemo, useState } from 'react'
import { Gantt, Task, ViewMode } from 'gantt-task-react'
import 'gantt-task-react/dist/index.css'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { CalendarDays, ZoomIn, ZoomOut, AlertCircle, Calendar } from 'lucide-react'
import { cn } from '@/lib/utils'

// Phase colors matching the design system
const PHASE_COLORS: Record<string, { bg: string; progress: string }> = {
  'Mobilization': { bg: '#94a3b8', progress: '#64748b' },
  'Concept': { bg: '#3b82f6', progress: '#2563eb' },
  'SD': { bg: '#06b6d4', progress: '#0891b2' },
  'DD': { bg: '#14b8a6', progress: '#0d9488' },
  'CD': { bg: '#10b981', progress: '#059669' },
  'CA': { bg: '#22c55e', progress: '#16a34a' },
}

// Status to progress mapping
const STATUS_PROGRESS: Record<string, number> = {
  'pending': 0,
  'in_progress': 50,
  'completed': 100,
}

interface PhaseData {
  phase_id: number
  phase_name: string
  status: string
  discipline?: string
  phase_fee_usd?: number | null
  start_date?: string | null
  expected_completion_date?: string | null
  actual_completion_date?: string | null
  phase_order?: number
}

interface DeliverableData {
  deliverable_id: number
  name: string
  status: string
  start_date?: string | null
  due_date?: string | null
  phase_id?: number | null
}

interface TaskData {
  task_id: number
  title: string
  status: string
  due_date?: string | null
  created_at?: string
}

interface ProjectGanttProps {
  projectCode: string
  projectName: string
  contractStartDate?: string | null
  targetCompletion?: string | null
  phases: PhaseData[]
  deliverables?: DeliverableData[]
  tasks?: TaskData[]
  isLoading?: boolean
}

export function ProjectGantt({
  projectCode,
  projectName,
  contractStartDate,
  targetCompletion,
  phases,
  deliverables = [],
  tasks = [],
  isLoading = false,
}: ProjectGanttProps) {
  const [viewMode, setViewMode] = useState<ViewMode>(ViewMode.Month)

  // Transform data into Gantt tasks
  const ganttTasks = useMemo(() => {
    const result: Task[] = []
    const now = new Date()

    // Default project timeline if no dates
    const projectStart = contractStartDate
      ? new Date(contractStartDate)
      : new Date(now.getTime() - 180 * 24 * 60 * 60 * 1000) // 6 months ago
    const projectEnd = targetCompletion
      ? new Date(targetCompletion)
      : new Date(now.getTime() + 365 * 24 * 60 * 60 * 1000) // 1 year from now

    // Add project as parent
    result.push({
      id: `project-${projectCode}`,
      type: 'project',
      name: projectName.substring(0, 40),
      start: projectStart,
      end: projectEnd,
      progress: calculateOverallProgress(phases),
      hideChildren: false,
      styles: {
        backgroundColor: '#0d9488',
        progressColor: '#0f766e',
      },
    })

    // Calculate phase durations (divide project timeline by number of phases)
    const totalDays = Math.ceil((projectEnd.getTime() - projectStart.getTime()) / (24 * 60 * 60 * 1000))
    const phaseDuration = Math.max(30, Math.floor(totalDays / Math.max(phases.length, 6)))

    // Sort phases by order
    const sortedPhases = [...phases].sort((a, b) => (a.phase_order || 0) - (b.phase_order || 0))

    // Add phases
    sortedPhases.forEach((phase, index) => {
      const phaseStart = phase.start_date
        ? new Date(phase.start_date)
        : new Date(projectStart.getTime() + index * phaseDuration * 24 * 60 * 60 * 1000)

      const phaseEnd = phase.expected_completion_date
        ? new Date(phase.expected_completion_date)
        : phase.actual_completion_date
          ? new Date(phase.actual_completion_date)
          : new Date(phaseStart.getTime() + phaseDuration * 24 * 60 * 60 * 1000)

      // Ensure end is after start
      const finalEnd = phaseEnd > phaseStart ? phaseEnd : new Date(phaseStart.getTime() + 30 * 24 * 60 * 60 * 1000)

      const colors = PHASE_COLORS[phase.phase_name] || { bg: '#6b7280', progress: '#4b5563' }
      const progress = STATUS_PROGRESS[phase.status] || 0

      result.push({
        id: `phase-${phase.phase_id}`,
        type: 'task',
        name: `${phase.phase_name}${phase.discipline ? ` (${phase.discipline})` : ''}`,
        start: phaseStart,
        end: finalEnd,
        progress,
        project: `project-${projectCode}`,
        styles: {
          backgroundColor: colors.bg,
          progressColor: colors.progress,
        },
        // Dependencies: each phase depends on previous
        dependencies: index > 0 ? [`phase-${sortedPhases[index - 1].phase_id}`] : undefined,
      })

      // Add deliverables for this phase
      const phaseDeliverables = deliverables.filter(d => d.phase_id === phase.phase_id)
      phaseDeliverables.forEach(deliverable => {
        const delStart = deliverable.start_date
          ? new Date(deliverable.start_date)
          : phaseStart
        const delEnd = deliverable.due_date
          ? new Date(deliverable.due_date)
          : finalEnd

        result.push({
          id: `deliverable-${deliverable.deliverable_id}`,
          type: 'milestone',
          name: `📦 ${deliverable.name.substring(0, 30)}`,
          start: delEnd, // Milestones use single date
          end: delEnd,
          progress: STATUS_PROGRESS[deliverable.status] || 0,
          project: `phase-${phase.phase_id}`,
          styles: {
            backgroundColor: '#f59e0b',
            progressColor: '#d97706',
          },
        })
      })
    })

    // Add unlinked deliverables as milestones
    const unlinkedDeliverables = deliverables.filter(d => !d.phase_id)
    unlinkedDeliverables.forEach(deliverable => {
      const delDate = deliverable.due_date
        ? new Date(deliverable.due_date)
        : new Date()

      result.push({
        id: `deliverable-${deliverable.deliverable_id}`,
        type: 'milestone',
        name: `📦 ${deliverable.name.substring(0, 30)}`,
        start: delDate,
        end: delDate,
        progress: STATUS_PROGRESS[deliverable.status] || 0,
        project: `project-${projectCode}`,
        styles: {
          backgroundColor: '#f59e0b',
          progressColor: '#d97706',
        },
      })
    })

    // Add tasks with due dates
    const tasksWithDates = tasks.filter(t => t.due_date)
    tasksWithDates.slice(0, 10).forEach(task => { // Limit to 10 tasks to avoid clutter
      const taskEnd = new Date(task.due_date!)
      const taskStart = task.created_at
        ? new Date(task.created_at)
        : new Date(taskEnd.getTime() - 7 * 24 * 60 * 60 * 1000) // 1 week before due

      result.push({
        id: `task-${task.task_id}`,
        type: 'task',
        name: `✓ ${task.title.substring(0, 25)}`,
        start: taskStart,
        end: taskEnd,
        progress: STATUS_PROGRESS[task.status] || 0,
        project: `project-${projectCode}`,
        styles: {
          backgroundColor: '#8b5cf6',
          progressColor: '#7c3aed',
        },
      })
    })

    return result
  }, [projectCode, projectName, contractStartDate, targetCompletion, phases, deliverables, tasks])

  if (isLoading) {
    return (
      <Card className="border-slate-200">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CalendarDays className="h-5 w-5 text-teal-600" />
            Project Timeline
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[300px] w-full" />
        </CardContent>
      </Card>
    )
  }

  // Check if we have any usable data
  const hasPhases = phases.length > 0
  const hasDates = phases.some(p => p.start_date || p.expected_completion_date) ||
                   contractStartDate ||
                   targetCompletion

  if (!hasPhases) {
    return (
      <Card className="border-slate-200">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CalendarDays className="h-5 w-5 text-slate-600" />
            Project Timeline
          </CardTitle>
        </CardHeader>
        <CardContent className="py-12 text-center">
          <Calendar className="mx-auto h-16 w-16 text-slate-300 mb-4" />
          <p className="text-lg font-medium text-slate-700 mb-2">
            No phases defined
          </p>
          <p className="text-sm text-slate-500">
            Add phases to see the project timeline.
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="border-slate-200">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <CalendarDays className="h-5 w-5 text-teal-600" />
            Project Timeline
          </CardTitle>
          <div className="flex items-center gap-2">
            {!hasDates && (
              <Badge variant="outline" className="bg-amber-50 text-amber-700 border-amber-200 gap-1">
                <AlertCircle className="h-3 w-3" />
                Estimated dates
              </Badge>
            )}
            <div className="flex gap-1">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setViewMode(ViewMode.Week)}
                className={cn(viewMode === ViewMode.Week && "bg-slate-100")}
              >
                Week
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setViewMode(ViewMode.Month)}
                className={cn(viewMode === ViewMode.Month && "bg-slate-100")}
              >
                Month
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setViewMode(ViewMode.Year)}
                className={cn(viewMode === ViewMode.Year && "bg-slate-100")}
              >
                Year
              </Button>
            </div>
          </div>
        </div>
        {!hasDates && (
          <p className="text-xs text-amber-600 mt-1">
            Phase dates not set. Showing estimated timeline based on project duration.
          </p>
        )}
      </CardHeader>
      <CardContent>
        <div className="border rounded-lg overflow-hidden bg-white">
          <Gantt
            tasks={ganttTasks}
            viewMode={viewMode}
            listCellWidth=""
            columnWidth={viewMode === ViewMode.Year ? 300 : viewMode === ViewMode.Month ? 150 : 60}
            ganttHeight={Math.max(200, ganttTasks.length * 40)}
            barCornerRadius={4}
            barFill={70}
            fontSize="12px"
            todayColor="rgba(220, 38, 38, 0.15)"
            projectBackgroundColor="#0d9488"
            projectProgressColor="#0f766e"
            barBackgroundColor="#94a3b8"
            barProgressColor="#64748b"
            milestoneBackgroundColor="#f59e0b"
          />
        </div>

        {/* Legend */}
        <div className="mt-4 flex flex-wrap gap-4 text-xs text-slate-600">
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded bg-teal-600" />
            <span>Project</span>
          </div>
          {Object.entries(PHASE_COLORS).slice(0, 4).map(([phase, colors]) => (
            <div key={phase} className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded" style={{ backgroundColor: colors.bg }} />
              <span>{phase}</span>
            </div>
          ))}
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded bg-amber-500" />
            <span>Milestone</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded bg-violet-500" />
            <span>Task</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function calculateOverallProgress(phases: PhaseData[]): number {
  if (phases.length === 0) return 0
  const totalProgress = phases.reduce((sum, phase) => {
    return sum + (STATUS_PROGRESS[phase.status] || 0)
  }, 0)
  return Math.round(totalProgress / phases.length)
}
