import { useMemo } from "react";
import { ProposalSummary } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { HealthBadge } from "./health-badge";
import { Search } from "lucide-react";
import { cn } from "@/lib/utils";
import { ds } from "@/lib/design-system";

type Props = {
  proposals?: ProposalSummary[];
  isLoading?: boolean;
  selectedCode?: string | null;
  onSelect?: (projectCode: string) => void;
  searchTerm: string;
  onSearchTermChange: (value: string) => void;
};

export default function ProposalTable({
  proposals,
  isLoading,
  selectedCode,
  onSelect,
  searchTerm,
  onSearchTermChange,
}: Props) {
  const formatStatus = (value?: string) => {
    if (!value) return "Status unknown";
    return value.replace(/[_-]/g, " ").toUpperCase();
  };

  const formatLastContact = (days?: number | null) => {
    if (days == null) return "No contact logged";
    if (days === 0) return "Today";
    if (days === 1) return "1 day ago";
    return `${days} days ago`;
  };

  const getHealthStatus = (score?: number | null) => {
    if (score == null) return undefined;
    if (score >= 70) return "healthy";
    if (score >= 50) return "at_risk";
    return "critical";
  };

  const grouped = useMemo(() => {
    const buckets: Record<"critical" | "attention" | "onTrack", ProposalSummary[]> = {
      critical: [],
      attention: [],
      onTrack: [],
    };
    (proposals ?? []).forEach((proposal) => {
      const score = proposal.health_score ?? 0;
      if (score < 50 || (proposal.status ?? "").toLowerCase().includes("hold")) {
        buckets.critical.push(proposal);
      } else if (score < 70) {
        buckets.attention.push(proposal);
      } else {
        buckets.onTrack.push(proposal);
      }
    });
    return buckets;
  }, [proposals]);

  const groupMeta: Array<{
    key: "critical" | "attention" | "onTrack";
    title: string;
    description: string;
    accent: string;
  }> = [
    {
      key: "critical",
      title: "Needs intervention",
      description: "Projects that require immediate follow-up.",
      accent: "border-rose-200 bg-rose-50/90",
    },
    {
      key: "attention",
      title: "Needs attention",
      description: "Keep warm or close small gaps.",
      accent: "border-amber-200 bg-amber-50/80",
    },
    {
      key: "onTrack",
      title: "On track",
      description: "Healthy projects to monitor.",
      accent: "border-emerald-200 bg-emerald-50/80",
    },
  ];

  return (
    <Card className={cn("flex h-full flex-col border border-slate-200/80 shadow-sm", ds.borderRadius.cardLarge)}>
      <CardHeader className="space-y-4">
        <div className="flex items-center justify-between gap-4">
          <div>
            <CardTitle className="text-lg font-semibold">
              Proposal Tracker
            </CardTitle>
            <p className="text-sm text-muted-foreground">
              {proposals?.length ?? 0} proposals loaded
            </p>
          </div>
        </div>
        <div className="relative">
          <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search by name, client, or code"
            className="pl-9"
            value={searchTerm}
            onChange={(event) => onSearchTermChange(event.target.value)}
          />
        </div>
      </CardHeader>
      <CardContent className="flex-1 p-0">
        {isLoading ? (
          <div className="space-y-2 p-6">
            <Skeleton className="h-6 w-full" />
            <Skeleton className="h-6 w-full" />
            <Skeleton className="h-6 w-full" />
          </div>
        ) : !proposals || proposals.length === 0 ? (
          <div className="p-8 text-center text-sm text-muted-foreground">
            No proposals yet. Once data is synced, they will appear here.
          </div>
        ) : (
          <ScrollArea className="h-full max-h-[600px] px-6 pb-6">
            <div className="space-y-6">
              {groupMeta.map((group) => {
                const bucket = grouped[group.key];
                if (bucket.length === 0) {
                  return null;
                }
                return (
                  <div key={group.key} className="space-y-3">
                    <div>
                      <p className="text-sm font-semibold text-slate-900">
                        {group.title}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {group.description}
                      </p>
                    </div>
                    {bucket.map((proposal) => {
                      const selected = selectedCode === proposal.project_code;
                      const healthScore =
                        proposal.health_score != null
                          ? Math.round(proposal.health_score)
                          : undefined;
                      const nextAction =
                        proposal.next_action ?? "No next action logged";

                      return (
                        <button
                          type="button"
                          key={proposal.project_code}
                          className={cn(
                            "w-full border p-5 text-left transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40",
                            ds.borderRadius.cardLarge,
                            group.accent,
                            selected &&
                              "border-slate-900 bg-slate-950 text-white shadow-[0_20px_60px_rgba(15,23,42,0.45)]"
                          )}
                          onClick={() => onSelect?.(proposal.project_code)}
                        >
                          <div className="flex flex-wrap items-start justify-between gap-4">
                            <div className="space-y-2">
                              <p
                                className={cn(
                                  "text-base font-semibold tracking-tight",
                                  selected ? "text-white" : "text-slate-900"
                                )}
                              >
                                {proposal.project_name ?? proposal.project_code}
                              </p>
                              <p
                                className={cn(
                                  "text-sm",
                                  selected
                                    ? "text-white/80"
                                    : "text-muted-foreground"
                                )}
                              >
                                {proposal.client_name ?? "Unknown client"}
                              </p>
                              <div className="flex flex-wrap gap-2">
                                <Badge
                                  variant={selected ? "secondary" : "outline"}
                                  className="rounded-full text-xs"
                                >
                                  {proposal.project_code}
                                </Badge>
                                {proposal.pm && (
                                  <Badge
                                    variant="outline"
                                    className={cn(
                                      "rounded-full text-xs",
                                      selected && "border-white/30 text-white/80"
                                    )}
                                  >
                                    PM {proposal.pm}
                                  </Badge>
                                )}
                              </div>
                            </div>
                            <div className="text-right">
                              <p
                                className={cn(
                                  "text-xs uppercase tracking-[0.3em]",
                                  selected
                                    ? "text-white/70"
                                    : "text-muted-foreground"
                                )}
                              >
                                Health
                              </p>
                              <p
                                className={cn(
                                  ds.typography.heading1,
                                  selected ? "text-white" : ds.textColors.primary
                                )}
                              >
                                {healthScore ?? "—"}
                              </p>
                              <HealthBadge status={getHealthStatus(healthScore)} />
                            </div>
                          </div>
                          <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-2 text-xs uppercase tracking-wide">
                            <Badge
                              variant={selected ? "outline" : "secondary"}
                              className={cn(
                                "rounded-full px-3 py-1",
                                selected &&
                                  "border-white/40 bg-white/10 text-white/80"
                              )}
                            >
                              {formatStatus(proposal.status)}
                            </Badge>
                            <span
                              className={cn(
                                selected ? "text-white/80" : "text-muted-foreground"
                              )}
                            >
                              Last contact {formatLastContact(proposal.days_since_contact)}
                            </span>
                            <span
                              className={cn(
                                "flex-1 text-left capitalize",
                                selected ? "text-white" : "text-slate-900"
                              )}
                            >
                              {nextAction}
                            </span>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                );
              })}
            </div>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  );
}
