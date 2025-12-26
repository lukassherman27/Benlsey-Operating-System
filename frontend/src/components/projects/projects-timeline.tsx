'use client'

import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import { CalendarDays, AlertCircle, ChevronRight } from 'lucide-react'
import { api } from '@/lib/api'
import { cn, formatCurrency } from '@/lib/utils'
import { useRouter } from 'next/navigation'

// Phase order and colors
const PHASE_ORDER: Record<string, number> = {
  'Mobilization': 1,
  'Concept': 2,
  'SD': 3,
  'DD': 4,
  'CD': 5,
  'CA': 6,
}

const PHASE_COLORS: Record<string, string> = {
  'Mobilization': 'bg-slate-400',
  'Concept': 'bg-blue-500',
  'SD': 'bg-cyan-500',
  'DD': 'bg-teal-500',
  'CD': 'bg-emerald-500',
  'CA': 'bg-green-600',
}

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
  pm_name?: string
  country?: string
}

export function ProjectsTimeline() {
  const router = useRouter()

  const projectsQuery = useQuery({
    queryKey: ['active-projects-timeline'],
    queryFn: () => api.getActiveProjects(),
    staleTime: 1000 * 60 * 5,
  })

  // Calculate timeline range and transform projects
  const { projects, timelineRange } = useMemo(() => {
    const rawProjects = projectsQuery.data?.data || []

    // Sort by contract date (newest first)
    const sorted = [...rawProjects].sort((a: ProjectData, b: ProjectData) => {
      const dateA = a.contract_signed_date || a.first_contact_date || '2020-01-01'
      const dateB = b.contract_signed_date || b.first_contact_date || '2020-01-01'
      return dateB.localeCompare(dateA)
    })

    // Limit to 20 projects
    const displayProjects = sorted.slice(0, 20)

    // Calculate date range
    const now = new Date()
    let minDate = new Date(now.getTime() - 365 * 24 * 60 * 60 * 1000) // 1 year ago
    let maxDate = new Date(now.getTime() + 365 * 24 * 60 * 60 * 1000) // 1 year from now

    displayProjects.forEach((project: ProjectData) => {
      const startDate = project.contract_signed_date || project.first_contact_date
      const endDate = project.target_completion_date

      if (startDate) {
        const d = new Date(startDate)
        if (d < minDate) minDate = d
      }
      if (endDate) {
        const d = new Date(endDate)
        if (d > maxDate) maxDate = d
      }
    })

    return {
      projects: displayProjects as ProjectData[],
      timelineRange: { minDate, maxDate },
    }
  }, [projectsQuery.data])

  // Generate month labels
  const monthLabels = useMemo(() => {
    const { minDate, maxDate } = timelineRange
    const labels: { month: string; year: string; position: number }[] = []

    const totalDays = Math.ceil((maxDate.getTime() - minDate.getTime()) / (24 * 60 * 60 * 1000))
    const current = new Date(minDate)
    current.setDate(1) // Start of month

    while (current <= maxDate) {
      const position = Math.max(0, Math.min(100,
        ((current.getTime() - minDate.getTime()) / (maxDate.getTime() - minDate.getTime())) * 100
      ))

      labels.push({
        month: current.toLocaleString('default', { month: 'short' }),
        year: current.getFullYear().toString(),
        position,
      })

      current.setMonth(current.getMonth() + 1)
    }

    return labels
  }, [timelineRange])

  // Calculate position for a date
  const getDatePosition = (dateStr: string | undefined, fallbackDate: Date = new Date()) => {
    const date = dateStr ? new Date(dateStr) : fallbackDate
    const { minDate, maxDate } = timelineRange
    const totalRange = maxDate.getTime() - minDate.getTime()
    const position = ((date.getTime() - minDate.getTime()) / totalRange) * 100
    return Math.max(0, Math.min(100, position))
  }

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

  if (projects.length === 0) {
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

  const totalProjects = projectsQuery.data?.data?.length || 0

  return (
    <Card className="border-slate-200">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center justify-between">
          <span className="flex items-center gap-2">
            <CalendarDays className="h-5 w-5 text-teal-600" />
            Project Timeline
          </span>
          <span className="text-sm font-normal text-slate-500">
            Showing {projects.length} of {totalProjects} projects
          </span>
        </CardTitle>
        <p className="text-sm text-slate-500 mt-1">
          Projects sorted by contract date. Click a project to view details.
        </p>
      </CardHeader>
      <CardContent>
        {/* Month labels header */}
        <div className="relative h-8 mb-2 border-b border-slate-200">
          <div className="absolute inset-0 flex">
            {monthLabels.map((label, i) => (
              <div
                key={i}
                className="absolute text-xs text-slate-500 transform -translate-x-1/2"
                style={{ left: `${label.position}%` }}
              >
                <div className="font-medium">{label.month}</div>
                {(i === 0 || monthLabels[i - 1]?.year !== label.year) && (
                  <div className="text-[10px] text-slate-400">{label.year}</div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Today marker */}
        <div className="relative h-0">
          <div
            className="absolute top-0 w-0.5 bg-red-500 z-10"
            style={{
              left: `${getDatePosition(new Date().toISOString())}%`,
              height: `${projects.length * 56 + 16}px`
            }}
          >
            <div className="absolute -top-5 left-1 text-[10px] font-medium text-red-500 whitespace-nowrap">
              Today
            </div>
          </div>
        </div>

        {/* Project rows */}
        <div className="space-y-2 pt-4">
          {projects.map((project) => {
            const startDate = project.contract_signed_date || project.first_contact_date
            const endDate = project.target_completion_date

            const startPos = getDatePosition(startDate)
            const endPos = endDate
              ? getDatePosition(endDate)
              : getDatePosition(undefined, new Date(new Date().getTime() + 180 * 24 * 60 * 60 * 1000))

            const width = Math.max(5, endPos - startPos)
            const currentPhase = project.current_phase || 'Concept'
            const phaseColor = PHASE_COLORS[currentPhase] || 'bg-slate-400'
            const progressPercent = ((PHASE_ORDER[currentPhase] || 1) / 6) * 100

            const projectName = project.project_title || project.project_name || project.client_name || 'Unnamed'

            return (
              <div
                key={project.project_code}
                className="group flex items-center gap-3 h-12 cursor-pointer hover:bg-slate-50 rounded-lg px-2 -mx-2 transition-colors"
                onClick={() => router.push(`/projects/${encodeURIComponent(project.project_code)}`)}
              >
                {/* Project info - fixed width */}
                <div className="w-48 flex-shrink-0">
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary" className="font-mono text-[10px] px-1.5 py-0.5">
                      {project.project_code}
                    </Badge>
                    <ChevronRight className="h-3 w-3 text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                  </div>
                  <p className="text-xs text-slate-600 truncate mt-0.5">
                    {projectName.substring(0, 25)}{projectName.length > 25 ? '...' : ''}
                  </p>
                </div>

                {/* Timeline bar */}
                <div className="flex-1 relative h-8 bg-slate-100 rounded-lg overflow-hidden">
                  {/* Project duration bar */}
                  <div
                    className={cn(
                      "absolute h-full rounded-lg transition-all",
                      phaseColor
                    )}
                    style={{
                      left: `${startPos}%`,
                      width: `${width}%`,
                    }}
                  >
                    {/* Progress indicator */}
                    <div
                      className="absolute inset-y-0 left-0 bg-white/20 rounded-l-lg"
                      style={{ width: `${progressPercent}%` }}
                    />

                    {/* Phase label */}
                    {width > 10 && (
                      <div className="absolute inset-0 flex items-center justify-center">
                        <span className="text-[10px] font-bold text-white drop-shadow-sm">
                          {currentPhase}
                        </span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Value - fixed width */}
                <div className="w-20 text-right flex-shrink-0">
                  <span className="text-xs font-semibold text-slate-700">
                    {formatCurrency(project.total_fee_usd || project.contract_value || 0)}
                  </span>
                </div>
              </div>
            )
          })}
        </div>

        {/* Legend */}
        <div className="mt-6 pt-4 border-t border-slate-200">
          <p className="text-xs text-slate-500 mb-2">Phase Legend:</p>
          <div className="flex flex-wrap gap-2">
            {Object.entries(PHASE_COLORS).map(([phase, color]) => (
              <div key={phase} className="flex items-center gap-1">
                <div className={cn("w-3 h-3 rounded", color)} />
                <span className="text-xs text-slate-600">{phase}</span>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
