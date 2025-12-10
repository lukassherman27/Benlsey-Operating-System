"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Clock,
  AlertTriangle,
  AlertCircle,
  Eye,
  ChevronRight,
  Mail,
  Phone,
} from "lucide-react";
import { formatCurrency, cn } from "@/lib/utils";
import Link from "next/link";
import { ProposalFollowUp } from "@/lib/types";

type TierKey = "critical" | "high" | "medium" | "watch";

const tierConfig: Record<
  TierKey,
  {
    label: string;
    color: string;
    bgColor: string;
    borderColor: string;
    icon: React.ReactNode;
    description: string;
  }
> = {
  critical: {
    label: "Critical",
    color: "text-red-700",
    bgColor: "bg-red-50",
    borderColor: "border-red-200",
    icon: <AlertTriangle className="h-4 w-4" />,
    description: "90+ days no response",
  },
  high: {
    label: "High",
    color: "text-orange-700",
    bgColor: "bg-orange-50",
    borderColor: "border-orange-200",
    icon: <AlertCircle className="h-4 w-4" />,
    description: "30-90 days no response",
  },
  medium: {
    label: "Medium",
    color: "text-amber-700",
    bgColor: "bg-amber-50",
    borderColor: "border-amber-200",
    icon: <Clock className="h-4 w-4" />,
    description: "14-30 days no response",
  },
  watch: {
    label: "Watch",
    color: "text-blue-700",
    bgColor: "bg-blue-50",
    borderColor: "border-blue-200",
    icon: <Eye className="h-4 w-4" />,
    description: "7-14 days no response",
  },
};

export function FollowUpWidget() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["proposals-needs-attention"],
    queryFn: () => api.getProposalsNeedsAttention(),
    staleTime: 1000 * 60 * 5, // 5 minutes
  });

  if (isLoading) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center gap-2">
            <Clock className="h-5 w-5 text-amber-500" />
            <h3 className="font-semibold">Follow-Up Needed</h3>
          </div>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-16 bg-slate-100 rounded-lg" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error || !data) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center gap-2">
            <Clock className="h-5 w-5 text-amber-500" />
            <h3 className="font-semibold">Follow-Up Needed</h3>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-slate-500">Unable to load follow-up data</p>
        </CardContent>
      </Card>
    );
  }

  const { summary, tiers } = data;

  if (summary.total === 0) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center gap-2">
            <Clock className="h-5 w-5 text-amber-500" />
            <h3 className="font-semibold">Follow-Up Needed</h3>
          </div>
        </CardHeader>
        <CardContent>
          <div className="text-center py-6 text-slate-500">
            <p className="text-sm">No proposals need follow-up</p>
            <p className="text-xs mt-1">All caught up!</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Clock className="h-5 w-5 text-amber-500" />
            <h3 className="font-semibold">Follow-Up Needed</h3>
            <Badge variant="secondary" className="ml-1">
              {summary.total}
            </Badge>
          </div>
          <Link
            href="/tracker?filter=needs-followup"
            className="text-xs text-slate-500 hover:text-slate-700 flex items-center gap-1"
          >
            View all <ChevronRight className="h-3 w-3" />
          </Link>
        </div>

        {/* Summary badges */}
        <div className="flex flex-wrap gap-2 mt-2">
          {(Object.keys(tierConfig) as TierKey[]).map((tier) => {
            const count = summary[tier];
            if (count === 0) return null;
            const config = tierConfig[tier];
            return (
              <Badge
                key={tier}
                variant="outline"
                className={cn(config.bgColor, config.borderColor, config.color)}
              >
                {config.icon}
                <span className="ml-1">
                  {count} {config.label}
                </span>
              </Badge>
            );
          })}
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        <div className="space-y-2 max-h-[400px] overflow-y-auto">
          {/* Show top items from each tier */}
          {(["critical", "high", "medium", "watch"] as TierKey[]).map((tier) => {
            const items = tiers[tier];
            if (!items || items.length === 0) return null;

            return (
              <div key={tier} className="space-y-2">
                <div className="text-xs font-medium text-slate-500 uppercase tracking-wide pt-2 first:pt-0">
                  {tierConfig[tier].label} Priority
                </div>
                {items.slice(0, tier === "critical" ? 5 : 3).map((proposal) => (
                  <FollowUpItem
                    key={proposal.proposal_id}
                    proposal={proposal}
                    tier={tier}
                  />
                ))}
                {items.length > (tier === "critical" ? 5 : 3) && (
                  <p className="text-xs text-slate-400 pl-2">
                    +{items.length - (tier === "critical" ? 5 : 3)} more
                  </p>
                )}
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

function FollowUpItem({
  proposal,
  tier,
}: {
  proposal: ProposalFollowUp;
  tier: TierKey;
}) {
  const config = tierConfig[tier];

  return (
    <Link href={`/tracker?code=${encodeURIComponent(proposal.project_code)}`}>
      <div
        className={cn(
          "p-3 rounded-lg border transition-colors cursor-pointer hover:shadow-sm",
          config.bgColor,
          config.borderColor
        )}
      >
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className={cn("flex-shrink-0", config.color)}>
                {config.icon}
              </span>
              <p className="text-sm font-medium text-slate-900 truncate">
                {proposal.project_name || proposal.project_code}
              </p>
            </div>
            <p className="text-xs text-slate-500 mt-0.5 truncate">
              {proposal.project_code} &bull; {proposal.status}
            </p>
          </div>
          <Badge variant="outline" className="flex-shrink-0 text-xs">
            {proposal.days_since_contact}d
          </Badge>
        </div>

        <div className="mt-2 flex items-center gap-4 text-xs text-slate-600">
          {proposal.contact_person && (
            <span className="flex items-center gap-1 truncate">
              <Phone className="h-3 w-3" />
              {proposal.contact_person}
            </span>
          )}
          {proposal.email_count > 0 && (
            <span className="flex items-center gap-1">
              <Mail className="h-3 w-3" />
              {proposal.email_count} emails
            </span>
          )}
          {proposal.project_value && (
            <span className="font-medium">
              {formatCurrency(proposal.project_value)}
            </span>
          )}
        </div>

        {proposal.last_subject && (
          <p className="mt-1 text-xs text-slate-500 truncate italic">
            Last: {proposal.last_subject.replace(/\r?\n/g, " ")}
          </p>
        )}
      </div>
    </Link>
  );
}
