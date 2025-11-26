"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { TrendingUp, ArrowRight, AlertCircle, ThumbsUp, ThumbsDown, Check } from "lucide-react";
import { formatCurrency, getStatusColor, cn } from "@/lib/utils";
import { ds } from "@/lib/design-system";
import { type ProposalStatus } from "@/lib/constants";

interface ProposalTrackerWidgetProps {
  compact?: boolean;
}

export function ProposalTrackerWidget({ compact = false }: ProposalTrackerWidgetProps) {
  const [feedbackSubmitted, setFeedbackSubmitted] = useState<boolean | null>(null);
  const [isSubmittingFeedback, setIsSubmittingFeedback] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ["proposalTrackerStats"],
    queryFn: () => api.getProposalTrackerStats(),
    refetchInterval: 60000, // Refresh every minute
  });

  const stats = data?.stats;

  const handleFeedback = async (helpful: boolean) => {
    if (feedbackSubmitted !== null || isSubmittingFeedback) return;

    setIsSubmittingFeedback(true);
    try {
      await api.logFeedback({
        feature_type: "proposal_tracker",
        feature_id: "dashboard_widget",
        helpful,
        context: {
          widget_location: "dashboard",
          compact_mode: compact,
          total_proposals: stats?.total_proposals,
          pipeline_value: stats?.total_pipeline_value,
        },
      });
      setFeedbackSubmitted(helpful);
    } catch (error) {
      console.error("Failed to submit feedback:", error);
    } finally {
      setIsSubmittingFeedback(false);
    }
  };

  if (isLoading) {
    return (
      <Card className={cn(ds.borderRadius.card)}>
        <CardHeader>
          <CardTitle className={cn(ds.typography.heading3, ds.textColors.primary)}>
            Proposal Tracker
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className={cn(ds.typography.caption, ds.textColors.tertiary)}>
            Loading...
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!stats) return null;

  return (
    <Card className={cn(ds.borderRadius.card, "border-slate-200/70")}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
        <div>
          <p className={cn(ds.typography.label, ds.textColors.muted)}>
            Pipeline Status
          </p>
          <CardTitle className={cn(ds.typography.heading3, ds.textColors.primary)}>
            Proposal Tracker
          </CardTitle>
        </div>
        <Badge variant="secondary" className={cn(ds.borderRadius.badge, ds.gap.tight)}>
          <TrendingUp className="h-3.5 w-3.5" />
          {stats.total_proposals}
        </Badge>
      </CardHeader>
      <CardContent className={cn(compact ? "space-y-3" : ds.gap.normal, compact ? "space-y-3" : "space-y-4")}>
        {/* Key Metrics - RESPONSIVE */}
        {!compact && <div className="grid grid-cols-2 gap-3">
          <div className={cn(
            ds.borderRadius.card,
            "bg-gradient-to-br from-blue-50 to-blue-100 border border-blue-200",
            ds.spacing.normal
          )}>
            <p className={cn(ds.typography.captionBold, "text-blue-900 mb-1")}>
              Active Proposals
            </p>
            <p className={cn(ds.typography.heading2, "text-blue-900")}>
              {stats.total_proposals}
            </p>
          </div>
          <div className={cn(
            ds.borderRadius.card,
            "bg-gradient-to-br from-green-50 to-green-100 border border-green-200",
            ds.spacing.normal
          )}>
            <p className={cn(ds.typography.captionBold, "text-green-900 mb-1")}>
              Pipeline Value
            </p>
            <p className={cn(ds.typography.heading2, "text-green-900")}>
              {formatCurrency(stats.total_pipeline_value)}
            </p>
          </div>
        </div>}

        {/* Follow-up Alert */}
        {stats.needs_followup > 0 && (
          <div className={cn(
            ds.borderRadius.card,
            ds.status.warning.bg,
            "border",
            ds.status.warning.border,
            ds.spacing.normal
          )}>
            <div className={cn(ds.gap.normal, "flex items-start")}>
              <AlertCircle className={cn("h-5 w-5 mt-0.5", ds.status.warning.icon)} />
              <div className="flex-1">
                <p className={cn(ds.typography.bodyBold, ds.status.warning.text)}>
                  {stats.needs_followup} proposal{stats.needs_followup > 1 ? "s" : ""} need
                  follow-up
                </p>
                <p className={cn(ds.typography.caption, ds.status.warning.text, "mt-1")}>
                  {">"}14 days in current status
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Status Breakdown */}
        <div className={cn(ds.gap.normal, compact ? "space-y-2" : "space-y-3")}>
          {!compact && <p className={cn(ds.typography.label, ds.textColors.muted)}>
            By Status
          </p>}
          <div className={cn(ds.gap.tight, "space-y-2")}>
            {stats.status_breakdown.slice(0, compact ? 3 : 4).map((status: Record<string, unknown>) => (
              <div
                key={status.current_status as string}
                className={cn(
                  ds.borderRadius.card,
                  "border border-slate-200 p-3",
                  "flex items-center justify-between",
                  ds.hover.card
                )}
              >
                <div className={cn(ds.gap.tight, "flex items-center flex-1")}>
                  <Badge
                    variant="outline"
                    className={cn(
                      ds.typography.tiny,
                      ds.borderRadius.badge,
                      getStatusColor(status.current_status as ProposalStatus)
                    )}
                  >
                    {status.current_status as string}
                  </Badge>
                  <span className={cn(ds.typography.caption, ds.textColors.tertiary)}>
                    {status.count as number} {(status.count as number) === 1 ? "proposal" : "proposals"}
                  </span>
                </div>
                <span className={cn(ds.typography.bodyBold, ds.textColors.primary)}>
                  {formatCurrency(status.total_value as number)}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* View All Link */}
        <Link href="/tracker" className="block">
          <Button
            variant="outline"
            className={cn(
              "w-full",
              ds.borderRadius.button,
              ds.gap.tight,
              ds.hover.button
            )}
            size="sm"
          >
            View All Proposals
            <ArrowRight className="h-3 w-3" />
          </Button>
        </Link>

        {/* RLHF Feedback Section */}
        <div className={cn(
          "pt-3 border-t border-slate-200",
          "flex items-center justify-between"
        )}>
          <p className={cn(ds.typography.caption, ds.textColors.tertiary)}>
            Was this helpful?
          </p>
          <div className="flex gap-2">
            {feedbackSubmitted === null ? (
              <>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => handleFeedback(true)}
                  disabled={isSubmittingFeedback}
                  className={cn(
                    "h-7 w-7 p-0",
                    ds.hover.button,
                    "hover:bg-green-50 hover:text-green-600"
                  )}
                >
                  <ThumbsUp className="h-3.5 w-3.5" />
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => handleFeedback(false)}
                  disabled={isSubmittingFeedback}
                  className={cn(
                    "h-7 w-7 p-0",
                    ds.hover.button,
                    "hover:bg-red-50 hover:text-red-600"
                  )}
                >
                  <ThumbsDown className="h-3.5 w-3.5" />
                </Button>
              </>
            ) : (
              <div className={cn(
                "flex items-center gap-1.5",
                ds.typography.caption,
                "text-green-600"
              )}>
                <Check className="h-3.5 w-3.5" />
                Thanks!
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
