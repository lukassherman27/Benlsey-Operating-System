"use client";

import { useParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
  ArrowLeft,
  FileText,
  Heart,
  AlertTriangle,
  Archive,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { format } from "date-fns";
import { ProposalStory } from "@/components/proposals/proposal-story";
import { TaskMiniKanban } from "@/components/tasks/task-mini-kanban";
import { ProposalMeetings } from "@/components/proposals/proposal-meetings";
import { StakeholdersCard } from "@/components/proposal/stakeholders-card";
import { BallInCourt } from "@/components/proposals/ball-in-court";
import { HealthPanel, calculateRisks, calculateHealthScore } from "@/components/proposals/health-panel";
import { ActionSuggestions, generateActionSuggestions } from "@/components/proposals/action-suggestions";
import { ConversationView } from "@/components/proposals/conversation-view";
import { NextActionCard } from "@/components/proposals/next-action-card";
import { HorizontalTimeline } from "@/components/proposals/horizontal-timeline";

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
  const displayName = proposal?.project_name || proposal?.project_code || projectCode;
  const emailCount = timeline?.stats?.total_emails ?? 0;
  const timelineCount = timeline?.stats?.timeline_events ?? 0;

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

  const totalEmailCount = timeline?.stats?.total_emails ?? 0;

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
                    {displayName}
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
                  {proposal?.project_value
                    ? formatCurrency(proposal.project_value, "USD")
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
              ballInCourt={proposal?.ball_in_court || "mutual"}
              waitingFor={proposal?.waiting_for || proposal?.next_steps}
              daysSinceContact={proposal?.days_since_contact}
              lastContactDate={proposal?.last_contact_date}
            />
          </div>

          {/* Health Panel */}
          <div>
            <HealthPanel
              healthScore={calculateHealthScore({
                days_since_contact: proposal?.days_since_contact,
                ball_in_court: proposal?.ball_in_court,
                status: proposal?.status,
                email_count: totalEmailCount,
              })}
              winProbability={proposal?.win_probability ?? null}
              winProbabilityChange={null}
              risks={calculateRisks({
                days_since_contact: proposal?.days_since_contact,
                ball_in_court: proposal?.ball_in_court,
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
            ball_in_court: proposal?.ball_in_court,
            days_since_contact: proposal?.days_since_contact,
            waiting_for: proposal?.waiting_for,
            next_action: proposal?.next_action || proposal?.next_steps,
            status: proposal?.status,
            primary_contact_name: proposal?.primary_contact_name,
            primary_contact_email: proposal?.primary_contact_email,
          });
          return actions.length > 0 ? <ActionSuggestions actions={actions} /> : null;
        })()}

        {/* Next Action Card - Prominent CTA */}
        <NextActionCard
          actionNeeded={proposal?.action_needed || proposal?.next_action || null}
          actionDue={proposal?.action_due || null}
          actionOwner={proposal?.action_owner || null}
          projectCode={projectCode}
          primaryContactEmail={proposal?.primary_contact_email}
          proposalId={proposal?.proposal_id}
        />

        {(emailCount === 0 || timelineCount === 0) && (
          <Card className="border-amber-200 bg-amber-50/60">
            <CardContent className="py-4 flex flex-col gap-2">
              <p className="text-sm font-semibold text-amber-800">Story data is still empty</p>
              <p className="text-sm text-amber-700">
                Link proposal emails to generate the timeline, summaries, and action items.
              </p>
              <div>
                <Button asChild variant="outline" size="sm">
                  <Link href="/emails/review">Review Email Links</Link>
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Horizontal Timeline - Visual proposal journey */}
        <Card className="border-slate-200">
          <CardContent className="py-4">
            <HorizontalTimeline
              currentStatus={proposal?.status || "First Contact"}
              firstContactDate={proposal?.first_contact_date}
              proposalSentDate={proposal?.proposal_sent_date}
              contractSignedDate={proposal?.contract_signed_date}
            />
          </CardContent>
        </Card>
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
            <TaskMiniKanban projectCode={projectCode} />
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

        {/* Archive Tab - Conversation View */}
        <TabsContent value="archive">
          <ConversationView projectCode={projectCode} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
