"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { format } from "date-fns";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  FileText,
  Search,
  Filter,
  Clock,
  Users,
  Sparkles,
  ChevronRight,
  ChevronDown,
  AlertCircle,
  Download,
  MessageSquare,
  Calendar,
  FolderOpen,
  Link2,
  PenSquare,
} from "lucide-react";
import { PasteSummaryModal } from "@/components/transcripts/paste-summary-modal";
import { FormattedSummary } from "@/components/transcripts/formatted-summary";
import { useQueryClient } from "@tanstack/react-query";
import { cn } from "@/lib/utils";
import { ds } from "@/lib/design-system";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

interface Transcript {
  id: number;
  meeting_id?: number;
  title: string;
  meeting_title?: string;
  meeting_date?: string;
  created_at: string;
  duration_minutes?: number;
  project_code?: string;
  project_id?: number;
  project_name?: string;
  participants?: string[];
  summary?: string;
  key_points?: string[];
  action_items?: string[];
  content?: string;
  word_count?: number;
  has_ai_summary?: boolean;
  final_summary?: string; // Polished email version
}

interface MeetingGroup {
  key: string;
  meeting_title: string;
  meeting_date: string;
  project_code?: string;
  transcripts: Transcript[];
  total_duration: number;
  has_summary: boolean;
}

// Fetch transcripts
async function fetchTranscripts(): Promise<Transcript[]> {
  const response = await fetch(`${API_BASE_URL}/api/meeting-transcripts`);
  if (!response.ok) {
    // Return empty if endpoint doesn't exist yet
    return [];
  }
  const data = await response.json();
  const rawTranscripts = data.transcripts || data || [];

  // Map backend fields to frontend expected fields
  return rawTranscripts.map((t: Record<string, unknown>) => ({
    id: t.id as number,
    title: (t.title as string) || (t.meeting_title as string) || (t.audio_filename as string) || 'Untitled Transcript',
    meeting_title: t.meeting_title as string,
    meeting_date: t.meeting_date as string || t.recorded_date as string || t.processed_date as string,
    created_at: t.created_at as string || t.processed_date as string || new Date().toISOString(),
    duration_minutes: t.duration_seconds ? Math.round((t.duration_seconds as number) / 60) : undefined,
    project_code: t.detected_project_code as string,
    project_id: t.project_id as number,
    participants: t.participants as string[],
    summary: t.summary as string,
    key_points: t.key_points as string[],
    action_items: t.action_items as string[],
    content: t.transcript as string,
    word_count: t.transcript ? (t.transcript as string).split(/\s+/).length : undefined,
    has_ai_summary: !!(t.summary || t.final_summary),
    final_summary: t.final_summary as string,
  }));
}

// Group transcripts by meeting (date + title)
function groupByMeeting(transcripts: Transcript[]): MeetingGroup[] {
  const groups = new Map<string, MeetingGroup>();

  transcripts.forEach((t) => {
    const date = t.meeting_date || t.created_at?.split('T')[0] || 'unknown';
    const title = t.meeting_title || t.title || 'Untitled Meeting';
    const key = `${date}-${title}`;

    if (!groups.has(key)) {
      groups.set(key, {
        key,
        meeting_title: title,
        meeting_date: date,
        project_code: t.project_code,
        transcripts: [],
        total_duration: 0,
        has_summary: false,
      });
    }

    const group = groups.get(key)!;
    group.transcripts.push(t);
    group.total_duration += t.duration_minutes || 0;
    if (t.has_ai_summary || t.summary) {
      group.has_summary = true;
    }
    if (t.project_code && !group.project_code) {
      group.project_code = t.project_code;
    }
  });

  // Sort by date descending
  return Array.from(groups.values()).sort((a, b) => {
    return new Date(b.meeting_date).getTime() - new Date(a.meeting_date).getTime();
  });
}

// Format duration
function formatDuration(minutes?: number): string {
  if (!minutes) return "—";
  if (minutes < 60) return `${minutes} min`;
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
}

// Loading skeleton
function TranscriptsSkeleton() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-1 space-y-3">
        {[...Array(5)].map((_, i) => (
          <Card key={i} className={cn(ds.borderRadius.card, "border-slate-200")}>
            <CardContent className="p-4">
              <Skeleton className="h-5 w-3/4 mb-2" />
              <Skeleton className="h-4 w-1/2 mb-2" />
              <Skeleton className="h-4 w-1/3" />
            </CardContent>
          </Card>
        ))}
      </div>
      <div className="lg:col-span-2">
        <Card className={cn(ds.borderRadius.card, "border-slate-200 h-[600px]")}>
          <CardContent className="p-6">
            <Skeleton className="h-8 w-1/2 mb-4" />
            <Skeleton className="h-4 w-full mb-2" />
            <Skeleton className="h-4 w-full mb-2" />
            <Skeleton className="h-4 w-3/4" />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

// Empty state
function EmptyState() {
  return (
    <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
      <CardContent className="py-16 text-center">
        <FileText className="mx-auto h-16 w-16 text-slate-300 mb-4" />
        <p className={cn(ds.typography.heading3, ds.textColors.primary, "mb-2")}>
          No transcripts yet
        </p>
        <p className={cn(ds.typography.body, ds.textColors.tertiary)}>
          Meeting transcripts will appear here once recorded.
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
          Failed to load transcripts
        </p>
        <p className={cn(ds.typography.body, "text-red-600 mb-4")}>
          The server is probably napping. Try again?
        </p>
        <Button onClick={onRetry} variant="outline" className="border-red-200 text-red-700 hover:bg-red-100">
          Try Again
        </Button>
      </CardContent>
    </Card>
  );
}

// Transcript viewer
function TranscriptViewer({
  transcript,
  onSaveSummary
}: {
  transcript: Transcript;
  onSaveSummary?: () => void;
}) {
  return (
    <Card className={cn(ds.borderRadius.card, "border-slate-200 h-full")}>
      <CardContent className="p-6 h-full flex flex-col">
        {/* Header */}
        <div className="flex items-start justify-between mb-6">
          <div>
            <h2 className={cn(ds.typography.heading2, ds.textColors.primary)}>
              {transcript.title}
            </h2>
            <div className="flex items-center gap-3 mt-2 text-sm text-slate-500">
              <span className="flex items-center gap-1">
                <Calendar className="h-4 w-4" />
                {format(new Date(transcript.meeting_date || transcript.created_at), "EEEE, MMMM d, yyyy")}
              </span>
              {transcript.duration_minutes && (
                <span className="flex items-center gap-1">
                  <Clock className="h-4 w-4" />
                  {formatDuration(transcript.duration_minutes)}
                </span>
              )}
              {transcript.word_count && (
                <span className="flex items-center gap-1">
                  <MessageSquare className="h-4 w-4" />
                  {transcript.word_count.toLocaleString()} words
                </span>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={onSaveSummary}
              className="bg-purple-50 text-purple-700 border-purple-200 hover:bg-purple-100"
            >
              <PenSquare className="h-4 w-4 mr-2" />
              Save Claude Summary
            </Button>
            <Button variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
          </div>
        </div>

        {/* Participants */}
        {transcript.participants && transcript.participants.length > 0 && (
          <div className="mb-6">
            <h4 className={cn(ds.typography.captionBold, ds.textColors.tertiary, "mb-2")}>
              Participants
            </h4>
            <div className="flex flex-wrap gap-2">
              {transcript.participants.map((participant, i) => {
                // Handle both string and object formats
                const name = typeof participant === 'string'
                  ? participant
                  : (participant as { name?: string })?.name || 'Unknown';
                return (
                  <Badge key={i} variant="outline" className="text-xs">
                    <Users className="h-3 w-3 mr-1" />
                    {name}
                  </Badge>
                );
              })}
            </div>
          </div>
        )}

        {/* Final Summary (polished email version) - preferred over raw fields */}
        {transcript.final_summary ? (
          <div className="mb-6 flex-1">
            <div className="flex items-center gap-2 mb-3">
              <FileText className="h-4 w-4 text-teal-600" />
              <h4 className={cn(ds.typography.captionBold, "text-teal-700")}>
                Meeting Summary
              </h4>
              <Badge variant="outline" className="text-xs bg-teal-50 text-teal-700 border-teal-200">
                Final Version
              </Badge>
            </div>
            <ScrollArea className="h-[500px] rounded-lg border border-slate-200 bg-white shadow-sm">
              <div className="p-6">
                <FormattedSummary content={transcript.final_summary} />
              </div>
            </ScrollArea>
          </div>
        ) : (
          <>
            {/* Fallback: AI Summary */}
            {transcript.summary && (
              <div className="mb-6 p-4 bg-purple-50 rounded-lg border border-purple-200">
                <div className="flex items-center gap-2 mb-2">
                  <Sparkles className="h-4 w-4 text-purple-600" />
                  <h4 className={cn(ds.typography.captionBold, "text-purple-700")}>
                    AI Summary
                  </h4>
                </div>
                <p className={cn(ds.typography.body, "text-purple-900")}>
                  {transcript.summary}
                </p>
              </div>
            )}

            {/* Fallback: Key Points */}
            {transcript.key_points && transcript.key_points.length > 0 && (
              <div className="mb-6">
                <h4 className={cn(ds.typography.captionBold, ds.textColors.tertiary, "mb-2")}>
                  Key Points
                </h4>
                <ul className="space-y-2">
                  {transcript.key_points.map((point, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-teal-500 mt-2 flex-shrink-0" />
                      <span className={cn(ds.typography.body, ds.textColors.primary)}>{point}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Fallback: Action Items */}
            {transcript.action_items && transcript.action_items.length > 0 && (
              <div className="mb-6">
                <h4 className={cn(ds.typography.captionBold, ds.textColors.tertiary, "mb-2")}>
                  Action Items
                </h4>
                <ul className="space-y-2">
                  {transcript.action_items.map((item, i) => {
                    // Handle both string and object formats
                    const text = typeof item === 'string'
                      ? item
                      : (item as { task?: string })?.task || JSON.stringify(item);
                    return (
                      <li
                        key={i}
                        className="flex items-start gap-2 p-2 bg-amber-50 rounded-lg border border-amber-200"
                      >
                        <span className="w-5 h-5 rounded bg-amber-200 text-amber-700 text-xs flex items-center justify-center flex-shrink-0">
                          {i + 1}
                        </span>
                        <span className={cn(ds.typography.body, "text-amber-900")}>{text}</span>
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}
          </>
        )}

        {/* Full Transcript */}
        {transcript.content && (
          <div className="flex-1 min-h-0">
            <h4 className={cn(ds.typography.captionBold, ds.textColors.tertiary, "mb-2")}>
              Full Transcript
            </h4>
            <ScrollArea className="h-[300px] rounded-lg border border-slate-200 p-4">
              <div className="prose prose-sm max-w-none">
                <p className="whitespace-pre-wrap text-slate-700">{transcript.content}</p>
              </div>
            </ScrollArea>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default function TranscriptsPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [projectFilter, setProjectFilter] = useState<string>("all");
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());
  const [summaryModalOpen, setSummaryModalOpen] = useState(false);

  // Fetch transcripts
  const { data: transcripts = [], isLoading, error, refetch } = useQuery({
    queryKey: ["transcripts"],
    queryFn: fetchTranscripts,
    staleTime: 1000 * 60 * 5,
  });

  // Filter transcripts
  const filteredTranscripts = transcripts.filter((t) => {
    const matchesSearch =
      !searchQuery ||
      t.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.project_code?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.summary?.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesProject = projectFilter === "all" || t.project_code === projectFilter;

    return matchesSearch && matchesProject;
  });

  // Group transcripts by meeting
  const meetingGroups = groupByMeeting(filteredTranscripts);

  // Toggle group expansion
  const toggleGroup = (key: string) => {
    setExpandedGroups((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(key)) {
        newSet.delete(key);
      } else {
        newSet.add(key);
      }
      return newSet;
    });
  };

  // Get unique projects
  const uniqueProjects = [...new Set(transcripts.map((t) => t.project_code).filter(Boolean))];

  // Get selected transcript
  const selectedTranscript = selectedId
    ? transcripts.find((t) => t.id === selectedId) || null
    : filteredTranscripts[0] || null;

  // Stats
  const stats = {
    total: transcripts.length,
    meetings: meetingGroups.length,
    withSummary: transcripts.filter((t) => t.has_ai_summary || t.summary).length,
    totalMinutes: transcripts.reduce((sum, t) => sum + (t.duration_minutes || 0), 0),
  };

  return (
    <div className="space-y-6 w-full max-w-full overflow-x-hidden">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className={cn(ds.typography.heading1, ds.textColors.primary)}>
            Meeting Transcripts
          </h1>
          <p className={cn(ds.typography.body, ds.textColors.secondary, "mt-1")}>
            Every word, preserved. Because memory is unreliable.
          </p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-teal-100">
                <FolderOpen className="h-5 w-5 text-teal-700" />
              </div>
              <div>
                <p className={cn(ds.typography.caption, ds.textColors.tertiary)}>Meetings</p>
                <p className={cn(ds.typography.heading2, ds.textColors.primary)}>
                  {isLoading ? "—" : stats.meetings}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-slate-100">
                <FileText className="h-5 w-5 text-slate-700" />
              </div>
              <div>
                <p className={cn(ds.typography.caption, ds.textColors.tertiary)}>Transcripts</p>
                <p className={cn(ds.typography.heading2, ds.textColors.primary)}>
                  {isLoading ? "—" : stats.total}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className={cn(ds.borderRadius.card, "border-purple-200 bg-purple-50/30")}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-purple-100">
                <Sparkles className="h-5 w-5 text-purple-700" />
              </div>
              <div>
                <p className={cn(ds.typography.caption, "text-purple-700")}>AI Summarized</p>
                <p className={cn(ds.typography.heading2, "text-purple-800")}>
                  {isLoading ? "—" : stats.withSummary}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-100">
                <Clock className="h-5 w-5 text-blue-700" />
              </div>
              <div>
                <p className={cn(ds.typography.caption, ds.textColors.tertiary)}>Total Duration</p>
                <p className={cn(ds.typography.heading2, ds.textColors.primary)}>
                  {isLoading ? "—" : formatDuration(stats.totalMinutes)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
        <CardContent className="py-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                placeholder="Search transcripts..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={projectFilter} onValueChange={setProjectFilter}>
              <SelectTrigger className="w-[200px]">
                <Filter className="h-4 w-4 mr-2 text-slate-400" />
                <SelectValue placeholder="Filter by project" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Projects</SelectItem>
                {uniqueProjects.map((project) => (
                  <SelectItem key={project} value={project!}>
                    {project}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Main Content */}
      {isLoading ? (
        <TranscriptsSkeleton />
      ) : error ? (
        <ErrorState onRetry={() => refetch()} />
      ) : transcripts.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Meeting List (Grouped) */}
          <div className="lg:col-span-1 space-y-3">
            {meetingGroups.length === 0 ? (
              <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
                <CardContent className="py-8 text-center">
                  <p className={cn(ds.typography.body, ds.textColors.tertiary)}>
                    No transcripts match your search
                  </p>
                </CardContent>
              </Card>
            ) : (
              meetingGroups.map((group) => {
                const isExpanded = expandedGroups.has(group.key);
                return (
                  <Card
                    key={group.key}
                    className={cn(ds.borderRadius.card, "border-slate-200 overflow-hidden")}
                  >
                    {/* Meeting Header */}
                    <button
                      onClick={() => toggleGroup(group.key)}
                      className={cn(
                        "w-full p-4 text-left flex items-start justify-between gap-2 transition-colors",
                        isExpanded ? "bg-teal-50 border-b border-teal-200" : "hover:bg-slate-50"
                      )}
                    >
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          {isExpanded ? (
                            <ChevronDown className="h-4 w-4 text-teal-600 flex-shrink-0" />
                          ) : (
                            <ChevronRight className="h-4 w-4 text-slate-400 flex-shrink-0" />
                          )}
                          <h3 className={cn(ds.typography.bodyBold, ds.textColors.primary, "line-clamp-1")}>
                            {group.meeting_title}
                          </h3>
                        </div>
                        <div className="flex flex-wrap items-center gap-2 mt-2 ml-6">
                          <span className="flex items-center gap-1 text-sm text-slate-500">
                            <Calendar className="h-3.5 w-3.5" />
                            {format(new Date(group.meeting_date), "MMM d, yyyy")}
                          </span>
                          {group.total_duration > 0 && (
                            <span className="flex items-center gap-1 text-sm text-slate-500">
                              <Clock className="h-3.5 w-3.5" />
                              {formatDuration(group.total_duration)}
                            </span>
                          )}
                          <Badge variant="secondary" className="text-xs">
                            {group.transcripts.length} chunk{group.transcripts.length !== 1 ? 's' : ''}
                          </Badge>
                        </div>
                        <div className="flex flex-wrap items-center gap-2 mt-2 ml-6">
                          {group.project_code && (
                            <Badge variant="outline" className="text-xs bg-blue-50 text-blue-700 border-blue-200">
                              <Link2 className="h-3 w-3 mr-1" />
                              {group.project_code}
                            </Badge>
                          )}
                          {group.has_summary && (
                            <Badge variant="outline" className="text-xs bg-purple-50 text-purple-700 border-purple-200">
                              <Sparkles className="h-3 w-3 mr-1" />
                              AI Summary
                            </Badge>
                          )}
                        </div>
                      </div>
                    </button>

                    {/* Expanded Transcripts */}
                    {isExpanded && (
                      <div className="divide-y divide-slate-100">
                        {group.transcripts.map((transcript) => (
                          <div
                            key={transcript.id}
                            onClick={() => setSelectedId(transcript.id)}
                            className={cn(
                              "p-3 pl-10 cursor-pointer transition-colors",
                              selectedTranscript?.id === transcript.id
                                ? "bg-teal-100 border-l-2 border-teal-500"
                                : "hover:bg-slate-50"
                            )}
                          >
                            <p className={cn(ds.typography.body, "line-clamp-1")}>
                              {transcript.title}
                            </p>
                            <div className="flex items-center gap-2 mt-1 text-xs text-slate-500">
                              {transcript.duration_minutes && (
                                <span>{formatDuration(transcript.duration_minutes)}</span>
                              )}
                              {transcript.word_count && (
                                <span>{transcript.word_count.toLocaleString()} words</span>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </Card>
                );
              })
            )}
          </div>

          {/* Transcript Viewer */}
          <div className="lg:col-span-2">
            {selectedTranscript ? (
              <TranscriptViewer
                transcript={selectedTranscript}
                onSaveSummary={() => setSummaryModalOpen(true)}
              />
            ) : (
              <Card className={cn(ds.borderRadius.card, "border-slate-200 h-[600px]")}>
                <CardContent className="h-full flex items-center justify-center">
                  <div className="text-center">
                    <FileText className="mx-auto h-12 w-12 text-slate-300 mb-4" />
                    <p className={cn(ds.typography.body, ds.textColors.tertiary)}>
                      Expand a meeting and select a transcript to view
                    </p>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      )}

      {/* Paste Summary Modal */}
      {selectedTranscript && (
        <PasteSummaryModal
          open={summaryModalOpen}
          onOpenChange={setSummaryModalOpen}
          transcriptId={selectedTranscript.id}
          transcriptTitle={selectedTranscript.title}
          detectedProjectCode={selectedTranscript.project_code}
        />
      )}
    </div>
  );
}
