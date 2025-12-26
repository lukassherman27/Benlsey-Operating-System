"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { format, parseISO } from "date-fns";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  FileText,
  Search,
  Clock,
  Sparkles,
  ChevronRight,
  AlertCircle,
  MessageSquare,
  Calendar,
  Building2,
  Mic,
  Play,
  ExternalLink,
  FileAudio,
  ArrowRight,
  ListFilter,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api";

// ============================================================================
// TYPES
// ============================================================================

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
  key_points?: string[];
  action_items?: unknown[];
  participants?: unknown[];
}

// ============================================================================
// HELPERS
// ============================================================================

function formatDuration(seconds?: number): string {
  if (!seconds) return "—";
  const mins = Math.floor(seconds / 60);
  if (mins < 60) return `${mins} min`;
  const hours = Math.floor(mins / 60);
  const remainingMins = mins % 60;
  return remainingMins > 0 ? `${hours}h ${remainingMins}m` : `${hours}h`;
}

function getDisplayTitle(t: Transcript): string {
  // Priority: meeting_title > proposal_name > derived from filename
  if (t.meeting_title) return t.meeting_title;
  if (t.proposal_name) return `${t.detected_project_code} - ${t.proposal_name}`;
  if (t.detected_project_code) return `Meeting - ${t.detected_project_code}`;

  // Extract date from filename like "meeting_20251209_135941_chunk4.m4a"
  if (t.audio_filename) {
    const match = t.audio_filename.match(/meeting_(\d{8})_(\d{6})/);
    if (match) {
      const dateStr = match[1];
      const year = dateStr.substring(0, 4);
      const month = dateStr.substring(4, 6);
      const day = dateStr.substring(6, 8);
      return `Recording - ${month}/${day}/${year}`;
    }
    // Strip file extension
    return t.audio_filename.replace(/\.(m4a|wav|mp3)$/, '');
  }

  return "Untitled Recording";
}

function getDisplayDate(t: Transcript): string {
  const dateStr = t.meeting_date || t.recorded_date || t.created_at;
  if (!dateStr) return "Unknown date";
  try {
    return format(parseISO(dateStr), "MMM d, yyyy");
  } catch {
    return dateStr.split('T')[0];
  }
}

function parseJsonField<T>(field: T | string | null | undefined): T | null {
  if (!field) return null;
  if (typeof field === 'string') {
    try {
      return JSON.parse(field);
    } catch {
      return null;
    }
  }
  return field;
}

// ============================================================================
// COMPONENTS
// ============================================================================

function PageHeader() {
  return (
    <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-violet-900 via-purple-800 to-violet-900 p-8 text-white">
      <div className="absolute inset-0 opacity-10">
        <div className="absolute top-0 left-0 w-full h-full" style={{
          backgroundImage: `radial-gradient(circle at 25% 25%, rgba(255,255,255,0.2) 1px, transparent 1px)`,
          backgroundSize: '32px 32px'
        }} />
      </div>
      <div className="relative">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 bg-white/10 rounded-lg">
                <Mic className="h-6 w-6" />
              </div>
              <h1 className="text-3xl font-bold tracking-tight">Transcripts</h1>
            </div>
            <p className="mt-2 text-violet-200 max-w-xl">
              Meeting recordings and AI-generated summaries
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatsBar({ transcripts, isLoading }: { transcripts: Transcript[]; isLoading: boolean }) {
  const withSummary = transcripts.filter(t => t.summary || t.polished_summary).length;
  const linkedCount = transcripts.filter(t => t.detected_project_code).length;
  const totalDuration = transcripts.reduce((sum, t) => sum + (t.duration_seconds || 0), 0);

  const stats = [
    { label: "Total", value: transcripts.length, icon: FileAudio, color: "text-violet-600" },
    { label: "With Summary", value: withSummary, icon: Sparkles, color: "text-purple-600" },
    { label: "Linked", value: linkedCount, icon: Building2, color: "text-blue-600" },
    { label: "Total Time", value: formatDuration(totalDuration), icon: Clock, color: "text-amber-600", isText: true },
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
                  {isLoading ? "—" : stat.isText ? stat.value : stat.value}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function TranscriptCard({
  transcript,
  onClick,
  isSelected,
}: {
  transcript: Transcript;
  onClick: () => void;
  isSelected: boolean;
}) {
  const title = getDisplayTitle(transcript);
  const date = getDisplayDate(transcript);
  const hasSummary = !!(transcript.summary || transcript.polished_summary);
  const hasPolished = !!transcript.polished_summary;
  const wordCount = transcript.transcript ? transcript.transcript.split(/\s+/).length : 0;

  return (
    <Card
      className={cn(
        "border-slate-200 hover:border-slate-300 hover:shadow-md transition-all cursor-pointer group",
        isSelected && "ring-2 ring-violet-500/30 border-violet-300"
      )}
      onClick={onClick}
    >
      <CardContent className="p-0">
        <div className="flex">
          {/* Left color bar */}
          <div className={cn(
            "w-1 rounded-l-lg",
            hasPolished ? "bg-emerald-500" : hasSummary ? "bg-purple-500" : "bg-slate-300"
          )} />

          <div className="flex-1 p-4">
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <h3 className="font-semibold text-slate-900 truncate">
                    {title}
                  </h3>
                  {hasPolished ? (
                    <Badge className="bg-emerald-100 text-emerald-700 border-0 gap-1">
                      <Sparkles className="h-3 w-3" />
                      Full Notes
                    </Badge>
                  ) : hasSummary ? (
                    <Badge className="bg-purple-100 text-purple-700 border-0 gap-1">
                      <FileText className="h-3 w-3" />
                      Summary
                    </Badge>
                  ) : null}
                </div>

                <div className="flex items-center gap-4 mt-2 text-sm text-slate-500">
                  <span className="flex items-center gap-1.5">
                    <Calendar className="h-3.5 w-3.5" />
                    {date}
                  </span>
                  {transcript.duration_seconds && (
                    <span className="flex items-center gap-1.5">
                      <Clock className="h-3.5 w-3.5" />
                      {formatDuration(transcript.duration_seconds)}
                    </span>
                  )}
                  {wordCount > 0 && (
                    <span className="flex items-center gap-1.5">
                      <MessageSquare className="h-3.5 w-3.5" />
                      {wordCount.toLocaleString()} words
                    </span>
                  )}
                </div>

                {/* Project link */}
                {transcript.detected_project_code && (
                  <div className="mt-3">
                    <Link
                      href={`/proposals/${transcript.detected_project_code}`}
                      onClick={(e) => e.stopPropagation()}
                      className="inline-flex items-center gap-1.5 text-sm text-blue-600 hover:text-blue-700 hover:underline"
                    >
                      <Building2 className="h-3.5 w-3.5" />
                      <span className="font-mono">{transcript.detected_project_code}</span>
                      {transcript.proposal_name && (
                        <span className="text-slate-500">- {transcript.proposal_name}</span>
                      )}
                      <ExternalLink className="h-3 w-3" />
                    </Link>
                  </div>
                )}
              </div>

              {/* Hover arrow */}
              <div className="flex items-center opacity-0 group-hover:opacity-100 transition-opacity">
                <ArrowRight className="h-5 w-5 text-slate-400" />
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function TranscriptDetailModal({
  transcript,
  open,
  onClose,
}: {
  transcript: Transcript | null;
  open: boolean;
  onClose: () => void;
}) {
  if (!transcript) return null;

  const title = getDisplayTitle(transcript);
  const date = getDisplayDate(transcript);
  const hasSummary = !!(transcript.summary || transcript.polished_summary);
  const hasPolished = !!transcript.polished_summary;
  const summaryContent = transcript.polished_summary || transcript.summary || "";
  const wordCount = transcript.transcript ? transcript.transcript.split(/\s+/).length : 0;

  const keyPoints = parseJsonField<string[]>(transcript.key_points) || [];
  const actionItems = parseJsonField<unknown[]>(transcript.action_items) || [];

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="max-w-4xl max-h-[90vh] p-0 overflow-hidden">
        {/* Header */}
        <div className={cn(
          "p-6 border-b",
          hasPolished ? "bg-gradient-to-r from-emerald-50 to-teal-50" : "bg-violet-50"
        )}>
          <DialogHeader>
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  {hasPolished ? (
                    <Badge className="bg-emerald-100 text-emerald-700 border-0 gap-1">
                      <Sparkles className="h-3 w-3" />
                      Full Notes
                    </Badge>
                  ) : hasSummary ? (
                    <Badge className="bg-purple-100 text-purple-700 border-0 gap-1">
                      <Sparkles className="h-3 w-3" />
                      AI Summary
                    </Badge>
                  ) : (
                    <Badge variant="outline" className="text-slate-500">
                      <FileAudio className="h-3 w-3 mr-1" />
                      Raw Transcript
                    </Badge>
                  )}
                </div>
                <DialogTitle className="text-xl font-bold text-slate-900">
                  {title}
                </DialogTitle>
              </div>
            </div>
          </DialogHeader>

          {/* Quick info */}
          <div className="flex flex-wrap gap-4 mt-4 text-sm">
            <div className="flex items-center gap-2 text-slate-600">
              <Calendar className="h-4 w-4" />
              {date}
            </div>
            {transcript.duration_seconds && (
              <div className="flex items-center gap-2 text-slate-600">
                <Clock className="h-4 w-4" />
                {formatDuration(transcript.duration_seconds)}
              </div>
            )}
            {wordCount > 0 && (
              <div className="flex items-center gap-2 text-slate-600">
                <MessageSquare className="h-4 w-4" />
                {wordCount.toLocaleString()} words
              </div>
            )}
            {transcript.detected_project_code && (
              <Link
                href={`/proposals/${transcript.detected_project_code}`}
                className="flex items-center gap-2 text-blue-600 hover:text-blue-700 hover:underline"
              >
                <Building2 className="h-4 w-4" />
                <span className="font-mono">{transcript.detected_project_code}</span>
                <ExternalLink className="h-3 w-3" />
              </Link>
            )}
          </div>
        </div>

        {/* Content */}
        <ScrollArea className="max-h-[60vh]">
          <div className="p-6 space-y-6">
            {/* Summary */}
            {hasSummary ? (
              <div className="space-y-4">
                <div className="flex items-center gap-2">
                  <FileText className={cn(
                    "h-5 w-5",
                    hasPolished ? "text-emerald-600" : "text-purple-600"
                  )} />
                  <h3 className="font-semibold text-slate-900">
                    {hasPolished ? "Meeting Notes" : "Summary"}
                  </h3>
                </div>

                <div className={cn(
                  "rounded-xl p-5 border",
                  hasPolished
                    ? "bg-white border-slate-200"
                    : "bg-purple-50 border-purple-100"
                )}>
                  <pre className="whitespace-pre-wrap font-sans text-sm text-slate-700 leading-relaxed bg-transparent p-0 m-0">
                    {summaryContent}
                  </pre>
                </div>
              </div>
            ) : null}

            {/* Key Points (only if no polished) */}
            {!hasPolished && keyPoints.length > 0 && (
              <div className="space-y-3">
                <h4 className="font-semibold text-slate-700 text-sm uppercase tracking-wider">
                  Key Points
                </h4>
                <ul className="space-y-2">
                  {keyPoints.map((point, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-slate-600">
                      <span className="text-purple-400 mt-1.5">•</span>
                      <span>{String(point)}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Action Items (only if no polished) */}
            {!hasPolished && actionItems.length > 0 && (
              <div className="space-y-3">
                <h4 className="font-semibold text-slate-700 text-sm uppercase tracking-wider">
                  Action Items
                </h4>
                <ul className="space-y-2">
                  {actionItems.map((item, i) => {
                    const text = typeof item === 'string'
                      ? item
                      : (item as { task?: string })?.task || JSON.stringify(item);
                    return (
                      <li key={i} className="flex items-start gap-2 text-sm text-slate-600">
                        <span className="w-5 h-5 rounded bg-amber-100 text-amber-700 text-xs flex items-center justify-center flex-shrink-0">
                          {i + 1}
                        </span>
                        <span>{text}</span>
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}

            {/* Full Transcript */}
            {transcript.transcript && (
              <div className="space-y-3">
                <h4 className="font-semibold text-slate-700 text-sm uppercase tracking-wider">
                  Full Transcript
                </h4>
                <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 max-h-[300px] overflow-auto">
                  <pre className="whitespace-pre-wrap font-sans text-sm text-slate-600 leading-relaxed">
                    {transcript.transcript}
                  </pre>
                </div>
              </div>
            )}

            {/* No content */}
            {!hasSummary && !transcript.transcript && (
              <div className="text-center py-8">
                <FileAudio className="mx-auto h-12 w-12 text-slate-300 mb-3" />
                <p className="text-slate-500">No transcript content available.</p>
              </div>
            )}
          </div>
        </ScrollArea>

        {/* Footer */}
        <div className="border-t bg-slate-50 px-6 py-4 flex items-center justify-between">
          <div className="text-xs text-slate-400">
            ID: {transcript.id}
            {transcript.audio_filename && (
              <span className="ml-2">• {transcript.audio_filename}</span>
            )}
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
          <Skeleton key={i} className="h-24 w-full rounded-xl" />
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
          Failed to load transcripts
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

export default function TranscriptsPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [filter, setFilter] = useState<"all" | "with_summary" | "linked">("all");
  const [selectedTranscript, setSelectedTranscript] = useState<Transcript | null>(null);

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["transcripts"],
    queryFn: () => api.getMeetingTranscripts({}),
    staleTime: 1000 * 60 * 5,
  });

  const transcripts: Transcript[] = data?.transcripts ?? [];

  // Filter transcripts
  const filteredTranscripts = transcripts.filter((t) => {
    // Search filter
    const searchLower = searchQuery.toLowerCase();
    const matchesSearch = !searchQuery ||
      getDisplayTitle(t).toLowerCase().includes(searchLower) ||
      t.detected_project_code?.toLowerCase().includes(searchLower) ||
      t.proposal_name?.toLowerCase().includes(searchLower) ||
      t.client_company?.toLowerCase().includes(searchLower);

    // Type filter
    let matchesFilter = true;
    if (filter === "with_summary") {
      matchesFilter = !!(t.summary || t.polished_summary);
    } else if (filter === "linked") {
      matchesFilter = !!t.detected_project_code;
    }

    return matchesSearch && matchesFilter;
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
        <ErrorState onRetry={() => refetch()} />
      </div>
    );
  }

  return (
    <div className="space-y-6 w-full max-w-full">
      <PageHeader />

      <StatsBar transcripts={transcripts} isLoading={isLoading} />

      {/* Search and filters */}
      <div className="flex flex-wrap items-center gap-4">
        <div className="flex-1 relative max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
          <Input
            placeholder="Search transcripts, projects..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>

        <div className="flex items-center gap-2">
          <ListFilter className="h-4 w-4 text-slate-400" />
          <div className="flex gap-1">
            {[
              { value: "all", label: "All" },
              { value: "with_summary", label: "With Summary" },
              { value: "linked", label: "Linked to Project" },
            ].map((opt) => (
              <button
                key={opt.value}
                onClick={() => setFilter(opt.value as typeof filter)}
                className={cn(
                  "px-3 py-1.5 text-xs font-medium rounded-full transition-all",
                  filter === opt.value
                    ? "bg-violet-900 text-white"
                    : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                )}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Transcripts list */}
      {filteredTranscripts.length === 0 ? (
        <Card className="border-slate-200">
          <CardContent className="py-16 text-center">
            <FileAudio className="mx-auto h-12 w-12 text-slate-300 mb-4" />
            <p className="text-lg font-medium text-slate-900 mb-1">
              {transcripts.length === 0 ? "No transcripts yet" : "No matching transcripts"}
            </p>
            <p className="text-sm text-slate-500">
              {transcripts.length === 0
                ? "Meeting recordings will appear here once processed."
                : "Try adjusting your search or filters."}
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {filteredTranscripts.map((transcript) => (
            <TranscriptCard
              key={transcript.id}
              transcript={transcript}
              onClick={() => setSelectedTranscript(transcript)}
              isSelected={selectedTranscript?.id === transcript.id}
            />
          ))}
        </div>
      )}

      {/* Detail modal */}
      <TranscriptDetailModal
        transcript={selectedTranscript}
        open={!!selectedTranscript}
        onClose={() => setSelectedTranscript(null)}
      />
    </div>
  );
}
