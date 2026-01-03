"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  FileText,
  Clock,
  CheckCircle,
  ChevronDown,
  ChevronRight,
  MessageSquare,
  Search,
  Loader2,
  AlertCircle,
  Circle,
  CheckCircle2,
  ArrowRight,
  Zap,
} from "lucide-react";
import { format } from "date-fns";
import { cn } from "@/lib/utils";
import { useState } from "react";
import Link from "next/link";

// Types
interface StoryData {
  success: boolean;
  project_code: string;
  project_name: string;
  client: { name: string | null; company: string | null; email: string | null };
  value: number | null;
  currency: string;
  correspondence_summary: string | null;
  internal_notes: string | null;
  remarks: string | null;
  timeline: TimelineEvent[];
  proposal_versions: unknown[];
  events: ProposalEvent[];
  threads: unknown[];
  action_items: ActionItem[];
  current_status: CurrentStatus;
}

interface TimelineEvent {
  type: string;
  date: string | null;
  title: string;
  summary: string | null;
  email_id?: number;
  direction?: string;
  fee_amount?: number;
  is_future?: boolean;
}

interface ActionItem {
  task: string;
  date: string | null;
  source: string;
  priority?: string;
  email_id?: number;
  completed?: boolean;
}

interface ProposalEvent {
  event_id: number;
  event_type: string;
  event_date: string;
  title: string;
  description?: string;
  location?: string;
  attendees?: string;
  is_confirmed: number;
  completed: number;
  outcome?: string;
}

interface CurrentStatus {
  status: string;
  last_contact_date: string | null;
  days_since_contact: number | null;
  email_count: number;
  ball_in_court?: string;
  waiting_for?: string;
  last_action?: string;
  suggested_action?: string;
}

interface ProposalStoryProps {
  projectCode: string;
}

interface CorrectionInfo {
  suggestion_id: number;
  type: string;
  title: string;
  description: string;
}

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  correction?: CorrectionInfo;
}

export function ProposalStory({ projectCode }: ProposalStoryProps) {
  const [showAllMilestones, setShowAllMilestones] = useState(false);
  const [showDetails, setShowDetails] = useState(false);
  const [query, setQuery] = useState("");
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [isQuerying, setIsQuerying] = useState(false);

  const { data, isLoading, error } = useQuery<StoryData>({
    queryKey: ["proposal-story", projectCode],
    queryFn: () => api.getProposalStory(projectCode) as unknown as Promise<StoryData>,
    enabled: !!projectCode,
  });

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "Unknown";
    try {
      return format(new Date(dateStr), "MMM d, yyyy");
    } catch {
      return dateStr.slice(0, 10);
    }
  };

  const handleQuery = async () => {
    if (!query.trim()) return;
    setIsQuerying(true);
    const userQuestion = query.trim();
    setQuery("");

    const newHistory: ChatMessage[] = [...chatHistory, { role: "user", content: userQuestion }];
    setChatHistory(newHistory);

    try {
      const result = await api.proposalChat(
        projectCode,
        userQuestion,
        true,
        chatHistory.map(m => ({ role: m.role, content: m.content }))
      );
      const answer = result.success && result.answer
        ? result.answer
        : result.detail
        ? `Error: ${result.detail}`
        : "No answer found for that question";

      const assistantMsg: ChatMessage = { role: "assistant", content: answer };
      if (result.correction_created) {
        assistantMsg.correction = result.correction_created;
      }

      setChatHistory([...newHistory, assistantMsg]);
    } catch {
      setChatHistory([...newHistory, { role: "assistant", content: "Failed to query. Try again." }]);
    }
    setIsQuerying(false);
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-32 w-full" />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <Skeleton className="h-48 w-full" />
          <Skeleton className="h-48 w-full" />
        </div>
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <Card className="border-destructive">
        <CardContent className="pt-6">
          <p className="text-destructive">Failed to load proposal story</p>
        </CardContent>
      </Card>
    );
  }

  const { correspondence_summary, internal_notes, timeline, action_items, current_status, remarks } = data;

  const hasStory =
    Boolean(correspondence_summary || internal_notes || remarks) ||
    (timeline?.length || 0) > 0 ||
    (action_items?.length || 0) > 0;

  if (!hasStory) {
    return (
      <Card className="border-slate-200">
        <CardContent className="py-10 text-center space-y-3">
          <AlertCircle className="mx-auto h-10 w-10 text-slate-400" />
          <p className="text-lg font-semibold text-slate-800">No story data yet</p>
          <p className="text-sm text-slate-500 max-w-md mx-auto">
            Link emails and run extraction to build the proposal timeline, key milestones,
            and action items.
          </p>
          <div className="flex justify-center gap-2 pt-2">
            <Button asChild variant="outline">
              <Link href="/emails/review">Review Email Links</Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Filter timeline - skip garbage first contact summaries
  const cleanTimeline = timeline.filter(event => {
    if (event.type === "first_contact" && event.summary?.toLowerCase().includes("not pertain")) return false;
    return true;
  });

  const displayedMilestones = showAllMilestones ? cleanTimeline : cleanTimeline.slice(0, 6);

  // Determine ball in court display
  const ballInCourt = current_status?.ball_in_court;
  const waitingFor = current_status?.waiting_for;
  const suggestedAction = current_status?.suggested_action;

  // Get pending action items (not completed)
  const pendingActions = action_items?.filter(a => !a.completed) || [];
  const completedActions = action_items?.filter(a => a.completed) || [];

  return (
    <div className="space-y-6">
      {/* ===== EXECUTIVE SUMMARY ===== */}
      <Card className="border-2 border-slate-200 bg-gradient-to-br from-slate-50 to-white">
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-lg">
            <FileText className="h-5 w-5 text-slate-600" />
            Executive Summary
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="prose prose-sm max-w-none text-slate-700">
            {correspondence_summary ? (
              <p className="leading-relaxed">{correspondence_summary}</p>
            ) : remarks ? (
              <p className="leading-relaxed">{remarks}</p>
            ) : (
              <div className="text-center py-4">
                <p className="text-slate-400 italic mb-2">No summary available yet.</p>
                <p className="text-xs text-slate-400">
                  A summary will be generated once emails are linked to this proposal.
                </p>
              </div>
            )}
          </div>

            {/* Ball in Court / Next Action */}
            {(ballInCourt || waitingFor || suggestedAction) && (
              <div className="mt-4 pt-4 border-t border-slate-200">
                <div className="flex flex-wrap gap-3 items-center">
                  {ballInCourt && (
                    <Badge
                      className={cn(
                        "text-sm px-3 py-1",
                        ballInCourt.toLowerCase() === "us"
                          ? "bg-amber-100 text-amber-800 border-amber-300"
                          : "bg-blue-100 text-blue-800 border-blue-300"
                      )}
                    >
                      Ball with: {ballInCourt.toUpperCase()}
                    </Badge>
                  )}
                  {waitingFor && (
                    <span className="text-sm text-slate-600">
                      <span className="font-medium">Waiting for:</span> {waitingFor}
                    </span>
                  )}
                </div>
                {suggestedAction && (
                  <div className="mt-2 flex items-start gap-2">
                    <ArrowRight className="h-4 w-4 text-emerald-600 mt-0.5 flex-shrink-0" />
                    <span className="text-sm text-emerald-700 font-medium">{suggestedAction}</span>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

      {/* ===== TWO COLUMN GRID: ACTION ITEMS + STAKEHOLDER STATUS ===== */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Action Items */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-base">
              <Zap className="h-4 w-4 text-amber-600" />
              Action Items
              {pendingActions.length > 0 && (
                <Badge variant="secondary" className="ml-auto">
                  {pendingActions.length} pending
                </Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {pendingActions.length === 0 && completedActions.length === 0 ? (
              <p className="text-sm text-slate-400">No action items extracted yet.</p>
            ) : (
              <div className="space-y-2">
                {pendingActions.slice(0, 5).map((item, i) => (
                  <div key={i} className="flex items-start gap-2 p-2 rounded-lg hover:bg-slate-50">
                    <Circle className="h-4 w-4 text-slate-300 mt-0.5 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-slate-700">{item.task}</p>
                      <div className="flex items-center gap-2 mt-1">
                        {item.date && (
                          <span className="text-xs text-slate-400">{formatDate(item.date)}</span>
                        )}
                        {item.priority && (
                          <Badge
                            variant="outline"
                            className={cn(
                              "text-xs",
                              item.priority === "high" && "border-red-300 text-red-600",
                              item.priority === "medium" && "border-amber-300 text-amber-600"
                            )}
                          >
                            {item.priority}
                          </Badge>
                        )}
                        <span className="text-xs text-slate-400">via {item.source}</span>
                      </div>
                    </div>
                  </div>
                ))}
                {completedActions.length > 0 && (
                  <div className="pt-2 mt-2 border-t">
                    <p className="text-xs text-slate-400 mb-2">{completedActions.length} completed</p>
                    {completedActions.slice(0, 2).map((item, i) => (
                      <div key={i} className="flex items-start gap-2 p-2 opacity-60">
                        <CheckCircle2 className="h-4 w-4 text-emerald-500 mt-0.5 flex-shrink-0" />
                        <p className="text-sm text-slate-500 line-through">{item.task}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Current Status Summary */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-base">
              <AlertCircle className="h-4 w-4 text-blue-600" />
              Current Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-600">Status</span>
                <Badge variant="outline">{current_status?.status || "Unknown"}</Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-600">Last Contact</span>
                <span className="text-sm font-medium">
                  {current_status?.days_since_contact != null
                    ? `${current_status.days_since_contact} days ago`
                    : "Never"}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-600">Communications</span>
                <span className="text-sm font-medium">{current_status?.email_count || 0} tracked</span>
              </div>
              {current_status?.last_action && (
                <div className="pt-2 border-t">
                  <p className="text-xs text-slate-400 mb-1">Last Action</p>
                  <p className="text-sm text-slate-700">{current_status.last_action}</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ===== KEY MILESTONES ===== */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-base">
            <Clock className="h-4 w-4 text-slate-500" />
            Key Milestones
            <Badge variant="secondary" className="ml-auto">{cleanTimeline.length}</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {cleanTimeline.length === 0 ? (
            <p className="text-sm text-slate-400 text-center py-4">No milestones recorded yet.</p>
          ) : (
            <>
              <div className="relative">
                {/* Timeline line */}
                <div className="absolute left-[59px] top-0 bottom-0 w-0.5 bg-slate-200" />

                <div className="space-y-3">
                  {displayedMilestones.map((event, i) => {
                    const typeColors: Record<string, string> = {
                      first_contact: "bg-blue-100 text-blue-700 border-blue-200",
                      proposal_sent: "bg-emerald-100 text-emerald-700 border-emerald-200",
                      proposal_version: "bg-purple-100 text-purple-700 border-purple-200",
                      meeting: "bg-indigo-100 text-indigo-700 border-indigo-200",
                      meeting_scheduled: "bg-indigo-100 text-indigo-700 border-indigo-200",
                      upcoming_meeting: "bg-amber-100 text-amber-700 border-amber-200",
                      client_response: "bg-cyan-100 text-cyan-700 border-cyan-200",
                      status_change: "bg-slate-100 text-slate-700 border-slate-200",
                    };
                    const colorClass = typeColors[event.type] || "bg-slate-100 text-slate-600 border-slate-200";

                    return (
                      <div key={i} className="flex items-start gap-3 relative">
                        <div className="text-xs text-muted-foreground w-14 text-right pt-0.5 flex-shrink-0">
                          {formatDate(event.date).replace(", 2025", "").replace(", 2024", "")}
                        </div>
                        <div className={cn(
                          "w-3 h-3 rounded-full border-2 z-10 bg-white",
                          event.is_future ? "border-dashed border-amber-400" : colorClass.replace("bg-", "border-").split(" ")[0]
                        )} />
                        <div className="flex-1 pb-3">
                          <div className="flex items-center gap-2 flex-wrap">
                            <Badge className={cn("text-xs", colorClass)}>
                              {event.type.replace(/_/g, " ")}
                            </Badge>
                            <span className="font-medium text-sm">{event.title}</span>
                            {event.fee_amount && (
                              <Badge className="bg-emerald-100 text-emerald-700 text-xs">
                                ${(event.fee_amount / 1000000).toFixed(2)}M
                              </Badge>
                            )}
                            {event.is_future && (
                              <Badge variant="outline" className="text-xs border-amber-300 text-amber-600">
                                Upcoming
                              </Badge>
                            )}
                          </div>
                          {event.summary && (
                            <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{event.summary}</p>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {cleanTimeline.length > 6 && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full mt-3"
                  onClick={() => setShowAllMilestones(!showAllMilestones)}
                >
                  {showAllMilestones ? (
                    <>Show fewer milestones</>
                  ) : (
                    <>Show all {cleanTimeline.length} milestones</>
                  )}
                </Button>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* ===== PROPOSAL DETAILS (Collapsible) ===== */}
      {internal_notes && (
        <Card className="bg-slate-50/50">
          <CardHeader
            className="pb-2 cursor-pointer hover:bg-slate-100/50 transition-colors"
            onClick={() => setShowDetails(!showDetails)}
          >
            <CardTitle className="flex items-center justify-between text-base">
              <div className="flex items-center gap-2">
                <FileText className="h-4 w-4 text-slate-500" />
                <span>Internal Notes</span>
                <Badge variant="secondary" className="text-xs">Fee History, Scope, Notes</Badge>
              </div>
              {showDetails ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
            </CardTitle>
          </CardHeader>
          {showDetails && (
            <CardContent>
              <pre className="text-sm whitespace-pre-wrap font-sans text-slate-700 bg-white p-4 rounded-lg border">
                {internal_notes}
              </pre>
            </CardContent>
          )}
        </Card>
      )}

      {/* ===== ASK ABOUT THIS PROPOSAL ===== */}
      <Card className="bg-slate-50">
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-base">
            <Search className="h-4 w-4 text-slate-500" />
            Ask About This Proposal
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {/* Chat History */}
          {chatHistory.length > 0 && (
            <div className="space-y-3 max-h-[400px] overflow-y-auto">
              {chatHistory.map((msg, i) => (
                <div key={i} className={cn(
                  "p-3 rounded-lg text-sm",
                  msg.role === "user"
                    ? "bg-blue-50 border border-blue-200 ml-8"
                    : "bg-white border mr-8"
                )}>
                  <p className="text-xs font-medium text-slate-500 mb-1">
                    {msg.role === "user" ? "You" : "Assistant"}
                  </p>
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                  {msg.correction && (
                    <div className="mt-3 p-3 bg-emerald-50 border border-emerald-200 rounded-lg">
                      <div className="flex items-center gap-2 text-emerald-700 mb-1">
                        <CheckCircle className="h-4 w-4" />
                        <span className="font-medium text-sm">Suggestion Created</span>
                      </div>
                      <p className="text-sm text-emerald-800 font-medium">{msg.correction.title}</p>
                      <p className="text-xs text-emerald-600">{msg.correction.description}</p>
                      <a
                        href="/admin/suggestions"
                        className="text-xs text-emerald-700 underline mt-2 inline-block hover:text-emerald-900"
                      >
                        Review in Suggestions &rarr;
                      </a>
                    </div>
                  )}
                </div>
              ))}
              {isQuerying && (
                <div className="p-3 bg-white rounded-lg border text-sm mr-8">
                  <p className="text-xs font-medium text-slate-500 mb-1">Assistant</p>
                  <p className="text-slate-400 flex items-center gap-2">
                    <Loader2 className="h-3 w-3 animate-spin" /> Thinking...
                  </p>
                </div>
              )}
            </div>
          )}
          {/* Input */}
          <div className="flex gap-2">
            <Textarea
              placeholder="e.g., What contract terms did the client ask about?"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleQuery(); } }}
              className="min-h-[50px] text-sm bg-white flex-1"
            />
            <Button onClick={handleQuery} disabled={isQuerying || !query.trim()} size="sm" className="self-end">
              {isQuerying ? <Loader2 className="h-4 w-4 animate-spin" /> : <MessageSquare className="h-4 w-4" />}
            </Button>
          </div>
          {chatHistory.length > 0 && (
            <Button variant="ghost" size="sm" onClick={() => setChatHistory([])} className="text-xs text-slate-400">
              Clear conversation
            </Button>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
