'use client'

import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Gantt } from 'wx-react-gantt'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { CalendarDays, AlertCircle } from 'lucide-react'
import { api } from '@/lib/api'

interface GanttTask {
  id: number
  text: string
  start: Date
  end: Date
  duration: number
  progress: number
  parent: number
  type: 'project' | 'task' | 'summary' | 'milestone'
  open?: boolean
}

// Phase order for visual display
const PHASE_ORDER: Record<string, number> = {
  'Mobilization': 1,
  'Concept': 2,
  'SD': 3,
  'DD': 4,
  'CD': 5,
  'CA': 6,
}

export function ProjectsTimeline() {
  // Fetch active projects
  const projectsQuery = useQuery({
    queryKey: ['active-projects-timeline'],
    queryFn: () => api.getActiveProjects(),
    staleTime: 1000 * 60 * 5,
  })

  // Transform projects into Gantt format
  const { tasks, scales } = useMemo(() => {
    const projects = projectsQuery.data?.projects || []
    const ganttTasks: GanttTask[] = []
    let taskId = 1

    // Default scales - show months and weeks
    const defaultScales = [
      { unit: 'month' as const, step: 1, format: 'MMMM yyyy' },
      { unit: 'week' as const, step: 1, format: 'w' },
    ]

    projects.forEach((project) => {
      const projectId = taskId++

      // Project start and end dates
      const startDate = project.contract_signed_date
        ? new Date(project.contract_signed_date)
        : project.first_contact_date
          ? new Date(project.first_contact_date)
          : new Date()

      // Default to 6 months if no end date
      const endDate = project.target_completion_date
        ? new Date(project.target_completion_date)
        : new Date(startDate.getTime() + 180 * 24 * 60 * 60 * 1000)

      // Calculate progress based on current phase
      const currentPhaseOrder = project.current_phase
        ? PHASE_ORDER[project.current_phase] || 0
        : 0
      const progressPercent = Math.min(100, Math.round((currentPhaseOrder / 6) * 100))

      // Add project as summary task
      ganttTasks.push({
        id: projectId,
        text: `${project.project_code} - ${project.project_name?.substring(0, 30) || 'Unnamed'}`,
        start: startDate,
        end: endDate,
        duration: Math.ceil((endDate.getTime() - startDate.getTime()) / (24 * 60 * 60 * 1000)),
        progress: progressPercent,
        parent: 0,
        type: 'summary',
        open: true,
      })

      // Add current phase as a task bar
      if (project.current_phase) {
        const phaseId = taskId++
        const phaseStart = new Date(startDate)
        const phaseEnd = new Date()

        ganttTasks.push({
          id: phaseId,
          text: project.current_phase,
          start: phaseStart,
          end: phaseEnd,
          duration: Math.max(1, Math.ceil((phaseEnd.getTime() - phaseStart.getTime()) / (24 * 60 * 60 * 1000))),
          progress: 50,
          parent: projectId,
          type: 'task',
        })
      }
    })

    return { tasks: ganttTasks, scales: defaultScales }
  }, [projectsQuery.data])

  if (projectsQuery.isLoading) {
    return (
      <Card className="border-slate-200">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CalendarDays className="h-5 w-5 text-slate-600" />
            Project Timeline
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[400px] w-full" />
        </CardContent>
      </Card>
    )
  }

  if (projectsQuery.isError) {
    return (
      <Card className="border-red-200 bg-red-50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-red-700">
            <AlertCircle className="h-5 w-5" />
            Failed to load timeline
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-red-600">
            Could not load project data for timeline view.
          </p>
        </CardContent>
      </Card>
    )
  }

  if (tasks.length === 0) {
    return (
      <Card className="border-slate-200">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CalendarDays className="h-5 w-5 text-slate-600" />
            Project Timeline
          </CardTitle>
        </CardHeader>
        <CardContent className="py-12 text-center">
          <CalendarDays className="mx-auto h-16 w-16 text-slate-300 mb-4" />
          <p className="text-lg font-medium text-slate-700 mb-2">
            No active projects
          </p>
          <p className="text-sm text-slate-500">
            Active projects will appear here on the timeline.
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="border-slate-200">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CalendarDays className="h-5 w-5 text-slate-600" />
          Project Timeline ({tasks.filter(t => t.parent === 0).length} projects)
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[500px] w-full">
          <Gantt
            tasks={tasks}
            scales={scales}
            cellWidth={40}
            cellHeight={38}
          />
        </div>
      </CardContent>
    </Card>
  )
}
