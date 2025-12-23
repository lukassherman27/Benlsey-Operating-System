"use client";

import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Flag, Calendar, AlertTriangle } from "lucide-react";
import { format, differenceInDays } from "date-fns";

interface Deliverable {
  deliverable_id: number;
  project_code: string | null;
  project_title: string | null;
  deliverable_name: string | null;
  deliverable_type: string | null;
  phase: string | null;
  due_date: string | null;
  status: string;
  priority: string;
  assigned_pm: string | null;
  days_until_due?: number;
  is_overdue?: number;
  urgency_level?: string;
}

interface UpcomingResponse {
  success: boolean;
  upcoming_deliverables: Deliverable[];
  count: number;
  days_ahead: number;
}

interface OverdueResponse {
  success: boolean;
  overdue_deliverables: Deliverable[];
  count: number;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export function MilestonesWidget() {
  // Fetch upcoming deliverables (next 14 days)
  const upcomingQuery = useQuery<UpcomingResponse>({
    queryKey: ["deliverables-upcoming"],
    queryFn: async () => {
      const res = await fetch(`${API_BASE_URL}/api/deliverables/upcoming?days=14`);
      if (!res.ok) throw new Error("Failed to fetch upcoming deliverables");
      return res.json();
    },
    refetchInterval: 5 * 60 * 1000,
  });

  // Fetch overdue deliverables
  const overdueQuery = useQuery<OverdueResponse>({
    queryKey: ["deliverables-overdue"],
    queryFn: async () => {
      const res = await fetch(`${API_BASE_URL}/api/deliverables/overdue`);
      if (!res.ok) throw new Error("Failed to fetch overdue deliverables");
      return res.json();
    },
    refetchInterval: 5 * 60 * 1000,
  });

  if (upcomingQuery.isLoading || overdueQuery.isLoading) {
    return <MilestonesSkeleton />;
  }

  if (upcomingQuery.error || overdueQuery.error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Flag className="h-5 w-5 text-blue-500" />
            Upcoming Milestones
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-destructive">Error loading milestones</p>
        </CardContent>
      </Card>
    );
  }

  const upcomingDeliverables = upcomingQuery.data?.upcoming_deliverables || [];
  const overdueDeliverables = overdueQuery.data?.overdue_deliverables || [];

  // Combine and sort: overdue first, then by due date
  const allDeliverables = [
    ...overdueDeliverables.map(d => ({ ...d, _isOverdue: true })),
    ...upcomingDeliverables.filter(d =>
      !overdueDeliverables.some(o => o.deliverable_id === d.deliverable_id)
    ).map(d => ({ ...d, _isOverdue: false })),
  ].slice(0, 8);

  const overdueCount = overdueDeliverables.length;
  const dueThisWeek = upcomingDeliverables.filter(d => {
    if (!d.due_date) return false;
    const daysUntil = differenceInDays(new Date(d.due_date), new Date());
    return daysUntil >= 0 && daysUntil <= 7;
  }).length;

  return (
    <Card className="h-full">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-lg flex items-center gap-2">
          <Flag className="h-5 w-5 text-blue-500" />
          Upcoming Milestones
        </CardTitle>
        <div className="flex gap-2">
          {overdueCount > 0 && (
            <Badge variant="destructive">{overdueCount} overdue</Badge>
          )}
          <Badge variant="outline">{dueThisWeek} this week</Badge>
        </div>
      </CardHeader>
      <CardContent>
        {allDeliverables.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <Calendar className="h-12 w-12 mx-auto mb-2 text-gray-400" />
            <p>No upcoming milestones</p>
            <p className="text-xs mt-1">
              All deliverables are on track
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {allDeliverables.map((deliverable) => {
              const dueDate = deliverable.due_date
                ? new Date(deliverable.due_date)
                : null;
              const daysUntil = dueDate
                ? differenceInDays(dueDate, new Date())
                : null;
              const isOverdue = Boolean(deliverable.is_overdue) || (daysUntil !== null && daysUntil < 0);

              const getUrgencyColor = () => {
                if (isOverdue) return "bg-red-50 border-red-200";
                if (daysUntil !== null && daysUntil <= 2) return "bg-orange-50 border-orange-200";
                if (daysUntil !== null && daysUntil <= 7) return "bg-yellow-50 border-yellow-200";
                return "bg-gray-50 border-gray-200";
              };

              return (
                <div
                  key={deliverable.deliverable_id}
                  className={`p-3 rounded-lg border ${getUrgencyColor()}`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        {isOverdue && (
                          <AlertTriangle className="h-4 w-4 text-red-500 flex-shrink-0" />
                        )}
                        <p className="font-medium text-sm truncate">
                          {deliverable.deliverable_name || deliverable.phase || "Unnamed milestone"}
                        </p>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        {deliverable.project_code}
                        {deliverable.phase && ` - ${deliverable.phase}`}
                      </p>
                      {deliverable.project_title && (
                        <p className="text-xs text-blue-600 mt-0.5 truncate">
                          {deliverable.project_title}
                        </p>
                      )}
                      {deliverable.assigned_pm && (
                        <p className="text-xs text-muted-foreground mt-0.5">
                          Assigned: {deliverable.assigned_pm}
                        </p>
                      )}
                    </div>
                    <div className="flex flex-col items-end gap-1">
                      {dueDate && (
                        <Badge
                          variant={isOverdue ? "destructive" : daysUntil !== null && daysUntil <= 2 ? "default" : "outline"}
                          className="flex-shrink-0 text-xs"
                        >
                          {isOverdue
                            ? `${Math.abs(daysUntil!)}d overdue`
                            : format(dueDate, "MMM d")}
                        </Badge>
                      )}
                      {deliverable.priority === "high" && (
                        <Badge variant="outline" className="text-xs bg-amber-100 text-amber-700 border-amber-200">
                          High
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
            {(upcomingDeliverables.length + overdueDeliverables.length) > 8 && (
              <p className="text-xs text-center text-muted-foreground pt-2">
                + {(upcomingDeliverables.length + overdueDeliverables.length) - 8} more milestones
              </p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function MilestonesSkeleton() {
  return (
    <Card className="h-full">
      <CardHeader>
        <div className="h-6 w-40 bg-gray-200 rounded animate-pulse" />
      </CardHeader>
      <CardContent className="space-y-2">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i} className="h-16 bg-gray-100 rounded animate-pulse" />
        ))}
      </CardContent>
    </Card>
  );
}
