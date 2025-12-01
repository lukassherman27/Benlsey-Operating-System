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
import {
  ArrowLeft,
  Activity,
  Clock,
  Mail,
  FileText,
  DollarSign,
  Calendar,
  Users,
  AlertCircle,
  CheckCircle,
  TrendingUp,
  Briefcase
} from "lucide-react";
import { format } from "date-fns";
import { HealthBadge } from "@/components/dashboard/health-badge";
import { ProposalTimeline } from "@/components/proposals/proposal-timeline";
import { UnifiedTimeline } from "@/components/project/unified-timeline";

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

  const healthQuery = useQuery({
    queryKey: ["proposal-health", projectCode],
    queryFn: () => api.getProposalHealth(projectCode),
    enabled: !!projectCode,
  });

  const timelineQuery = useQuery({
    queryKey: ["proposal-timeline", projectCode],
    queryFn: () => api.getProposalTimeline(projectCode),
    enabled: !!projectCode,
  });

  const briefingQuery = useQuery({
    queryKey: ["proposal-briefing", projectCode],
    queryFn: () => api.getProposalBriefing(projectCode),
    enabled: !!projectCode,
    retry: false,
  });

  const isLoading = proposalQuery.isLoading || healthQuery.isLoading;
  const proposal = proposalQuery.data;
  const health = healthQuery.data;
  const timeline = timelineQuery.data;
  const briefing = briefingQuery.data;

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
        <div className="flex gap-2">
          <Badge variant={proposal?.is_active_project === 1 ? "default" : "secondary"}>
            {proposal?.is_active_project === 1 ? "Active Project" : "Proposal"}
          </Badge>
          <Badge variant="outline">{statusLabel}</Badge>
        </div>
      </div>

      {/* Hero Section */}
      <Card className="border-2">
        <CardContent className="p-4 sm:p-6 lg:p-8">
          <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-6">
            <div className="space-y-4 flex-1 min-w-0">
              <div>
                <p className="text-xs uppercase tracking-wider text-muted-foreground mb-2">
                  Project Details
                </p>
                <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold mb-2 break-words">
                  {proposal?.project_name ?? "Unknown Project"}
                </h1>
                <p className="text-base sm:text-lg lg:text-xl text-muted-foreground break-words">
                  {proposal?.client_name ?? "Client not specified"}
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
              </div>
            </div>

            {/* Health Score */}
            <div className="text-center lg:border-l lg:pl-8 pt-4 lg:pt-0 border-t lg:border-t-0">
              <p className="text-xs uppercase tracking-wider text-muted-foreground mb-2">
                Health Score
              </p>
              <div className="flex items-center justify-center gap-3">
                <span className="text-4xl sm:text-5xl font-bold">
                  {health?.health_score != null
                    ? Math.round(health.health_score)
                    : "—"}
                </span>
                <Activity className="h-5 w-5 sm:h-6 sm:w-6 text-muted-foreground" />
              </div>
              <div className="mt-3">
                <HealthBadge status={health?.health_status} />
              </div>
              {proposal?.health_calculated === false && (
                <Badge variant="outline" className="mt-2 text-xs">
                  Preliminary estimate
                </Badge>
              )}
            </div>
          </div>

          <Separator className="my-6" />

          {/* Quick Stats */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="space-y-1">
              <p className="text-xs text-muted-foreground flex items-center gap-1">
                <Users className="h-3 w-3" />
                Project Manager
              </p>
              <p className="font-semibold">{proposal?.pm ?? "Not assigned"}</p>
            </div>
            <div className="space-y-1">
              <p className="text-xs text-muted-foreground flex items-center gap-1">
                <Clock className="h-3 w-3" />
                Last Contact
              </p>
              <p className="font-semibold">
                {proposal?.days_since_contact != null
                  ? `${proposal.days_since_contact} days ago`
                  : "Never"}
              </p>
              <p className="text-xs text-muted-foreground">
                {formatDate(proposal?.last_contact_date)}
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-xs text-muted-foreground flex items-center gap-1">
                <TrendingUp className="h-3 w-3" />
                Win Probability
              </p>
              <p className="font-semibold">
                {proposal?.win_probability != null
                  ? `${Math.round(proposal.win_probability * 100)}%`
                  : "Not set"}
              </p>
            </div>
            <div className="space-y-1 min-w-0">
              <p className="text-xs text-muted-foreground flex items-center gap-1">
                <Briefcase className="h-3 w-3" />
                Next Action
              </p>
              <p className="font-semibold text-sm truncate">
                {proposal?.next_action ?? "No action set"}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Content Tabs */}
      <Tabs defaultValue="overview" className="space-y-4">
        <div className="w-full overflow-x-auto">
          <TabsList className="inline-flex w-full lg:w-auto">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="emails">
              Emails ({timeline?.stats?.total_emails ?? 0})
            </TabsTrigger>
            <TabsTrigger value="documents">
              Docs ({timeline?.stats?.total_documents ?? 0})
            </TabsTrigger>
            <TabsTrigger value="financials">Financials</TabsTrigger>
            <TabsTrigger value="timeline">Timeline</TabsTrigger>
          </TabsList>
        </div>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            {/* Health Breakdown */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5" />
                  Health Breakdown
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {health?.factors && Object.keys(health.factors).length > 0 ? (
                  <div className="space-y-2">
                    {Object.entries(health.factors).map(([key, value]) => (
                      <div key={key} className="flex justify-between items-center">
                        <span className="text-sm font-medium">
                          {key.replace(/_/g, " ")}
                        </span>
                        <span className="text-sm text-muted-foreground">
                          {value ?? "N/A"}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    No detailed factors available
                  </p>
                )}

                {health?.recommendation && (
                  <>
                    <Separator />
                    <div>
                      <p className="text-sm font-semibold mb-1">Recommendation</p>
                      <p className="text-sm text-muted-foreground">
                        {health.recommendation}
                      </p>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>

            {/* Risks */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertCircle className="h-5 w-5" />
                  Identified Risks
                </CardTitle>
              </CardHeader>
              <CardContent>
                {health?.risks && health.risks.length > 0 ? (
                  <div className="space-y-3">
                    {health.risks.map((risk, index) => (
                      <div
                        key={index}
                        className="p-3 rounded-lg border bg-muted/50"
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-semibold text-sm">{risk.type}</span>
                          <Badge
                            variant={
                              risk.severity === "high"
                                ? "destructive"
                                : risk.severity === "medium"
                                ? "default"
                                : "secondary"
                            }
                          >
                            {risk.severity}
                          </Badge>
                        </div>
                        <p className="text-xs text-muted-foreground">
                          {risk.description}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    No risks identified
                  </p>
                )}
              </CardContent>
            </Card>

            {/* Contact Info */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Mail className="h-5 w-5" />
                  Contact Information
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <p className="text-xs text-muted-foreground">Client</p>
                  <p className="font-semibold">
                    {briefing?.client?.name ?? proposal?.client_name ?? "Not set"}
                  </p>
                </div>
                {briefing?.client?.contact && (
                  <div>
                    <p className="text-xs text-muted-foreground">Contact Person</p>
                    <p className="font-semibold">{briefing.client.contact}</p>
                  </div>
                )}
                {briefing?.client?.email && (
                  <div>
                    <p className="text-xs text-muted-foreground">Email</p>
                    <p className="font-semibold text-sm">{briefing.client.email}</p>
                  </div>
                )}
                <Separator />
                <div>
                  <p className="text-xs text-muted-foreground">Last Contact</p>
                  <p className="font-semibold">
                    {formatDate(proposal?.last_contact_date)}
                  </p>
                  {proposal?.days_since_contact != null && (
                    <p className="text-xs text-muted-foreground">
                      {proposal.days_since_contact} days ago
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Project Dates */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Calendar className="h-5 w-5" />
                  Important Dates
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <p className="text-xs text-muted-foreground">Created</p>
                  <p className="font-semibold">{formatDate(proposal?.created_date)}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Last Updated</p>
                  <p className="font-semibold">{formatDate(proposal?.updated_date)}</p>
                </div>
                {briefing?.financials?.next_payment && (
                  <div>
                    <p className="text-xs text-muted-foreground">Next Payment</p>
                    <p className="font-semibold">
                      {formatDate(briefing.financials.next_payment)}
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Status Timeline */}
          <ProposalTimeline projectCode={projectCode} />

          {/* Full Timeline - The Story */}
          <UnifiedTimeline projectCode={projectCode} limit={50} showStory={true} />

          {/* Milestones */}
          {briefing?.milestones && briefing.milestones.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <CheckCircle className="h-5 w-5" />
                  Milestones
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {briefing.milestones.map((milestone, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-3 rounded-lg border"
                    >
                      <div>
                        <p className="font-semibold">{milestone.milestone_name}</p>
                        <p className="text-xs text-muted-foreground">
                          {milestone.responsible_party}
                        </p>
                      </div>
                      <div className="text-right">
                        <Badge variant="outline">{milestone.status}</Badge>
                        <p className="text-xs text-muted-foreground mt-1">
                          {formatDate(milestone.expected_date)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Emails Tab */}
        <TabsContent value="emails">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Mail className="h-5 w-5" />
                Email Communications
              </CardTitle>
              <CardDescription>
                All emails related to this project
              </CardDescription>
            </CardHeader>
            <CardContent>
              {timelineQuery.isLoading ? (
                <div className="space-y-2">
                  {[1, 2, 3].map((i) => (
                    <Skeleton key={i} className="h-16 w-full" />
                  ))}
                </div>
              ) : timeline?.emails && timeline.emails.length > 0 ? (
                <div className="rounded-md border overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="min-w-[100px]">Date</TableHead>
                        <TableHead className="min-w-[200px]">Subject</TableHead>
                        <TableHead className="min-w-[150px]">From</TableHead>
                        <TableHead className="min-w-[100px]">Category</TableHead>
                        <TableHead className="min-w-[120px]">Action Required</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {timeline.emails.map((email) => (
                        <TableRow key={email.email_id}>
                          <TableCell className="text-sm">
                            {formatDate(email.date)}
                          </TableCell>
                          <TableCell className="font-medium">
                            {email.subject}
                          </TableCell>
                          <TableCell className="text-sm truncate max-w-[200px]">
                            {email.sender_email}
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline">
                              {email.category ?? "Uncategorized"}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            {email.action_required ? (
                              <Badge variant="destructive">Yes</Badge>
                            ) : (
                              <Badge variant="secondary">No</Badge>
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              ) : (
                <p className="text-center py-8 text-muted-foreground">
                  No emails found for this project
                </p>
              )}
            </CardContent>
          </Card>
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
                All documents related to this project
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

        {/* Financials Tab */}
        <TabsContent value="financials">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <DollarSign className="h-5 w-5" />
                Financial Information
              </CardTitle>
            </CardHeader>
            <CardContent>
              {briefingQuery.isLoading ? (
                <div className="space-y-2">
                  {[1, 2, 3, 4].map((i) => (
                    <Skeleton key={i} className="h-12 w-full" />
                  ))}
                </div>
              ) : briefing?.financials ? (
                <div className="space-y-4">
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="p-4 rounded-lg border">
                      <p className="text-xs text-muted-foreground mb-1">
                        Total Contract Value
                      </p>
                      <p className="text-2xl font-bold">
                        {formatCurrency(
                          briefing.financials.total_contract_value,
                          briefing.financials.currency
                        )}
                      </p>
                    </div>
                    <div className="p-4 rounded-lg border">
                      <p className="text-xs text-muted-foreground mb-1">
                        Payment Received
                      </p>
                      <p className="text-2xl font-bold text-green-600">
                        {formatCurrency(
                          briefing.financials.initial_payment_received,
                          briefing.financials.currency
                        )}
                      </p>
                    </div>
                    <div className="p-4 rounded-lg border">
                      <p className="text-xs text-muted-foreground mb-1">
                        Outstanding Balance
                      </p>
                      <p className="text-2xl font-bold text-orange-600">
                        {formatCurrency(
                          briefing.financials.outstanding_balance,
                          briefing.financials.currency
                        )}
                      </p>
                    </div>
                    <div className="p-4 rounded-lg border">
                      <p className="text-xs text-muted-foreground mb-1">
                        Overdue Amount
                      </p>
                      <p className="text-2xl font-bold text-red-600">
                        {formatCurrency(
                          briefing.financials.overdue_amount,
                          briefing.financials.currency
                        )}
                      </p>
                    </div>
                  </div>
                  {briefing.financials.next_payment && (
                    <div className="p-4 rounded-lg bg-muted">
                      <p className="text-xs text-muted-foreground mb-1">
                        Next Payment Due
                      </p>
                      <p className="font-semibold">
                        {formatDate(briefing.financials.next_payment)}
                      </p>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-center py-8 text-muted-foreground">
                  No financial data available for this project
                </p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Timeline Tab */}
        <TabsContent value="timeline">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock className="h-5 w-5" />
                Activity Timeline
              </CardTitle>
              <CardDescription>
                Chronological view of all project activities
              </CardDescription>
            </CardHeader>
            <CardContent>
              {timelineQuery.isLoading ? (
                <div className="space-y-2">
                  {[1, 2, 3, 4, 5].map((i) => (
                    <Skeleton key={i} className="h-20 w-full" />
                  ))}
                </div>
              ) : timeline?.timeline && timeline.timeline.length > 0 ? (
                <div className="space-y-4">
                  {timeline.timeline.map((event, index) => (
                    <div key={index} className="flex gap-4">
                      <div className="flex flex-col items-center">
                        <div className="w-3 h-3 rounded-full bg-primary" />
                        {index < timeline.timeline.length - 1 && (
                          <div className="w-0.5 flex-1 bg-border mt-2" />
                        )}
                      </div>
                      <div className="flex-1 pb-6">
                        <div className="flex items-center justify-between mb-1">
                          <Badge variant="outline">{event.type}</Badge>
                          <span className="text-xs text-muted-foreground">
                            {formatDate(event.date)}
                          </span>
                        </div>
                        <div className="text-sm">
                          {Object.entries(event)
                            .filter(([key]) => key !== "type" && key !== "date")
                            .map(([key, value]) => (
                              <div key={key} className="mt-1">
                                <span className="font-medium">{key}: </span>
                                <span className="text-muted-foreground">
                                  {String(value)}
                                </span>
                              </div>
                            ))}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-center py-8 text-muted-foreground">
                  No timeline events available
                </p>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
