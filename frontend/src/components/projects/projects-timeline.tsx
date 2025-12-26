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
    const projects = projectsQuery.data?.data || projectsQuery.data?.projects || []
    const ganttTasks: GanttTask[] = []
    let taskId = 1

    // Default scales - show months and weeks
    const defaultScales = [
      { unit: 'month' as const, step: 1, format: 'MMMM yyyy' },
      { unit: 'week' as const, step: 1, format: 'w' },
    ]

    // Type for project data
    interface ProjectData {
      project_code: string
      project_title?: string
      project_name?: string
      client_name?: string
      contract_signed_date?: string
      first_contact_date?: string
      target_completion_date?: string
      current_phase?: string
      total_fee_usd?: number
      contract_value?: number
    }

    // Sort projects by contract date (newest first)
    const sortedProjects = [...projects].sort((a: ProjectData, b: ProjectData) => {
      const dateA = a.contract_signed_date || a.first_contact_date || '2020-01-01'
      const dateB = b.contract_signed_date || b.first_contact_date || '2020-01-01'
      return dateB.localeCompare(dateA)
    })

    // Limit to 20 projects for performance
    const displayProjects = sortedProjects.slice(0, 20)

    displayProjects.forEach((project: ProjectData) => {
      const projectId = taskId++

      // Project start and end dates
      const startDate = project.contract_signed_date
        ? new Date(project.contract_signed_date)
        : project.first_contact_date
          ? new Date(project.first_contact_date)
          : new Date()

      // Default to 12 months if no end date
      const endDate = project.target_completion_date
        ? new Date(project.target_completion_date)
        : new Date(startDate.getTime() + 365 * 24 * 60 * 60 * 1000)

      // Calculate progress based on current phase
      const currentPhaseOrder = project.current_phase
        ? PHASE_ORDER[project.current_phase] || 0
        : 0
      const progressPercent = Math.min(100, Math.round((currentPhaseOrder / 6) * 100))

      // Project name
      const projectName = project.project_title || project.project_name || project.client_name || 'Unnamed'

      // Add project as summary task
      ganttTasks.push({
        id: projectId,
        text: `${project.project_code} - ${projectName.substring(0, 35)}`,
        start: startDate,
        end: endDate,
        duration: Math.max(1, Math.ceil((endDate.getTime() - startDate.getTime()) / (24 * 60 * 60 * 1000))),
        progress: progressPercent,
        parent: 0,
        type: 'summary',
        open: false, // Collapsed by default for cleaner view
      })

      // Add current phase as a task bar (if phase exists)
      if (project.current_phase) {
        const phaseId = taskId++
        const phaseStart = new Date(startDate)
        const phaseEnd = new Date()

        // Only add phase if it's a reasonable duration
        if (phaseEnd > phaseStart) {
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

  const totalProjects = projectsQuery.data?.data?.length || projectsQuery.data?.projects?.length || 0
  const displayedProjects = tasks.filter(t => t.parent === 0).length

  return (
    <Card className="border-slate-200">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center justify-between">
          <span className="flex items-center gap-2">
            <CalendarDays className="h-5 w-5 text-teal-600" />
            Project Timeline
          </span>
          <span className="text-sm font-normal text-slate-500">
            Showing {displayedProjects} of {totalProjects} projects
          </span>
        </CardTitle>
        <p className="text-sm text-slate-500 mt-1">
          Projects sorted by contract date. Click a row to expand and see current phase.
        </p>
      </CardHeader>
      <CardContent>
        <div className="h-[600px] w-full border rounded-lg overflow-hidden">
          <Gantt
            tasks={tasks}
            scales={scales}
            cellWidth={50}
            cellHeight={40}
          />
        </div>
      </CardContent>
    </Card>
  )
}
