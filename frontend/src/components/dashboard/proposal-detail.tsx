import {
  ProposalDetail,
  ProposalHealth,
  ProposalTimelineResponse,
} from "@/lib/types";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { HealthBadge } from "./health-badge";
import { Activity, Clock, Mail } from "lucide-react";
import { Button } from "@/components/ui/button";
import { format } from "date-fns";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

type Props = {
  proposal?: ProposalDetail;
  health?: ProposalHealth;
  timeline?: ProposalTimelineResponse;
  isLoading?: boolean;
};

export default function ProposalDetailPanel({
  proposal,
  health,
  timeline,
  isLoading,
}: Props) {
  const formatDate = (value?: string | null) => {
    if (!value) return "—";
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return "—";
    return format(parsed, "MMM d, yyyy");
  };

  const infoTiles = [
    {
      label: "Phase",
      value: proposal?.phase ?? "Not set",
    },
    {
      label: "Win probability",
      value:
        proposal?.win_probability != null
          ? `${Math.round(proposal.win_probability * 100)}%`
          : "—",
    },
    {
      label: "Emails linked",
      value: proposal?.email_count ?? timeline?.stats?.total_emails ?? 0,
    },
    {
      label: "Documents linked",
      value: proposal?.document_count ?? timeline?.stats?.total_documents ?? 0,
    },
  ];

  const renderSkeleton = () => (
    <Card className="h-full rounded-[32px] border border-slate-200/80 shadow-sm">
      <CardContent className="space-y-4 p-6">
        <Skeleton className="h-12 w-2/3 rounded-2xl" />
        <Skeleton className="h-24 w-full rounded-3xl" />
        <Skeleton className="h-32 w-full rounded-3xl" />
      </CardContent>
    </Card>
  );

  if (isLoading) {
    return renderSkeleton();
  }

  const lastContactDisplay = formatDate(proposal?.last_contact_date);
  const statusLabel = proposal?.status
    ? proposal.status.replace(/[_-]/g, " ").toUpperCase()
    : "Awaiting status";
  const pmLabel = proposal?.pm ?? "PM not assigned";

  return (
    <Card className="h-full rounded-[32px] border border-slate-200/80 shadow-sm">
      <CardContent className="space-y-6 p-6">
        <div className="rounded-[28px] border border-slate-900/15 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6 text-white shadow-[0_25px_80px_rgba(15,23,42,0.45)]">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="space-y-3">
              <p className="text-xs uppercase tracking-[0.4em] text-white/70">
                Live briefing
              </p>
              <div>
                <h3 className="text-2xl font-semibold">
                  {proposal?.project_name ?? "Select a proposal"}
                </h3>
                <p className="text-sm text-white/80">
                  {proposal?.client_name ?? "Client pending"}
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                {proposal?.project_code && (
                  <Badge className="rounded-full bg-white/10 text-white">
                    {proposal.project_code}
                  </Badge>
                )}
                <Badge
                  variant="outline"
                  className="rounded-full border-white/30 text-white/80"
                >
                  {statusLabel}
                </Badge>
              </div>
            </div>
            <div className="text-right">
              <p className="text-xs uppercase tracking-[0.3em] text-white/70">
                Health
              </p>
              <div className="mt-1 flex items-center justify-end gap-2">
                <span className="text-4xl font-semibold">
                  {health?.health_score != null
                    ? Math.round(health.health_score)
                    : "—"}
                </span>
                <Activity className="h-5 w-5 text-white/70" />
              </div>
              <HealthBadge status={health?.health_status} />
              <div className="mt-2 flex justify-end">
                <Dialog>
                  <DialogTrigger asChild>
                    <Button
                      variant="secondary"
                      size="sm"
                      className="rounded-full bg-white/10 px-3 text-xs text-white hover:bg-white/20"
                    >
                      View breakdown
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="max-w-lg">
                    <DialogHeader>
                      <DialogTitle>Health Score Breakdown</DialogTitle>
                      <DialogDescription>
                        Factors for {proposal?.project_code ?? "this proposal"}.
                      </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 text-sm">
                      <div>
                        <p className="font-semibold">Factors</p>
                        {health?.factors &&
                        Object.keys(health.factors).length ? (
                          <ul className="mt-2 list-disc space-y-1 pl-4 text-muted-foreground">
                            {Object.entries(health.factors).map(
                              ([key, value]) => (
                                <li key={key}>
                                  <span className="font-medium text-foreground">
                                    {key.replaceAll("_", " ")}:
                                  </span>{" "}
                                  {value ?? "n/a"}
                                </li>
                              )
                            )}
                          </ul>
                        ) : (
                          <p className="mt-2 text-muted-foreground">
                            No detailed factors recorded.
                          </p>
                        )}
                      </div>
                      <div>
                        <p className="font-semibold">Risks</p>
                        {health?.risks && health.risks.length ? (
                          <ul className="mt-2 space-y-2 text-muted-foreground">
                            {health.risks.map((risk, index) => (
                              <li
                                key={`${risk.type}-${index}`}
                                className="rounded-md border p-2 text-xs"
                              >
                                <span className="font-semibold text-foreground">
                                  {risk.type} ({risk.severity})
                                </span>
                                <p>{risk.description}</p>
                              </li>
                            ))}
                          </ul>
                        ) : (
                          <p className="mt-2 text-muted-foreground">
                            No explicit risks logged.
                          </p>
                        )}
                      </div>
                      {health?.recommendation && (
                        <div>
                          <p className="font-semibold">Recommendation</p>
                          <p className="mt-1 text-muted-foreground">
                            {health.recommendation}
                          </p>
                        </div>
                      )}
                    </div>
                  </DialogContent>
                </Dialog>
              </div>
              {proposal && proposal.health_calculated === false && (
                <Badge
                  variant="outline"
                  className="mt-2 rounded-full border-white/30 text-xs text-white/80"
                >
                  Pending real data
                </Badge>
              )}
            </div>
          </div>
          <div className="mt-4 flex flex-wrap gap-4 text-sm text-white/80">
            <span>Client contact: {proposal?.client_name ?? "—"}</span>
            <span>PM: {pmLabel}</span>
            <span>Last contact: {lastContactDisplay}</span>
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          {infoTiles.map((tile) => (
            <div
              key={tile.label}
              className="rounded-2xl border border-slate-200/80 bg-white/80 p-4"
            >
              <p className="text-xs uppercase text-muted-foreground">
                {tile.label}
              </p>
              <p className="text-base font-semibold text-slate-900">
                {tile.value}
              </p>
            </div>
          ))}
        </div>

        <Separator />

        <div className="grid gap-4 text-sm">
          <div className="flex items-center gap-2 text-muted-foreground">
            <Clock className="h-4 w-4" />
            Last contact
            <span className="font-semibold text-foreground">
              {lastContactDisplay}
            </span>
          </div>
          <div className="flex items-center gap-2 text-muted-foreground">
            <Mail className="h-4 w-4" />
            Emails linked
            <span className="font-semibold text-foreground">
              {proposal?.email_count ?? timeline?.stats?.total_emails ?? 0}
            </span>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200/80 bg-white/90 p-4">
          <p className="text-xs uppercase text-muted-foreground">
            Next action
          </p>
          <p className="text-sm font-semibold text-slate-900">
            {proposal?.next_action ?? "No next action logged"}
          </p>
          <p className="text-xs text-muted-foreground">
            Last updated {lastContactDisplay}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
