"use client";

import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Mail, Mic, AlertCircle, DollarSign, Flag,
  ChevronDown, ChevronRight, Calendar, CheckCircle,
  Sparkles, FileText, TrendingUp, Clock, Send, Inbox,
  Users, Building2, Globe, Filter
} from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useState } from "react";
import { format, parseISO, isValid } from "date-fns";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api";

interface TimelineEvent {
  type: "email" | "transcript" | "rfi" | "invoice" | "milestone" | "status_change" | "suggestion_approved" | "first_contact" | "proposal_sent";
  date: string;
  title: string;
  summary: string;
  id: number;
  // Email specific
  sender?: string;
  sender_name?: string;
  recipient_emails?: string;
  confidence?: number;
  link_method?: string;
  email_category?: "internal" | "client" | "external";
  direction?: "sent" | "received";
  category?: string;
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
  email_category_counts?: {
    internal: number;
    client: number;
    external: number;
  };
  unique_people?: string[];
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

// Email category styling
const EMAIL_CATEGORY_STYLES: Record<string, { badge: string; icon: typeof Users; label: string }> = {
  internal: {
    badge: "bg-slate-100 text-slate-700 border-slate-200",
    icon: Users,
    label: "Internal",
  },
  client: {
    badge: "bg-teal-50 text-teal-700 border-teal-200",
    icon: Building2,
    label: "Client",
  },
  external: {
    badge: "bg-purple-50 text-purple-700 border-purple-200",
    icon: Globe,
    label: "External",
  },
};

const DIRECTION_STYLES: Record<string, { badge: string; icon: typeof Send; label: string }> = {
  sent: {
    badge: "bg-blue-50 text-blue-700 border-blue-200",
    icon: Send,
    label: "Sent",
  },
  received: {
    badge: "bg-emerald-50 text-emerald-700 border-emerald-200",
    icon: Inbox,
    label: "Received",
  },
};

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
  const [personFilter, setPersonFilter] = useState<string>("all");
  const [emailCategoryFilter, setEmailCategoryFilter] = useState<string>("all");

  const { data, isLoading, error } = useQuery({
    queryKey: ["unified-timeline", projectCode, typeFilter, personFilter, limit],
    queryFn: () => api.getUnifiedTimeline(projectCode, {
      limit,
      item_types: typeFilter !== "all" ? typeFilter : undefined,
      person: personFilter !== "all" ? personFilter : undefined,
    }) as unknown as Promise<TimelineResponse>,
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
  const emailCategoryCounts = data?.email_category_counts || { internal: 0, client: 0, external: 0 };
  const uniquePeople = data?.unique_people || [];

  // Apply client-side email category filter
  const filteredEvents = events.filter((event) => {
    if (emailCategoryFilter === "all") return true;
    if (event.type !== "email") return emailCategoryFilter === "all";
    return event.email_category === emailCategoryFilter;
  });

  // Group events by month for date markers
  const eventsByMonth: Map<string, TimelineEvent[]> = new Map();
  filteredEvents.forEach((event) => {
    const monthYear = getMonthYear(event.date) || "Unknown";
    if (!eventsByMonth.has(monthYear)) {
      eventsByMonth.set(monthYear, []);
    }
    eventsByMonth.get(monthYear)!.push(event);
  });

  const filterTypes = ["all", "email", "transcript", "rfi", "invoice", "status_change"];
  const emailCategoryTypes = ["all", "internal", "client", "external"];

  return (
    <Card>
      <CardHeader className="pb-3 space-y-3">
        <div className="flex flex-row items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            {showStory ? "The Story" : "Project Timeline"}
            <Badge variant="secondary" className="ml-2">
              {filteredEvents.length} events
            </Badge>
          </CardTitle>

          {/* Person Filter */}
          {uniquePeople.length > 0 && (
            <Select value={personFilter} onValueChange={setPersonFilter}>
              <SelectTrigger className="w-[180px] h-8 text-xs">
                <Filter className="h-3 w-3 mr-1" />
                <SelectValue placeholder="Filter by person" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All People</SelectItem>
                {uniquePeople.map((person) => (
                  <SelectItem key={person} value={person}>
                    {person}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        </div>

        {/* Type Filters */}
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

        {/* Email Category Filters (only show when emails are selected) */}
        {(typeFilter === "all" || typeFilter === "email") && itemCounts.email > 0 && (
          <div className="flex gap-1.5 flex-wrap items-center">
            <span className="text-xs text-slate-500 mr-1">Email type:</span>
            {emailCategoryTypes.map((cat) => {
              const style = cat !== "all" ? EMAIL_CATEGORY_STYLES[cat] : null;
              const count = cat === "all"
                ? emailCategoryCounts.internal + emailCategoryCounts.client + emailCategoryCounts.external
                : emailCategoryCounts[cat as keyof typeof emailCategoryCounts] || 0;
              return (
                <Badge
                  key={cat}
                  variant="outline"
                  className={cn(
                    "cursor-pointer capitalize text-xs px-2 py-0.5",
                    emailCategoryFilter === cat
                      ? style?.badge || "bg-slate-900 text-white border-slate-900"
                      : "hover:bg-slate-100"
                  )}
                  onClick={() => setEmailCategoryFilter(cat)}
                >
                  {cat === "all" ? "All" : style?.label}
                  {` (${count})`}
                </Badge>
              );
            })}
          </div>
        )}
      </CardHeader>
      <CardContent className="pt-0">
        {filteredEvents.length === 0 ? (
          <div className="text-center py-12">
            <Clock className="h-12 w-12 mx-auto text-slate-200 mb-3" />
            <p className="text-muted-foreground">
              {events.length === 0 ? "No events found for this project" : "No events match the current filters"}
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
                                  <div className="flex items-center gap-2 min-w-0">
                                    <p className="font-medium text-sm truncate">{event.title}</p>
                                    {/* Email category and direction badges */}
                                    {event.type === "email" && (
                                      <div className="flex gap-1 flex-shrink-0">
                                        {event.email_category && EMAIL_CATEGORY_STYLES[event.email_category] && (
                                          <Badge
                                            variant="outline"
                                            className={cn(
                                              "text-[10px] px-1.5 py-0 h-4 font-normal",
                                              EMAIL_CATEGORY_STYLES[event.email_category].badge
                                            )}
                                          >
                                            {EMAIL_CATEGORY_STYLES[event.email_category].label}
                                          </Badge>
                                        )}
                                        {event.direction && DIRECTION_STYLES[event.direction] && (
                                          <Badge
                                            variant="outline"
                                            className={cn(
                                              "text-[10px] px-1.5 py-0 h-4 font-normal",
                                              DIRECTION_STYLES[event.direction].badge
                                            )}
                                          >
                                            {DIRECTION_STYLES[event.direction].label}
                                          </Badge>
                                        )}
                                      </div>
                                    )}
                                  </div>
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
              <span><strong>From:</strong> {event.sender_name || event.sender}</span>
            )}
            {event.recipient_emails && (
              <span><strong>To:</strong> {event.recipient_emails.slice(0, 50)}{event.recipient_emails.length > 50 ? '...' : ''}</span>
            )}
          </div>
          <div className="flex gap-4 text-xs flex-wrap">
            {event.confidence && (
              <span><strong>Match Confidence:</strong> {Math.round(event.confidence * 100)}%</span>
            )}
            {event.link_method && (
              <span><strong>Linked by:</strong> {event.link_method}</span>
            )}
            {event.category && (
              <span><strong>Category:</strong> {event.category}</span>
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
