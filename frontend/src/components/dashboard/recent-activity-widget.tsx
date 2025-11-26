"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  FileText,
  DollarSign,
  Clock,
} from "lucide-react";
import { formatCurrency, cn } from "@/lib/utils";
import { ds } from "@/lib/design-system";

type ActivityItem = {
  id: string;
  type: "payment" | "proposal" | "invoice" | "email";
  title: string;
  description: string;
  timestamp: string;
  amount?: number;
  icon: React.ElementType;
  iconColor: string;
  bgColor: string;
};

export function RecentActivityWidget() {
  const recentPaymentsQuery = useQuery({
    queryKey: ["recent-payments"],
    queryFn: () => api.getRecentPayments(3),
    staleTime: 1000 * 60 * 5,
  });

  const proposalStatsQuery = useQuery({
    queryKey: ["proposalTrackerStats"],
    queryFn: api.getProposalTrackerStats,
    refetchInterval: 1000 * 60 * 5,
  });

  // Build activity feed from different sources
  const activities: ActivityItem[] = [];

  // Add recent payments
  if (recentPaymentsQuery.data?.payments) {
    recentPaymentsQuery.data.payments.slice(0, 3).forEach((payment) => {
      activities.push({
        id: `payment-${payment.invoice_id}`,
        type: "payment",
        title: payment.project_name || payment.project_code,
        description: `${payment.project_code} • Invoice ${payment.invoice_number} • ${formatCurrency(payment.amount_usd)}`,
        timestamp: payment.paid_on || "Recently",
        amount: payment.amount_usd,
        icon: DollarSign,
        iconColor: ds.status.success.icon,
        bgColor: ds.status.success.bg,
      });
    });
  }

  // Add proposal updates
  if (proposalStatsQuery.data?.stats) {
    const stats = proposalStatsQuery.data.stats;
    const proposalSentCount = stats.status_breakdown?.find(
      (b) => b.current_status === "Proposal Sent"
    )?.count || 0;
    if (proposalSentCount > 0) {
      activities.push({
        id: "proposals-sent",
        type: "proposal",
        title: "Proposals Sent",
        description: `${proposalSentCount} proposals awaiting response`,
        timestamp: "Active",
        icon: FileText,
        iconColor: ds.status.info.icon,
        bgColor: ds.status.info.bg,
      });
    }
  }

  // Sort by timestamp (most recent first)
  activities.sort((a, b) => {
    if (a.timestamp === "Active" || a.timestamp === "Recently") return -1;
    if (b.timestamp === "Active" || b.timestamp === "Recently") return 1;
    return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
  });

  // Limit to 5 items
  const recentActivities = activities.slice(0, 5);

  return (
    <Card className={cn(ds.borderRadius.card, "border-slate-200/70")}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <p className={cn(ds.typography.label, ds.textColors.muted)}>
              Recent Activity
            </p>
            <CardTitle className={cn(ds.typography.heading3, ds.textColors.primary)}>
              Latest Updates
            </CardTitle>
          </div>
          <Badge variant="secondary" className={cn(ds.borderRadius.badge, ds.gap.tight)}>
            <Clock className="h-3.5 w-3.5" />
            Live
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        {recentPaymentsQuery.isLoading ? (
          <p className={cn(ds.typography.caption, ds.textColors.tertiary)}>
            Loading activity...
          </p>
        ) : recentActivities.length === 0 ? (
          <div className="text-center py-8">
            <div className={cn(ds.borderRadius.badge, "bg-slate-100 p-4 inline-flex mb-3")}>
              <Clock className={cn("h-6 w-6", ds.textColors.muted)} />
            </div>
            <p className={cn(ds.typography.caption, ds.textColors.tertiary)}>
              No recent activity
            </p>
          </div>
        ) : (
          <div className={cn(ds.gap.normal, "space-y-3")}>
            {recentActivities.map((activity) => {
              const Icon = activity.icon;
              return (
                <div
                  key={activity.id}
                  className={cn(
                    ds.borderRadius.card,
                    "border border-slate-200 p-4 transition-all",
                    activity.bgColor,
                    ds.hover.card
                  )}
                >
                  <div className={cn(ds.gap.normal, "flex items-start")}>
                    <div className={cn(ds.borderRadius.button, "bg-white p-2.5", ds.shadows.sm)}>
                      <Icon className={cn("h-4 w-4", activity.iconColor)} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1">
                          <p className={cn(ds.typography.bodyBold, ds.textColors.primary)}>
                            {activity.title}
                          </p>
                          <p className={cn(ds.typography.caption, ds.textColors.secondary, "mt-0.5")}>
                            {activity.description}
                          </p>
                        </div>
                      </div>
                      <div className={cn(ds.gap.tight, "flex items-center mt-2")}>
                        <Badge variant="outline" className={ds.typography.tiny}>
                          {activity.type}
                        </Badge>
                        <span className={cn(ds.typography.tiny, ds.textColors.tertiary)}>
                          {typeof activity.timestamp === "string" &&
                          activity.timestamp.includes("-")
                            ? new Date(activity.timestamp).toLocaleDateString()
                            : activity.timestamp}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
