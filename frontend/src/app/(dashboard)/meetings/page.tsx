"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { format, startOfWeek, endOfWeek, addDays, isToday, isSameDay, startOfMonth, endOfMonth, isSameMonth, addMonths } from "date-fns";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Calendar,
  Clock,
  MapPin,
  Users,
  ChevronLeft,
  ChevronRight,
  Video,
  AlertCircle,
  CalendarDays,
  FileText,
  CheckCircle2,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import { ds } from "@/lib/design-system";
import { api } from "@/lib/api";

type Meeting = Awaited<ReturnType<typeof api.getMeetings>>["meetings"][number];

// Get meeting type badge color
function getMeetingTypeColor(type?: string): string {
  switch (type?.toLowerCase()) {
    case "client":
      return "bg-blue-50 text-blue-700 border-blue-200";
    case "internal":
      return "bg-slate-50 text-slate-700 border-slate-200";
    case "site_visit":
      return "bg-emerald-50 text-emerald-700 border-emerald-200";
    case "review":
      return "bg-purple-50 text-purple-700 border-purple-200";
    default:
      return "bg-slate-50 text-slate-700 border-slate-200";
  }
}

// Get status badge
function getStatusBadge(status?: string) {
  switch (status?.toLowerCase()) {
    case "completed":
      return <Badge variant="outline" className="bg-emerald-50 text-emerald-700 border-emerald-200">Completed</Badge>;
    case "cancelled":
      return <Badge variant="outline" className="bg-slate-50 text-slate-500 border-slate-200">Cancelled</Badge>;
    case "upcoming":
      return <Badge variant="outline" className="bg-amber-50 text-amber-700 border-amber-200">Upcoming</Badge>;
    default:
      return <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">Scheduled</Badge>;
  }
}

// Loading skeleton
function MeetingsSkeleton() {
  return (
    <div className="space-y-4">
      {[...Array(5)].map((_, i) => (
        <Card key={i} className={cn(ds.borderRadius.card, "border-slate-200")}>
          <CardContent className="p-4">
            <div className="flex items-start gap-4">
              <Skeleton className="h-12 w-12 rounded-lg" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-5 w-3/4" />
                <Skeleton className="h-4 w-1/2" />
                <Skeleton className="h-4 w-1/3" />
              </div>
              <Skeleton className="h-6 w-20" />
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

// Empty state
function EmptyState({ message }: { message: string }) {
  return (
    <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
      <CardContent className="py-16 text-center">
        <CalendarDays className="mx-auto h-16 w-16 text-slate-300 mb-4" />
        <p className={cn(ds.typography.heading3, ds.textColors.primary, "mb-2")}>
          {message}
        </p>
        <p className={cn(ds.typography.body, ds.textColors.tertiary)}>
          Suspiciously quiet. Is everyone on holiday?
        </p>
      </CardContent>
    </Card>
  );
}

// Error state
function ErrorState({ onRetry }: { onRetry: () => void }) {
  return (
    <Card className={cn(ds.borderRadius.card, "border-red-200 bg-red-50")}>
      <CardContent className="py-12 text-center">
        <AlertCircle className="mx-auto h-12 w-12 text-red-400 mb-4" />
        <p className={cn(ds.typography.heading3, "text-red-700 mb-2")}>
          Failed to load meetings
        </p>
        <p className={cn(ds.typography.body, "text-red-600 mb-4")}>
          The calendar gremlins are at it again. Try again?
        </p>
        <Button onClick={onRetry} variant="outline" className="border-red-200 text-red-700 hover:bg-red-100">
          Try Again
        </Button>
      </CardContent>
    </Card>
  );
}

// Meeting card component
function MeetingCard({ meeting, onClick }: { meeting: Meeting; onClick?: () => void }) {
  const startDate = new Date(meeting.start_time);
  const isUpcoming = startDate > new Date();

  return (
    <Card
      className={cn(
        ds.borderRadius.card,
        "border-slate-200 hover:border-slate-300 transition-colors cursor-pointer",
        isToday(startDate) && "border-teal-300 bg-teal-50/30"
      )}
      onClick={onClick}
    >
      <CardContent className="p-4">
        <div className="flex items-start gap-4">
          {/* Date block */}
          <div className={cn(
            "flex flex-col items-center justify-center w-14 h-14 rounded-lg",
            isToday(startDate) ? "bg-teal-600 text-white" : "bg-slate-100 text-slate-700"
          )}>
            <span className="text-xs font-medium uppercase">
              {format(startDate, "MMM")}
            </span>
            <span className="text-xl font-bold">
              {format(startDate, "d")}
            </span>
          </div>

          {/* Meeting details */}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <div className="flex items-center gap-2">
                <h3 className={cn(ds.typography.bodyBold, ds.textColors.primary, "truncate")}>
                  {meeting.title}
                </h3>
                {meeting.has_polished_summary ? (
                  <Badge className="bg-emerald-100 text-emerald-700 text-xs">
                    <FileText className="h-3 w-3 mr-1" /> Full Notes
                  </Badge>
                ) : meeting.has_transcript ? (
                  <Badge className="bg-purple-100 text-purple-700 text-xs">
                    <FileText className="h-3 w-3 mr-1" /> Notes
                  </Badge>
                ) : null}
              </div>
              {getStatusBadge(isUpcoming ? "upcoming" : meeting.status)}
            </div>

            <div className="flex flex-wrap items-center gap-3 mt-2 text-sm text-slate-600">
              <span className="flex items-center gap-1">
                <Clock className="h-3.5 w-3.5" />
                {format(startDate, "h:mm a")}
                {meeting.end_time && ` - ${format(new Date(meeting.end_time), "h:mm a")}`}
              </span>

              {meeting.location && (
                <span className="flex items-center gap-1">
                  {meeting.is_virtual ? <Video className="h-3.5 w-3.5" /> : <MapPin className="h-3.5 w-3.5" />}
                  {meeting.location}
                </span>
              )}

              {meeting.project_code && (
                <Badge variant="outline" className="text-xs">
                  {meeting.project_code}
                </Badge>
              )}
            </div>

            {meeting.attendees && meeting.attendees.length > 0 && (
              <div className="flex items-center gap-1 mt-2 text-sm text-slate-500">
                <Users className="h-3.5 w-3.5" />
                <span>{meeting.attendees.length} attendee{meeting.attendees.length !== 1 ? "s" : ""}</span>
              </div>
            )}

            {meeting.description && (
              <p className={cn(ds.typography.caption, ds.textColors.tertiary, "mt-2 line-clamp-2")}>
                {meeting.description}
              </p>
            )}
          </div>

          {/* Meeting type badge */}
          {meeting.meeting_type && (
            <Badge variant="outline" className={cn("text-xs", getMeetingTypeColor(meeting.meeting_type))}>
              {meeting.meeting_type.replace("_", " ")}
            </Badge>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// Week calendar view
function WeekCalendar({
  meetings,
  currentDate,
  onDateChange
}: {
  meetings: Meeting[];
  currentDate: Date;
  onDateChange: (date: Date) => void;
}) {
  const weekStart = startOfWeek(currentDate, { weekStartsOn: 1 });
  const weekEnd = endOfWeek(currentDate, { weekStartsOn: 1 });
  const days = [];

  for (let i = 0; i < 7; i++) {
    days.push(addDays(weekStart, i));
  }

  const getMeetingsForDay = (date: Date) => {
    return meetings.filter(m => isSameDay(new Date(m.start_time), date));
  };

  return (
    <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className={cn(ds.typography.heading3, ds.textColors.primary)}>
            Week of {format(weekStart, "MMM d")} - {format(weekEnd, "MMM d, yyyy")}
          </CardTitle>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onDateChange(addDays(currentDate, -7))}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onDateChange(new Date())}
            >
              Today
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onDateChange(addDays(currentDate, 7))}
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-7 gap-2">
          {days.map((day) => {
            const dayMeetings = getMeetingsForDay(day);
            const isCurrentDay = isToday(day);

            return (
              <div
                key={day.toISOString()}
                className={cn(
                  "min-h-[120px] p-2 rounded-lg border",
                  isCurrentDay ? "border-teal-300 bg-teal-50" : "border-slate-200 bg-slate-50/50"
                )}
              >
                <div className={cn(
                  "text-center mb-2",
                  isCurrentDay ? "text-teal-700" : "text-slate-600"
                )}>
                  <div className="text-xs font-medium uppercase">
                    {format(day, "EEE")}
                  </div>
                  <div className={cn(
                    "text-lg font-bold",
                    isCurrentDay && "text-teal-700"
                  )}>
                    {format(day, "d")}
                  </div>
                </div>

                <div className="space-y-1">
                  {dayMeetings.slice(0, 3).map((meeting) => (
                    <div
                      key={meeting.id}
                      className={cn(
                        "text-xs p-1.5 rounded truncate",
                        getMeetingTypeColor(meeting.meeting_type)
                      )}
                      title={meeting.title}
                    >
                      {format(new Date(meeting.start_time), "h:mm")} {meeting.title}
                    </div>
                  ))}
                  {dayMeetings.length > 3 && (
                    <div className="text-xs text-slate-500 text-center">
                      +{dayMeetings.length - 3} more
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

// Month calendar view
function MonthCalendar({
  meetings,
  currentDate,
  onDateChange
}: {
  meetings: Meeting[];
  currentDate: Date;
  onDateChange: (date: Date) => void;
}) {
  const monthStart = startOfMonth(currentDate);
  const monthEnd = endOfMonth(currentDate);
  const calendarStart = startOfWeek(monthStart, { weekStartsOn: 1 });
  const calendarEnd = endOfWeek(monthEnd, { weekStartsOn: 1 });

  const days: Date[] = [];
  let day = calendarStart;
  while (day <= calendarEnd) {
    days.push(day);
    day = addDays(day, 1);
  }

  const getMeetingsForDay = (date: Date) => {
    return meetings.filter(m => isSameDay(new Date(m.start_time), date));
  };

  const weeks: Date[][] = [];
  for (let i = 0; i < days.length; i += 7) {
    weeks.push(days.slice(i, i + 7));
  }

  return (
    <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className={cn(ds.typography.heading3, ds.textColors.primary)}>
            {format(currentDate, "MMMM yyyy")}
          </CardTitle>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onDateChange(addMonths(currentDate, -1))}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onDateChange(new Date())}
            >
              Today
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onDateChange(addMonths(currentDate, 1))}
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {/* Day headers */}
        <div className="grid grid-cols-7 gap-1 mb-2">
          {["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map((dayName) => (
            <div key={dayName} className="text-center text-xs font-medium text-slate-500 py-2">
              {dayName}
            </div>
          ))}
        </div>

        {/* Calendar grid */}
        <div className="space-y-1">
          {weeks.map((week, weekIndex) => (
            <div key={weekIndex} className="grid grid-cols-7 gap-1">
              {week.map((day) => {
                const dayMeetings = getMeetingsForDay(day);
                const isCurrentDay = isToday(day);
                const isCurrentMonth = isSameMonth(day, currentDate);

                return (
                  <div
                    key={day.toISOString()}
                    className={cn(
                      "min-h-[80px] p-1 rounded-lg border",
                      !isCurrentMonth && "opacity-40",
                      isCurrentDay ? "border-teal-300 bg-teal-50" : "border-slate-100 bg-white"
                    )}
                  >
                    <div className={cn(
                      "text-xs font-medium mb-1",
                      isCurrentDay ? "text-teal-700" : "text-slate-600"
                    )}>
                      {format(day, "d")}
                    </div>
                    <div className="space-y-0.5">
                      {dayMeetings.slice(0, 2).map((meeting) => (
                        <div
                          key={meeting.id}
                          className={cn(
                            "text-[10px] px-1 py-0.5 rounded truncate",
                            getMeetingTypeColor(meeting.meeting_type)
                          )}
                          title={`${format(new Date(meeting.start_time), "h:mm a")} - ${meeting.title}`}
                        >
                          {meeting.title}
                        </div>
                      ))}
                      {dayMeetings.length > 2 && (
                        <div className="text-[10px] text-slate-500 text-center">
                          +{dayMeetings.length - 2}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

// Helper to parse JSON fields from transcript
function parseJsonField(field: string | null | undefined): unknown[] {
  if (!field) return [];
  try {
    const parsed = JSON.parse(field);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

// Extract display text from action item (can be string or object with task field)
function getActionItemText(item: unknown): string {
  if (typeof item === 'string') return item;
  if (item && typeof item === 'object' && 'task' in item) return (item as { task: string }).task;
  return String(item);
}

export default function MeetingsPage() {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [activeTab, setActiveTab] = useState<"upcoming" | "past">("upcoming");
  const [viewMode, setViewMode] = useState<"week" | "month">("week");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [selectedMeeting, setSelectedMeeting] = useState<Meeting | null>(null);

  // Fetch all meetings
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["meetings"],
    queryFn: () => api.getMeetings(),
    staleTime: 1000 * 60 * 5,
  });
  const meetings = data?.meetings ?? [];

  // Apply type filter
  const filteredMeetings = typeFilter === "all"
    ? meetings
    : meetings.filter(m => m.meeting_type?.toLowerCase() === typeFilter);

  // Filter meetings by tab
  const now = new Date();
  const upcomingMeetings = filteredMeetings
    .filter(m => new Date(m.start_time) >= now)
    .sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime());

  const pastMeetings = filteredMeetings
    .filter(m => new Date(m.start_time) < now)
    .sort((a, b) => new Date(b.start_time).getTime() - new Date(a.start_time).getTime());

  // Stats
  const todayMeetings = meetings.filter(m => isToday(new Date(m.start_time)));
  const thisWeekMeetings = meetings.filter(m => {
    const meetingDate = new Date(m.start_time);
    const weekStart = startOfWeek(now, { weekStartsOn: 1 });
    const weekEnd = endOfWeek(now, { weekStartsOn: 1 });
    return meetingDate >= weekStart && meetingDate <= weekEnd;
  });

  return (
    <div className="space-y-6 w-full max-w-full overflow-x-hidden">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className={cn(ds.typography.heading1, ds.textColors.primary)}>
            Meetings
          </h1>
          <p className={cn(ds.typography.body, ds.textColors.secondary, "mt-1")}>
            Your schedule at a glance. Never miss the important ones.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="gap-1">
            <Calendar className="h-3.5 w-3.5" />
            {format(new Date(), "EEEE, MMM d")}
          </Badge>
        </div>
      </div>

      {/* View Controls */}
      <div className="flex flex-wrap items-center gap-4">
        <div className="flex items-center gap-2 bg-slate-100 rounded-lg p-1">
          <Button
            variant={viewMode === "week" ? "default" : "ghost"}
            size="sm"
            onClick={() => setViewMode("week")}
          >
            Week
          </Button>
          <Button
            variant={viewMode === "month" ? "default" : "ghost"}
            size="sm"
            onClick={() => setViewMode("month")}
          >
            Month
          </Button>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-sm text-slate-500">Type:</span>
          <div className="flex gap-1">
            {["all", "client", "internal", "site_visit", "review"].map((type) => (
              <Badge
                key={type}
                variant={typeFilter === type ? "default" : "outline"}
                className={cn(
                  "cursor-pointer transition-colors",
                  typeFilter === type ? "" : getMeetingTypeColor(type === "all" ? undefined : type)
                )}
                onClick={() => setTypeFilter(type)}
              >
                {type === "all" ? "All" : type.replace("_", " ")}
              </Badge>
            ))}
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-teal-100">
                <CalendarDays className="h-5 w-5 text-teal-700" />
              </div>
              <div>
                <p className={cn(ds.typography.caption, ds.textColors.tertiary)}>Today</p>
                <p className={cn(ds.typography.heading2, ds.textColors.primary)}>
                  {isLoading ? "—" : todayMeetings.length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-100">
                <Calendar className="h-5 w-5 text-blue-700" />
              </div>
              <div>
                <p className={cn(ds.typography.caption, ds.textColors.tertiary)}>This Week</p>
                <p className={cn(ds.typography.heading2, ds.textColors.primary)}>
                  {isLoading ? "—" : thisWeekMeetings.length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-amber-100">
                <Clock className="h-5 w-5 text-amber-700" />
              </div>
              <div>
                <p className={cn(ds.typography.caption, ds.textColors.tertiary)}>Upcoming</p>
                <p className={cn(ds.typography.heading2, ds.textColors.primary)}>
                  {isLoading ? "—" : upcomingMeetings.length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Calendar View */}
      {!isLoading && !error && (
        viewMode === "week" ? (
          <WeekCalendar
            meetings={filteredMeetings}
            currentDate={currentDate}
            onDateChange={setCurrentDate}
          />
        ) : (
          <MonthCalendar
            meetings={filteredMeetings}
            currentDate={currentDate}
            onDateChange={setCurrentDate}
          />
        )
      )}

      {/* Meeting List */}
      <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as "upcoming" | "past")}>
        <TabsList>
          <TabsTrigger value="upcoming">
            Upcoming ({upcomingMeetings.length})
          </TabsTrigger>
          <TabsTrigger value="past">
            Past ({pastMeetings.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="upcoming" className="mt-4">
          {isLoading ? (
            <MeetingsSkeleton />
          ) : error ? (
            <ErrorState onRetry={() => refetch()} />
          ) : upcomingMeetings.length === 0 ? (
            <EmptyState message="No upcoming meetings" />
          ) : (
            <div className="space-y-3">
              {upcomingMeetings.map((meeting) => (
                <MeetingCard key={meeting.id} meeting={meeting} onClick={() => setSelectedMeeting(meeting)} />
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="past" className="mt-4">
          {isLoading ? (
            <MeetingsSkeleton />
          ) : error ? (
            <ErrorState onRetry={() => refetch()} />
          ) : pastMeetings.length === 0 ? (
            <EmptyState message="No past meetings" />
          ) : (
            <div className="space-y-3">
              {pastMeetings.map((meeting) => (
                <MeetingCard key={meeting.id} meeting={meeting} onClick={() => setSelectedMeeting(meeting)} />
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Meeting Detail Modal */}
      <Dialog open={!!selectedMeeting} onOpenChange={(open) => !open && setSelectedMeeting(null)}>
        <DialogContent className="max-w-2xl max-h-[85vh]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {selectedMeeting?.title}
              {selectedMeeting?.has_polished_summary ? (
                <Badge className="bg-emerald-100 text-emerald-700">
                  <FileText className="h-3 w-3 mr-1" /> Full Notes
                </Badge>
              ) : selectedMeeting?.has_transcript ? (
                <Badge className="bg-purple-100 text-purple-700">
                  <FileText className="h-3 w-3 mr-1" /> Has Meeting Notes
                </Badge>
              ) : null}
            </DialogTitle>
          </DialogHeader>
          <ScrollArea className="max-h-[60vh]">
            {selectedMeeting && (
              <div className="space-y-4 pr-4">
                {/* Meeting Info */}
                <div className="grid grid-cols-2 gap-4 p-4 bg-slate-50 rounded-lg">
                  <div>
                    <p className="text-xs font-medium text-slate-500 uppercase">Date</p>
                    <p className="text-sm text-slate-900">
                      {format(new Date(selectedMeeting.start_time), "EEEE, MMMM d, yyyy")}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs font-medium text-slate-500 uppercase">Time</p>
                    <p className="text-sm text-slate-900">
                      {format(new Date(selectedMeeting.start_time), "h:mm a")}
                      {selectedMeeting.end_time && ` - ${format(new Date(selectedMeeting.end_time), "h:mm a")}`}
                    </p>
                  </div>
                  {selectedMeeting.meeting_type && (
                    <div>
                      <p className="text-xs font-medium text-slate-500 uppercase">Type</p>
                      <Badge variant="outline" className={cn("text-xs", getMeetingTypeColor(selectedMeeting.meeting_type))}>
                        {selectedMeeting.meeting_type.replace(/_/g, " ")}
                      </Badge>
                    </div>
                  )}
                  {selectedMeeting.project_code && (
                    <div>
                      <p className="text-xs font-medium text-slate-500 uppercase">Project</p>
                      <Badge variant="outline" className="text-xs">
                        {selectedMeeting.project_code}
                      </Badge>
                    </div>
                  )}
                  {selectedMeeting.location && (
                    <div className="col-span-2">
                      <p className="text-xs font-medium text-slate-500 uppercase">Location</p>
                      <p className="text-sm text-slate-900 flex items-center gap-1">
                        <MapPin className="h-3 w-3" />
                        {selectedMeeting.location}
                      </p>
                    </div>
                  )}
                </div>

                {/* Polished Summary (preferred) or Transcript Summary */}
                {(selectedMeeting.transcript_polished_summary || selectedMeeting.transcript_summary) && (
                  <div className="space-y-3">
                    <h3 className={cn(
                      "text-sm font-semibold flex items-center gap-2",
                      selectedMeeting.transcript_polished_summary ? "text-emerald-800" : "text-purple-800"
                    )}>
                      <FileText className="h-4 w-4" />
                      {selectedMeeting.transcript_polished_summary ? "Meeting Notes" : "Meeting Summary"}
                    </h3>
                    <div className={cn(
                      "p-4 rounded-lg border",
                      selectedMeeting.transcript_polished_summary
                        ? "bg-slate-50 border-slate-200"
                        : "bg-purple-50 border-purple-100"
                    )}>
                      <div className="text-sm text-slate-700 whitespace-pre-wrap font-mono leading-relaxed">
                        {selectedMeeting.transcript_polished_summary || selectedMeeting.transcript_summary}
                      </div>
                    </div>

                    {/* Key Points - only show if no polished summary */}
                    {!selectedMeeting.transcript_polished_summary && selectedMeeting.transcript_key_points && parseJsonField(selectedMeeting.transcript_key_points).length > 0 && (
                      <div>
                        <h4 className="text-xs font-semibold text-purple-700 uppercase mb-2">Key Points</h4>
                        <ul className="space-y-1">
                          {parseJsonField(selectedMeeting.transcript_key_points).map((point, i) => (
                            <li key={i} className="text-sm text-slate-600 flex items-start gap-2">
                              <span className="text-purple-400 mt-1">•</span>
                              <span>{String(point)}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Action Items - only show if no polished summary */}
                    {!selectedMeeting.transcript_polished_summary && selectedMeeting.transcript_action_items && parseJsonField(selectedMeeting.transcript_action_items).length > 0 && (
                      <div>
                        <h4 className="text-xs font-semibold text-purple-700 uppercase mb-2">Action Items</h4>
                        <ul className="space-y-1">
                          {parseJsonField(selectedMeeting.transcript_action_items).map((item, i) => (
                            <li key={i} className="text-sm text-slate-600 flex items-start gap-2">
                              <CheckCircle2 className="h-4 w-4 text-purple-400 mt-0.5 flex-shrink-0" />
                              <span>{getActionItemText(item)}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}

                {/* Description if no transcript */}
                {!selectedMeeting.transcript_summary && !selectedMeeting.transcript_polished_summary && selectedMeeting.description && (
                  <div className="p-4 bg-slate-50 rounded-lg">
                    <h3 className="text-xs font-semibold text-slate-500 uppercase mb-2">Description</h3>
                    <p className="text-sm text-slate-700">{selectedMeeting.description}</p>
                  </div>
                )}
              </div>
            )}
          </ScrollArea>
          <DialogFooter>
            <Button variant="outline" onClick={() => setSelectedMeeting(null)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
