"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  format,
  startOfWeek,
  endOfWeek,
  addDays,
  isToday,
  isSameDay,
  startOfMonth,
  endOfMonth,
  isSameMonth,
  addMonths,
  isPast,
  isFuture,
  parseISO
} from "date-fns";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Calendar,
  Clock,
  MapPin,
  Users,
  ChevronLeft,
  ChevronRight,
  Video,
  AlertCircle,
  FileText,
  CheckCircle2,
  ArrowRight,
  Sparkles,
  CalendarDays,
  ListFilter,
  LayoutGrid,
  List,
  ExternalLink,
  Building2,
  Mail,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api";

type Meeting = Awaited<ReturnType<typeof api.getMeetings>>["meetings"][number];

// Meeting type colors - more refined palette
const MEETING_TYPE_STYLES: Record<string, { bg: string; text: string; border: string; dot: string }> = {
  client_call: { bg: "bg-blue-50", text: "text-blue-700", border: "border-blue-200", dot: "bg-blue-500" },
  client: { bg: "bg-blue-50", text: "text-blue-700", border: "border-blue-200", dot: "bg-blue-500" },
  internal: { bg: "bg-slate-50", text: "text-slate-600", border: "border-slate-200", dot: "bg-slate-400" },
  site_visit: { bg: "bg-emerald-50", text: "text-emerald-700", border: "border-emerald-200", dot: "bg-emerald-500" },
  design_review: { bg: "bg-violet-50", text: "text-violet-700", border: "border-violet-200", dot: "bg-violet-500" },
  review: { bg: "bg-violet-50", text: "text-violet-700", border: "border-violet-200", dot: "bg-violet-500" },
  contract_negotiation: { bg: "bg-amber-50", text: "text-amber-700", border: "border-amber-200", dot: "bg-amber-500" },
  kickoff: { bg: "bg-teal-50", text: "text-teal-700", border: "border-teal-200", dot: "bg-teal-500" },
  proposal_discussion: { bg: "bg-rose-50", text: "text-rose-700", border: "border-rose-200", dot: "bg-rose-500" },
  default: { bg: "bg-slate-50", text: "text-slate-600", border: "border-slate-200", dot: "bg-slate-400" },
};

function getMeetingTypeStyle(type?: string) {
  if (!type) return MEETING_TYPE_STYLES.default;
  return MEETING_TYPE_STYLES[type.toLowerCase()] || MEETING_TYPE_STYLES.default;
}

function formatMeetingType(type?: string): string {
  if (!type) return "Meeting";
  return type.split("_").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ");
}

// Parse JSON fields safely
function parseJsonField(field: string | null | undefined): unknown[] {
  if (!field) return [];
  try {
    const parsed = JSON.parse(field);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function getActionItemText(item: unknown): string {
  if (typeof item === 'string') return item;
  if (item && typeof item === 'object' && 'task' in item) return (item as { task: string }).task;
  return String(item);
}

// ============================================================================
// COMPONENTS
// ============================================================================

function PageHeader() {
  const today = new Date();

  return (
    <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-8 text-white">
      {/* Background pattern */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute top-0 left-0 w-full h-full" style={{
          backgroundImage: `radial-gradient(circle at 25% 25%, rgba(255,255,255,0.2) 1px, transparent 1px)`,
          backgroundSize: '32px 32px'
        }} />
      </div>

      <div className="relative">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Meetings</h1>
            <p className="mt-2 text-slate-300 max-w-xl">
              Your schedule and meeting notes, all in one place.
            </p>
          </div>
          <div className="text-right">
            <div className="text-sm text-slate-400">Today</div>
            <div className="text-2xl font-semibold">{format(today, "EEEE")}</div>
            <div className="text-slate-300">{format(today, "MMMM d, yyyy")}</div>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatsBar({ meetings, isLoading }: { meetings: Meeting[]; isLoading: boolean }) {
  const now = new Date();
  const todayCount = meetings.filter(m => isToday(new Date(m.start_time))).length;
  const upcomingCount = meetings.filter(m => isFuture(new Date(m.start_time))).length;
  const withNotesCount = meetings.filter(m => m.has_polished_summary || m.has_transcript).length;

  const weekStart = startOfWeek(now, { weekStartsOn: 1 });
  const weekEnd = endOfWeek(now, { weekStartsOn: 1 });
  const thisWeekCount = meetings.filter(m => {
    const d = new Date(m.start_time);
    return d >= weekStart && d <= weekEnd;
  }).length;

  const stats = [
    { label: "Today", value: todayCount, icon: CalendarDays, color: "text-teal-600" },
    { label: "This Week", value: thisWeekCount, icon: Calendar, color: "text-blue-600" },
    { label: "Upcoming", value: upcomingCount, icon: Clock, color: "text-amber-600" },
    { label: "With Notes", value: withNotesCount, icon: FileText, color: "text-emerald-600" },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {stats.map((stat) => (
        <Card key={stat.label} className="border-slate-200 hover:border-slate-300 transition-colors">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className={cn("p-2 rounded-lg bg-slate-100", stat.color)}>
                <stat.icon className="h-4 w-4" />
              </div>
              <div>
                <p className="text-xs text-slate-500 font-medium">{stat.label}</p>
                <p className="text-xl font-bold text-slate-900">
                  {isLoading ? "—" : stat.value}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function ViewToggle({
  view,
  onViewChange
}: {
  view: "calendar" | "list";
  onViewChange: (v: "calendar" | "list") => void;
}) {
  return (
    <div className="flex items-center gap-1 bg-slate-100 rounded-lg p-1">
      <Button
        variant={view === "calendar" ? "default" : "ghost"}
        size="sm"
        onClick={() => onViewChange("calendar")}
        className="gap-2"
      >
        <LayoutGrid className="h-4 w-4" />
        Calendar
      </Button>
      <Button
        variant={view === "list" ? "default" : "ghost"}
        size="sm"
        onClick={() => onViewChange("list")}
        className="gap-2"
      >
        <List className="h-4 w-4" />
        List
      </Button>
    </div>
  );
}

function TypeFilter({
  selected,
  onChange
}: {
  selected: string;
  onChange: (type: string) => void;
}) {
  const types = [
    { value: "all", label: "All" },
    { value: "client_call", label: "Client" },
    { value: "internal", label: "Internal" },
    { value: "site_visit", label: "Site Visit" },
    { value: "design_review", label: "Review" },
  ];

  return (
    <div className="flex items-center gap-2">
      <ListFilter className="h-4 w-4 text-slate-400" />
      <div className="flex gap-1">
        {types.map((type) => {
          const style = getMeetingTypeStyle(type.value === "all" ? undefined : type.value);
          const isSelected = selected === type.value;

          return (
            <button
              key={type.value}
              onClick={() => onChange(type.value)}
              className={cn(
                "px-3 py-1.5 text-xs font-medium rounded-full transition-all",
                isSelected
                  ? "bg-slate-900 text-white"
                  : cn(style.bg, style.text, "hover:opacity-80")
              )}
            >
              {type.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function MeetingCard({
  meeting,
  onClick,
  compact = false
}: {
  meeting: Meeting;
  onClick: () => void;
  compact?: boolean;
}) {
  const startDate = new Date(meeting.start_time);
  const isUpcoming = isFuture(startDate);
  const isTodayMeeting = isToday(startDate);
  const style = getMeetingTypeStyle(meeting.meeting_type);

  if (compact) {
    return (
      <button
        onClick={onClick}
        className={cn(
          "w-full text-left p-2 rounded-lg transition-all text-xs",
          style.bg, style.text,
          "hover:ring-2 hover:ring-offset-1 hover:ring-slate-300"
        )}
      >
        <div className="font-medium truncate">{meeting.title}</div>
        <div className="text-[10px] opacity-75 mt-0.5">
          {format(startDate, "h:mm a")}
        </div>
      </button>
    );
  }

  return (
    <Card
      className={cn(
        "border-slate-200 hover:border-slate-300 hover:shadow-md transition-all cursor-pointer group",
        isTodayMeeting && "ring-2 ring-teal-500/20 border-teal-300"
      )}
      onClick={onClick}
    >
      <CardContent className="p-0">
        <div className="flex">
          {/* Date sidebar */}
          <div className={cn(
            "flex flex-col items-center justify-center w-20 py-4 border-r",
            isTodayMeeting
              ? "bg-teal-600 text-white border-teal-600"
              : "bg-slate-50 text-slate-600 border-slate-200"
          )}>
            <span className="text-xs font-medium uppercase tracking-wider">
              {format(startDate, "MMM")}
            </span>
            <span className="text-2xl font-bold">
              {format(startDate, "d")}
            </span>
            <span className="text-xs opacity-75">
              {format(startDate, "EEE")}
            </span>
          </div>

          {/* Content */}
          <div className="flex-1 p-4">
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <h3 className="font-semibold text-slate-900 truncate">
                    {meeting.title}
                  </h3>
                  {meeting.has_polished_summary ? (
                    <Badge className="bg-emerald-100 text-emerald-700 border-0 gap-1">
                      <Sparkles className="h-3 w-3" />
                      Full Notes
                    </Badge>
                  ) : meeting.has_transcript ? (
                    <Badge className="bg-purple-100 text-purple-700 border-0 gap-1">
                      <FileText className="h-3 w-3" />
                      Notes
                    </Badge>
                  ) : null}
                </div>

                <div className="flex items-center gap-4 mt-2 text-sm text-slate-500">
                  <span className="flex items-center gap-1.5">
                    <Clock className="h-3.5 w-3.5" />
                    {format(startDate, "h:mm a")}
                    {meeting.end_time && (
                      <span className="text-slate-400">
                        — {format(new Date(meeting.end_time), "h:mm a")}
                      </span>
                    )}
                  </span>

                  {meeting.location && (
                    <span className="flex items-center gap-1.5">
                      {meeting.is_virtual ? (
                        <Video className="h-3.5 w-3.5" />
                      ) : (
                        <MapPin className="h-3.5 w-3.5" />
                      )}
                      <span className="truncate max-w-[150px]">{meeting.location}</span>
                    </span>
                  )}
                </div>

                {meeting.project_code && (
                  <div className="mt-2">
                    <Badge variant="outline" className="text-xs font-mono">
                      {meeting.project_code}
                    </Badge>
                  </div>
                )}
              </div>

              {/* Right side */}
              <div className="flex flex-col items-end gap-2">
                <Badge
                  variant="outline"
                  className={cn("text-xs border", style.bg, style.text, style.border)}
                >
                  <span className={cn("w-1.5 h-1.5 rounded-full mr-1.5", style.dot)} />
                  {formatMeetingType(meeting.meeting_type)}
                </Badge>

                {isUpcoming ? (
                  <span className="text-xs text-amber-600 font-medium">Upcoming</span>
                ) : (
                  <span className="text-xs text-slate-400">Completed</span>
                )}
              </div>
            </div>
          </div>

          {/* Hover arrow */}
          <div className="flex items-center pr-4 opacity-0 group-hover:opacity-100 transition-opacity">
            <ArrowRight className="h-5 w-5 text-slate-400" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function CalendarView({
  meetings,
  currentDate,
  onDateChange,
  onMeetingClick,
}: {
  meetings: Meeting[];
  currentDate: Date;
  onDateChange: (date: Date) => void;
  onMeetingClick: (meeting: Meeting) => void;
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

  const weeks: Date[][] = [];
  for (let i = 0; i < days.length; i += 7) {
    weeks.push(days.slice(i, i + 7));
  }

  const getMeetingsForDay = (date: Date) => {
    return meetings.filter(m => isSameDay(new Date(m.start_time), date));
  };

  return (
    <Card className="border-slate-200">
      <CardContent className="p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-slate-900">
            {format(currentDate, "MMMM yyyy")}
          </h2>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="icon"
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
              size="icon"
              onClick={() => onDateChange(addMonths(currentDate, 1))}
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Day headers */}
        <div className="grid grid-cols-7 gap-1 mb-2">
          {["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map((dayName) => (
            <div key={dayName} className="text-center text-xs font-semibold text-slate-500 py-2 uppercase tracking-wider">
              {dayName}
            </div>
          ))}
        </div>

        {/* Calendar grid */}
        <div className="space-y-1">
          {weeks.map((week, weekIndex) => (
            <div key={weekIndex} className="grid grid-cols-7 gap-1">
              {week.map((date) => {
                const dayMeetings = getMeetingsForDay(date);
                const isCurrentDay = isToday(date);
                const isCurrentMonth = isSameMonth(date, currentDate);

                return (
                  <div
                    key={date.toISOString()}
                    className={cn(
                      "min-h-[100px] p-2 rounded-lg border transition-colors",
                      !isCurrentMonth && "opacity-40 bg-slate-50",
                      isCurrentMonth && "bg-white hover:bg-slate-50",
                      isCurrentDay && "ring-2 ring-teal-500 border-teal-300 bg-teal-50/50"
                    )}
                  >
                    <div className={cn(
                      "text-sm font-semibold mb-1",
                      isCurrentDay ? "text-teal-700" : "text-slate-700"
                    )}>
                      {format(date, "d")}
                    </div>
                    <div className="space-y-1">
                      {dayMeetings.slice(0, 3).map((meeting) => (
                        <MeetingCard
                          key={meeting.id}
                          meeting={meeting}
                          onClick={() => onMeetingClick(meeting)}
                          compact
                        />
                      ))}
                      {dayMeetings.length > 3 && (
                        <div className="text-xs text-slate-500 text-center font-medium">
                          +{dayMeetings.length - 3} more
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

function ListView({
  meetings,
  onMeetingClick,
}: {
  meetings: Meeting[];
  onMeetingClick: (meeting: Meeting) => void;
}) {
  const now = new Date();
  const upcomingMeetings = meetings
    .filter(m => new Date(m.start_time) >= now)
    .sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime());

  const pastMeetings = meetings
    .filter(m => new Date(m.start_time) < now)
    .sort((a, b) => new Date(b.start_time).getTime() - new Date(a.start_time).getTime());

  const [showPast, setShowPast] = useState(false);

  const displayMeetings = showPast ? pastMeetings : upcomingMeetings;

  return (
    <div className="space-y-4">
      {/* Toggle */}
      <div className="flex items-center gap-2 bg-slate-100 rounded-lg p-1 w-fit">
        <Button
          variant={!showPast ? "default" : "ghost"}
          size="sm"
          onClick={() => setShowPast(false)}
        >
          Upcoming ({upcomingMeetings.length})
        </Button>
        <Button
          variant={showPast ? "default" : "ghost"}
          size="sm"
          onClick={() => setShowPast(true)}
        >
          Past ({pastMeetings.length})
        </Button>
      </div>

      {/* Meetings list */}
      {displayMeetings.length === 0 ? (
        <Card className="border-slate-200">
          <CardContent className="py-16 text-center">
            <CalendarDays className="mx-auto h-12 w-12 text-slate-300 mb-4" />
            <p className="text-lg font-medium text-slate-900 mb-1">
              {showPast ? "No past meetings" : "No upcoming meetings"}
            </p>
            <p className="text-sm text-slate-500">
              {showPast ? "Your meeting history will appear here." : "Schedule a meeting to get started."}
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {displayMeetings.map((meeting) => (
            <MeetingCard
              key={meeting.id}
              meeting={meeting}
              onClick={() => onMeetingClick(meeting)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function MeetingDetailModal({
  meeting,
  open,
  onClose,
}: {
  meeting: Meeting | null;
  open: boolean;
  onClose: () => void;
}) {
  if (!meeting) return null;

  const startDate = new Date(meeting.start_time);
  const style = getMeetingTypeStyle(meeting.meeting_type);
  const hasPolishedSummary = !!meeting.transcript_polished_summary;
  const hasSummary = hasPolishedSummary || !!meeting.transcript_summary;

  // Parse polished summary sections for better display
  const summaryContent = meeting.transcript_polished_summary || meeting.transcript_summary || "";

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="max-w-3xl max-h-[90vh] p-0 overflow-hidden">
        {/* Header */}
        <div className={cn(
          "p-6 border-b",
          hasPolishedSummary ? "bg-gradient-to-r from-emerald-50 to-teal-50" : "bg-slate-50"
        )}>
          <DialogHeader>
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <Badge
                    variant="outline"
                    className={cn("text-xs border", style.bg, style.text, style.border)}
                  >
                    <span className={cn("w-1.5 h-1.5 rounded-full mr-1.5", style.dot)} />
                    {formatMeetingType(meeting.meeting_type)}
                  </Badge>
                  {hasPolishedSummary && (
                    <Badge className="bg-emerald-100 text-emerald-700 border-0 gap-1">
                      <Sparkles className="h-3 w-3" />
                      Full Notes Available
                    </Badge>
                  )}
                </div>
                <DialogTitle className="text-xl font-bold text-slate-900">
                  {meeting.title}
                </DialogTitle>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-slate-900">
                  {format(startDate, "d")}
                </div>
                <div className="text-sm text-slate-500">
                  {format(startDate, "MMM yyyy")}
                </div>
              </div>
            </div>
          </DialogHeader>

          {/* Quick info */}
          <div className="flex flex-wrap gap-4 mt-4 text-sm">
            <div className="flex items-center gap-2 text-slate-600">
              <Clock className="h-4 w-4" />
              {format(startDate, "EEEE, h:mm a")}
              {meeting.end_time && (
                <span className="text-slate-400">
                  — {format(new Date(meeting.end_time), "h:mm a")}
                </span>
              )}
            </div>
            {meeting.location && (
              <div className="flex items-center gap-2 text-slate-600">
                {meeting.is_virtual ? <Video className="h-4 w-4" /> : <MapPin className="h-4 w-4" />}
                {meeting.location}
              </div>
            )}
            {meeting.project_code && (
              <div className="flex items-center gap-2">
                <Building2 className="h-4 w-4 text-slate-400" />
                <Badge variant="outline" className="font-mono text-xs">
                  {meeting.project_code}
                </Badge>
              </div>
            )}
          </div>
        </div>

        {/* Content */}
        <ScrollArea className="max-h-[60vh]">
          <div className="p-6 space-y-6">
            {/* Summary content */}
            {hasSummary ? (
              <div className="space-y-4">
                <div className="flex items-center gap-2">
                  <FileText className={cn(
                    "h-5 w-5",
                    hasPolishedSummary ? "text-emerald-600" : "text-purple-600"
                  )} />
                  <h3 className="font-semibold text-slate-900">
                    {hasPolishedSummary ? "Meeting Notes" : "Summary"}
                  </h3>
                </div>

                <div className={cn(
                  "rounded-xl p-5 border",
                  hasPolishedSummary
                    ? "bg-white border-slate-200"
                    : "bg-purple-50 border-purple-100"
                )}>
                  <div className={cn(
                    "prose prose-sm max-w-none",
                    hasPolishedSummary && "prose-headings:text-slate-900 prose-h2:text-lg prose-h3:text-base"
                  )}>
                    <pre className="whitespace-pre-wrap font-sans text-sm text-slate-700 leading-relaxed bg-transparent p-0 m-0 overflow-visible">
                      {summaryContent}
                    </pre>
                  </div>
                </div>
              </div>
            ) : meeting.description ? (
              <div className="space-y-4">
                <h3 className="font-semibold text-slate-900">Description</h3>
                <p className="text-sm text-slate-600">{meeting.description}</p>
              </div>
            ) : (
              <div className="text-center py-8">
                <FileText className="mx-auto h-12 w-12 text-slate-300 mb-3" />
                <p className="text-slate-500">No notes available for this meeting.</p>
                <p className="text-sm text-slate-400 mt-1">
                  Meeting notes will appear here once processed.
                </p>
              </div>
            )}

            {/* Key points & Action items (only if no polished summary) */}
            {!hasPolishedSummary && (
              <>
                {meeting.transcript_key_points && parseJsonField(meeting.transcript_key_points).length > 0 && (
                  <div className="space-y-3">
                    <h4 className="font-semibold text-slate-700 text-sm uppercase tracking-wider">
                      Key Points
                    </h4>
                    <ul className="space-y-2">
                      {parseJsonField(meeting.transcript_key_points).map((point, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-slate-600">
                          <span className="text-purple-400 mt-1.5">•</span>
                          <span>{String(point)}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {meeting.transcript_action_items && parseJsonField(meeting.transcript_action_items).length > 0 && (
                  <div className="space-y-3">
                    <h4 className="font-semibold text-slate-700 text-sm uppercase tracking-wider">
                      Action Items
                    </h4>
                    <ul className="space-y-2">
                      {parseJsonField(meeting.transcript_action_items).map((item, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-slate-600">
                          <CheckCircle2 className="h-4 w-4 text-emerald-500 mt-0.5 flex-shrink-0" />
                          <span>{getActionItemText(item)}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </>
            )}
          </div>
        </ScrollArea>

        {/* Footer */}
        <div className="border-t bg-slate-50 px-6 py-4 flex items-center justify-between">
          <div className="text-xs text-slate-400">
            Meeting ID: {meeting.id}
          </div>
          <div className="flex items-center gap-2">
            {meeting.meeting_link && (
              <Button variant="outline" size="sm" className="gap-2" asChild>
                <a href={meeting.meeting_link} target="_blank" rel="noopener noreferrer">
                  <ExternalLink className="h-4 w-4" />
                  Join Meeting
                </a>
              </Button>
            )}
            <Button variant="outline" size="sm" onClick={onClose}>
              Close
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function LoadingSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-36 w-full rounded-2xl" />
      <div className="grid grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <Skeleton key={i} className="h-20 w-full rounded-xl" />
        ))}
      </div>
      <Skeleton className="h-[500px] w-full rounded-xl" />
    </div>
  );
}

function ErrorState({ onRetry }: { onRetry: () => void }) {
  return (
    <Card className="border-red-200 bg-red-50">
      <CardContent className="py-12 text-center">
        <AlertCircle className="mx-auto h-12 w-12 text-red-400 mb-4" />
        <p className="text-lg font-medium text-red-700 mb-2">
          Failed to load meetings
        </p>
        <p className="text-sm text-red-600 mb-4">
          Something went wrong. Please try again.
        </p>
        <Button onClick={onRetry} variant="outline" className="border-red-200 text-red-700 hover:bg-red-100">
          Try Again
        </Button>
      </CardContent>
    </Card>
  );
}

// ============================================================================
// MAIN PAGE
// ============================================================================

export default function MeetingsPage() {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [view, setView] = useState<"calendar" | "list">("list");
  const [typeFilter, setTypeFilter] = useState("all");
  const [selectedMeeting, setSelectedMeeting] = useState<Meeting | null>(null);

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["meetings"],
    queryFn: () => api.getMeetings(),
    staleTime: 1000 * 60 * 5,
  });

  const meetings = data?.meetings ?? [];

  // Filter by type
  const filteredMeetings = typeFilter === "all"
    ? meetings
    : meetings.filter(m => m.meeting_type?.toLowerCase() === typeFilter);

  if (isLoading) {
    return (
      <div className="space-y-6 w-full max-w-full">
        <LoadingSkeleton />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6 w-full max-w-full">
        <PageHeader />
        <ErrorState onRetry={() => refetch()} />
      </div>
    );
  }

  return (
    <div className="space-y-6 w-full max-w-full">
      <PageHeader />

      <StatsBar meetings={meetings} isLoading={isLoading} />

      {/* Controls */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <TypeFilter selected={typeFilter} onChange={setTypeFilter} />
        <ViewToggle view={view} onViewChange={setView} />
      </div>

      {/* Main content */}
      {view === "calendar" ? (
        <CalendarView
          meetings={filteredMeetings}
          currentDate={currentDate}
          onDateChange={setCurrentDate}
          onMeetingClick={setSelectedMeeting}
        />
      ) : (
        <ListView
          meetings={filteredMeetings}
          onMeetingClick={setSelectedMeeting}
        />
      )}

      {/* Meeting detail modal */}
      <MeetingDetailModal
        meeting={selectedMeeting}
        open={!!selectedMeeting}
        onClose={() => setSelectedMeeting(null)}
      />
    </div>
  );
}
