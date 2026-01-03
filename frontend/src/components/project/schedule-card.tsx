"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Users, Calendar, Briefcase } from "lucide-react";
import { cn } from "@/lib/utils";
import { ds } from "@/lib/design-system";

interface StaffSummary {
  name: string;
  hours: number;
  phases: string[];
  role?: string;
  department?: string;
  days_worked?: number;
}

interface ScheduleResponse {
  success: boolean;
  project_code: string;
  days: number;
  entries: Array<{
    entry_id: number;
    schedule_date: string;
    staff_name: string | null;
    discipline: string | null;
    phase: string | null;
    activity_type: string | null;
    hours_worked: number | null;
  }>;
  summary: {
    total_hours: number;
    unique_staff: number;
  };
  staff_summary?: StaffSummary[];
  unique_staff?: number;
  total_entries?: number;
}

interface ScheduleCardProps {
  projectCode: string;
  days?: number;
  className?: string;
}

export function ScheduleCard({ projectCode, days = 90, className }: ScheduleCardProps) {
  const scheduleQuery = useQuery({
    queryKey: ["project-schedule", projectCode, days],
    queryFn: () => api.getProjectSchedule(projectCode, days) as unknown as Promise<ScheduleResponse>,
    staleTime: 1000 * 60 * 5,
  });

  const schedule = scheduleQuery.data;
  const staffSummary: StaffSummary[] = schedule?.staff_summary ?? [];

  if (scheduleQuery.isLoading) {
    return (
      <Card className={cn(ds.cards.default, className)}>
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-base">
            <Users className="h-4 w-4 text-blue-600" />
            Team Schedule
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-16 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (staffSummary.length === 0) {
    return (
      <Card className={cn(ds.cards.default, className)}>
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-base">
            <Users className="h-4 w-4 text-blue-600" />
            Team Schedule
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-slate-500 text-center py-6">
            No schedule data available for this project
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={cn(ds.cards.default, className)}>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center justify-between">
          <span className="flex items-center gap-2 text-base">
            <Users className="h-4 w-4 text-blue-600" />
            Team Schedule
          </span>
          <Badge variant="secondary" className="text-xs">
            {schedule?.unique_staff ?? 0} people
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="space-y-3">
          {staffSummary.slice(0, 8).map((staff) => (
            <div
              key={staff.name}
              className="flex items-center justify-between p-3 rounded-lg bg-slate-50 hover:bg-slate-100 transition-colors"
            >
              <div className="flex items-center gap-3">
                <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center">
                  <span className="text-xs font-semibold text-blue-700">
                    {staff.name?.split(' ').map(n => n[0]).join('').slice(0, 2) || '?'}
                  </span>
                </div>
                <div>
                  <p className="text-sm font-medium text-slate-900">
                    {staff.name?.trim() || 'Unknown'}
                  </p>
                  <p className="text-xs text-slate-500">
                    {staff.role || staff.department || 'Team Member'}
                  </p>
                </div>
              </div>
              <div className="text-right">
                <div className="flex items-center gap-1 text-xs text-slate-600">
                  <Calendar className="h-3 w-3" />
                  <span>{staff.days_worked} days</span>
                </div>
                {staff.phases.length > 0 && (
                  <div className="flex gap-1 mt-1">
                    {staff.phases.slice(0, 2).map((phase) => (
                      <Badge key={phase} variant="outline" className="text-xs px-1.5 py-0">
                        {phase}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {staffSummary.length > 8 && (
          <p className="text-xs text-slate-500 text-center mt-3">
            +{staffSummary.length - 8} more team members
          </p>
        )}

        {schedule?.total_entries && (
          <div className="mt-4 pt-3 border-t border-slate-100">
            <div className="flex items-center justify-between text-xs text-slate-500">
              <span className="flex items-center gap-1">
                <Briefcase className="h-3 w-3" />
                Last {days} days
              </span>
              <span>{schedule.total_entries} work entries</span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
