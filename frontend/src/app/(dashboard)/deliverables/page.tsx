'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api, Deliverable, PMWorkload } from '@/lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Skeleton } from '@/components/ui/skeleton'
import {
  CheckCircle2,
  Clock,
  Users,
  ChevronRight,
  RefreshCw,
  Package,
  AlertCircle,
  FileCheck,
  ExternalLink,
  Plus,
} from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useState } from 'react'
import { cn } from '@/lib/utils'
import { ds } from '@/lib/design-system'
import Link from 'next/link'

// Deliverable types as defined in database
const DELIVERABLE_TYPES = [
  'drawing', 'presentation', 'document', 'model',
  'specification', 'report', 'review', 'other'
] as const

export default function DeliverablesPage() {
  const queryClient = useQueryClient()
  const [selectedPM, setSelectedPM] = useState<string | null>(null)
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [newDeliverable, setNewDeliverable] = useState({
    name: '',
    project_code: '',
    deliverable_type: 'document' as string,
    due_date: '',
    description: '',
  })

  // Fetch data
  const { data: workload, isLoading: workloadLoading, error: workloadError } = useQuery({
    queryKey: ['pm-workload'],
    queryFn: () => api.getPMWorkload(),
  })

  const { data: deliverables, isLoading: deliverablesLoading, error: deliverablesError } = useQuery({
    queryKey: ['deliverables', selectedPM],
    queryFn: () => api.getDeliverables(selectedPM ? { assigned_pm: selectedPM } : undefined),
  })

  const { data: pmList } = useQuery({
    queryKey: ['pm-list'],
    queryFn: () => api.getPMList(),
  })

  // Status update mutation
  const updateStatus = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) =>
      api.updateDeliverableStatus(id, { status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deliverables'] })
      queryClient.invalidateQueries({ queryKey: ['pm-workload'] })
    },
  })

  // Create deliverable mutation
  const createDeliverableMutation = useMutation({
    mutationFn: (data: {
      project_code: string
      deliverable_name: string
      due_date?: string
      deliverable_type?: string
      description?: string
    }) => api.createDeliverable(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deliverables'] })
      queryClient.invalidateQueries({ queryKey: ['pm-workload'] })
      setCreateModalOpen(false)
      setNewDeliverable({
        name: '',
        project_code: '',
        deliverable_type: 'document',
        due_date: '',
        description: '',
      })
    },
  })

  const handleCreateDeliverable = () => {
    if (!newDeliverable.name.trim() || !newDeliverable.project_code.trim()) return
    createDeliverableMutation.mutate({
      project_code: newDeliverable.project_code.trim(),
      deliverable_name: newDeliverable.name.trim(),
      due_date: newDeliverable.due_date || undefined,
      deliverable_type: newDeliverable.deliverable_type || undefined,
      description: newDeliverable.description.trim() || undefined,
    })
  }

  const statusColors: Record<string, string> = {
    pending: 'bg-slate-100 text-slate-700 border-slate-200',
    in_progress: 'bg-blue-100 text-blue-700 border-blue-200',
    completed: 'bg-emerald-100 text-emerald-700 border-emerald-200',
    submitted: 'bg-purple-100 text-purple-700 border-purple-200',
    approved: 'bg-teal-100 text-teal-700 border-teal-200',
  }

  // Calculate stats
  const stats = {
    total: deliverables?.count || 0,
    completed: deliverables?.deliverables?.filter((d: Deliverable) => d.status === 'completed').length || 0,
    inProgress: deliverables?.deliverables?.filter((d: Deliverable) => d.status === 'in_progress').length || 0,
    pending: deliverables?.deliverables?.filter((d: Deliverable) => d.status === 'pending').length || 0,
  }

  // Loading skeleton
  if (deliverablesLoading && workloadLoading) {
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
  if (deliverablesError || workloadError) {
    return (
      <div className="space-y-6">
        <Card className={cn(ds.borderRadius.card, "border-red-200 bg-red-50")}>
          <CardContent className="py-12 text-center">
            <AlertCircle className="mx-auto h-12 w-12 text-red-400 mb-4" />
            <p className={cn(ds.typography.heading3, "text-red-700 mb-2")}>
              Failed to load deliverables
            </p>
            <p className={cn(ds.typography.body, "text-red-600 mb-4")}>
              Something broke. Our fault, not yours.
            </p>
            <Button
              onClick={() => queryClient.invalidateQueries()}
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
            Deliverables
          </h1>
          <p className={cn(ds.typography.body, ds.textColors.secondary, "mt-1")}>
            Track project deliverables and team workload
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => queryClient.invalidateQueries()}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button
            size="sm"
            onClick={() => setCreateModalOpen(true)}
            className="bg-teal-600 hover:bg-teal-700 text-white"
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Deliverable
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-slate-100">
                <Package className="h-5 w-5 text-slate-700" />
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

        <Card className={cn(ds.borderRadius.card, "border-blue-200 bg-blue-50/30")}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-100">
                <Clock className="h-5 w-5 text-blue-700" />
              </div>
              <div>
                <p className={cn(ds.typography.caption, "text-blue-700")}>In Progress</p>
                <p className={cn(ds.typography.heading2, "text-blue-800")}>
                  {stats.inProgress}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className={cn(ds.borderRadius.card, "border-slate-200 bg-slate-50/30")}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-slate-100">
                <FileCheck className="h-5 w-5 text-slate-600" />
              </div>
              <div>
                <p className={cn(ds.typography.caption, ds.textColors.tertiary)}>Pending</p>
                <p className={cn(ds.typography.heading2, ds.textColors.primary)}>
                  {stats.pending}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="all" className="space-y-4">
        <TabsList>
          <TabsTrigger value="all">All Deliverables</TabsTrigger>
          <TabsTrigger value="workload">
            <Users className="h-4 w-4 mr-2" />
            PM Workload
          </TabsTrigger>
        </TabsList>

        {/* All Deliverables Tab */}
        <TabsContent value="all" className="space-y-4">
          <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className={ds.typography.heading3}>All Deliverables</CardTitle>
                  {selectedPM && (
                    <p className={cn(ds.typography.caption, "text-teal-600 mt-1")}>
                      Filtered by: {selectedPM}
                    </p>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <select
                    className="border rounded-lg px-3 py-1.5 text-sm bg-white"
                    value={selectedPM || ''}
                    onChange={(e) => setSelectedPM(e.target.value || null)}
                  >
                    <option value="">All PMs</option>
                    <option value="Unassigned">Unassigned</option>
                    {pmList?.pms?.map((pm) => (
                      <option key={pm.member_id} value={pm.full_name}>
                        {pm.full_name}
                      </option>
                    ))}
                  </select>
                  {selectedPM && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setSelectedPM(null)}
                      className="text-slate-500 hover:text-slate-700"
                    >
                      Clear
                    </Button>
                  )}
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {deliverables?.count === 0 ? (
                <div className="text-center py-12">
                  <Package className="mx-auto h-12 w-12 text-slate-300 mb-4" />
                  <p className={cn(ds.typography.heading3, ds.textColors.primary, "mb-2")}>
                    No deliverables tracked yet
                  </p>
                  <p className={cn(ds.typography.body, ds.textColors.tertiary, "max-w-md mx-auto")}>
                    Deliverables are things you need to deliver to clients: drawings, presentations, reports, etc.
                    Add them from a project&apos;s detail page.
                  </p>
                </div>
              ) : (
                <div className="space-y-2 max-h-[600px] overflow-y-auto">
                  {deliverables?.deliverables?.map((d: Deliverable) => (
                    <Link
                      key={d.deliverable_id}
                      href={d.project_code ? `/projects/${encodeURIComponent(d.project_code)}` : '#'}
                      className="flex items-center justify-between p-4 border rounded-lg hover:bg-slate-50 hover:border-teal-300 transition-colors cursor-pointer group block"
                    >
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <p className={cn(ds.typography.bodyBold, ds.textColors.primary, "truncate group-hover:text-teal-700")}>
                            {d.deliverable_name || d.title || "Unnamed deliverable"}
                          </p>
                          <ExternalLink className="h-3 w-3 text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                        </div>
                        <div className="flex items-center gap-2 mt-1">
                          <span className={cn(ds.typography.caption, "text-teal-600 font-medium")}>
                            {d.project_code}
                          </span>
                          {d.project_title && (
                            <>
                              <span className={ds.textColors.tertiary}>•</span>
                              <span className={cn(ds.typography.caption, ds.textColors.tertiary, "truncate max-w-[200px]")}>
                                {d.project_title}
                              </span>
                            </>
                          )}
                          {d.phase && (
                            <>
                              <span className={ds.textColors.tertiary}>•</span>
                              <span className={cn(ds.typography.caption, ds.textColors.tertiary)}>
                                {d.phase}
                              </span>
                            </>
                          )}
                          {d.assigned_pm && (
                            <>
                              <span className={ds.textColors.tertiary}>•</span>
                              <span className={cn(ds.typography.caption, ds.textColors.secondary)}>
                                {d.assigned_pm}
                              </span>
                            </>
                          )}
                          {d.due_date && (
                            <>
                              <span className={ds.textColors.tertiary}>•</span>
                              <span className={cn(ds.typography.caption, ds.textColors.tertiary)}>
                                Due: {d.due_date}
                              </span>
                            </>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-2 ml-4">
                        <Badge
                          variant="outline"
                          className={statusColors[d.status] || 'bg-slate-100 text-slate-600'}
                        >
                          {d.status.replace('_', ' ')}
                        </Badge>
                        {d.is_overdue === 1 && (
                          <Badge variant="destructive">Overdue</Badge>
                        )}
                        <ChevronRight className="h-4 w-4 text-slate-400 group-hover:text-teal-600 transition-colors" />
                      </div>
                    </Link>
                  ))}
                </div>
              )}
              {deliverables && deliverables.count > 0 && (
                <div className="mt-4 pt-4 border-t">
                  <p className={cn(ds.typography.caption, ds.textColors.tertiary, "text-center")}>
                    Showing {deliverables.count} deliverables
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* PM Workload Tab */}
        <TabsContent value="workload" className="space-y-4">
          <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className={cn(ds.typography.heading3, "flex items-center gap-2")}>
                    <Users className="h-5 w-5" />
                    PM Workload
                  </CardTitle>
                  <CardDescription className={ds.typography.body}>
                    Deliverables grouped by assigned team member. Click to filter.
                  </CardDescription>
                </div>
                {selectedPM && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setSelectedPM(null)}
                    className="text-teal-600 border-teal-200 hover:bg-teal-50"
                  >
                    Clear filter: {selectedPM}
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {workloadLoading ? (
                <div className="space-y-2">
                  {[...Array(3)].map((_, i) => (
                    <Skeleton key={i} className="h-16 w-full" />
                  ))}
                </div>
              ) : workload?.workload?.length === 0 ? (
                <div className="text-center py-12">
                  <Users className="mx-auto h-12 w-12 text-slate-300 mb-4" />
                  <p className={cn(ds.typography.heading3, ds.textColors.primary, "mb-2")}>
                    No deliverables to distribute
                  </p>
                  <p className={cn(ds.typography.body, ds.textColors.tertiary)}>
                    Once deliverables are created, you&apos;ll see workload by PM here.
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {workload?.workload?.map((pm: PMWorkload) => (
                    <div
                      key={pm.pm_name}
                      className={cn(
                        "flex items-center justify-between p-4 rounded-lg border cursor-pointer transition-colors",
                        selectedPM === pm.pm_name
                          ? "bg-teal-50 border-teal-300 ring-1 ring-teal-200"
                          : "hover:bg-slate-50"
                      )}
                      onClick={() => setSelectedPM(selectedPM === pm.pm_name ? null : pm.pm_name)}
                    >
                      <div className="flex items-center gap-3">
                        <div className={cn(
                          "w-10 h-10 rounded-full flex items-center justify-center font-medium",
                          pm.pm_name === 'Unassigned'
                            ? "bg-slate-100 text-slate-600"
                            : "bg-teal-100 text-teal-700"
                        )}>
                          {pm.pm_name === 'Unassigned' ? '?' : pm.pm_name.charAt(0)}
                        </div>
                        <div>
                          <p className={cn(ds.typography.bodyBold, ds.textColors.primary)}>
                            {pm.pm_name}
                          </p>
                          <p className={cn(ds.typography.caption, ds.textColors.tertiary)}>
                            {pm.total_deliverables} deliverables
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        {pm.overdue_count > 0 && (
                          <Badge variant="destructive">{pm.overdue_count} overdue</Badge>
                        )}
                        {pm.due_this_week > 0 && (
                          <Badge variant="secondary" className="bg-amber-100 text-amber-700 border-amber-200">
                            {pm.due_this_week} this week
                          </Badge>
                        )}
                        {pm.completed_count > 0 && (
                          <Badge variant="outline" className="bg-emerald-50 text-emerald-700 border-emerald-200">
                            {pm.completed_count} done
                          </Badge>
                        )}
                        <ChevronRight className="h-4 w-4 text-slate-400" />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Create Deliverable Modal */}
      <Dialog open={createModalOpen} onOpenChange={setCreateModalOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle className={ds.typography.heading3}>Create Deliverable</DialogTitle>
            <DialogDescription className={ds.typography.body}>
              Add a new deliverable to track for a project.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="deliverable-name">Name *</Label>
              <Input
                id="deliverable-name"
                placeholder="Schematic Design Package"
                value={newDeliverable.name}
                onChange={(e) => setNewDeliverable({ ...newDeliverable, name: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="project-code">Project Code *</Label>
              <Input
                id="project-code"
                placeholder="25 BK-033"
                value={newDeliverable.project_code}
                onChange={(e) => setNewDeliverable({ ...newDeliverable, project_code: e.target.value })}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="deliverable-type">Type</Label>
                <Select
                  value={newDeliverable.deliverable_type}
                  onValueChange={(value) => setNewDeliverable({ ...newDeliverable, deliverable_type: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select type" />
                  </SelectTrigger>
                  <SelectContent>
                    {DELIVERABLE_TYPES.map((type) => (
                      <SelectItem key={type} value={type}>
                        {type.charAt(0).toUpperCase() + type.slice(1)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="due-date">Due Date</Label>
                <Input
                  id="due-date"
                  type="date"
                  value={newDeliverable.due_date}
                  onChange={(e) => setNewDeliverable({ ...newDeliverable, due_date: e.target.value })}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Input
                id="description"
                placeholder="Optional description"
                value={newDeliverable.description}
                onChange={(e) => setNewDeliverable({ ...newDeliverable, description: e.target.value })}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setCreateModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleCreateDeliverable}
              disabled={!newDeliverable.name.trim() || !newDeliverable.project_code.trim() || createDeliverableMutation.isPending}
              className="bg-teal-600 hover:bg-teal-700 text-white"
            >
              {createDeliverableMutation.isPending ? 'Creating...' : 'Create Deliverable'}
            </Button>
          </DialogFooter>
          {createDeliverableMutation.isError && (
            <p className="text-sm text-red-600 mt-2">
              Error: {createDeliverableMutation.error?.message || 'Failed to create deliverable'}
            </p>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
