"use client";

import { useQuery } from "@tanstack/react-query";
import { format, differenceInDays } from "date-fns";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Flag, Calendar, AlertTriangle, CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { ds } from "@/lib/design-system";

interface Milestone {
  milestone_id?: number;
  id?: number;
  title: string;
  status: string;
  due_date: string | null;
  is_overdue: number;
  days_until?: number;
}

interface MilestonesCardProps {
  projectCode: string;
  className?: string;
}

const formatDate = (dateStr: string | null) => {
  if (!dateStr) return "—";
  try {
    return format(new Date(dateStr), "MMM d, yyyy");
  } catch {
    return dateStr;
  }
};

export function MilestonesCard({ projectCode, className }: MilestonesCardProps) {
  const milestonesQuery = useQuery({
    queryKey: ["project-milestones", projectCode],
    queryFn: () => api.getProjectMilestones(projectCode),
    staleTime: 1000 * 60 * 5,
  });

  const milestones = milestonesQuery.data?.milestones ?? [];

  if (milestonesQuery.isLoading) {
    return (
      <Card className={cn(ds.cards.default, className)}>
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-base">
            <Flag className="h-4 w-4 text-purple-600" />
            Milestones
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (milestones.length === 0) {
    return (
      <Card className={cn(ds.cards.default, className)}>
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-base">
            <Flag className="h-4 w-4 text-purple-600" />
            Milestones
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-slate-500 text-center py-6">
            No milestones defined for this project
          </p>
        </CardContent>
      </Card>
    );
  }

  // Split into upcoming and completed
  const upcoming = (milestones as Milestone[]).filter((m) => m.status !== 'completed').slice(0, 5);
  const overdue = (milestones as Milestone[]).filter((m) => m.is_overdue === 1);

  return (
    <Card className={cn(ds.cards.default, className)}>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center justify-between">
          <span className="flex items-center gap-2 text-base">
            <Flag className="h-4 w-4 text-purple-600" />
            Milestones
          </span>
          {overdue.length > 0 && (
            <Badge variant="destructive" className="text-xs">
              {overdue.length} overdue
            </Badge>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="space-y-3">
          {upcoming.map((milestone) => {
            const isOverdue = milestone.is_overdue === 1;
            const daysUntil = milestone.days_until;

            return (
              <div
                key={milestone.milestone_id}
                className={cn(
                  "flex items-start justify-between p-3 rounded-lg transition-colors",
                  isOverdue ? "bg-red-50" : "bg-slate-50 hover:bg-slate-100"
                )}
              >
                <div className="flex items-start gap-3 min-w-0">
                  {milestone.status === 'completed' ? (
                    <CheckCircle2 className="h-4 w-4 text-emerald-600 mt-0.5 flex-shrink-0" />
                  ) : isOverdue ? (
                    <AlertTriangle className="h-4 w-4 text-red-600 mt-0.5 flex-shrink-0" />
                  ) : (
                    <Calendar className="h-4 w-4 text-slate-400 mt-0.5 flex-shrink-0" />
                  )}
                  <div className="min-w-0">
                    <p className={cn(
                      "text-sm font-medium truncate",
                      isOverdue ? "text-red-900" : "text-slate-900"
                    )}>
                      {milestone.milestone_name}
                    </p>
                    <div className="flex items-center gap-2 mt-0.5">
                      {milestone.phase && (
                        <Badge variant="outline" className="text-xs px-1.5 py-0">
                          {milestone.phase}
                        </Badge>
                      )}
                      <span className={cn(
                        "text-xs",
                        isOverdue ? "text-red-600" : "text-slate-500"
                      )}>
                        {formatDate(milestone.planned_date)}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="text-right flex-shrink-0 ml-2">
                  {milestone.status === 'completed' ? (
                    <span className="text-xs text-emerald-600 font-medium">Done</span>
                  ) : isOverdue && daysUntil ? (
                    <span className="text-xs text-red-600 font-medium">
                      {Math.abs(daysUntil)} days late
                    </span>
                  ) : daysUntil !== null ? (
                    <span className={cn(
                      "text-xs font-medium",
                      daysUntil <= 7 ? "text-amber-600" : "text-slate-600"
                    )}>
                      {daysUntil === 0 ? "Today" :
                       daysUntil === 1 ? "Tomorrow" :
                       `${daysUntil} days`}
                    </span>
                  ) : null}
                </div>
              </div>
            );
          })}
        </div>

        {milestones.length > 5 && (
          <p className="text-xs text-slate-500 text-center mt-3">
            +{milestones.length - 5} more milestones
          </p>
        )}
      </CardContent>
    </Card>
  );
}
