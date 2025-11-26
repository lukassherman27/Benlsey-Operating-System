'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api, Deliverable, DeliverableAlert, PMWorkload } from '@/lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  AlertTriangle,
  Calendar,
  CheckCircle2,
  Clock,
  Users,
  ChevronRight,
  Bell,
  RefreshCw
} from 'lucide-react'
import { useState } from 'react'
import { cn } from '@/lib/utils'

export default function DeliverablesPage() {
  const queryClient = useQueryClient()
  const [selectedPM, setSelectedPM] = useState<string | null>(null)

  // Fetch data
  const { data: alerts, isLoading: alertsLoading } = useQuery({
    queryKey: ['deliverable-alerts'],
    queryFn: () => api.getDeliverableAlerts(),
    refetchInterval: 60000, // Refresh every minute
  })

  const { data: workload, isLoading: workloadLoading } = useQuery({
    queryKey: ['pm-workload'],
    queryFn: () => api.getPMWorkload(),
  })

  const { data: upcoming, isLoading: upcomingLoading } = useQuery({
    queryKey: ['upcoming-deliverables'],
    queryFn: () => api.getUpcomingDeliverables(14),
  })

  const { data: deliverables, isLoading: deliverablesLoading } = useQuery({
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
      queryClient.invalidateQueries({ queryKey: ['deliverable-alerts'] })
      queryClient.invalidateQueries({ queryKey: ['pm-workload'] })
    },
  })

  const priorityColors = {
    critical: 'bg-red-100 text-red-800 border-red-200',
    high: 'bg-orange-100 text-orange-800 border-orange-200',
    medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    low: 'bg-blue-100 text-blue-800 border-blue-200',
  }

  const statusColors = {
    pending: 'bg-gray-100 text-gray-800',
    in_progress: 'bg-blue-100 text-blue-800',
    completed: 'bg-green-100 text-green-800',
    submitted: 'bg-purple-100 text-purple-800',
    approved: 'bg-emerald-100 text-emerald-800',
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Deliverables & PM Workload</h1>
          <p className="text-muted-foreground">
            Track project deliverables, deadlines, and team assignments
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => queryClient.invalidateQueries()}
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Alerts Summary */}
      {alerts && alerts.count > 0 && (
        <Card className="border-red-200 bg-red-50">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center gap-2">
              <Bell className="h-5 w-5 text-red-600" />
              Active Alerts ({alerts.count})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">
                  {alerts.by_priority.critical.length}
                </div>
                <div className="text-sm text-muted-foreground">Critical</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">
                  {alerts.by_priority.high.length}
                </div>
                <div className="text-sm text-muted-foreground">High</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-yellow-600">
                  {alerts.by_priority.medium.length}
                </div>
                <div className="text-sm text-muted-foreground">Medium</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {alerts.by_priority.low.length}
                </div>
                <div className="text-sm text-muted-foreground">Low</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="alerts">
            Alerts {alerts && alerts.count > 0 && (
              <Badge variant="destructive" className="ml-2">{alerts.count}</Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="upcoming">Upcoming</TabsTrigger>
          <TabsTrigger value="all">All Deliverables</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          <div className="grid md:grid-cols-2 gap-4">
            {/* PM Workload Summary */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="h-5 w-5" />
                  PM Workload
                </CardTitle>
                <CardDescription>
                  Deliverable distribution by team member
                </CardDescription>
              </CardHeader>
              <CardContent>
                {workloadLoading ? (
                  <div className="text-muted-foreground">Loading...</div>
                ) : workload?.workload.length === 0 ? (
                  <div className="text-muted-foreground">No workload data</div>
                ) : (
                  <div className="space-y-3">
                    {workload?.workload.map((pm: PMWorkload) => (
                      <div
                        key={pm.pm_name}
                        className="flex items-center justify-between p-2 rounded-lg hover:bg-muted cursor-pointer"
                        onClick={() => setSelectedPM(pm.pm_name === 'Unassigned' ? null : pm.pm_name)}
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                            {pm.pm_name.charAt(0)}
                          </div>
                          <div>
                            <div className="font-medium">{pm.pm_name}</div>
                            <div className="text-sm text-muted-foreground">
                              {pm.total_deliverables} total
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {pm.overdue_count > 0 && (
                            <Badge variant="destructive">{pm.overdue_count} overdue</Badge>
                          )}
                          {pm.due_this_week > 0 && (
                            <Badge variant="secondary">{pm.due_this_week} this week</Badge>
                          )}
                          <ChevronRight className="h-4 w-4 text-muted-foreground" />
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Quick Stats */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Calendar className="h-5 w-5" />
                  Delivery Timeline
                </CardTitle>
                <CardDescription>
                  Upcoming deliverables summary
                </CardDescription>
              </CardHeader>
              <CardContent>
                {upcomingLoading ? (
                  <div className="text-muted-foreground">Loading...</div>
                ) : (
                  <div className="space-y-4">
                    <div className="grid grid-cols-3 gap-4 text-center">
                      <div className="p-3 bg-red-50 rounded-lg">
                        <div className="text-2xl font-bold text-red-600">
                          {alerts?.by_priority.critical.filter(a => a.type === 'overdue').length || 0}
                        </div>
                        <div className="text-sm text-muted-foreground">Overdue</div>
                      </div>
                      <div className="p-3 bg-orange-50 rounded-lg">
                        <div className="text-2xl font-bold text-orange-600">
                          {upcoming?.upcoming_deliverables.filter(d =>
                            d.days_until_due !== undefined && d.days_until_due <= 7
                          ).length || 0}
                        </div>
                        <div className="text-sm text-muted-foreground">This Week</div>
                      </div>
                      <div className="p-3 bg-blue-50 rounded-lg">
                        <div className="text-2xl font-bold text-blue-600">
                          {upcoming?.count || 0}
                        </div>
                        <div className="text-sm text-muted-foreground">Next 14 Days</div>
                      </div>
                    </div>

                    {/* Next 3 deliverables */}
                    <div className="space-y-2">
                      <h4 className="font-medium text-sm text-muted-foreground">Coming Up</h4>
                      {upcoming?.upcoming_deliverables.slice(0, 3).map((d: Deliverable) => (
                        <div key={d.deliverable_id} className="flex justify-between items-center p-2 bg-muted/50 rounded">
                          <div className="truncate flex-1">
                            <div className="font-medium text-sm truncate">{d.deliverable_name}</div>
                            <div className="text-xs text-muted-foreground">{d.project_code}</div>
                          </div>
                          <Badge variant="outline" className="ml-2">
                            {d.days_until_due !== undefined && d.days_until_due <= 0
                              ? 'Today'
                              : `${Math.ceil(d.days_until_due || 0)} days`}
                          </Badge>
                        </div>
                      ))}
                      {(!upcoming || upcoming.count === 0) && (
                        <div className="text-sm text-muted-foreground text-center py-4">
                          No upcoming deliverables in next 14 days
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Alerts Tab */}
        <TabsContent value="alerts" className="space-y-4">
          {alertsLoading ? (
            <div className="text-muted-foreground">Loading alerts...</div>
          ) : alerts?.count === 0 ? (
            <Card>
              <CardContent className="py-8 text-center">
                <CheckCircle2 className="h-12 w-12 mx-auto text-green-500 mb-3" />
                <h3 className="font-medium">All Clear!</h3>
                <p className="text-muted-foreground">No active alerts at this time</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {alerts?.alerts.map((alert: DeliverableAlert) => (
                <Card
                  key={`${alert.deliverable_id}-${alert.type}`}
                  className={cn('border-l-4', {
                    'border-l-red-500': alert.priority === 'critical',
                    'border-l-orange-500': alert.priority === 'high',
                    'border-l-yellow-500': alert.priority === 'medium',
                    'border-l-blue-500': alert.priority === 'low',
                  })}
                >
                  <CardContent className="py-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        {alert.type === 'overdue' ? (
                          <AlertTriangle className="h-5 w-5 text-red-500" />
                        ) : (
                          <Clock className="h-5 w-5 text-muted-foreground" />
                        )}
                        <div>
                          <div className="font-medium">{alert.message}</div>
                          <div className="text-sm text-muted-foreground">
                            {alert.project_code}
                            {alert.assigned_pm && ` | ${alert.assigned_pm}`}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge className={priorityColors[alert.priority]}>
                          {alert.priority}
                        </Badge>
                        {alert.type !== 'overdue' && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => updateStatus.mutate({
                              id: alert.deliverable_id,
                              status: 'completed'
                            })}
                          >
                            Mark Complete
                          </Button>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Upcoming Tab */}
        <TabsContent value="upcoming" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Upcoming Deliverables (Next 14 Days)</CardTitle>
            </CardHeader>
            <CardContent>
              {upcomingLoading ? (
                <div className="text-muted-foreground">Loading...</div>
              ) : upcoming?.count === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  No deliverables due in the next 14 days
                </div>
              ) : (
                <div className="space-y-2">
                  {upcoming?.upcoming_deliverables.map((d: Deliverable) => (
                    <div
                      key={d.deliverable_id}
                      className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50"
                    >
                      <div className="flex-1">
                        <div className="font-medium">{d.deliverable_name}</div>
                        <div className="text-sm text-muted-foreground">
                          {d.project_code} | {d.phase || 'No phase'} | {d.assigned_pm || 'Unassigned'}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge className={statusColors[d.status as keyof typeof statusColors] || 'bg-gray-100'}>
                          {d.status}
                        </Badge>
                        <Badge
                          variant="outline"
                          className={cn({
                            'border-red-300 text-red-700': d.days_until_due !== undefined && d.days_until_due <= 1,
                            'border-orange-300 text-orange-700': d.days_until_due !== undefined && d.days_until_due <= 7 && d.days_until_due > 1,
                          })}
                        >
                          {d.days_until_due !== undefined && d.days_until_due <= 0
                            ? 'Due Today'
                            : `${Math.ceil(d.days_until_due || 0)} days`}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* All Deliverables Tab */}
        <TabsContent value="all" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>All Deliverables</CardTitle>
                <div className="flex items-center gap-2">
                  <select
                    className="border rounded px-2 py-1 text-sm"
                    value={selectedPM || ''}
                    onChange={(e) => setSelectedPM(e.target.value || null)}
                  >
                    <option value="">All PMs</option>
                    {pmList?.pms.map((pm) => (
                      <option key={pm.member_id} value={pm.full_name}>
                        {pm.full_name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {deliverablesLoading ? (
                <div className="text-muted-foreground">Loading...</div>
              ) : deliverables?.count === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  No deliverables found
                </div>
              ) : (
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {deliverables?.deliverables.map((d: Deliverable) => (
                    <div
                      key={d.deliverable_id}
                      className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50"
                    >
                      <div className="flex-1">
                        <div className="font-medium">{d.deliverable_name}</div>
                        <div className="text-sm text-muted-foreground">
                          {d.project_code} | {d.phase || 'No phase'}
                          {d.due_date && ` | Due: ${d.due_date}`}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge className={statusColors[d.status as keyof typeof statusColors] || 'bg-gray-100'}>
                          {d.status}
                        </Badge>
                        {d.is_overdue === 1 && (
                          <Badge variant="destructive">Overdue</Badge>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
              <div className="mt-4 text-sm text-muted-foreground text-center">
                Showing {deliverables?.count || 0} deliverables
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
