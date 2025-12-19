"use client";

import { useMemo, useState } from "react";
import {
  useMutation,
  useQuery,
  useQueryClient,
  useQueries,
} from "@tanstack/react-query";
import { format } from "date-fns";
import { toast } from "sonner";
import QueryPanel from "./query-panel";
import RevenueBar from "../charts/revenue-bar";
import { QueryWidget } from "./query-widget";
import { MeetingsWidget } from "./meetings-widget";
import { api } from "@/lib/api";
import {
  BriefingAction,
  DailyBriefing,
  IntelligenceSuggestion,
  IntelligenceSuggestionGroup,
  DecisionTiles,
  ManualOverride,
  FinancePayment,
  ProjectedInvoice,
  RfiTileItem,
  MeetingTileItem,
  MilestoneTileItem,
} from "@/lib/types";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  AlertTriangle,
  Bot,
  CalendarDays,
  CheckCircle2,
  Circle,
  MessageSquarePlus,
  PhoneCall,
  TrendingUp,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { ds } from "@/lib/design-system";

const DEFAULT_OVERRIDE_AUTHOR =
  process.env.NEXT_PUBLIC_OVERRIDE_AUTHOR ?? "bill";

// ⚠️ WARNING: DEMO DATA ONLY - Remove in Phase 2 cleanup
// This fallback exists to prevent empty dashboard when API fails
// TODO: Replace with proper empty states and error handling
const FALLBACK_BRIEFING: DailyBriefing = {
  date: new Date().toISOString().slice(0, 10),
  business_health: {
    status: "caution",
    summary: "10 projects at risk, $4.6M outstanding",
  },
  urgent: [
    {
      type: "no_contact",
      priority: "high",
      project_code: "BK-084",
      project_name: "Amanpuri Villas",
      action: "Call Zaher today",
      context: "18 days no contact",
      detail: "Discuss updated fee letter",
    },
    {
      type: "no_contact",
      priority: "high",
      project_code: "BK-071",
      project_name: "Saudi Royal Court",
      action: "Ping Marcus & client",
      context: "25 days no contact",
      detail: "Send revised scope clarifications",
    },
    {
      type: "payment",
      priority: "high",
      project_code: "BK-066",
      project_name: "Shanghai Waterside",
      action: "Escalate invoice",
      context: "$420K overdue",
      detail: "Payment now 32 days late",
    },
  ],
  needs_attention: [
    {
      type: "follow_up",
      project_code: "BK-029",
      project_name: "Qinhu Resort China",
      action: "Follow up: review drawings",
      context: "9 days since last contact",
      detail: "Client waiting for update",
    },
    {
      type: "milestone",
      project_code: "BK-051",
      project_name: "Fenfushi Maldives",
      action: "Confirm immersion workshop",
      context: "Target Feb 24",
      detail: "Lock attendee list",
    },
  ],
  insights: [
    "Email volume down 30% versus last week",
    "$4.6M outstanding with 3 invoices overdue",
    "Concept deck timeline slipping on two projects",
  ],
  wins: [
    {
      title: "Concept deck approved",
      project_code: "BK-071",
      project_name: "Saudi Royal Court",
      description: "Royal Court signed off on schematic package",
      amount_usd: 950000,
      date: new Date().toISOString(),
    },
  ],
  metrics: {
    total_projects: 39,
    at_risk: 10,
    revenue: 50175020,
    outstanding: 4596578.75,
  },
};

// ⚠️ WARNING: DEMO DATA ONLY - Remove in Phase 2 cleanup
const FALLBACK_SUGGESTIONS: IntelligenceSuggestionGroup[] = [
  {
    bucket: "urgent",
    label: "Urgent data fixes",
    description: "High impact issues blocking reporting",
    items: [
      {
        id: "sgg-fallback-1",
        project_code: "BK-013",
        project_name: "Sandstone Villas",
        suggestion_type: "status_mismatch",
        summary: "Mark BK-013 as archived",
        proposed_fix: { status: "archived", is_active_project: 0 },
        impact_type: "financial_risk",
        impact_value_usd: 1200000,
        impact_summary: "$1.2M stuck under active projects",
        confidence: 0.84,
        severity: "high",
        bucket: "urgent",
        pattern_id: "pattern-legacy",
        pattern_label: "Legacy 2013 projects",
        auto_apply_candidate: false,
        created_at: new Date().toISOString(),
        evidence: {
          root_cause: "proposal_code implies 2013 but contact date still 2013",
          signals: [
            { label: "Last contact", value: "2013-04-12" },
            { label: "Status", value: "active_project" },
          ],
          supporting_files: [{ type: "email", reference: "email_774" }],
        },
      },
      {
        id: "sgg-fallback-2",
        project_code: "BK-084",
        project_name: "Amanpuri Villas",
        suggestion_type: "missing_pm",
        summary: "Assign PM to Amanpuri",
        proposed_fix: { pm: "Sophie Park" },
        impact_type: "ops_risk",
        impact_summary: "No PM assigned while in delivery phase",
        confidence: 0.76,
        severity: "medium",
        bucket: "urgent",
        pattern_id: "pattern-missing-pm",
        pattern_label: "Unassigned leadership",
        auto_apply_candidate: false,
        created_at: new Date().toISOString(),
        evidence: {
          signals: [
            { label: "Phase", value: "concept" },
            { label: "PM", value: "NULL" },
          ],
        },
      },
    ],
  },
  {
    bucket: "needs_attention",
    label: "Needs review",
    description: "Quality improvements that benefit forecasting",
    items: [
      {
        id: "sgg-fallback-3",
        project_code: "BK-029",
        project_name: "Qinhu Resort China",
        suggestion_type: "payment_alignment",
        summary: "Log partial payment from Oct 4 wire",
        proposed_fix: { paid_to_date_usd: 1625000 },
        impact_type: "cash_flow",
        impact_value_usd: 450000,
        impact_summary: "Paid-to-date doesn't match bank record",
        confidence: 0.71,
        severity: "medium",
        bucket: "needs_attention",
        evidence: {
          signals: [
            { label: "Invoices", value: "2 issued" },
            { label: "Bank ref", value: "Wire 8840" },
          ],
        },
      },
    ],
  },
];

const SUGGESTION_GROUP_META: Array<{
  bucket: string;
  label: string;
  description: string;
}> = [
  {
    bucket: "urgent",
    label: "Urgent data fixes",
    description: "High impact issues blocking reporting",
  },
  {
    bucket: "needs_attention",
    label: "Needs review",
    description: "Quality improvements that benefit forecasting",
  },
  {
    bucket: "fyi",
    label: "FYI insights",
    description: "Context to monitor next",
  },
];

const FALLBACK_SUGGESTION_MAP = FALLBACK_SUGGESTIONS.reduce<
  Record<string, IntelligenceSuggestionGroup>
>((acc, group) => {
  acc[group.bucket] = group;
  return acc;
}, {});

const HEALTH_STYLES: Record<
  string,
  { label: string; badgeClass: string; borderClass: string }
> = {
  healthy: {
    label: "Business health: steady",
    badgeClass:
      "bg-emerald-500/20 text-emerald-200 border border-emerald-400/30",
    borderClass: "from-emerald-500/10 to-emerald-900/20",
  },
  caution: {
    label: "Business health: watchlist",
    badgeClass: "bg-amber-500/20 text-amber-200 border border-amber-400/30",
    borderClass: "from-amber-400/10 to-amber-900/30",
  },
  needs_attention: {
    label: "Business health: needs attention",
    badgeClass: "bg-rose-500/20 text-rose-200 border border-rose-400/30",
    borderClass: "from-rose-500/10 to-rose-900/30",
  },
  critical: {
    label: "Business health: critical",
    badgeClass: "bg-red-600/20 text-red-200 border border-red-500/30",
    borderClass: "from-red-500/10 to-red-900/40",
  },
};

const formatCurrency = (value?: number | null) => {
  if (value == null) return "$0";
  if (Math.abs(value) >= 1_000_000) {
    return `$${(value / 1_000_000).toFixed(1)}M`;
  }
  if (Math.abs(value) >= 1_000) {
    return `$${(value / 1_000).toFixed(1)}K`;
  }
  return `$${value.toLocaleString()}`;
};

const formatDisplayDate = (value?: string | null) => {
  if (!value) return "—";
  try {
    return format(new Date(value), "MMM d");
  } catch {
    return value;
  }
};

export default function DashboardPage() {
  const [isContextOpen, setIsContextOpen] = useState(false);
  const [contextNote, setContextNote] = useState("");
  const [contextScope, setContextScope] = useState<
    "emails" | "documents" | "billing" | "rfis" | "scheduling" | "general"
  >("general");
  const [contextUrgency, setContextUrgency] =
    useState<"informational" | "urgent">("informational");
  const [isAssistantOpen, setIsAssistantOpen] = useState(false);
  const [selectedSuggestion, setSelectedSuggestion] =
    useState<IntelligenceSuggestion | null>(null);

  const queryClient = useQueryClient();

  const dailyBriefingQuery = useQuery({
    queryKey: ["daily-briefing"],
    queryFn: api.getDailyBriefing,
    staleTime: 1000 * 60 * 5,
  });

  const decisionTilesQuery = useQuery({
    queryKey: ["decision-tiles"],
    queryFn: api.getDecisionTiles,
    refetchInterval: 1000 * 60 * 5,
  });

  const dashboardStatsQuery = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: () => api.getDashboardStats(),
    refetchInterval: 1000 * 60 * 5,
  });

  const manualOverridesQuery = useQuery({
    queryKey: ["manual-overrides", "dashboard"],
    queryFn: () => api.getManualOverrides({ status: "active", per_page: 5 }),
  });

  const querySuggestionsQuery = useQuery({
    queryKey: ["query-suggestions"],
    queryFn: api.getQuerySuggestions,
  });

  const intelSuggestionQueries = useQueries({
    queries: SUGGESTION_GROUP_META.map((group) => ({
      queryKey: ["intel-suggestions", group.bucket],
      queryFn: () => api.getIntelSuggestions({ group: group.bucket }),
      staleTime: 1000 * 60 * 5,
      retry: false,
    })),
  });

  const recentPaymentsQuery = useQuery({
    queryKey: ["recent-payments"],
    queryFn: () => api.getRecentPayments(5),
    staleTime: 1000 * 60 * 10,
  });

  const projectedInvoicesQuery = useQuery({
    queryKey: ["projected-invoices"],
    queryFn: () => api.getProjectedInvoices(5),
    staleTime: 1000 * 60 * 10,
  });

  const queryMutation = useMutation({
    mutationFn: api.executeQuery,
  });

  const manualOverrideMutation = useMutation({
    mutationFn: api.createManualOverride,
    onSuccess: () => {
      toast.success("Context logged for Claude");
      queryClient.invalidateQueries({ queryKey: ["manual-overrides"] });
      setContextNote("");
      setIsContextOpen(false);
    },
    onError: (error: unknown) => {
      const message =
        error instanceof Error ? error.message : "Unable to submit context";
      toast.error(message);
    },
  });

  const suggestionDecisionMutation = useMutation({
    mutationFn: ({
      suggestionId,
      decision,
    }: {
      suggestionId: string;
      decision: "approved" | "rejected" | "snoozed";
    }) =>
      api.postIntelDecision(suggestionId, {
        decision,
        apply_now: decision === "approved",
      }),
    onSuccess: (_, variables) => {
      const verb =
        variables.decision === "approved"
          ? "Applied"
          : variables.decision === "snoozed"
          ? "Snoozed"
          : "Dismissed";
      toast.success(`${verb} ${variables.suggestionId}`);
      queryClient.invalidateQueries({ queryKey: ["intel-suggestions"] });
    },
    onError: (error: unknown) => {
      const message =
        error instanceof Error
          ? error.message
          : "Unable to update suggestion queue";
      toast.error(message);
    },
  });

  const briefing = dailyBriefingQuery.data ?? FALLBACK_BRIEFING;
  const urgentItems =
    briefing.urgent && briefing.urgent.length > 0
      ? briefing.urgent
      : FALLBACK_BRIEFING.urgent;
  const attentionItems =
    briefing.needs_attention && briefing.needs_attention.length > 0
      ? briefing.needs_attention
      : FALLBACK_BRIEFING.needs_attention;
  const insights =
    briefing.insights && briefing.insights.length > 0
      ? briefing.insights
      : FALLBACK_BRIEFING.insights;
  const wins =
    briefing.wins && briefing.wins.length > 0
      ? briefing.wins
      : FALLBACK_BRIEFING.wins;

  const intelAnyLoading = intelSuggestionQueries.some(
    (query) => query.isLoading
  );
  const intelAnyError = intelSuggestionQueries.some((query) => query.isError);

  const suggestionGroups = SUGGESTION_GROUP_META.map((meta, index) => {
    const query = intelSuggestionQueries[index];
    const useFallback = Boolean(query?.isError);
    const fallbackGroup = FALLBACK_SUGGESTION_MAP[meta.bucket];
    const items =
      !useFallback && query?.data?.items
        ? query.data.items
        : fallbackGroup?.items ?? [];
    return {
      bucket: meta.bucket,
      label: meta.label ?? fallbackGroup?.label ?? meta.bucket,
      description: meta.description ?? fallbackGroup?.description,
      items,
      isLoading: query?.isLoading,
      isError: query?.isError,
      readOnly: useFallback,
    };
  });

  const manualOverrides = manualOverridesQuery.data?.data ?? [];
  const manualOverridesTotal =
    manualOverridesQuery.data?.pagination?.total ?? manualOverrides.length;

  const decisionTilesData: DecisionTiles | undefined = decisionTilesQuery.data;

  const outstandingInvoices = {
    amount:
      decisionTilesData?.overdue_payments?.items?.reduce((sum, item) => sum + (item.amount || 0), 0) ??
      briefing.metrics.outstanding ??
      0,
    count: decisionTilesData?.overdue_payments?.count ?? 0,
  };

  const projectedInvoices = [
    ...(projectedInvoicesQuery.data?.invoices ?? []),
  ];

  const projectedInvoicesLoading = projectedInvoicesQuery.isLoading;
  const projectedInvoicesError = projectedInvoicesQuery.isError;

  const recentPaidInvoices = [
    ...(recentPaymentsQuery.data?.payments ?? []),
  ];

  const briefingDateLabel = useMemo(() => {
    try {
      return format(new Date(briefing.date), "EEEE, MMM d");
    } catch {
      return format(new Date(), "EEEE, MMM d");
    }
  }, [briefing.date]);

  const healthStyle =
    HEALTH_STYLES[briefing.business_health.status] ?? HEALTH_STYLES.caution;

  const scheduleEntries: (MeetingTileItem | MilestoneTileItem)[] =
    decisionTilesData?.upcoming_meetings?.items?.slice(0, 3) ?? [];

  const rfiQueue: RfiTileItem[] = decisionTilesData?.unanswered_rfis?.items ?? [];

  const revenueStats = dashboardStatsQuery.data?.revenue;
  const revenueSeries = useMemo(() => {
    const paid = Math.round((revenueStats?.paid ?? 320000) / 1000);
    const outstanding = Math.round(
      (revenueStats?.outstanding ?? briefing.metrics.outstanding ?? 210000) /
        1000
    );
    const remaining = Math.max(
      Math.round(
        ((revenueStats?.total_contracts ?? briefing.metrics.revenue) -
          (revenueStats?.paid ?? 0)) /
          1000
      ),
      0
    );
    return {
      series: [
        { name: "Revenue", data: [paid, paid * 0.85, paid * 0.75] },
        { name: "Cost", data: [outstanding, remaining * 0.8, outstanding * 0.6] },
      ],
      categories: ["Q1", "Q2", "Q3"],
    };
  }, [revenueStats, briefing.metrics]);

  const handleContextSubmit = () => {
    if (!contextNote.trim()) {
      toast.error("Add a short note before submitting");
      return;
    }
    manualOverrideMutation.mutate({
      project_code: undefined,
      scope: contextScope,
      instruction: contextNote.trim(),
      author: DEFAULT_OVERRIDE_AUTHOR,
      urgency: contextUrgency,
    });
  };

  const handleSuggestionDecision = (
    suggestion: IntelligenceSuggestion,
    decision: "approved" | "snoozed" | "rejected"
  ) => {
    if (!suggestion.id) {
      return;
    }
    suggestionDecisionMutation.mutate({
      suggestionId: suggestion.id,
      decision,
    });
  };

  const assistantToggleLabel = isAssistantOpen
    ? "Close Bensley Brain"
    : "Open Bensley Brain";

  const intelHeaderBadge = intelAnyLoading ? (
    <Badge variant="outline">Loading suggestions…</Badge>
  ) : intelAnyError ? (
    <Badge variant="destructive" className="bg-rose-100 text-rose-600">
      Offline • showing fallback
    </Badge>
  ) : (
    <Badge variant="secondary" className="rounded-full">
      Updated {format(new Date(), "h:mm a")}
    </Badge>
  );

  return (
    <div className="relative min-h-screen bg-gradient-to-b from-slate-100 to-white pb-32">
      <div className="mx-auto flex max-w-6xl flex-col gap-8 px-4 py-8 lg:px-0">
        <section className={cn(ds.borderRadius.cardLarge, "bg-gradient-to-br from-slate-900 via-slate-900/90 to-slate-900/70 p-8 text-white shadow-2xl")}>
          <div className="flex flex-col gap-6 md:flex-row md:items-start md:justify-between">
            <div>
              <p className="text-sm uppercase tracking-[0.4em] text-white/60">
                Bensley Brain • Daily Briefing
              </p>
              <h1 className={cn("mt-3 lg:text-4xl", ds.typography.heading1)}>
                Calm command of every project pulse
              </h1>
              <p className="mt-3 max-w-xl text-base text-white/80">
                {briefing.business_health.summary}
              </p>
              <div className="mt-6 flex flex-wrap gap-3">
                <Badge className={healthStyle.badgeClass}>
                  {healthStyle.label}
                </Badge>
                <Badge variant="outline" className="border-white/40 text-white">
                  {briefingDateLabel}
                </Badge>
              </div>
            </div>
            <div className="flex flex-col gap-3 text-right">
              <p className="text-sm uppercase tracking-[0.3em] text-white/60">
                Today
              </p>
              <p className="text-4xl font-semibold">
                {urgentItems.length} urgent · {attentionItems.length} watch
              </p>
              <div className="flex flex-wrap justify-end gap-3">
                <Button
                  variant="secondary"
                  className="gap-2 rounded-full bg-white/10 text-white hover:bg-white/20"
                  onClick={() => setIsContextOpen(true)}
                >
                  <MessageSquarePlus className="h-4 w-4" />
                  Provide context
                </Button>
                <Button
                  variant="outline"
                  className="gap-2 rounded-full border-white/30 text-white hover:bg-white/10"
                  onClick={() => setIsAssistantOpen(true)}
                >
                  <Bot className="h-4 w-4" />
                  Ask Bensley Brain
                </Button>
              </div>
            </div>
          </div>

          <div className="mt-10 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <MetricTile
              label="Projects at risk"
              value={briefing.metrics.at_risk}
              subtitle="Need touchpoints"
            />
            <MetricTile
              label="Outstanding"
              value={formatCurrency(briefing.metrics.outstanding)}
              subtitle="Across portfolio"
            />
            <MetricTile
              label="Revenue under contract"
              value={formatCurrency(briefing.metrics.revenue)}
              subtitle="Total live work"
            />
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4 text-white/90">
              <p className="text-xs uppercase tracking-[0.3em] text-white/60">
                Next session
              </p>
              {scheduleEntries.length > 0 ? (
                <div className="mt-3 space-y-1 text-sm">
                  <p className="text-lg font-semibold text-white">
                    {("meeting_title" in scheduleEntries[0] ? scheduleEntries[0].meeting_title : null) ??
                     ("milestone_name" in scheduleEntries[0] ? scheduleEntries[0].milestone_name : null) ??
                      "Upcoming touchpoint"}
                  </p>
                  <p>{scheduleEntries[0].project_name ?? scheduleEntries[0].project_code}</p>
                  <p className="text-white/70">
                    {("scheduled_date" in scheduleEntries[0] && scheduleEntries[0].scheduled_date)
                      ? format(new Date(scheduleEntries[0].scheduled_date), "MMM d • h a")
                      : ("planned_date" in scheduleEntries[0] && scheduleEntries[0].planned_date)
                      ? format(new Date(scheduleEntries[0].planned_date), "MMM d • h a")
                      : "Date pending"}
                  </p>
                </div>
              ) : (
                <p className="mt-3 text-sm text-white/70">
                  No meetings synced yet
                </p>
              )}
            </div>
          </div>
        </section>

        <section className="grid gap-6 lg:grid-cols-[2fr,1fr]">
          <PriorityFeed
            title="Needs your voice now"
            subtitle="Escalate or call personally"
            items={urgentItems}
            priority="urgent"
          />
          <InsightsPanel insights={insights} wins={wins} />
        </section>

        <section className="grid gap-6 lg:grid-cols-[1.6fr,1fr]">
          <PriorityFeed
            title="Keep on radar"
            subtitle="Check-in before it slips"
            items={attentionItems}
            priority="attention"
          />
          <SchedulePanel
            scheduleEntries={scheduleEntries}
            manualOverrides={manualOverrides}
            manualOverridesTotal={manualOverridesTotal}
            onAddContext={() => setIsContextOpen(true)}
          />
        </section>

        <section className="grid gap-6 lg:grid-cols-[1.2fr,0.8fr]">
          <Card className={cn(ds.borderRadius.cardLarge, "border-slate-200/70")}>
            <CardContent className="space-y-6 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm uppercase tracking-[0.3em] text-slate-400">
                    Business snapshot
                  </p>
                  <h2 className={cn(ds.typography.heading2, ds.textColors.primary)}>
                    Revenue & cadence
                  </h2>
                </div>
                <Badge variant="secondary" className="gap-1 rounded-full">
                  <TrendingUp className="h-3.5 w-3.5" />
                  refreshed {dailyBriefingQuery.isFetching ? "now" : "5 min"}
                </Badge>
              </div>
              <RevenueBar
                hideCard
                className={cn(ds.borderRadius.cardLarge, "bg-slate-900/5 p-4")}
                series={revenueSeries.series}
                categories={revenueSeries.categories}
              />
              <div className="grid gap-3 text-sm text-slate-600 md:grid-cols-3">
                <div>
                  <p className="text-xs uppercase tracking-[0.3em] text-slate-400">
                    Paid to date
                  </p>
                  <p className="text-lg font-semibold text-slate-900">
                    {formatCurrency(revenueStats?.paid)}
                  </p>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-[0.3em] text-slate-400">
                    Outstanding
                  </p>
                  <p className="text-lg font-semibold text-slate-900">
                    {formatCurrency(revenueStats?.outstanding ?? briefing.metrics.outstanding)}
                  </p>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-[0.3em] text-slate-400">
                    Remaining scope
                  </p>
                  <p className="text-lg font-semibold text-slate-900">
                    {formatCurrency(
                      (revenueStats?.total_contracts ?? briefing.metrics.revenue) -
                        (revenueStats?.paid ?? 0)
                    )}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className={cn(ds.borderRadius.cardLarge, "border-slate-200/70")}>
            <CardContent className="p-6">
              <p className="text-sm uppercase tracking-[0.3em] text-slate-400">
                Intelligence notes
              </p>
              <div className="mt-4 space-y-3 text-sm text-slate-600">
                {insights.map((insight) => (
                  <div key={insight} className="flex items-start gap-3">
                    <Circle className="mt-1 h-2.5 w-2.5 text-slate-400" />
                    <p>{insight}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </section>

        <section className="grid gap-6 lg:grid-cols-3">
          <FinancialWidget
            title="Outstanding invoices"
            amount={outstandingInvoices.amount}
            count={outstandingInvoices.count}
            description="Waiting on client payment"
            variant="alert"
          />
          <ProjectedWidget
            items={projectedInvoices}
            isLoading={projectedInvoicesLoading}
            isError={projectedInvoicesError}
          />
          <RecentPaidInvoices
            items={recentPaidInvoices}
            isLoading={recentPaymentsQuery.isLoading}
            isError={recentPaymentsQuery.isError}
          />
          <QueryWidget compact={true} />
        </section>

        <section className="grid gap-6 lg:grid-cols-2">
          <MeetingsWidget />
          <RfiStatusCard rfiItems={rfiQueue} />
        </section>

        <section className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-sm uppercase tracking-[0.3em] text-slate-400">
                AI data suggestions
              </p>
              <h2 className={cn(ds.typography.heading2, ds.textColors.primary)}>
                Cleanup queue
              </h2>
            </div>
            {intelHeaderBadge}
          </div>
          <div className="space-y-6">
            {suggestionGroups.map((group) => (
              <Card key={group.bucket} className={cn(ds.borderRadius.cardLarge, "border-slate-200/80")}>
                <CardContent className="space-y-4 p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs uppercase tracking-[0.3em] text-slate-400">
                        {group.label}
                      </p>
                      <p className="text-lg text-slate-600">{group.description}</p>
                    </div>
                    <Badge
                      variant={
                        group.bucket === "urgent" ? "destructive" : "secondary"
                      }
                      className="rounded-full"
                    >
                      {group.isLoading
                        ? "Syncing…"
                        : group.isError
                        ? "Offline"
                        : `${group.items.length} items`}
                    </Badge>
                  </div>
                  <div className="space-y-4">
                    {group.items.length === 0 ? (
                      <p className="rounded-2xl border border-dashed border-slate-200/70 p-4 text-sm text-slate-500">
                        {group.isLoading
                          ? "Syncing..."
                          : "Nothing in this bucket right now."}
                      </p>
                    ) : (
                      group.items.map((suggestion) => (
                        <SuggestionCard
                          key={suggestion.id}
                          suggestion={suggestion}
                          onApprove={() =>
                            handleSuggestionDecision(suggestion, "approved")
                          }
                          onSnooze={() =>
                            handleSuggestionDecision(suggestion, "snoozed")
                          }
                          onMore={() => setSelectedSuggestion(suggestion)}
                          disabled={
                            group.readOnly || suggestionDecisionMutation.isPending
                          }
                        />
                      ))
                    )}
                 </div>
               </CardContent>
             </Card>
           ))}
          </div>
        </section>

        <section>
          <IntelligenceSummary
            insights={insights}
            briefingDateLabel={briefingDateLabel}
          />
        </section>
      </div>

      <button
        type="button"
        className="fixed bottom-6 right-6 flex items-center gap-2 rounded-full bg-slate-900 px-5 py-3 text-sm font-medium text-white shadow-xl"
        onClick={() => setIsAssistantOpen(true)}
      >
        <Bot className="h-4 w-4" />
        {assistantToggleLabel}
      </button>

      <Dialog open={isAssistantOpen} onOpenChange={setIsAssistantOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Ask Bensley Brain</DialogTitle>
            <DialogDescription>
              Natural-language interface into proposals, documents, and emails
            </DialogDescription>
          </DialogHeader>
          <QueryPanel
            variant="panel"
            suggestions={querySuggestionsQuery.data}
            onSubmit={(question) => queryMutation.mutateAsync(question)}
            title="Query Brain"
            description="Ask context-aware questions across the portfolio"
          />
        </DialogContent>
      </Dialog>

      <Dialog open={isContextOpen} onOpenChange={setIsContextOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Provide context to the system</DialogTitle>
            <DialogDescription>
              Your notes synchronize with Claude’s backend agents for training and overrides.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <Textarea
              placeholder="e.g. BK-084 is active, classify Zaher’s emails as financial"
              value={contextNote}
              onChange={(event) => setContextNote(event.target.value)}
              rows={4}
            />
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <p className="text-sm text-slate-500">Scope</p>
                <Select
                  value={contextScope}
                  onValueChange={(value) =>
                    setContextScope(value as typeof contextScope)
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {[
                      "general",
                      "emails",
                      "documents",
                      "billing",
                      "rfis",
                      "scheduling",
                    ].map((scope) => (
                      <SelectItem key={scope} value={scope}>
                        {scope}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <p className="text-sm text-slate-500">Urgency</p>
                <Select
                  value={contextUrgency}
                  onValueChange={(value) =>
                    setContextUrgency(value as typeof contextUrgency)
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="informational">Informational</SelectItem>
                    <SelectItem value="urgent">Urgent</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button
              onClick={handleContextSubmit}
              disabled={manualOverrideMutation.isPending}
            >
              {manualOverrideMutation.isPending ? "Sending…" : "Send to Claude"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={Boolean(selectedSuggestion)} onOpenChange={() => setSelectedSuggestion(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>
              Evidence for {selectedSuggestion?.project_code} · {selectedSuggestion?.project_name}
            </DialogTitle>
            <DialogDescription>
              Why the AI suggested this correction
            </DialogDescription>
          </DialogHeader>
          {selectedSuggestion ? (
            <div className="space-y-4 text-sm text-slate-600">
              <div>
                <p className="text-xs uppercase tracking-[0.3em] text-slate-400">
                  Proposed fix
                </p>
                <pre className="mt-2 rounded-2xl bg-slate-900/5 p-4 text-xs">
                  {JSON.stringify(selectedSuggestion.proposed_fix, null, 2)}
                </pre>
              </div>
              {selectedSuggestion.evidence?.root_cause && (
                <div>
                  <p className="text-xs uppercase tracking-[0.3em] text-slate-400">
                    Root cause
                  </p>
                  <p className="mt-2">{selectedSuggestion.evidence.root_cause}</p>
                </div>
              )}
              {selectedSuggestion.evidence?.signals && (
                <div>
                  <p className="text-xs uppercase tracking-[0.3em] text-slate-400">
                    Signals
                  </p>
                  <div className="mt-2 grid gap-2 md:grid-cols-2">
                    {selectedSuggestion.evidence.signals.map((signal) => (
                      <div
                        key={`${signal.label}-${signal.value}`}
                        className="rounded-2xl border border-slate-200 p-3"
                      >
                        <p className="text-xs uppercase tracking-[0.3em] text-slate-400">
                          {signal.label}
                        </p>
                        <p className="text-base text-slate-800">{signal.value}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {selectedSuggestion.evidence?.detection_logic && (
                <div>
                  <p className="text-xs uppercase tracking-[0.3em] text-slate-400">
                    Detection logic
                  </p>
                  <p className="mt-2 whitespace-pre-wrap">
                    {selectedSuggestion.evidence.detection_logic}
                  </p>
                </div>
              )}
            </div>
          ) : null}
          <DialogFooter>
            <Button onClick={() => setSelectedSuggestion(null)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function MetricTile({
  label,
  value,
  subtitle,
}: {
  label: string;
  value: string | number;
  subtitle?: string;
}) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-4 text-white/80">
      <p className="text-xs uppercase tracking-[0.3em] text-white/60">{label}</p>
      <p className={cn("mt-3", ds.typography.heading2, "text-white")}>{value}</p>
      {subtitle && <p className="text-sm text-white/60">{subtitle}</p>}
    </div>
  );
}

function PriorityFeed({
  title,
  subtitle,
  items,
  priority,
}: {
  title: string;
  subtitle?: string;
  items: BriefingAction[];
  priority: "urgent" | "attention";
}) {
  return (
    <div className="rounded-[28px] border border-slate-200/80 bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-400">
            {title}
          </p>
          {subtitle && <p className="text-sm text-slate-500">{subtitle}</p>}
        </div>
        <Badge
          variant={priority === "urgent" ? "destructive" : "secondary"}
          className="rounded-full"
        >
          {items.length} items
        </Badge>
      </div>
      <div className="mt-4 space-y-4">
        {items.map((item) => (
          <div
            key={`${item.project_code}-${item.action}`}
            className={cn(ds.borderRadius.cardLarge, "border border-slate-200/70 bg-gradient-to-r from-white to-slate-50 p-4")}
          >
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-xs uppercase tracking-[0.3em] text-slate-400">
                  {item.project_name ?? item.project_code}
                </p>
                <p className={cn("mt-2", ds.typography.heading3, ds.textColors.primary)}>
                  {item.action}
                </p>
                <p className="text-sm text-slate-500">{item.detail ?? item.context}</p>
              </div>
              <Badge
                variant="outline"
                className="rounded-full border-dashed text-slate-500"
              >
                {item.context ?? ""}
              </Badge>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function InsightsPanel({
  insights,
  wins,
}: {
  insights: string[];
  wins: DailyBriefing["wins"];
}) {
  return (
    <div className="rounded-[28px] border border-slate-200/80 bg-white p-6 shadow-sm">
      <p className="text-xs uppercase tracking-[0.3em] text-slate-400">
        Recent wins & insights
      </p>
      <div className="mt-4 space-y-4">
        {wins.map((win) => (
          <div key={`${win.project_code}-${win.title}`} className="rounded-2xl border border-emerald-100 bg-emerald-50/50 p-4">
            <div className="flex items-center gap-2 text-emerald-600">
              <CheckCircle2 className="h-4 w-4" />
              <p className="text-sm font-medium">
                {win.title ?? "Client update"}
              </p>
            </div>
            <p className="mt-2 text-lg font-semibold text-slate-900">
              {win.project_name ?? win.project_code}
            </p>
            <p className="text-sm text-slate-500">{win.description}</p>
            {win.amount_usd ? (
              <p className="mt-2 text-sm text-emerald-700">
                {formatCurrency(win.amount_usd)} impact
              </p>
            ) : null}
          </div>
        ))}
        {insights.map((insight) => (
          <div key={insight} className="flex items-start gap-3 rounded-2xl border border-slate-200/70 p-4">
            <AlertTriangle className="mt-1 h-4 w-4 text-amber-500" />
            <p className="text-sm text-slate-600">{insight}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function SchedulePanel({
  scheduleEntries,
  manualOverrides,
  manualOverridesTotal,
  onAddContext,
}: {
  scheduleEntries: (MeetingTileItem | MilestoneTileItem)[];
  manualOverrides: ManualOverride[];
  manualOverridesTotal: number;
  onAddContext: () => void;
}) {
  return (
    <div className="rounded-[28px] border border-slate-200/80 bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-400">
            Calendar & operator notes
          </p>
          <p className="text-sm text-slate-500">
            Auto-synced from Claude + manual overrides
          </p>
        </div>
        <Button variant="ghost" className="gap-2" onClick={onAddContext}>
          <MessageSquarePlus className="h-4 w-4" /> Add note
        </Button>
      </div>
      <div className="mt-4 space-y-6">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-400">
            Upcoming sessions
          </p>
          {scheduleEntries.length === 0 ? (
            <p className="mt-2 text-sm text-slate-500">Nothing scheduled yet</p>
          ) : (
            <div className="mt-3 space-y-3">
              {scheduleEntries.map((entry, idx) => (
                <div
                  key={`${entry.project_code}-${idx}`}
                  className="rounded-2xl border border-slate-100 p-4"
                >
                  <div className="flex items-center justify-between text-sm text-slate-500">
                    <div className="flex items-center gap-2">
                      <CalendarDays className="h-4 w-4" />
                      <span>
                        {("scheduled_date" in entry && entry.scheduled_date)
                          ? format(new Date(String(entry.scheduled_date)), "MMM d • h a")
                          : ("planned_date" in entry && entry.planned_date)
                          ? format(new Date(String(entry.planned_date)), "MMM d • h a")
                          : "Date TBC"}
                      </span>
                    </div>
                    <span className="text-xs uppercase tracking-[0.3em] text-slate-400">
                      {("meeting_type" in entry ? entry.meeting_type : null) ?? "session"}
                    </span>
                  </div>
                  <p className="mt-2 text-base font-semibold text-slate-900">
                    {("meeting_title" in entry ? entry.meeting_title : null) ??
                     ("milestone_name" in entry ? entry.milestone_name : null) ??
                     "Internal review"}
                  </p>
                  <p className="text-sm text-slate-500">
                    {entry.project_name ?? entry.project_code}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-400">
            Operator overrides
          </p>
          <div className="mt-3 space-y-3 text-sm text-slate-600">
            {manualOverrides.length === 0 ? (
              <p className="text-sm text-slate-500">No notes yet</p>
            ) : (
              manualOverrides.map((override) => (
                <div
                  key={override.override_id}
                  className="rounded-2xl border border-slate-100 p-3"
                >
                  <p className="font-medium text-slate-900">{override.instruction}</p>
                  <p className="text-xs text-slate-500">
                    {override.author} • {format(new Date(override.created_at), "MMM d h:mm a")}
                  </p>
                </div>
              ))
            )}
            {manualOverridesTotal > manualOverrides.length && (
              <p className="text-xs text-slate-400">
                +{manualOverridesTotal - manualOverrides.length} more logged
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function SuggestionCard({
  suggestion,
  onApprove,
  onSnooze,
  onMore,
  disabled,
}: {
  suggestion: IntelligenceSuggestion;
  onApprove: () => void;
  onSnooze: () => void;
  onMore: () => void;
  disabled?: boolean;
}) {
  const confidencePercent = Math.round(suggestion.confidence * 100);
  const impactSummary =
    suggestion.impact_summary ?? suggestion.impact?.summary ?? null;
  const disableActions = Boolean(disabled);
  return (
    <div className={cn(ds.borderRadius.cardLarge, "border border-slate-200/80 bg-white p-5")}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-400">
            {suggestion.project_name ?? suggestion.project_code}
          </p>
          <p className="mt-2 text-lg font-semibold text-slate-900">
            {suggestion.summary ?? suggestion.suggestion_type.replaceAll("_", " ")}
          </p>
          {impactSummary && (
            <p className="text-sm text-slate-500">{impactSummary}</p>
          )}
        </div>
        <div className="text-right">
          <p className="text-xs uppercase tracking-[0.3em] text-slate-400">
            Confidence
          </p>
          <p className="text-lg font-semibold text-slate-900">
            {confidencePercent}%
          </p>
          <Badge variant="outline" className="mt-2 rounded-full text-slate-500">
            {suggestion.project_code}
          </Badge>
        </div>
      </div>
      <div className="mt-4 flex flex-wrap gap-3 text-xs text-slate-500">
        {suggestion.evidence?.signals?.slice(0, 3).map((signal) => (
          <span
            key={`${suggestion.id}-${signal.label}-${signal.value}`}
            className="rounded-full bg-slate-100 px-3 py-1"
          >
            {signal.label}: {signal.value}
          </span>
        ))}
        {suggestion.pattern_label && (
          <span className="rounded-full bg-indigo-50 px-3 py-1 text-indigo-600">
            {suggestion.pattern_label}
          </span>
        )}
      </div>
      <div className="mt-5 flex flex-wrap gap-3">
        <Button
          size="sm"
          className="gap-2"
          onClick={onApprove}
          disabled={disableActions}
        >
          <PhoneCall className="h-4 w-4" /> Approve fix
        </Button>
        <Button
          size="sm"
          variant="secondary"
          onClick={onSnooze}
          disabled={disableActions}
        >
          Snooze 1 day
        </Button>
        <Button size="sm" variant="ghost" onClick={onMore}>
          View evidence
        </Button>
      </div>
    </div>
  );
}

function FinancialWidget({
  title,
  amount,
  count,
  description,
  variant = "default",
}: {
  title: string;
  amount: number;
  count?: number;
  description?: string;
  variant?: "default" | "alert";
}) {
  const border =
    variant === "alert"
      ? "border-rose-100 bg-rose-50/40"
      : "border-slate-200/80 bg-white";
  const textColor = variant === "alert" ? "text-rose-700" : "text-slate-900";
  return (
    <Card className={`rounded-3xl ${border}`}>
      <CardContent className="p-6">
        <p className="text-xs uppercase tracking-[0.3em] text-slate-500">{title}</p>
        <p className={cn("mt-3", ds.typography.heading1, textColor)}>
          {formatCurrency(amount)}
        </p>
        {typeof count === "number" && (
          <p className="text-sm text-slate-500">{count} invoices</p>
        )}
        {description && (
          <p className="mt-3 text-sm text-slate-500">{description}</p>
        )}
      </CardContent>
    </Card>
  );
}

function ProjectedWidget({
  items,
  isLoading,
  isError,
}: {
  items: ProjectedInvoice[];
  isLoading?: boolean;
  isError?: boolean;
}) {
  return (
    <Card className={cn(ds.borderRadius.cardLarge, "border-slate-200/80")}>
      <CardContent className="p-6">
        <p className="text-xs uppercase tracking-[0.3em] text-slate-400">
          Upcoming invoices
        </p>
        <p className="text-sm text-slate-500">Based on scheduled presentations</p>
        {isLoading ? (
          <p className="mt-4 text-sm text-slate-500">Loading...</p>
        ) : isError ? (
          <p className="mt-4 text-sm text-rose-600">Unable to fetch invoices.</p>
        ) : items.length === 0 ? (
          <p className="mt-4 text-sm text-slate-500">No upcoming invoices yet.</p>
        ) : (
          <div className="mt-4 space-y-3">
            {items.map((item) => (
              <div
                key={`${item.project_code}-${item.presentation_date}-${item.phase}`}
                className="rounded-2xl border border-slate-100 p-3"
              >
                <div className="flex items-center justify-between text-xs text-slate-500">
                  <span>{item.scope ?? item.phase}</span>
                  <span>{formatDisplayDate(item.presentation_date)}</span>
                </div>
                <p className="mt-1 text-base font-semibold text-slate-900">
                  {item.project_name}
                </p>
                <p className="text-sm text-slate-600">
                  {formatCurrency(item.projected_fee_usd)}
                </p>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function RecentPaidInvoices({
  items,
  isLoading,
  isError,
}: {
  items: FinancePayment[];
  isLoading?: boolean;
  isError?: boolean;
}) {
  return (
    <Card className={cn(ds.borderRadius.cardLarge, "border-slate-200/80")}>
      <CardContent className="space-y-4 p-6">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-400">
            Recently paid
          </p>
          <p className="text-sm text-slate-500">Last 5 confirmed payments</p>
        </div>
        {isLoading ? (
          <p className="text-sm text-slate-500">Loading...</p>
        ) : isError ? (
          <p className="text-sm text-rose-600">Unable to fetch payments.</p>
        ) : items.length === 0 ? (
          <p className="text-sm text-slate-500">No payments recorded yet.</p>
        ) : (
          <div className="space-y-3">
            {items.map((item) => (
              <div
                key={`${item.project_code}-${item.paid_on}-${item.invoice_id ?? item.invoice_number}`}
                className="flex items-center justify-between rounded-2xl border border-slate-100 p-3"
              >
                <div>
                  <p className="text-sm font-semibold text-slate-900">
                    {item.project_name}
                  </p>
                  <p className="text-xs uppercase tracking-[0.3em] text-slate-400">
                    {(item.discipline ?? "General")} • {formatDisplayDate(item.paid_on)}
                  </p>
                </div>
                <p className="text-sm font-semibold text-slate-900">
                  {formatCurrency(item.amount_usd)}
                </p>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function RfiStatusCard({ rfiItems }: { rfiItems: RfiTileItem[] }) {
  const lateCount = rfiItems.filter((item) =>
    item.status?.toLowerCase().includes("late") ||
    item.status?.toLowerCase().includes("awaiting")
  ).length;
  return (
    <Card className={cn(ds.borderRadius.cardLarge, "border-slate-200/80")}>
      <CardContent className="space-y-4 p-6">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-400">
            RFI overview
          </p>
          <p className="text-sm text-slate-500">
            {rfiItems.length} open • {lateCount} need attention
          </p>
        </div>
        <div className="space-y-3">
          {rfiItems.slice(0, 3).map((item) => (
            <div key={item.rfi_id} className="rounded-2xl border border-slate-100 p-3">
              <div className="flex items-center justify-between text-xs text-slate-500">
                <span>{item.rfi_number}</span>
                <span>{item.asked_date ? new Date(item.asked_date).toLocaleDateString() : "—"}</span>
              </div>
              <p className="mt-1 text-base font-semibold text-slate-900">
                {item.project_name}
              </p>
              <p className="text-sm text-slate-600">{item.status || "Open"}</p>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

// StudioSchedulePanel removed - was 100% hardcoded fake data

function IntelligenceSummary({
  insights,
  briefingDateLabel,
}: {
  insights: string[];
  briefingDateLabel: string;
}) {
  const summary =
    insights.length > 0
      ? insights[0]
      : "No major shifts detected over the past week.";
  return (
    <Card className={cn(ds.borderRadius.cardLarge, "border-slate-200/80")}>
      <CardContent className="flex flex-col gap-3 p-6 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-400">
            Weekly intelligence
          </p>
          <p className={cn(ds.typography.heading2, ds.textColors.primary)}>{summary}</p>
          {insights.slice(1, 3).map((item) => (
            <p key={item} className="text-sm text-slate-500">
              • {item}
            </p>
          ))}
        </div>
        <Badge variant="secondary" className="rounded-full">
          Updated {briefingDateLabel}
        </Badge>
      </CardContent>
    </Card>
  );
}
