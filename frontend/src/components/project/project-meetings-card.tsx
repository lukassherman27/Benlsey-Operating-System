"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Calendar,
  FileText,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  Clock,
  Users,
} from "lucide-react";
import { format } from "date-fns";
import { useState } from "react";
import { cn } from "@/lib/utils";
import { ds } from "@/lib/design-system";

interface ProjectMeetingsCardProps {
  projectCode: string;
}

interface Transcript {
  id: number;
  meeting_title: string | null;
  meeting_date: string | null;
  summary: string | null;
  key_points: string[] | string | null;
  action_items: string[] | string | null;
  participants: string[] | string | null;
  meeting_type: string | null;
}

export function ProjectMeetingsCard({ projectCode }: ProjectMeetingsCardProps) {
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ["project", projectCode, "transcripts"],
    queryFn: () => api.getProjectTranscripts(projectCode),
    staleTime: 1000 * 60 * 5,
  });

  const transcripts: Transcript[] = (data?.transcripts ?? []) as Transcript[];

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "No date";
    try {
      return format(new Date(dateStr), "MMM d, yyyy");
    } catch {
      return dateStr;
    }
  };

  const parseJsonArray = (value: string[] | string | null): string[] => {
    if (!value) return [];
    // Already an array
    if (Array.isArray(value)) return value;
    // Try to parse as JSON string
    try {
      const parsed = JSON.parse(value);
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return value.split("\n").filter(Boolean);
    }
  };

  if (isLoading) {
    return (
      <Card className={ds.cards.default}>
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-base">
            <Calendar className="h-4 w-4 text-purple-600" />
            Meetings & Transcripts
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-3">
            {[1, 2].map((i) => (
              <div key={i} className="h-20 bg-slate-100 rounded-lg" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error || transcripts.length === 0) {
    return (
      <Card className={ds.cards.default}>
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-base">
            <Calendar className="h-4 w-4 text-purple-600" />
            Meetings & Transcripts
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-slate-500">
            No meeting transcripts found for this project.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={ds.cards.default}>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-base">
          <Calendar className="h-4 w-4 text-purple-600" />
          Meetings & Transcripts
          <Badge variant="secondary" className="ml-auto">
            {transcripts.length}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="space-y-3">
          {transcripts.map((transcript) => {
            const isExpanded = expandedId === transcript.id;
            const actionItems = parseJsonArray(transcript.action_items);
            const keyPoints = parseJsonArray(transcript.key_points);

            return (
              <div
                key={transcript.id}
                className="border rounded-lg overflow-hidden"
              >
                {/* Meeting Header */}
                <button
                  onClick={() => setExpandedId(isExpanded ? null : transcript.id)}
                  className="w-full p-3 text-left bg-slate-50 hover:bg-slate-100 transition-colors"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-slate-900 truncate">
                          {transcript.meeting_title || "Meeting"}
                        </span>
                        {transcript.meeting_type && (
                          <Badge variant="outline" className="text-xs">
                            {transcript.meeting_type}
                          </Badge>
                        )}
                      </div>
                      <div className="flex items-center gap-3 text-xs text-slate-500 mt-1">
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {formatDate(transcript.meeting_date)}
                        </span>
                        {actionItems.length > 0 && (
                          <span className="flex items-center gap-1 text-amber-600">
                            <CheckCircle2 className="h-3 w-3" />
                            {actionItems.length} action items
                          </span>
                        )}
                      </div>
                    </div>
                    {isExpanded ? (
                      <ChevronUp className="h-4 w-4 text-slate-400" />
                    ) : (
                      <ChevronDown className="h-4 w-4 text-slate-400" />
                    )}
                  </div>
                </button>

                {/* Expanded Content */}
                {isExpanded && (
                  <div className="p-4 border-t bg-white space-y-4">
                    {/* Summary */}
                    {transcript.summary && (
                      <div>
                        <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
                          Summary
                        </h4>
                        <p className="text-sm text-slate-700 whitespace-pre-wrap">
                          {transcript.summary}
                        </p>
                      </div>
                    )}

                    {/* Key Points */}
                    {keyPoints.length > 0 && (
                      <div>
                        <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
                          Key Points
                        </h4>
                        <ul className="space-y-1">
                          {keyPoints.map((point, idx) => (
                            <li
                              key={idx}
                              className="text-sm text-slate-700 flex items-start gap-2"
                            >
                              <span className="text-blue-500 mt-1">•</span>
                              {point}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Action Items */}
                    {actionItems.length > 0 && (
                      <div>
                        <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
                          Action Items
                        </h4>
                        <ul className="space-y-1">
                          {actionItems.map((item, idx) => (
                            <li
                              key={idx}
                              className="text-sm text-slate-700 flex items-start gap-2"
                            >
                              <CheckCircle2 className="h-4 w-4 text-amber-500 mt-0.5 flex-shrink-0" />
                              {item}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Participants */}
                    {transcript.participants && (
                      <div className="text-xs text-slate-500 flex items-center gap-1 pt-2 border-t">
                        <Users className="h-3 w-3" />
                        {Array.isArray(transcript.participants)
                          ? transcript.participants.join(", ")
                          : transcript.participants}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
