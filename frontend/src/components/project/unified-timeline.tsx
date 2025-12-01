"use client";

import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Mail, Mic, AlertCircle, DollarSign, Flag,
  ChevronDown, ChevronRight, Calendar, CheckCircle,
  Sparkles, FileText, TrendingUp, Clock
} from "lucide-react";
import { useState } from "react";
import { format, parseISO, isValid } from "date-fns";
import { cn } from "@/lib/utils";

interface TimelineEvent {
  type: "email" | "transcript" | "rfi" | "invoice" | "milestone" | "status_change" | "suggestion_approved" | "first_contact" | "proposal_sent";
  date: string;
  title: string;
  summary: string;
  id: number;
  // Email specific
  sender?: string;
  confidence?: number;
  link_method?: string;
  // Transcript specific
  participants?: string;
  duration_seconds?: number;
  // Invoice specific
  invoice_amount?: number;
  payment_amount?: number;
  status?: string;
  // RFI specific
  priority?: string;
  // Status change specific
  old_status?: string;
  new_status?: string;
  changed_by?: string;
}

interface TimelineResponse {
  success: boolean;
  project_code: string;
  timeline: TimelineEvent[];
  total: number;
  item_counts: {
    email: number;
    transcript: number;
    invoice: number;
    rfi: number;
    status_change?: number;
    suggestion_approved?: number;
  };
}

interface UnifiedTimelineProps {
  projectCode: string;
  limit?: number;
  showStory?: boolean; // Enable "story mode" - shows the journey from first contact
}

const EVENT_ICONS: Record<string, typeof Mail> = {
  email: Mail,
  transcript: Mic,
  rfi: AlertCircle,
  invoice: DollarSign,
  milestone: Flag,
  status_change: TrendingUp,
  suggestion_approved: Sparkles,
  first_contact: Mail,
  proposal_sent: FileText,
};

const EVENT_COLORS: Record<string, string> = {
  email: "bg-blue-100 text-blue-700 border-blue-200",
  transcript: "bg-purple-100 text-purple-700 border-purple-200",
  rfi: "bg-orange-100 text-orange-700 border-orange-200",
  invoice: "bg-green-100 text-green-700 border-green-200",
  milestone: "bg-gray-100 text-gray-700 border-gray-200",
  status_change: "bg-indigo-100 text-indigo-700 border-indigo-200",
  suggestion_approved: "bg-emerald-100 text-emerald-700 border-emerald-200",
  first_contact: "bg-cyan-100 text-cyan-700 border-cyan-200",
  proposal_sent: "bg-amber-100 text-amber-700 border-amber-200",
};

const EVENT_DOT_COLORS: Record<string, string> = {
  email: "bg-blue-500",
  transcript: "bg-purple-500",
  rfi: "bg-orange-500",
  invoice: "bg-green-500",
  milestone: "bg-gray-500",
  status_change: "bg-indigo-500",
  suggestion_approved: "bg-emerald-500",
  first_contact: "bg-cyan-500",
  proposal_sent: "bg-amber-500",
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

// Helper to format date safely
const formatDate = (dateStr: string, formatStr: string = "MMM d, yyyy h:mm a") => {
  try {
    const date = parseISO(dateStr);
    if (!isValid(date)) return dateStr;
    return format(date, formatStr);
  } catch {
    return dateStr;
  }
};

// Helper to get month/year header for grouping
const getMonthYear = (dateStr: string) => {
  try {
    const date = parseISO(dateStr);
    if (!isValid(date)) return null;
    return format(date, "MMMM yyyy");
  } catch {
    return null;
  }
};

export function UnifiedTimeline({ projectCode, limit = 20, showStory = false }: UnifiedTimelineProps) {
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
          return { success: true, timeline: [], total: 0, project_code: projectCode, item_counts: { email: 0, transcript: 0, invoice: 0, rfi: 0 } };
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

  const events: TimelineEvent[] = data?.timeline || [];
  const itemCounts = data?.item_counts || { email: 0, transcript: 0, invoice: 0, rfi: 0 };

  // Group events by month for date markers
  const eventsByMonth: Map<string, TimelineEvent[]> = new Map();
  events.forEach((event) => {
    const monthYear = getMonthYear(event.date) || "Unknown";
    if (!eventsByMonth.has(monthYear)) {
      eventsByMonth.set(monthYear, []);
    }
    eventsByMonth.get(monthYear)!.push(event);
  });

  const filterTypes = ["all", "email", "transcript", "rfi", "invoice", "status_change"];

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-3">
        <CardTitle className="flex items-center gap-2">
          <Calendar className="h-5 w-5" />
          {showStory ? "The Story" : "Project Timeline"}
          <Badge variant="secondary" className="ml-2">
            {data?.total || 0} events
          </Badge>
        </CardTitle>
        <div className="flex gap-1.5 flex-wrap">
          {filterTypes.map((type) => (
            <Badge
              key={type}
              variant={typeFilter === type ? "default" : "outline"}
              className={cn(
                "cursor-pointer capitalize text-xs px-2 py-0.5",
                typeFilter !== type && "hover:bg-slate-100"
              )}
              onClick={() => setTypeFilter(type)}
            >
              {type === "all" ? "All" : type.replace(/_/g, " ")}
              {type !== "all" && ` (${itemCounts[type as keyof typeof itemCounts] || 0})`}
            </Badge>
          ))}
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        {events.length === 0 ? (
          <div className="text-center py-12">
            <Clock className="h-12 w-12 mx-auto text-slate-200 mb-3" />
            <p className="text-muted-foreground">
              No events found for this project
            </p>
          </div>
        ) : (
          <div className="relative">
            {/* Vertical timeline line */}
            <div className="absolute left-[19px] top-0 bottom-0 w-0.5 bg-slate-200" />

            {/* Events grouped by month */}
            {Array.from(eventsByMonth.entries()).map(([monthYear, monthEvents], groupIdx) => (
              <div key={monthYear} className="relative">
                {/* Month/Year header marker */}
                <div className="relative flex items-center gap-3 mb-4 mt-4 first:mt-0">
                  <div className="relative z-10 flex items-center justify-center w-10 h-10 rounded-full bg-slate-100 border-2 border-slate-300">
                    <Calendar className="h-4 w-4 text-slate-500" />
                  </div>
                  <span className="text-sm font-semibold text-slate-600 bg-white px-2">
                    {monthYear}
                  </span>
                </div>

                {/* Events in this month */}
                <div className="space-y-3 ml-5">
                  {monthEvents.map((event, eventIdx) => {
                    const Icon = EVENT_ICONS[event.type] || Mail;
                    const colorClass = EVENT_COLORS[event.type] || EVENT_COLORS.email;
                    const dotColor = EVENT_DOT_COLORS[event.type] || "bg-slate-400";
                    const eventKey = `${event.type}-${event.id}`;
                    const isExpanded = expandedEvents.has(eventKey);
                    const isLast = eventIdx === monthEvents.length - 1 && groupIdx === eventsByMonth.size - 1;

                    return (
                      <div key={eventKey} className="relative flex gap-4">
                        {/* Timeline dot */}
                        <div className="relative z-10 flex-shrink-0">
                          <div className={cn(
                            "w-3.5 h-3.5 rounded-full border-2 border-white shadow-sm",
                            dotColor
                          )} />
                          {/* Connecting line to next event */}
                          {!isLast && (
                            <div className="absolute left-[6px] top-4 bottom-[-12px] w-0.5 bg-slate-200" />
                          )}
                        </div>

                        {/* Event card */}
                        <div
                          className={cn(
                            "flex-1 border rounded-lg transition-all duration-200",
                            colorClass,
                            isExpanded ? "shadow-md" : "hover:shadow-sm"
                          )}
                        >
                          <div
                            className="p-3 cursor-pointer"
                            onClick={() => toggleExpanded(eventKey)}
                          >
                            <div className="flex items-start gap-2">
                              <div className="flex items-center gap-1.5 flex-shrink-0">
                                {isExpanded ? (
                                  <ChevronDown className="h-4 w-4" />
                                ) : (
                                  <ChevronRight className="h-4 w-4" />
                                )}
                                <Icon className="h-4 w-4" />
                              </div>
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center justify-between gap-2">
                                  <p className="font-medium text-sm truncate">{event.title}</p>
                                  <span className="text-xs opacity-75 flex-shrink-0 whitespace-nowrap">
                                    {formatDate(event.date)}
                                  </span>
                                </div>
                                <p className="text-xs opacity-80 mt-0.5 line-clamp-2">
                                  {event.summary}
                                </p>
                              </div>
                            </div>
                          </div>

                          {isExpanded && (
                            <div className="px-3 pb-3 pt-2 border-t border-current/10">
                              <EventDetails event={event} />
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function EventDetails({ event }: { event: TimelineEvent }) {
  switch (event.type) {
    case "transcript":
      return (
        <div className="space-y-2">
          <div className="flex gap-4 text-xs flex-wrap">
            {event.participants && (
              <span><strong>Participants:</strong> {event.participants}</span>
            )}
            {event.duration_seconds && (
              <span><strong>Duration:</strong> {Math.round(event.duration_seconds / 60)} min</span>
            )}
          </div>
          <p className="text-sm">{event.summary}</p>
        </div>
      );

    case "email":
      return (
        <div className="space-y-2">
          <div className="flex gap-4 text-xs flex-wrap">
            {event.sender && (
              <span><strong>From:</strong> {event.sender}</span>
            )}
            {event.confidence && (
              <span><strong>Match Confidence:</strong> {Math.round(event.confidence * 100)}%</span>
            )}
            {event.link_method && (
              <span><strong>Linked by:</strong> {event.link_method}</span>
            )}
          </div>
          <p className="text-sm">{event.summary}</p>
        </div>
      );

    case "rfi":
      return (
        <div className="space-y-2">
          <div className="flex gap-4 text-xs flex-wrap">
            {event.status && (
              <span><strong>Status:</strong> {event.status}</span>
            )}
            {event.priority && (
              <span><strong>Priority:</strong> {event.priority}</span>
            )}
          </div>
          <p className="text-sm">{event.summary}</p>
        </div>
      );

    case "invoice":
      return (
        <div className="space-y-2">
          <div className="flex gap-4 text-xs flex-wrap">
            {event.invoice_amount && (
              <span><strong>Amount:</strong> ${event.invoice_amount.toLocaleString()}</span>
            )}
            {event.status && (
              <span><strong>Status:</strong> {event.status}</span>
            )}
            {event.payment_amount !== undefined && event.payment_amount > 0 && (
              <span><strong>Paid:</strong> ${event.payment_amount.toLocaleString()}</span>
            )}
          </div>
        </div>
      );

    case "status_change":
      return (
        <div className="space-y-2">
          <div className="flex gap-4 text-xs flex-wrap items-center">
            {event.old_status && event.new_status && (
              <span className="flex items-center gap-1">
                <Badge variant="outline" className="text-xs bg-slate-100">{event.old_status}</Badge>
                <span>→</span>
                <Badge variant="default" className="text-xs">{event.new_status}</Badge>
              </span>
            )}
            {event.changed_by && (
              <span><strong>Changed by:</strong> {event.changed_by}</span>
            )}
          </div>
          {event.summary && <p className="text-sm">{event.summary}</p>}
        </div>
      );

    case "suggestion_approved":
      return (
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-xs">
            <CheckCircle className="h-4 w-4 text-emerald-600" />
            <span className="text-emerald-700 font-medium">AI suggestion approved</span>
          </div>
          <p className="text-sm">{event.summary}</p>
        </div>
      );

    case "first_contact":
    case "proposal_sent":
      return (
        <div className="space-y-2">
          <div className="flex gap-4 text-xs flex-wrap">
            {event.sender && (
              <span><strong>From:</strong> {event.sender}</span>
            )}
          </div>
          <p className="text-sm">{event.summary}</p>
        </div>
      );

    default:
      return (
        <p className="text-sm">{event.summary}</p>
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
