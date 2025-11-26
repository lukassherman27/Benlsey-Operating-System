"use client";

import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Mic, Clock, Users, Target, ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";
import { format } from "date-fns";

interface Transcript {
  transcript_id: number;
  audio_filename: string;
  processed_date: string;
  meeting_type: string | null;
  detected_project_code: string | null;
  match_confidence: number | null;
  summary: string | null;
  key_points: string | null;
  action_items: string | null;
  participants: string | null;
  transcript: string | null;
}

interface TranscriptViewerProps {
  transcriptId: number;
  compact?: boolean;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export function TranscriptViewer({ transcriptId, compact = false }: TranscriptViewerProps) {
  const [showFullTranscript, setShowFullTranscript] = useState(false);

  const { data: transcript, isLoading, error } = useQuery<Transcript>({
    queryKey: ["transcript", transcriptId],
    queryFn: async () => {
      const res = await fetch(
        `${API_BASE_URL}/api/meeting-transcripts/${transcriptId}`
      );
      if (!res.ok) {
        if (res.status === 404) {
          throw new Error("Transcript not found");
        }
        throw new Error("Failed to fetch transcript");
      }
      return res.json();
    },
    retry: 1,
  });

  if (isLoading) {
    return <TranscriptSkeleton />;
  }

  if (error || !transcript) {
    return (
      <Card className="border-amber-200 bg-amber-50">
        <CardContent className="pt-6">
          <p className="text-amber-700 text-sm">
            {error?.message === "Transcript not found"
              ? "Transcript not found"
              : "Meeting transcript API not available yet. This feature is coming soon."}
          </p>
        </CardContent>
      </Card>
    );
  }

  const keyPoints = safeParseJSON(transcript.key_points, []);
  const actionItems = safeParseJSON(transcript.action_items, []);
  const participants = safeParseJSON(transcript.participants, []);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Mic className="h-5 w-5 text-purple-600" />
            {transcript.audio_filename || "Meeting Transcript"}
          </CardTitle>
          <div className="flex gap-2">
            {transcript.meeting_type && (
              <Badge variant="outline">{transcript.meeting_type}</Badge>
            )}
            {transcript.match_confidence && (
              <Badge
                variant={transcript.match_confidence > 0.7 ? "default" : "secondary"}
              >
                {Math.round((transcript.match_confidence || 0) * 100)}% match
              </Badge>
            )}
          </div>
        </div>
        <div className="flex gap-4 text-sm text-muted-foreground">
          <span className="flex items-center gap-1">
            <Clock className="h-4 w-4" />
            {transcript.processed_date && format(new Date(transcript.processed_date), "MMM d, yyyy")}
          </span>
          {transcript.detected_project_code && (
            <span>Project: {transcript.detected_project_code}</span>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Summary */}
        {transcript.summary && (
          <div>
            <h4 className="font-medium mb-2">Summary</h4>
            <p className="text-sm text-muted-foreground">{transcript.summary}</p>
          </div>
        )}

        {/* Participants */}
        {participants.length > 0 && (
          <div>
            <h4 className="font-medium mb-2 flex items-center gap-2">
              <Users className="h-4 w-4" />
              Participants
            </h4>
            <div className="flex flex-wrap gap-2">
              {participants.map((p: any, i: number) => (
                <Badge key={i} variant="outline">
                  {typeof p === "string" ? p : p.name}
                  {p.type && <span className="ml-1 opacity-50">({p.type})</span>}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Key Points */}
        {keyPoints.length > 0 && (
          <div>
            <h4 className="font-medium mb-2">Key Points</h4>
            <ul className="list-disc list-inside text-sm space-y-1 text-muted-foreground">
              {keyPoints.map((point: string, i: number) => (
                <li key={i}>{point}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Action Items */}
        {actionItems.length > 0 && (
          <div>
            <h4 className="font-medium mb-2 flex items-center gap-2">
              <Target className="h-4 w-4" />
              Action Items ({actionItems.length})
            </h4>
            <div className="space-y-2">
              {actionItems.map((item: any, i: number) => (
                <div
                  key={i}
                  className="flex items-start gap-2 p-2 bg-orange-50 border border-orange-200 rounded"
                >
                  <input type="checkbox" className="mt-1" disabled />
                  <div>
                    <p className="text-sm font-medium">
                      {typeof item === "string" ? item : item.task}
                    </p>
                    {typeof item === "object" && (item.owner || item.deadline) && (
                      <p className="text-xs text-muted-foreground">
                        {item.owner && <span>Owner: {item.owner}</span>}
                        {item.deadline && <span> - Due: {item.deadline}</span>}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Full Transcript Toggle */}
        {!compact && transcript.transcript && (
          <div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowFullTranscript(!showFullTranscript)}
              className="w-full"
            >
              {showFullTranscript ? (
                <>
                  <ChevronUp className="h-4 w-4 mr-2" />
                  Hide Full Transcript
                </>
              ) : (
                <>
                  <ChevronDown className="h-4 w-4 mr-2" />
                  Show Full Transcript
                </>
              )}
            </Button>
            {showFullTranscript && (
              <div className="mt-4 p-4 bg-gray-50 rounded-lg max-h-96 overflow-y-auto">
                <pre className="text-sm whitespace-pre-wrap font-sans">
                  {transcript.transcript}
                </pre>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * Safe JSON parser that returns a default value on failure
 */
function safeParseJSON(value: string | null | undefined, defaultValue: any[] = []): any[] {
  if (!value) return defaultValue;
  if (typeof value !== "string") return value;
  try {
    const parsed = JSON.parse(value);
    return Array.isArray(parsed) ? parsed : defaultValue;
  } catch {
    return defaultValue;
  }
}

function TranscriptSkeleton() {
  return (
    <Card>
      <CardHeader>
        <div className="h-6 w-48 bg-gray-200 rounded animate-pulse" />
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="h-20 bg-gray-100 rounded animate-pulse" />
        <div className="h-16 bg-gray-100 rounded animate-pulse" />
      </CardContent>
    </Card>
  );
}
