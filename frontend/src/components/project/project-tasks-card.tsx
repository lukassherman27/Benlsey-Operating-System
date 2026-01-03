"use client";

import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ClipboardList, AlertTriangle, Clock, CheckCircle2, CalendarDays } from "lucide-react";
import { format, parseISO, isValid, differenceInDays } from "date-fns";
import { cn } from "@/lib/utils";
import { ds } from "@/lib/design-system";
import { api } from "@/lib/api";

interface Deliverable {
  deliverable_id: number;
  deliverable_name: string;
  deliverable_type?: string;
  phase?: string;
  due_date?: string;
  status: string;
  priority?: string;
  assigned_pm?: string;
  days_until_due?: number;
  is_overdue?: number;
  days_overdue?: number;
}

interface DeliverablesResponse {
  success: boolean;
  deliverables: Deliverable[];
  count: number;
}

interface ProjectTasksCardProps {
  projectCode: string;
  maxItems?: number;
}

const formatDate = (dateStr?: string) => {
  if (!dateStr) return "No date";
  try {
    const date = parseISO(dateStr);
    if (!isValid(date)) return dateStr;
    return format(date, "MMM d, yyyy");
  } catch {
    return dateStr;
  }
};

const getUrgencyStyle = (dueDate?: string, status?: string) => {
  if (status === "completed" || status === "approved") {
    return { badge: ds.badges.success, label: "Done", icon: CheckCircle2 };
  }

  if (!dueDate) {
    return { badge: ds.badges.neutral, label: "No date", icon: CalendarDays };
  }

  try {
    const due = parseISO(dueDate);
    if (!isValid(due)) return { badge: ds.badges.neutral, label: "No date", icon: CalendarDays };

    const daysUntil = differenceInDays(due, new Date());

    if (daysUntil < 0) {
      return { badge: ds.badges.danger, label: `${Math.abs(daysUntil)}d overdue`, icon: AlertTriangle };
    }
    if (daysUntil === 0) {
      return { badge: ds.badges.danger, label: "Due today", icon: AlertTriangle };
    }
    if (daysUntil <= 7) {
      return { badge: ds.badges.warning, label: `${daysUntil}d left`, icon: Clock };
    }
    return { badge: ds.badges.info, label: `${daysUntil}d left`, icon: CalendarDays };
  } catch {
    return { badge: ds.badges.neutral, label: "No date", icon: CalendarDays };
  }
};

export function ProjectTasksCard({ projectCode, maxItems = 5 }: ProjectTasksCardProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["deliverables", projectCode],
    queryFn: () => api.getDeliverables({ project_code: projectCode }) as Promise<DeliverablesResponse>,
  });

  if (isLoading) {
    return (
      <Card className={ds.cards.default}>
        <CardContent className="p-6">
          <div className="animate-pulse space-y-3">
            <div className="h-5 w-32 bg-slate-200 rounded" />
            <div className="space-y-2">
              <div className="h-12 w-full bg-slate-200 rounded" />
              <div className="h-12 w-full bg-slate-200 rounded" />
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={ds.cards.default}>
        <CardContent className="p-6">
          <p className="text-sm text-slate-500">Could not load tasks</p>
        </CardContent>
      </Card>
    );
  }

  const deliverables = data?.deliverables || [];

  // Filter to pending/in_progress and sort by due date
  const pendingTasks = deliverables
    .filter((d) => d.status !== "completed" && d.status !== "approved")
    .sort((a, b) => {
      // Sort by due date (earliest first), nulls last
      if (!a.due_date && !b.due_date) return 0;
      if (!a.due_date) return 1;
      if (!b.due_date) return -1;
      return new Date(a.due_date).getTime() - new Date(b.due_date).getTime();
    })
    .slice(0, maxItems);

  // Count stats
  const overdue = deliverables.filter((d) => {
    if (d.status === "completed" || d.status === "approved") return false;
    if (!d.due_date) return false;
    try {
      return differenceInDays(parseISO(d.due_date), new Date()) < 0;
    } catch {
      return false;
    }
  }).length;

  const dueThisWeek = deliverables.filter((d) => {
    if (d.status === "completed" || d.status === "approved") return false;
    if (!d.due_date) return false;
    try {
      const daysUntil = differenceInDays(parseISO(d.due_date), new Date());
      return daysUntil >= 0 && daysUntil <= 7;
    } catch {
      return false;
    }
  }).length;

  const completed = deliverables.filter((d) => d.status === "completed" || d.status === "approved").length;
  const total = deliverables.length;

  return (
    <Card className={ds.cards.default}>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-base">
            <ClipboardList className="h-4 w-4 text-purple-600" />
            Pending Tasks
          </div>
          {total > 0 && (
            <Badge variant="secondary" className="text-xs font-normal">
              {completed}/{total} done
            </Badge>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        {/* Stats row */}
        {total > 0 && (
          <div className="flex gap-3 mb-4">
            {overdue > 0 && (
              <Badge className={ds.badges.danger}>
                <AlertTriangle className="h-3 w-3 mr-1" />
                {overdue} overdue
              </Badge>
            )}
            {dueThisWeek > 0 && (
              <Badge className={ds.badges.warning}>
                <Clock className="h-3 w-3 mr-1" />
                {dueThisWeek} this week
              </Badge>
            )}
          </div>
        )}

        {/* Task list */}
        {pendingTasks.length === 0 ? (
          <div className="text-center py-6">
            <CheckCircle2 className="h-8 w-8 mx-auto text-emerald-300 mb-2" />
            <p className="text-sm text-slate-500">
              {total === 0 ? "No tasks for this project" : "All tasks completed!"}
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {pendingTasks.map((task) => {
              const urgency = getUrgencyStyle(task.due_date, task.status);
              const UrgencyIcon = urgency.icon;

              return (
                <div
                  key={task.deliverable_id}
                  className="flex items-start gap-3 p-3 rounded-lg border border-slate-200 bg-slate-50/50 hover:bg-slate-50 transition-colors"
                >
                  <div className="flex-shrink-0 mt-0.5">
                    <UrgencyIcon className={cn(
                      "h-4 w-4",
                      urgency.badge.includes("danger") ? "text-red-600" :
                      urgency.badge.includes("warning") ? "text-amber-600" :
                      urgency.badge.includes("success") ? "text-emerald-600" :
                      "text-slate-400"
                    )} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-900 truncate">
                      {task.deliverable_name}
                    </p>
                    <div className="flex items-center gap-2 mt-1 flex-wrap">
                      {task.phase && (
                        <span className="text-xs text-slate-500">{task.phase}</span>
                      )}
                      {task.assigned_pm && (
                        <span className="text-xs text-slate-500">• {task.assigned_pm}</span>
                      )}
                    </div>
                  </div>
                  <div className="flex-shrink-0 text-right">
                    <Badge className={cn("text-xs", urgency.badge)}>
                      {urgency.label}
                    </Badge>
                    {task.due_date && (
                      <p className="text-xs text-slate-500 mt-1">
                        {formatDate(task.due_date)}
                      </p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
