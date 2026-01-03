"use client";

import { useQuery } from "@tanstack/react-query";
import { format, startOfWeek, addDays, isToday, parseISO } from "date-fns";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import { Calendar, Clock, User } from "lucide-react";
import { cn } from "@/lib/utils";

interface WeeklyScheduleGridProps {
  projectCode: string;
}

interface ScheduleEntry {
  entry_id: number;
  schedule_date: string;
  staff_name: string | null;
  nickname: string | null;
  discipline: string | null;
  phase: string | null;
  activity_type: string | null;
  hours_worked: number | null;
}

export function WeeklyScheduleGrid({ projectCode }: WeeklyScheduleGridProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["project-schedule", projectCode, 30],
    queryFn: () => api.getProjectSchedule(projectCode, 30),
    staleTime: 1000 * 60 * 5,
  });

  if (isLoading) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-base">
            <Calendar className="h-4 w-4 text-purple-600" />
            Weekly Schedule
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {[1, 2, 3, 4, 5].map((i) => (
              <Skeleton key={i} className="h-16 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  const entries = (data?.entries ?? []) as ScheduleEntry[];

  if (entries.length === 0) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-base">
            <Calendar className="h-4 w-4 text-purple-600" />
            Weekly Schedule
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-sm text-slate-500">
            No schedule entries found for this project
          </div>
        </CardContent>
      </Card>
    );
  }

  // Group entries by staff member
  const staffSchedules = new Map<string, ScheduleEntry[]>();
  entries.forEach((entry) => {
    const name = entry.staff_name || entry.nickname || "Unknown";
    if (!staffSchedules.has(name)) {
      staffSchedules.set(name, []);
    }
    staffSchedules.get(name)!.push(entry);
  });

  // Get the week's dates (Mon-Fri)
  const today = new Date();
  const weekStart = startOfWeek(today, { weekStartsOn: 1 }); // Monday
  const weekDays = Array.from({ length: 5 }, (_, i) => addDays(weekStart, i));

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-base">
            <Calendar className="h-4 w-4 text-purple-600" />
            Weekly Schedule
          </CardTitle>
          <Badge variant="secondary">
            {staffSchedules.size} staff • {entries.length} entries
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200">
                <th className="text-left py-2 px-3 font-medium text-slate-500 w-32">Team Member</th>
                {weekDays.map((day) => (
                  <th
                    key={day.toISOString()}
                    className={cn(
                      "text-center py-2 px-2 font-medium text-slate-500",
                      isToday(day) && "bg-teal-50"
                    )}
                  >
                    <div className="text-xs">{format(day, "EEE")}</div>
                    <div className={cn("text-sm", isToday(day) && "text-teal-600 font-bold")}>
                      {format(day, "d")}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {Array.from(staffSchedules.entries()).map(([staffName, staffEntries]) => (
                <tr key={staffName} className="border-b border-slate-100 hover:bg-slate-50">
                  <td className="py-2 px-3">
                    <div className="flex items-center gap-2">
                      <div className="h-7 w-7 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 font-medium text-xs">
                        {staffName.charAt(0)}
                      </div>
                      <span className="font-medium text-slate-900 truncate max-w-[100px]">
                        {staffName}
                      </span>
                    </div>
                  </td>
                  {weekDays.map((day) => {
                    const dayStr = format(day, "yyyy-MM-dd");
                    const dayEntry = staffEntries.find((e) => e.schedule_date === dayStr);
                    return (
                      <td
                        key={day.toISOString()}
                        className={cn(
                          "py-1 px-1 text-center align-top",
                          isToday(day) && "bg-teal-50/50"
                        )}
                      >
                        {dayEntry ? (
                          <div className="p-1.5 rounded bg-slate-100 text-xs">
                            <p className="font-medium text-slate-700 truncate">
                              {dayEntry.activity_type || dayEntry.phase || "Assigned"}
                            </p>
                            {dayEntry.phase && dayEntry.activity_type && (
                              <Badge variant="outline" className="mt-1 text-xs px-1 py-0">
                                {dayEntry.phase}
                              </Badge>
                            )}
                          </div>
                        ) : (
                          <span className="text-slate-300">—</span>
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Summary */}
        <div className="mt-4 pt-4 border-t border-slate-200">
          <div className="flex items-center gap-4 text-sm text-slate-500">
            <div className="flex items-center gap-1">
              <User className="h-4 w-4" />
              <span>{data?.summary?.staff_involved?.length ?? 0} team members</span>
            </div>
            {data?.summary?.phases_worked && data.summary.phases_worked.length > 0 && (
              <div className="flex items-center gap-1">
                <Clock className="h-4 w-4" />
                <span>Phases: {data.summary.phases_worked.join(", ")}</span>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
