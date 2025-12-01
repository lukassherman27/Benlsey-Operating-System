"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { format, startOfWeek, endOfWeek, addDays, isToday, isSameDay } from "date-fns";
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
} from "lucide-react";
import { cn } from "@/lib/utils";
import { ds } from "@/lib/design-system";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

interface Meeting {
  id: number;
  title: string;
  description?: string;
  start_time: string;
  end_time?: string;
  location?: string;
  meeting_type?: string;
  project_code?: string;
  attendees?: string[];
  status?: string;
  is_virtual?: boolean;
  meeting_link?: string;
}

interface CalendarEvent {
  id: number;
  title: string;
  date: string;
  time?: string;
  type: string;
  project_code?: string;
}

// Fetch meetings
async function fetchMeetings(): Promise<Meeting[]> {
  const response = await fetch(`${API_BASE_URL}/api/meetings`);
  if (!response.ok) throw new Error("Failed to fetch meetings");
  const data = await response.json();
  return data.meetings || data || [];
}

// Fetch calendar events for a date range
async function fetchCalendarEvents(startDate: string, endDate: string): Promise<CalendarEvent[]> {
  const response = await fetch(`${API_BASE_URL}/api/calendar/events?start=${startDate}&end=${endDate}`);
  if (!response.ok) {
    // Fallback - try upcoming endpoint
    const upcomingResponse = await fetch(`${API_BASE_URL}/api/calendar/upcoming`);
    if (!upcomingResponse.ok) return [];
    const data = await upcomingResponse.json();
    return data.events || [];
  }
  const data = await response.json();
  return data.events || [];
}

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
function MeetingCard({ meeting }: { meeting: Meeting }) {
  const startDate = new Date(meeting.start_time);
  const isUpcoming = startDate > new Date();

  return (
    <Card className={cn(
      ds.borderRadius.card,
      "border-slate-200 hover:border-slate-300 transition-colors",
      isToday(startDate) && "border-teal-300 bg-teal-50/30"
    )}>
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
              <h3 className={cn(ds.typography.bodyBold, ds.textColors.primary, "truncate")}>
                {meeting.title}
              </h3>
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

export default function MeetingsPage() {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [activeTab, setActiveTab] = useState<"upcoming" | "past">("upcoming");

  // Fetch all meetings
  const { data: meetings = [], isLoading, error, refetch } = useQuery({
    queryKey: ["meetings"],
    queryFn: fetchMeetings,
    staleTime: 1000 * 60 * 5,
  });

  // Filter meetings by tab
  const now = new Date();
  const upcomingMeetings = meetings
    .filter(m => new Date(m.start_time) >= now)
    .sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime());

  const pastMeetings = meetings
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

      {/* Week Calendar View */}
      {!isLoading && !error && (
        <WeekCalendar
          meetings={meetings}
          currentDate={currentDate}
          onDateChange={setCurrentDate}
        />
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
                <MeetingCard key={meeting.id} meeting={meeting} />
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
                <MeetingCard key={meeting.id} meeting={meeting} />
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
