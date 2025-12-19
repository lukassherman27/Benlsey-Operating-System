"use client";

import { useParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import {
  ArrowLeft,
  Clock,
  Mail,
  FileText,
  Users,
  Briefcase,
  Heart,
  AlertTriangle,
  Search,
  Archive,
  Send,
  Inbox,
  Paperclip,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { format, formatDistanceToNow } from "date-fns";
import { useState } from "react";
import { ProposalStory } from "@/components/proposals/proposal-story";
import { ProposalTasks } from "@/components/proposals/proposal-tasks";
import { ProposalMeetings } from "@/components/proposals/proposal-meetings";
import { StakeholdersCard } from "@/components/proposal/stakeholders-card";
import { BallInCourt } from "@/components/proposals/ball-in-court";
import { HealthPanel, calculateRisks, calculateHealthScore } from "@/components/proposals/health-panel";
import { ActionSuggestions, generateActionSuggestions } from "@/components/proposals/action-suggestions";

// Calculate health score from days since contact
function getHealthInfo(daysSinceContact: number | null | undefined): {
  score: "healthy" | "ok" | "attention" | "at_risk";
  label: string;
  color: string;
  icon: typeof Heart | typeof AlertTriangle;
} {
  const days = daysSinceContact ?? 999;
  if (days <= 7) {
    return { score: "healthy", label: "Healthy", color: "bg-emerald-100 text-emerald-700 border-emerald-200", icon: Heart };
  } else if (days <= 14) {
    return { score: "ok", label: "OK", color: "bg-amber-100 text-amber-700 border-amber-200", icon: Heart };
  } else if (days <= 30) {
    return { score: "attention", label: "Needs Attention", color: "bg-orange-100 text-orange-700 border-orange-200", icon: AlertTriangle };
  } else {
    return { score: "at_risk", label: "At Risk", color: "bg-red-100 text-red-700 border-red-200", icon: AlertTriangle };
  }
}

export default function ProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [emailSearch, setEmailSearch] = useState("");

  // Decode the project code in case it's URL-encoded (e.g., "24%20BK-015" -> "24 BK-015")
  const rawProjectCode = params?.projectCode as string;
  const projectCode = rawProjectCode ? decodeURIComponent(rawProjectCode) : "";

  const proposalQuery = useQuery({
    queryKey: ["proposal", projectCode],
    queryFn: () => api.getProposalDetail(projectCode),
    enabled: !!projectCode,
  });

  const timelineQuery = useQuery({
    queryKey: ["proposal-timeline", projectCode],
    queryFn: () => api.getProposalTimeline(projectCode),
    enabled: !!projectCode,
  });

  const isLoading = proposalQuery.isLoading;
  const proposal = proposalQuery.data;
  const timeline = timelineQuery.data;

  const formatDate = (value?: string | null) => {
    if (!value) return "Not set";
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return "Invalid date";
    return format(parsed, "MMM d, yyyy");
  };

  const formatCurrency = (value?: number | null, currency = "USD") => {
    if (!value) return "Not set";
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency,
    }).format(value);
  };

  const formatRelativeDate = (dateStr: string | null | undefined) => {
    if (!dateStr) return "";
    try {
      const date = new Date(dateStr);
      const now = new Date();
      const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
      if (diffDays < 7) {
        return formatDistanceToNow(date, { addSuffix: true });
      }
      return format(date, "MMM d");
    } catch {
      return String(dateStr);
    }
  };

  // Extract and filter emails for archive search
  const timelineEmails = (timeline?.timeline ?? []).filter(
    (item: { type?: string }) => item.type === "email"
  );
  const directEmails = timeline?.emails ?? [];
  const allEmails = [...directEmails, ...timelineEmails];
  const seenIds = new Set<number>();
  const uniqueEmails = allEmails.filter((e: any) => {
    const id = e.email_id || e.id;
    if (!id || seenIds.has(id)) return false;
    seenIds.add(id);
    return true;
  });

  // Filter emails by search
  const filteredEmails = emailSearch.trim()
    ? uniqueEmails.filter((e: any) => {
        const subject = (e.subject || e.title || "").toLowerCase();
        const sender = (e.sender_email || e.from || "").toLowerCase();
        const snippet = (e.snippet || e.ai_summary || "").toLowerCase();
        const search = emailSearch.toLowerCase();
        return subject.includes(search) || sender.includes(search) || snippet.includes(search);
      })
    : uniqueEmails;

  const totalEmailCount = timeline?.stats?.total_emails ?? uniqueEmails.length;

  if (proposalQuery.isError) {
    return (
      <div className="p-6">
        <Button
          variant="ghost"
          onClick={() => router.back()}
          className="mb-4"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Button>
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="text-destructive">Error Loading Project</CardTitle>
            <CardDescription>
              {proposalQuery.error instanceof Error
                ? proposalQuery.error.message
                : "Failed to load project details"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Project code: {projectCode}
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="p-6 space-y-6">
        <Skeleton className="h-10 w-32" />
        <Skeleton className="h-64 w-full" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  const statusLabel = proposal?.status
    ? proposal.status.replace(/[_-]/g, " ").toUpperCase()
    : "Not set";

  return (
    <div className="p-4 sm:p-6 space-y-4 sm:space-y-6 max-w-[100vw] overflow-x-hidden">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <Button
          variant="ghost"
          onClick={() => router.back()}
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Proposals
        </Button>
        <div className="flex gap-2 flex-wrap">
          <Badge variant={proposal?.is_active_project === 1 ? "default" : "secondary"}>
            {proposal?.is_active_project === 1 ? "Active Project" : "Proposal"}
          </Badge>
          <Badge variant="outline">{statusLabel}</Badge>
          {(() => {
            const health = getHealthInfo(proposal?.days_since_contact);
            const HealthIcon = health.icon;
            return (
              <Badge className={cn("flex items-center gap-1", health.color)}>
                <HealthIcon className="h-3 w-3" />
                {health.label}
              </Badge>
            );
          })()}
        </div>
      </div>

      {/* Hero Section - Redesigned */}
      <div className="space-y-4">
        {/* Title Card */}
        <Card className="border-2">
          <CardContent className="p-4 sm:p-6">
            <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
              <div className="space-y-3 flex-1 min-w-0">
                <div>
                  <h1 className="text-2xl sm:text-3xl font-bold break-words">
                    {proposal?.project_name ?? "Unknown Project"}
                  </h1>
                  <p className="text-lg text-muted-foreground break-words mt-1">
                    {proposal?.client_company || proposal?.client_name || "Client not specified"}
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Badge className="text-sm px-3 py-1 font-mono">
                    {proposal?.project_code ?? projectCode}
                  </Badge>
                  {proposal?.phase && (
                    <Badge variant="secondary" className="text-sm px-3 py-1">
                      {proposal.phase}
                    </Badge>
                  )}
                  <Badge variant="outline" className="text-sm px-3 py-1">
                    PM: {proposal?.pm ?? "TBD"}
                  </Badge>
                </div>
              </div>

              {/* Value Card */}
              <div className="lg:border-l lg:pl-6 pt-4 lg:pt-0 border-t lg:border-t-0 text-center lg:text-right">
                <p className="text-xs uppercase tracking-wider text-muted-foreground mb-1">
                  Contract Value
                </p>
                <span className="text-2xl sm:text-3xl font-bold text-slate-800">
                  {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                  {(proposal as any)?.project_value
                    ? formatCurrency((proposal as any).project_value, "USD")
                    : "TBD"}
                </span>
                <p className="text-xs text-muted-foreground mt-1">
                  {totalEmailCount} communications tracked
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Ball in Court + Health Panel + Actions Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Ball in Court - Takes 2 columns on large */}
          <div className="lg:col-span-2">
            <BallInCourt
              ballInCourt={(proposal as any)?.ball_in_court || "mutual"}
              waitingFor={proposal?.waiting_for || (proposal as any)?.next_steps}
              daysSinceContact={proposal?.days_since_contact}
              lastContactDate={proposal?.last_contact_date}
            />
          </div>

          {/* Health Panel */}
          <div>
            <HealthPanel
              healthScore={calculateHealthScore({
                days_since_contact: proposal?.days_since_contact,
                ball_in_court: (proposal as any)?.ball_in_court,
                status: proposal?.status,
                email_count: totalEmailCount,
              })}
              winProbability={(proposal as any)?.win_probability ?? null}
              winProbabilityChange={null}
              risks={calculateRisks({
                days_since_contact: proposal?.days_since_contact,
                ball_in_court: (proposal as any)?.ball_in_court,
                status: proposal?.status,
                next_action: proposal?.next_action || proposal?.next_steps,
                waiting_for: proposal?.waiting_for,
              })}
            />
          </div>
        </div>

        {/* Action Suggestions */}
        {(() => {
          const actions = generateActionSuggestions({
            project_code: projectCode,
            ball_in_court: (proposal as any)?.ball_in_court,
            days_since_contact: proposal?.days_since_contact,
            waiting_for: proposal?.waiting_for,
            next_action: proposal?.next_action || proposal?.next_steps,
            status: proposal?.status,
            primary_contact_name: (proposal as any)?.primary_contact_name,
            primary_contact_email: (proposal as any)?.primary_contact_email,
          });
          return actions.length > 0 ? <ActionSuggestions actions={actions} /> : null;
        })()}
      </div>

      {/* Main Content Tabs - Simplified: Story | Team | Documents | Archive */}
      <Tabs defaultValue="story" className="space-y-4">
        <div className="w-full overflow-x-auto">
          <TabsList className="inline-flex w-full lg:w-auto">
            <TabsTrigger value="story">Story</TabsTrigger>
            <TabsTrigger value="team">Team</TabsTrigger>
            <TabsTrigger value="documents">
              Documents ({timeline?.stats?.total_documents ?? 0})
            </TabsTrigger>
            <TabsTrigger value="archive" className="flex items-center gap-1">
              <Archive className="h-3 w-3" />
              Archive
            </TabsTrigger>
          </TabsList>
        </div>

        {/* Story Tab - Synthesized Intelligence View */}
        <TabsContent value="story" className="space-y-4">
          {/* Tasks and Meetings widgets */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <ProposalTasks projectCode={projectCode} />
            <ProposalMeetings projectCode={projectCode} />
          </div>
          {/* Main story component with Executive Summary, Action Items, Milestones */}
          <ProposalStory projectCode={projectCode} />
        </TabsContent>

        {/* Team Tab */}
        <TabsContent value="team" className="space-y-4">
          <StakeholdersCard projectCode={projectCode} />
        </TabsContent>

        {/* Documents Tab */}
        <TabsContent value="documents">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Project Documents
              </CardTitle>
              <CardDescription>
                Proposals, contracts, drawings and other documents
              </CardDescription>
            </CardHeader>
            <CardContent>
              {timelineQuery.isLoading ? (
                <div className="space-y-2">
                  {[1, 2, 3].map((i) => (
                    <Skeleton key={i} className="h-16 w-full" />
                  ))}
                </div>
              ) : timeline?.documents && timeline.documents.length > 0 ? (
                <div className="rounded-md border overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="min-w-[200px]">File Name</TableHead>
                        <TableHead className="min-w-[100px]">Type</TableHead>
                        <TableHead className="min-w-[120px]">Modified Date</TableHead>
                        <TableHead className="text-right min-w-[80px]">Size</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {timeline.documents.map((doc) => (
                        <TableRow key={doc.document_id}>
                          <TableCell className="font-medium truncate max-w-[300px]">
                            {doc.file_name}
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline">{doc.document_type}</Badge>
                          </TableCell>
                          <TableCell className="text-sm">
                            {formatDate(doc.modified_date)}
                          </TableCell>
                          <TableCell className="text-right text-sm">
                            {doc.file_size
                              ? `${(doc.file_size / 1024 / 1024).toFixed(2)} MB`
                              : "Unknown"}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              ) : (
                <p className="text-center py-8 text-muted-foreground">
                  No documents found for this project
                </p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Archive Tab - Searchable Email List */}
        <TabsContent value="archive">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Archive className="h-5 w-5" />
                Email Archive
              </CardTitle>
              <CardDescription>
                Search through all {totalEmailCount} communications related to this proposal
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Search */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <Input
                  placeholder="Search by subject, sender, or content..."
                  value={emailSearch}
                  onChange={(e) => setEmailSearch(e.target.value)}
                  className="pl-10"
                />
              </div>

              {/* Results */}
              {timelineQuery.isLoading ? (
                <div className="space-y-2">
                  {[1, 2, 3].map((i) => (
                    <Skeleton key={i} className="h-16 w-full" />
                  ))}
                </div>
              ) : filteredEmails.length > 0 ? (
                <div className="space-y-2 max-h-[600px] overflow-y-auto">
                  {filteredEmails.map((email: any) => {
                    const sender = email.sender_email || email.from || "";
                    const isOutbound = sender.toLowerCase().includes("@bensley.com");
                    const subject = email.subject || email.title || "(No subject)";
                    const date = email.date_normalized || email.date;
                    const snippet = email.ai_summary || email.snippet;

                    // Extract sender name
                    const nameMatch = sender.match(/^([^<]+)</);
                    const emailMatch = sender.match(/([^@]+)@/);
                    const senderName = nameMatch ? nameMatch[1].trim() : emailMatch ? emailMatch[1] : sender;

                    return (
                      <div
                        key={email.email_id || email.id}
                        className="p-3 rounded-lg border hover:bg-slate-50 transition-colors"
                      >
                        <div className="flex items-start gap-3">
                          <div className="mt-1">
                            {isOutbound ? (
                              <Send className="h-4 w-4 text-blue-500" />
                            ) : (
                              <Inbox className="h-4 w-4 text-green-500" />
                            )}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className="font-medium text-sm">{senderName}</span>
                              <span className="text-xs text-slate-400">
                                {formatRelativeDate(date)}
                              </span>
                              {email.has_attachments === 1 && (
                                <Paperclip className="h-3 w-3 text-slate-400" />
                              )}
                              {email.category && (
                                <Badge variant="outline" className="text-xs">
                                  {email.category}
                                </Badge>
                              )}
                            </div>
                            <p className="text-sm text-slate-700 truncate mt-1">{subject}</p>
                            {snippet && (
                              <p className="text-xs text-slate-500 mt-1 line-clamp-2">{snippet}</p>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : emailSearch.trim() ? (
                <p className="text-center py-8 text-muted-foreground">
                  No emails match your search &ldquo;{emailSearch}&rdquo;
                </p>
              ) : (
                <p className="text-center py-8 text-muted-foreground">
                  No emails found for this project
                </p>
              )}

              {/* Results count */}
              {filteredEmails.length > 0 && (
                <p className="text-xs text-slate-400 text-center">
                  Showing {filteredEmails.length} of {totalEmailCount} communications
                </p>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
