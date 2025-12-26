"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import {
  format,
  isToday,
  isFuture,
  parseISO,
  startOfWeek,
  endOfWeek,
  startOfMonth,
  endOfMonth,
  addMonths,
  addDays,
  isSameDay,
  isSameMonth,
} from "date-fns";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Input } from "@/components/ui/input";
import {
  Calendar,
  Clock,
  MapPin,
  Video,
  AlertCircle,
  FileText,
  ArrowRight,
  Sparkles,
  CalendarDays,
  ListFilter,
  ExternalLink,
  Building2,
  Mic,
  MessageSquare,
  Search,
  ChevronLeft,
  ChevronRight,
  LayoutGrid,
  List,
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

// ============================================================================
// TYPES
// ============================================================================

type Meeting = Awaited<ReturnType<typeof api.getMeetings>>["meetings"][number];

interface Transcript {
  id: number;
  audio_filename?: string;
  meeting_title?: string;
  meeting_date?: string;
  recorded_date?: string;
  created_at: string;
  duration_seconds?: number;
  detected_project_code?: string;
  proposal_name?: string;
  client_company?: string;
  transcript?: string;
  summary?: string;
  polished_summary?: string;
  key_points?: unknown[];
  action_items?: unknown[];
  participants?: unknown[];
}

// Unified item that can be either a meeting or transcript
interface UnifiedItem {
  type: "meeting" | "transcript";
  id: string;
  title: string;
  date: Date;
  dateStr: string;
  projectCode?: string;
  projectName?: string;
  hasSummary: boolean;
  hasPolishedSummary: boolean;
  meetingType?: string;
  location?: string;
  isVirtual?: boolean;
  duration?: number;
  wordCount?: number;
  original: Meeting | Transcript;
}

// ============================================================================
// HELPERS
// ============================================================================

const MEETING_TYPE_STYLES: Record<string, { bg: string; text: string; border: string; dot: string }> = {
  client_call: { bg: "bg-blue-50", text: "text-blue-700", border: "border-blue-200", dot: "bg-blue-500" },
  client: { bg: "bg-blue-50", text: "text-blue-700", border: "border-blue-200", dot: "bg-blue-500" },
  internal: { bg: "bg-slate-50", text: "text-slate-600", border: "border-slate-200", dot: "bg-slate-400" },
  site_visit: { bg: "bg-emerald-50", text: "text-emerald-700", border: "border-emerald-200", dot: "bg-emerald-500" },
  design_review: { bg: "bg-violet-50", text: "text-violet-700", border: "border-violet-200", dot: "bg-violet-500" },
  recording: { bg: "bg-purple-50", text: "text-purple-700", border: "border-purple-200", dot: "bg-purple-500" },
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

function formatDuration(seconds?: number): string {
  if (!seconds) return "";
  const mins = Math.floor(seconds / 60);
  if (mins < 60) return `${mins} min`;
  const hours = Math.floor(mins / 60);
  const remainingMins = mins % 60;
  return remainingMins > 0 ? `${hours}h ${remainingMins}m` : `${hours}h`;
}

function getTranscriptTitle(t: Transcript): string {
  if (t.meeting_title) return t.meeting_title;
  if (t.proposal_name) return `${t.detected_project_code} - ${t.proposal_name}`;
  if (t.detected_project_code) return `Meeting - ${t.detected_project_code}`;
  if (t.audio_filename) {
    const match = t.audio_filename.match(/meeting_(\d{8})_(\d{6})/);
    if (match) {
      const dateStr = match[1];
      const month = dateStr.substring(4, 6);
      const day = dateStr.substring(6, 8);
      return `Recording - ${month}/${day}`;
    }
    return t.audio_filename.replace(/\.(m4a|wav|mp3)$/, '');
  }
  return "Untitled Recording";
}

function unifyMeetingsAndTranscripts(meetings: Meeting[], transcripts: Transcript[]): UnifiedItem[] {
  const items: UnifiedItem[] = [];

  // Add meetings
  for (const m of meetings) {
    const date = new Date(m.start_time);
    items.push({
      type: "meeting",
      id: `meeting-${m.id}`,
      title: m.title,
      date,
      dateStr: m.start_time,
      projectCode: m.project_code || undefined,
      hasSummary: !!m.transcript_summary,
      hasPolishedSummary: !!m.transcript_polished_summary,
      meetingType: m.meeting_type || undefined,
      location: m.location || undefined,
      isVirtual: m.is_virtual,
      original: m,
    });
  }

  // Add transcripts
  for (const t of transcripts) {
    const dateStr = t.meeting_date || t.recorded_date || t.created_at;
    let date: Date;
    try {
      date = parseISO(dateStr);
    } catch {
      date = new Date(dateStr);
    }
    const wordCount = t.transcript ? t.transcript.split(/\s+/).length : 0;

    items.push({
      type: "transcript",
      id: `transcript-${t.id}`,
      title: getTranscriptTitle(t),
      date,
      dateStr,
      projectCode: t.detected_project_code || undefined,
      projectName: t.proposal_name || undefined,
      hasSummary: !!(t.summary || t.polished_summary),
      hasPolishedSummary: !!t.polished_summary,
      meetingType: "recording",
      duration: t.duration_seconds,
      wordCount,
      original: t,
    });
  }

  // Sort by date descending
  items.sort((a, b) => b.date.getTime() - a.date.getTime());

  return items;
}

// ============================================================================
// COMPONENTS
// ============================================================================

function PageHeader() {
  const today = new Date();

  return (
    <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-8 text-white">
      <div className="absolute inset-0 opacity-10">
        <div className="absolute top-0 left-0 w-full h-full" style={{
          backgroundImage: `radial-gradient(circle at 25% 25%, rgba(255,255,255,0.2) 1px, transparent 1px)`,
          backgroundSize: '32px 32px'
        }} />
      </div>
      <div className="relative">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Meetings & Recordings</h1>
            <p className="mt-2 text-slate-300 max-w-xl">
              Your schedule, recordings, and meeting notes in one place.
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

function StatsBar({
  meetings,
  transcripts,
  isLoading
}: {
  meetings: Meeting[];
  transcripts: Transcript[];
  isLoading: boolean;
}) {
  const todayMeetings = meetings.filter(m => isToday(new Date(m.start_time))).length;
  const upcomingMeetings = meetings.filter(m => isFuture(new Date(m.start_time))).length;
  const withNotes = meetings.filter(m => m.has_polished_summary || m.has_transcript).length +
                    transcripts.filter(t => t.summary || t.polished_summary).length;
  const totalRecordings = transcripts.length;

  const stats = [
    { label: "Today", value: todayMeetings, icon: CalendarDays, color: "text-teal-600" },
    { label: "Upcoming", value: upcomingMeetings, icon: Calendar, color: "text-blue-600" },
    { label: "Recordings", value: totalRecordings, icon: Mic, color: "text-purple-600" },
    { label: "With Notes", value: withNotes, icon: FileText, color: "text-emerald-600" },
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

function FilterBar({
  filter,
  onFilterChange,
  searchQuery,
  onSearchChange,
}: {
  filter: string;
  onFilterChange: (f: string) => void;
  searchQuery: string;
  onSearchChange: (q: string) => void;
}) {
  const filters = [
    { value: "all", label: "All" },
    { value: "meetings", label: "Scheduled" },
    { value: "recordings", label: "Recordings" },
    { value: "with_notes", label: "With Notes" },
  ];

  return (
    <div className="flex flex-wrap items-center justify-between gap-4">
      <div className="flex items-center gap-2">
        <ListFilter className="h-4 w-4 text-slate-400" />
        <div className="flex gap-1">
          {filters.map((f) => (
            <button
              key={f.value}
              onClick={() => onFilterChange(f.value)}
              className={cn(
                "px-3 py-1.5 text-xs font-medium rounded-full transition-all",
                filter === f.value
                  ? "bg-slate-900 text-white"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              )}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      <div className="relative max-w-xs">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
        <Input
          placeholder="Search..."
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          className="pl-10 h-9"
        />
      </div>
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

function CalendarView({
  items,
  currentDate,
  onDateChange,
  onItemClick,
}: {
  items: UnifiedItem[];
  currentDate: Date;
  onDateChange: (date: Date) => void;
  onItemClick: (item: UnifiedItem) => void;
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

  const getItemsForDay = (date: Date) => {
    return items.filter(item => isSameDay(item.date, date));
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
                const dayItems = getItemsForDay(date);
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
                      {dayItems.slice(0, 3).map((item) => {
                        const style = getMeetingTypeStyle(item.meetingType);
                        return (
                          <button
                            key={item.id}
                            onClick={() => onItemClick(item)}
                            className={cn(
                              "w-full text-left p-1.5 rounded-md transition-all text-xs",
                              item.type === "transcript" ? "bg-purple-50 text-purple-700" : cn(style.bg, style.text),
                              "hover:ring-2 hover:ring-offset-1 hover:ring-slate-300"
                            )}
                          >
                            <div className="font-medium truncate flex items-center gap-1">
                              {item.type === "transcript" && <Mic className="h-3 w-3 flex-shrink-0" />}
                              <span className="truncate">{item.title}</span>
                            </div>
                            {item.type === "meeting" && (
                              <div className="text-[10px] opacity-75 mt-0.5">
                                {format(item.date, "h:mm a")}
                              </div>
                            )}
                          </button>
                        );
                      })}
                      {dayItems.length > 3 && (
                        <div className="text-xs text-slate-500 text-center font-medium">
                          +{dayItems.length - 3} more
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

function UnifiedCard({
  item,
  onClick,
}: {
  item: UnifiedItem;
  onClick: () => void;
}) {
  const isUpcoming = isFuture(item.date);
  const isTodayItem = isToday(item.date);
  const style = getMeetingTypeStyle(item.meetingType);
  const isRecording = item.type === "transcript";

  return (
    <Card
      className={cn(
        "border-slate-200 hover:border-slate-300 hover:shadow-md transition-all cursor-pointer group",
        isTodayItem && "ring-2 ring-teal-500/20 border-teal-300"
      )}
      onClick={onClick}
    >
      <CardContent className="p-0">
        <div className="flex">
          {/* Date sidebar */}
          <div className={cn(
            "flex flex-col items-center justify-center w-20 py-4 border-r",
            isTodayItem
              ? "bg-teal-600 text-white border-teal-600"
              : isRecording
                ? "bg-purple-50 text-purple-700 border-purple-100"
                : "bg-slate-50 text-slate-600 border-slate-200"
          )}>
            <span className="text-xs font-medium uppercase tracking-wider">
              {format(item.date, "MMM")}
            </span>
            <span className="text-2xl font-bold">
              {format(item.date, "d")}
            </span>
            <span className="text-xs opacity-75">
              {format(item.date, "EEE")}
            </span>
          </div>

          {/* Content */}
          <div className="flex-1 p-4">
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <h3 className="font-semibold text-slate-900 truncate">
                    {item.title}
                  </h3>
                  {item.hasPolishedSummary ? (
                    <Badge className="bg-emerald-100 text-emerald-700 border-0 gap-1">
                      <Sparkles className="h-3 w-3" />
                      Full Notes
                    </Badge>
                  ) : item.hasSummary ? (
                    <Badge className="bg-purple-100 text-purple-700 border-0 gap-1">
                      <FileText className="h-3 w-3" />
                      Notes
                    </Badge>
                  ) : null}
                </div>

                <div className="flex items-center gap-4 mt-2 text-sm text-slate-500">
                  {!isRecording && (
                    <span className="flex items-center gap-1.5">
                      <Clock className="h-3.5 w-3.5" />
                      {format(item.date, "h:mm a")}
                    </span>
                  )}

                  {isRecording && item.duration && (
                    <span className="flex items-center gap-1.5">
                      <Clock className="h-3.5 w-3.5" />
                      {formatDuration(item.duration)}
                    </span>
                  )}

                  {isRecording && item.wordCount && item.wordCount > 0 && (
                    <span className="flex items-center gap-1.5">
                      <MessageSquare className="h-3.5 w-3.5" />
                      {item.wordCount.toLocaleString()} words
                    </span>
                  )}

                  {!isRecording && item.location && (
                    <span className="flex items-center gap-1.5">
                      {item.isVirtual ? (
                        <Video className="h-3.5 w-3.5" />
                      ) : (
                        <MapPin className="h-3.5 w-3.5" />
                      )}
                      <span className="truncate max-w-[150px]">
                        {item.location}
                      </span>
                    </span>
                  )}
                </div>

                {/* Project link */}
                {item.projectCode && (
                  <div className="mt-3">
                    <Link
                      href={`/proposals/${item.projectCode}`}
                      onClick={(e) => e.stopPropagation()}
                      className="inline-flex items-center gap-1.5 text-sm text-blue-600 hover:text-blue-700 hover:underline"
                    >
                      <Building2 className="h-3.5 w-3.5" />
                      <span className="font-mono">{item.projectCode}</span>
                      {item.projectName && (
                        <span className="text-slate-500">- {item.projectName}</span>
                      )}
                      <ExternalLink className="h-3 w-3" />
                    </Link>
                  </div>
                )}
              </div>

              {/* Right side */}
              <div className="flex flex-col items-end gap-2">
                <Badge
                  variant="outline"
                  className={cn("text-xs border", style.bg, style.text, style.border)}
                >
                  {isRecording ? (
                    <Mic className="h-3 w-3 mr-1" />
                  ) : (
                    <span className={cn("w-1.5 h-1.5 rounded-full mr-1.5", style.dot)} />
                  )}
                  {isRecording ? "Recording" : formatMeetingType(item.meetingType)}
                </Badge>

                {!isRecording && (
                  isUpcoming ? (
                    <span className="text-xs text-amber-600 font-medium">Upcoming</span>
                  ) : (
                    <span className="text-xs text-slate-400">Completed</span>
                  )
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

function ItemDetailModal({
  item,
  open,
  onClose,
}: {
  item: UnifiedItem | null;
  open: boolean;
  onClose: () => void;
}) {
  if (!item) return null;

  const isRecording = item.type === "transcript";
  const style = getMeetingTypeStyle(item.meetingType);

  // Get summary content
  let summaryContent = "";
  if (isRecording) {
    const t = item.original as Transcript;
    summaryContent = t.polished_summary || t.summary || "";
  } else {
    const m = item.original as Meeting;
    summaryContent = m.transcript_polished_summary || m.transcript_summary || "";
  }

  // Get transcript content (for recordings)
  const transcriptContent = isRecording ? (item.original as Transcript).transcript : null;

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="max-w-3xl max-h-[90vh] p-0 overflow-hidden">
        {/* Header */}
        <div className={cn(
          "p-6 border-b",
          item.hasPolishedSummary
            ? "bg-gradient-to-r from-emerald-50 to-teal-50"
            : isRecording
              ? "bg-purple-50"
              : "bg-slate-50"
        )}>
          <DialogHeader>
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <Badge
                    variant="outline"
                    className={cn("text-xs border", style.bg, style.text, style.border)}
                  >
                    {isRecording ? (
                      <Mic className="h-3 w-3 mr-1" />
                    ) : (
                      <span className={cn("w-1.5 h-1.5 rounded-full mr-1.5", style.dot)} />
                    )}
                    {isRecording ? "Recording" : formatMeetingType(item.meetingType)}
                  </Badge>
                  {item.hasPolishedSummary && (
                    <Badge className="bg-emerald-100 text-emerald-700 border-0 gap-1">
                      <Sparkles className="h-3 w-3" />
                      Full Notes
                    </Badge>
                  )}
                </div>
                <DialogTitle className="text-xl font-bold text-slate-900">
                  {item.title}
                </DialogTitle>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-slate-900">
                  {format(item.date, "d")}
                </div>
                <div className="text-sm text-slate-500">
                  {format(item.date, "MMM yyyy")}
                </div>
              </div>
            </div>
          </DialogHeader>

          {/* Quick info */}
          <div className="flex flex-wrap gap-4 mt-4 text-sm">
            <div className="flex items-center gap-2 text-slate-600">
              <Clock className="h-4 w-4" />
              {format(item.date, "EEEE, h:mm a")}
            </div>
            {item.duration && (
              <div className="flex items-center gap-2 text-slate-600">
                <Clock className="h-4 w-4" />
                {formatDuration(item.duration)}
              </div>
            )}
            {item.wordCount && item.wordCount > 0 && (
              <div className="flex items-center gap-2 text-slate-600">
                <MessageSquare className="h-4 w-4" />
                {item.wordCount.toLocaleString()} words
              </div>
            )}
            {item.projectCode && (
              <Link
                href={`/proposals/${item.projectCode}`}
                className="flex items-center gap-2 text-blue-600 hover:text-blue-700 hover:underline"
              >
                <Building2 className="h-4 w-4" />
                <span className="font-mono">{item.projectCode}</span>
                <ExternalLink className="h-3 w-3" />
              </Link>
            )}
          </div>
        </div>

        {/* Content */}
        <ScrollArea className="max-h-[60vh]">
          <div className="p-6 space-y-6">
            {/* Summary content */}
            {summaryContent ? (
              <div className="space-y-4">
                <div className="flex items-center gap-2">
                  <FileText className={cn(
                    "h-5 w-5",
                    item.hasPolishedSummary ? "text-emerald-600" : "text-purple-600"
                  )} />
                  <h3 className="font-semibold text-slate-900">
                    {item.hasPolishedSummary ? "Meeting Notes" : "Summary"}
                  </h3>
                </div>

                <div className={cn(
                  "rounded-xl p-5 border",
                  item.hasPolishedSummary
                    ? "bg-white border-slate-200"
                    : "bg-purple-50 border-purple-100"
                )}>
                  <pre className="whitespace-pre-wrap font-sans text-sm text-slate-700 leading-relaxed bg-transparent p-0 m-0">
                    {summaryContent}
                  </pre>
                </div>
              </div>
            ) : null}

            {/* Full Transcript (for recordings) */}
            {transcriptContent && (
              <div className="space-y-3">
                <h4 className="font-semibold text-slate-700 text-sm uppercase tracking-wider">
                  Full Transcript
                </h4>
                <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 max-h-[300px] overflow-auto">
                  <pre className="whitespace-pre-wrap font-sans text-sm text-slate-600 leading-relaxed">
                    {transcriptContent}
                  </pre>
                </div>
              </div>
            )}

            {/* No content message */}
            {!summaryContent && !transcriptContent && (
              <div className="text-center py-8">
                <FileText className="mx-auto h-12 w-12 text-slate-300 mb-3" />
                <p className="text-slate-500">No notes available for this meeting.</p>
              </div>
            )}
          </div>
        </ScrollArea>

        {/* Footer */}
        <div className="border-t bg-slate-50 px-6 py-4 flex items-center justify-between">
          <div className="text-xs text-slate-400">
            {isRecording ? "Recording" : "Meeting"} ID: {item.id.split("-")[1]}
          </div>
          <Button variant="outline" size="sm" onClick={onClose}>
            Close
          </Button>
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
      <div className="space-y-3">
        {[...Array(5)].map((_, i) => (
          <Skeleton key={i} className="h-28 w-full rounded-xl" />
        ))}
      </div>
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
  const [filter, setFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedItem, setSelectedItem] = useState<UnifiedItem | null>(null);
  const [view, setView] = useState<"calendar" | "list">("list");
  const [calendarDate, setCalendarDate] = useState(new Date());

  // Fetch both meetings and transcripts
  const { data: meetingsData, isLoading: meetingsLoading, error: meetingsError, refetch: refetchMeetings } = useQuery({
    queryKey: ["meetings"],
    queryFn: () => api.getMeetings(),
    staleTime: 1000 * 60 * 5,
  });

  const { data: transcriptsData, isLoading: transcriptsLoading, error: transcriptsError, refetch: refetchTranscripts } = useQuery({
    queryKey: ["transcripts"],
    queryFn: () => api.getMeetingTranscripts({}),
    staleTime: 1000 * 60 * 5,
  });

  const isLoading = meetingsLoading || transcriptsLoading;
  const error = meetingsError || transcriptsError;

  const meetings = meetingsData?.meetings ?? [];
  const transcripts: Transcript[] = transcriptsData?.transcripts ?? [];

  // Unify and filter items
  const allItems = unifyMeetingsAndTranscripts(meetings, transcripts);

  const filteredItems = allItems.filter((item) => {
    // Filter by type
    if (filter === "meetings" && item.type !== "meeting") return false;
    if (filter === "recordings" && item.type !== "transcript") return false;
    if (filter === "with_notes" && !item.hasSummary) return false;

    // Search filter
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const matchesTitle = item.title.toLowerCase().includes(q);
      const matchesProject = item.projectCode?.toLowerCase().includes(q);
      const matchesProjectName = item.projectName?.toLowerCase().includes(q);
      if (!matchesTitle && !matchesProject && !matchesProjectName) return false;
    }

    return true;
  });

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
        <ErrorState onRetry={() => { refetchMeetings(); refetchTranscripts(); }} />
      </div>
    );
  }

  return (
    <div className="space-y-6 w-full max-w-full">
      <PageHeader />

      <StatsBar meetings={meetings} transcripts={transcripts} isLoading={isLoading} />

      <div className="flex flex-wrap items-center justify-between gap-4">
        <FilterBar
          filter={filter}
          onFilterChange={setFilter}
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
        />
        <ViewToggle view={view} onViewChange={setView} />
      </div>

      {/* Calendar or List View */}
      {view === "calendar" ? (
        <CalendarView
          items={filteredItems}
          currentDate={calendarDate}
          onDateChange={setCalendarDate}
          onItemClick={setSelectedItem}
        />
      ) : (
        <>
          {filteredItems.length === 0 ? (
            <Card className="border-slate-200">
              <CardContent className="py-16 text-center">
                <CalendarDays className="mx-auto h-12 w-12 text-slate-300 mb-4" />
                <p className="text-lg font-medium text-slate-900 mb-1">
                  {allItems.length === 0 ? "No meetings or recordings yet" : "No matching items"}
                </p>
                <p className="text-sm text-slate-500">
                  {allItems.length === 0
                    ? "Scheduled meetings and recordings will appear here."
                    : "Try adjusting your search or filters."}
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {filteredItems.map((item) => (
                <UnifiedCard
                  key={item.id}
                  item={item}
                  onClick={() => setSelectedItem(item)}
                />
              ))}
            </div>
          )}
        </>
      )}

      {/* Detail modal */}
      <ItemDetailModal
        item={selectedItem}
        open={!!selectedItem}
        onClose={() => setSelectedItem(null)}
      />
    </div>
  );
}
