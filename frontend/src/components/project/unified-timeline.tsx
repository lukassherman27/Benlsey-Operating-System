"use client";

import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Mail, Mic, AlertCircle, DollarSign, Flag,
  ChevronDown, ChevronRight, Calendar, Loader2
} from "lucide-react";
import { useState } from "react";
import { format } from "date-fns";

interface TimelineEvent {
  type: "email" | "meeting" | "rfi" | "invoice" | "milestone";
  date: string;
  title: string;
  summary: string;
  data: Record<string, any>;
  id: number;
}

interface TimelineResponse {
  success: boolean;
  events: TimelineEvent[];
  count: number;
}

interface UnifiedTimelineProps {
  projectCode: string;
  limit?: number;
}

const EVENT_ICONS = {
  email: Mail,
  meeting: Mic,
  rfi: AlertCircle,
  invoice: DollarSign,
  milestone: Flag,
};

const EVENT_COLORS = {
  email: "bg-blue-100 text-blue-700 border-blue-200",
  meeting: "bg-purple-100 text-purple-700 border-purple-200",
  rfi: "bg-orange-100 text-orange-700 border-orange-200",
  invoice: "bg-green-100 text-green-700 border-green-200",
  milestone: "bg-gray-100 text-gray-700 border-gray-200",
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export function UnifiedTimeline({ projectCode, limit = 20 }: UnifiedTimelineProps) {
  const [expandedEvents, setExpandedEvents] = useState<Set<string>>(new Set());
  const [typeFilter, setTypeFilter] = useState<string>("all");

  const { data, isLoading, error } = useQuery<TimelineResponse>({
    queryKey: ["unified-timeline", projectCode, typeFilter, limit],
    queryFn: async () => {
      const params = new URLSearchParams({ limit: String(limit) });
      if (typeFilter !== "all") params.set("types", typeFilter);

      const res = await fetch(
        `${API_BASE_URL}/api/projects/${encodeURIComponent(projectCode)}/unified-timeline?${params}`
      );
      if (!res.ok) {
        if (res.status === 404) {
          // API not implemented yet - return empty
          return { success: true, events: [], count: 0 };
        }
        throw new Error("Failed to fetch timeline");
      }
      return res.json();
    },
    retry: 1,
  });

  const toggleExpanded = (eventId: string) => {
    const newExpanded = new Set(expandedEvents);
    if (newExpanded.has(eventId)) {
      newExpanded.delete(eventId);
    } else {
      newExpanded.add(eventId);
    }
    setExpandedEvents(newExpanded);
  };

  if (isLoading) {
    return <TimelineSkeleton />;
  }

  if (error) {
    return (
      <Card className="border-amber-200 bg-amber-50">
        <CardContent className="pt-6">
          <p className="text-amber-700 text-sm">
            Timeline API not available yet. This feature is coming soon.
          </p>
        </CardContent>
      </Card>
    );
  }

  const events: TimelineEvent[] = data?.events || [];

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          <Calendar className="h-5 w-5" />
          Project Timeline
        </CardTitle>
        <div className="flex gap-2">
          {["all", "email", "meeting", "rfi", "invoice"].map((type) => (
            <Badge
              key={type}
              variant={typeFilter === type ? "default" : "outline"}
              className="cursor-pointer capitalize"
              onClick={() => setTypeFilter(type)}
            >
              {type}
            </Badge>
          ))}
        </div>
      </CardHeader>
      <CardContent>
        {events.length === 0 ? (
          <p className="text-muted-foreground text-center py-8">
            No events found for this project
          </p>
        ) : (
          <div className="space-y-4">
            {events.map((event) => {
              const Icon = EVENT_ICONS[event.type] || Mail;
              const colorClass = EVENT_COLORS[event.type] || EVENT_COLORS.email;
              const eventKey = `${event.type}-${event.id}`;
              const isExpanded = expandedEvents.has(eventKey);

              return (
                <div
                  key={eventKey}
                  className={`border rounded-lg p-4 ${colorClass} transition-all duration-200 hover:shadow-md`}
                >
                  <div
                    className="flex items-start gap-3 cursor-pointer"
                    onClick={() => toggleExpanded(eventKey)}
                  >
                    <div className="mt-1">
                      {isExpanded ? (
                        <ChevronDown className="h-4 w-4" />
                      ) : (
                        <ChevronRight className="h-4 w-4" />
                      )}
                    </div>
                    <Icon className="h-5 w-5 mt-0.5 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2">
                        <p className="font-medium truncate">{event.title}</p>
                        <span className="text-xs opacity-75 flex-shrink-0">
                          {format(new Date(event.date), "MMM d, yyyy h:mm a")}
                        </span>
                      </div>
                      <p className="text-sm opacity-90 mt-1 line-clamp-2">
                        {event.summary}
                      </p>
                    </div>
                  </div>

                  {isExpanded && (
                    <div className="mt-4 pt-4 border-t border-current/20">
                      <EventDetails event={event} />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function EventDetails({ event }: { event: TimelineEvent }) {
  switch (event.type) {
    case "meeting":
      return (
        <div className="space-y-3">
          <div>
            <p className="text-xs font-medium opacity-75">Full Summary</p>
            <p className="text-sm">{event.data.summary}</p>
          </div>
          {event.data.key_points && (
            <div>
              <p className="text-xs font-medium opacity-75">Key Points</p>
              <ul className="list-disc list-inside text-sm">
                {(typeof event.data.key_points === "string"
                  ? JSON.parse(event.data.key_points || "[]")
                  : event.data.key_points || []
                ).map((point: string, i: number) => (
                  <li key={i}>{point}</li>
                ))}
              </ul>
            </div>
          )}
          {event.data.action_items && (
            <div>
              <p className="text-xs font-medium opacity-75">Action Items</p>
              <ul className="list-disc list-inside text-sm">
                {(typeof event.data.action_items === "string"
                  ? JSON.parse(event.data.action_items || "[]")
                  : event.data.action_items || []
                ).map((item: any, i: number) => (
                  <li key={i}>
                    {typeof item === "string" ? item : item.task}
                    {item.owner && <span className="opacity-75"> - {item.owner}</span>}
                  </li>
                ))}
              </ul>
            </div>
          )}
          <div className="flex gap-4 text-xs opacity-75">
            <span>Type: {event.data.meeting_type}</span>
            {event.data.match_confidence && (
              <span>Confidence: {Math.round((event.data.match_confidence || 0) * 100)}%</span>
            )}
          </div>
        </div>
      );

    case "email":
      return (
        <div className="space-y-2">
          <div className="flex gap-4 text-xs">
            <span><strong>From:</strong> {event.data.sender_email}</span>
            <span><strong>To:</strong> {event.data.recipient_email}</span>
          </div>
          {event.data.body_preview && (
            <p className="text-sm whitespace-pre-wrap">{event.data.body_preview}</p>
          )}
        </div>
      );

    case "rfi":
      return (
        <div className="space-y-2">
          <div className="flex gap-4 text-xs">
            <span><strong>Status:</strong> {event.data.status}</span>
            <span><strong>Due:</strong> {event.data.date_due || "Not set"}</span>
            <span><strong>Priority:</strong> {event.data.priority || "Normal"}</span>
          </div>
          {event.data.description && (
            <p className="text-sm">{event.data.description}</p>
          )}
        </div>
      );

    case "invoice":
      return (
        <div className="space-y-2">
          <div className="flex gap-4 text-xs">
            <span><strong>Amount:</strong> ${event.data.amount?.toLocaleString()}</span>
            <span><strong>Status:</strong> {event.data.paid ? "Paid" : "Outstanding"}</span>
            <span><strong>Invoice #:</strong> {event.data.invoice_number}</span>
          </div>
        </div>
      );

    default:
      return (
        <pre className="text-xs overflow-auto">
          {JSON.stringify(event.data, null, 2)}
        </pre>
      );
  }
}

function TimelineSkeleton() {
  return (
    <Card>
      <CardHeader>
        <div className="h-6 w-40 bg-gray-200 rounded animate-pulse" />
      </CardHeader>
      <CardContent className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-24 bg-gray-100 rounded animate-pulse" />
        ))}
      </CardContent>
    </Card>
  );
}
