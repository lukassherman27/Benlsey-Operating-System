'use client'

import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { format, differenceInDays, isPast, addDays } from 'date-fns'
import { api } from '@/lib/api'
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
  Package,
  AlertTriangle,
  Clock,
  CheckCircle2,
  Search,
  Filter,
  Calendar,
  User,
  ChevronRight,
  ArrowUpRight,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useRouter } from 'next/navigation'

interface Deliverable {
  deliverable_id: number
  project_code: string
  project_name?: string
  name: string
  description?: string
  status: string
  priority: string
  due_date: string | null
  start_date?: string | null
  actual_completion_date?: string | null
  owner_staff_id?: number
  assigned_pm?: string
  phase_id?: number
  phase_name?: string
  deliverable_type?: string
}

const STATUS_CONFIG: Record<string, { color: string; bgColor: string; icon: React.ReactNode }> = {
  pending: {
    color: 'text-slate-600',
    bgColor: 'bg-slate-100 border-slate-200',
    icon: <Clock className="h-3 w-3" />,
  },
  in_progress: {
    color: 'text-blue-600',
    bgColor: 'bg-blue-50 border-blue-200',
    icon: <Package className="h-3 w-3" />,
  },
  delivered: {
    color: 'text-emerald-600',
    bgColor: 'bg-emerald-50 border-emerald-200',
    icon: <CheckCircle2 className="h-3 w-3" />,
  },
  approved: {
    color: 'text-green-600',
    bgColor: 'bg-green-50 border-green-200',
    icon: <CheckCircle2 className="h-3 w-3" />,
  },
  overdue: {
    color: 'text-red-600',
    bgColor: 'bg-red-50 border-red-200',
    icon: <AlertTriangle className="h-3 w-3" />,
  },
}

const PRIORITY_CONFIG: Record<string, { color: string }> = {
  critical: { color: 'text-red-600 bg-red-50 border-red-200' },
  high: { color: 'text-amber-600 bg-amber-50 border-amber-200' },
  normal: { color: 'text-slate-600 bg-slate-50 border-slate-200' },
  low: { color: 'text-slate-400 bg-slate-50 border-slate-200' },
}

export function DeliverablesDashboard() {
  const router = useRouter()
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [pmFilter, setPmFilter] = useState<string>('all')

  // Fetch all deliverables
  const deliverablesQuery = useQuery({
    queryKey: ['deliverables', 'all'],
    queryFn: () => api.getDeliverables(),
    staleTime: 1000 * 60 * 5,
  })

  // Fetch PM list for filtering
  const pmListQuery = useQuery({
    queryKey: ['pm-list'],
    queryFn: () => api.getPMList(),
    staleTime: 1000 * 60 * 30,
  })

  // Process and filter deliverables
  const { filteredDeliverables, stats } = useMemo(() => {
    const deliverables = deliverablesQuery.data?.deliverables || []
    const now = new Date()

    // Calculate stats
    const overdue = deliverables.filter(d =>
      d.due_date &&
      isPast(new Date(d.due_date)) &&
      !['delivered', 'approved'].includes(d.status)
    ).length

    const dueSoon = deliverables.filter(d => {
      if (!d.due_date || ['delivered', 'approved'].includes(d.status)) return false
      const dueDate = new Date(d.due_date)
      const daysUntil = differenceInDays(dueDate, now)
      return daysUntil >= 0 && daysUntil <= 7
    }).length

    const inProgress = deliverables.filter(d => d.status === 'in_progress').length
    const completed = deliverables.filter(d => ['delivered', 'approved'].includes(d.status)).length

    // Apply filters
    let filtered = [...deliverables]

    if (search) {
      const searchLower = search.toLowerCase()
      filtered = filtered.filter(d =>
        d.name.toLowerCase().includes(searchLower) ||
        d.project_code.toLowerCase().includes(searchLower) ||
        d.project_name?.toLowerCase().includes(searchLower) ||
        d.assigned_pm?.toLowerCase().includes(searchLower)
      )
    }

    if (statusFilter !== 'all') {
      if (statusFilter === 'overdue') {
        filtered = filtered.filter(d =>
          d.due_date &&
          isPast(new Date(d.due_date)) &&
          !['delivered', 'approved'].includes(d.status)
        )
      } else {
        filtered = filtered.filter(d => d.status === statusFilter)
      }
    }

    if (pmFilter !== 'all') {
      filtered = filtered.filter(d => d.assigned_pm === pmFilter)
    }

    // Sort by due date (overdue first, then upcoming, then no date)
    filtered.sort((a, b) => {
      if (!a.due_date && !b.due_date) return 0
      if (!a.due_date) return 1
      if (!b.due_date) return -1
      return new Date(a.due_date).getTime() - new Date(b.due_date).getTime()
    })

    return {
      filteredDeliverables: filtered,
      stats: { overdue, dueSoon, inProgress, completed, total: deliverables.length },
    }
  }, [deliverablesQuery.data, search, statusFilter, pmFilter])

  const pmList = pmListQuery.data?.pms || []

  if (deliverablesQuery.isLoading) {
    return (
      <Card className="border-slate-200">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Package className="h-5 w-5 text-teal-600" />
            Deliverables Dashboard
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[300px] w-full" />
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card
          className={cn(
            "border cursor-pointer transition-colors hover:bg-red-50/50",
            statusFilter === 'overdue' ? "border-red-400 bg-red-50" : "border-red-200 bg-red-50/30"
          )}
          onClick={() => setStatusFilter(statusFilter === 'overdue' ? 'all' : 'overdue')}
        >
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-red-600 mb-1">
              <AlertTriangle className="h-4 w-4" />
              <span className="text-xs font-medium uppercase">Overdue</span>
            </div>
            <p className="text-2xl font-bold text-red-700">{stats.overdue}</p>
          </CardContent>
        </Card>

        <Card
          className={cn(
            "border cursor-pointer transition-colors hover:bg-amber-50/50",
            "border-amber-200 bg-amber-50/30"
          )}
        >
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-amber-600 mb-1">
              <Clock className="h-4 w-4" />
              <span className="text-xs font-medium uppercase">Due This Week</span>
            </div>
            <p className="text-2xl font-bold text-amber-700">{stats.dueSoon}</p>
          </CardContent>
        </Card>

        <Card
          className={cn(
            "border cursor-pointer transition-colors hover:bg-blue-50/50",
            statusFilter === 'in_progress' ? "border-blue-400 bg-blue-50" : "border-blue-200 bg-blue-50/30"
          )}
          onClick={() => setStatusFilter(statusFilter === 'in_progress' ? 'all' : 'in_progress')}
        >
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-blue-600 mb-1">
              <Package className="h-4 w-4" />
              <span className="text-xs font-medium uppercase">In Progress</span>
            </div>
            <p className="text-2xl font-bold text-blue-700">{stats.inProgress}</p>
          </CardContent>
        </Card>

        <Card className="border border-emerald-200 bg-emerald-50/30">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-emerald-600 mb-1">
              <CheckCircle2 className="h-4 w-4" />
              <span className="text-xs font-medium uppercase">Completed</span>
            </div>
            <p className="text-2xl font-bold text-emerald-700">{stats.completed}</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Card */}
      <Card className="border-slate-200">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Package className="h-5 w-5 text-teal-600" />
              All Deliverables
            </CardTitle>
            <Badge variant="secondary" className="text-xs">
              {filteredDeliverables.length} of {stats.total}
            </Badge>
          </div>

          {/* Filters */}
          <div className="flex flex-col sm:flex-row gap-3 mt-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                placeholder="Search deliverables, projects, PMs..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[160px]">
                <Filter className="h-4 w-4 mr-2 text-slate-400" />
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="overdue">Overdue</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="in_progress">In Progress</SelectItem>
                <SelectItem value="delivered">Delivered</SelectItem>
                <SelectItem value="approved">Approved</SelectItem>
              </SelectContent>
            </Select>
            <Select value={pmFilter} onValueChange={setPmFilter}>
              <SelectTrigger className="w-[160px]">
                <User className="h-4 w-4 mr-2 text-slate-400" />
                <SelectValue placeholder="PM" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All PMs</SelectItem>
                {pmList.map((pm) => (
                  <SelectItem key={pm.pm_name || 'unknown'} value={pm.pm_name || 'unknown'}>
                    {pm.pm_name || 'Unassigned'}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardHeader>

        <CardContent className="pt-0">
          {filteredDeliverables.length === 0 ? (
            <div className="py-12 text-center">
              <Package className="mx-auto h-12 w-12 text-slate-300 mb-3" />
              <p className="text-sm text-slate-500">No deliverables found</p>
              {(search || statusFilter !== 'all' || pmFilter !== 'all') && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="mt-2"
                  onClick={() => {
                    setSearch('')
                    setStatusFilter('all')
                    setPmFilter('all')
                  }}
                >
                  Clear filters
                </Button>
              )}
            </div>
          ) : (
            <div className="space-y-2">
              {filteredDeliverables.slice(0, 20).map((deliverable) => {
                const isOverdue =
                  deliverable.due_date &&
                  isPast(new Date(deliverable.due_date)) &&
                  !['delivered', 'approved'].includes(deliverable.status)

                const daysUntilDue = deliverable.due_date
                  ? differenceInDays(new Date(deliverable.due_date), new Date())
                  : null

                const statusConfig = isOverdue
                  ? STATUS_CONFIG.overdue
                  : STATUS_CONFIG[deliverable.status] || STATUS_CONFIG.pending

                return (
                  <div
                    key={deliverable.deliverable_id}
                    className={cn(
                      "group flex items-center gap-4 p-3 rounded-lg border transition-colors cursor-pointer",
                      isOverdue
                        ? "border-red-200 bg-red-50/50 hover:bg-red-50"
                        : "border-slate-200 hover:bg-slate-50"
                    )}
                    onClick={() => router.push(`/projects/${encodeURIComponent(deliverable.project_code)}`)}
                  >
                    {/* Status Icon */}
                    <div className={cn(
                      "flex items-center justify-center w-8 h-8 rounded-full",
                      statusConfig.bgColor
                    )}>
                      <span className={statusConfig.color}>{statusConfig.icon}</span>
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-slate-900 truncate">
                          {deliverable.name}
                        </span>
                        <Badge variant="secondary" className="font-mono text-[10px] shrink-0">
                          {deliverable.project_code}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-3 mt-1 text-xs text-slate-500">
                        {deliverable.project_name && (
                          <span className="truncate max-w-[200px]">{deliverable.project_name}</span>
                        )}
                        {deliverable.assigned_pm && (
                          <>
                            <span>•</span>
                            <span className="flex items-center gap-1">
                              <User className="h-3 w-3" />
                              {deliverable.assigned_pm}
                            </span>
                          </>
                        )}
                        {deliverable.phase_name && (
                          <>
                            <span>•</span>
                            <span>{deliverable.phase_name}</span>
                          </>
                        )}
                      </div>
                    </div>

                    {/* Due Date */}
                    <div className="text-right shrink-0">
                      {deliverable.due_date ? (
                        <div className={cn(
                          "text-sm font-medium",
                          isOverdue ? "text-red-600" : daysUntilDue !== null && daysUntilDue <= 7 ? "text-amber-600" : "text-slate-600"
                        )}>
                          <div className="flex items-center gap-1">
                            <Calendar className="h-3 w-3" />
                            {format(new Date(deliverable.due_date), 'MMM d')}
                          </div>
                          <div className="text-xs font-normal">
                            {isOverdue
                              ? `${Math.abs(daysUntilDue!)} days overdue`
                              : daysUntilDue === 0
                                ? 'Due today'
                                : daysUntilDue === 1
                                  ? 'Due tomorrow'
                                  : `${daysUntilDue} days`}
                          </div>
                        </div>
                      ) : (
                        <span className="text-xs text-slate-400">No due date</span>
                      )}
                    </div>

                    {/* Arrow */}
                    <ChevronRight className="h-4 w-4 text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                  </div>
                )
              })}

              {filteredDeliverables.length > 20 && (
                <div className="text-center py-3">
                  <span className="text-sm text-slate-500">
                    Showing 20 of {filteredDeliverables.length} deliverables
                  </span>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
