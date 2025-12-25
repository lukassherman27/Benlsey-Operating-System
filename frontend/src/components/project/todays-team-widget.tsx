"use client";

import { useQuery } from "@tanstack/react-query";
import { format, isToday, parseISO, isThisWeek, addDays } from "date-fns";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Users, Calendar, ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";

interface TodaysTeamWidgetProps {
  projectCode: string;
  className?: string;
}

const DAYS_OF_WEEK = ["Mon", "Tue", "Wed", "Thu", "Fri"];

interface StaffEntry {
  staff_name: string;
  role: string | null;
  department: string | null;
  work_date: string;
  phase: string | null;
  task_description: string | null;
}

export function TodaysTeamWidget({ projectCode, className }: TodaysTeamWidgetProps) {
  const scheduleQuery = useQuery({
    queryKey: ["project-schedule", projectCode, 14], // Last 14 days
    queryFn: () => api.getProjectSchedule(projectCode, 14),
    staleTime: 1000 * 60 * 5,
  });

  const entries = scheduleQuery.data?.entries || [];

  if (scheduleQuery.isLoading) {
    return (
      <Card className={cn("border-slate-200", className)}>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base">
            <Users className="h-4 w-4 text-blue-600" />
            Team Activity
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[1, 2, 3, 4].map((i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  // Group entries by date
  const entriesByDate: Record<string, StaffEntry[]> = {};
  entries.forEach((entry) => {
    const date = entry.work_date;
    if (!entriesByDate[date]) {
      entriesByDate[date] = [];
    }
    entriesByDate[date].push(entry as StaffEntry);
  });

  // Get most recent date with entries
  const dates = Object.keys(entriesByDate).sort().reverse();
  const mostRecentDate = dates[0];
  const todaysEntries = entriesByDate[mostRecentDate] || [];

  // Group today's work by staff
  const staffWork: Record<string, { tasks: string[]; phase: string }> = {};
  todaysEntries.forEach((entry) => {
    const name = entry.staff_name || "Unknown";
    if (!staffWork[name]) {
      staffWork[name] = { tasks: [], phase: entry.phase || "" };
    }
    if (entry.task_description) {
      staffWork[name].tasks.push(entry.task_description);
    }
    if (entry.phase && !staffWork[name].phase) {
      staffWork[name].phase = entry.phase;
    }
  });

  const staffList = Object.entries(staffWork);

  // Calculate stats
  const uniqueDates = dates.length;
  const uniqueStaff = new Set(entries.map(e => e.staff_name)).size;

  if (staffList.length === 0) {
    return (
      <Card className={cn("border-slate-200", className)}>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base">
            <Users className="h-4 w-4 text-blue-600" />
            Team Activity
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <Users className="h-10 w-10 text-slate-300 mx-auto mb-3" />
            <p className="text-sm text-slate-500">
              No recent team activity recorded
            </p>
            <p className="text-xs text-slate-400 mt-1">
              Schedule data will appear once imported
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={cn("border-slate-200", className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-base">
            <Users className="h-4 w-4 text-blue-600" />
            Team Activity
          </CardTitle>
          <Badge variant="outline" className="text-xs font-normal">
            {format(parseISO(mostRecentDate), "MMM d, yyyy")}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        {/* Staff on this date */}
        <div className="space-y-2">
          {staffList.slice(0, 8).map(([name, work]) => (
            <div
              key={name}
              className="flex items-center justify-between p-2.5 rounded-lg bg-slate-50 hover:bg-slate-100 transition-colors"
            >
              <div className="flex items-center gap-3 min-w-0">
                {/* Avatar */}
                <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                  <span className="text-xs font-semibold text-blue-700">
                    {name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()}
                  </span>
                </div>
                {/* Name & Task */}
                <div className="min-w-0">
                  <p className="text-sm font-medium text-slate-900 truncate">
                    {name}
                  </p>
                  <p className="text-xs text-slate-500 truncate">
                    {work.tasks[0] || work.phase || "Working on project"}
                  </p>
                </div>
              </div>
              {/* Phase badge */}
              {work.phase && (
                <Badge variant="secondary" className="text-xs px-1.5 py-0 flex-shrink-0">
                  {work.phase}
                </Badge>
              )}
            </div>
          ))}
        </div>

        {staffList.length > 8 && (
          <p className="text-xs text-slate-500 text-center mt-3">
            +{staffList.length - 8} more team members
          </p>
        )}

        {/* Stats footer */}
        <div className="mt-4 pt-3 border-t border-slate-100">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span>{uniqueStaff} team members</span>
            <span>{uniqueDates} work days recorded</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
