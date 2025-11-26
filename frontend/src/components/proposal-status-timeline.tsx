"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Clock, ArrowRight } from "lucide-react";
import { ProposalStatus } from "@/lib/types";
import { getStatusColor, cn } from "@/lib/utils";
import { ds } from "@/lib/design-system";

interface ProposalStatusTimelineProps {
  projectCode: string;
}

export function ProposalStatusTimeline({ projectCode }: ProposalStatusTimelineProps) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["proposalStatusHistory", projectCode],
    queryFn: () => api.getProposalStatusHistory(projectCode),
    enabled: !!projectCode,
  });

  const history = data?.history || [];

  if (isLoading) {
    return (
      <Card className={cn(ds.borderRadius.card)}>
        <CardHeader>
          <CardTitle className={cn(ds.typography.heading3, ds.textColors.primary)}>
            Status History
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className={cn(ds.typography.caption, ds.textColors.tertiary)}>
            Loading history...
          </div>
        </CardContent>
      </Card>
    );
  }

  if (isError) {
    return (
      <Card className={cn(ds.borderRadius.card)}>
        <CardHeader>
          <CardTitle className={cn(ds.typography.heading3, ds.textColors.primary)}>
            Status History
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className={cn(ds.typography.caption, ds.status.danger.text)}>
            Failed to load history
          </div>
        </CardContent>
      </Card>
    );
  }

  if (history.length === 0) {
    return (
      <Card className={cn(ds.borderRadius.card)}>
        <CardHeader>
          <CardTitle className={cn(ds.typography.heading3, ds.textColors.primary)}>
            Status History
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className={cn(ds.typography.caption, ds.textColors.tertiary)}>
            No status changes recorded yet
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={cn(ds.borderRadius.card)}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className={cn(ds.typography.heading3, ds.textColors.primary)}>
            Status History
          </CardTitle>
          <Badge variant="outline" className={cn(ds.borderRadius.badge, ds.gap.tight, ds.typography.tiny)}>
            <Clock className="h-3 w-3" />
            {history.length} {history.length === 1 ? "change" : "changes"}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className={cn("relative", ds.gap.normal, "space-y-4")}>
          {/* Timeline line - Thicker for better visibility */}
          <div className="absolute left-2.5 top-0 bottom-0 w-0.5 bg-slate-200" />

          {history.map((item) => (
            <div key={item.id} className={cn("relative flex", ds.gap.normal)}>
              {/* Timeline dot - Simplified design */}
              <div className="relative z-10 flex-shrink-0">
                <div className={cn(
                  "h-5 w-5 rounded-full border-2 border-white",
                  ds.status.info.bg,
                  ds.shadows.sm
                )} />
              </div>

              {/* Content */}
              <div className="flex-1 pb-4">
                <div className={cn(
                  ds.borderRadius.card,
                  "border bg-white p-4",
                  ds.shadows.sm
                )}>
                  {/* Status transition */}
                  <div className={cn(ds.gap.tight, "flex items-center mb-2")}>
                    {item.old_status && (
                      <>
                        <Badge
                          variant="outline"
                          className={cn(
                            ds.typography.tiny,
                            ds.borderRadius.badge,
                            getStatusColor(item.old_status as ProposalStatus)
                          )}
                        >
                          {item.old_status}
                        </Badge>
                        <ArrowRight className={cn("h-3 w-3", ds.textColors.tertiary)} />
                      </>
                    )}
                    <Badge
                      variant="outline"
                      className={cn(
                        ds.typography.tiny,
                        ds.borderRadius.badge,
                        getStatusColor(item.new_status as ProposalStatus)
                      )}
                    >
                      {item.new_status}
                    </Badge>
                  </div>

                  {/* Timestamp */}
                  <div className={cn(ds.typography.tiny, ds.textColors.tertiary, "mb-2")}>
                    {new Date(item.changed_date).toLocaleString("en-US", {
                      year: "numeric",
                      month: "short",
                      day: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </div>

                  {/* Notes */}
                  {item.notes && (
                    <div className={cn(
                      ds.typography.caption,
                      ds.textColors.primary,
                      "mt-2 p-2",
                      ds.borderRadius.small,
                      ds.status.neutral.bg
                    )}>
                      {item.notes}
                    </div>
                  )}

                  {/* Changed by */}
                  {item.changed_by && (
                    <div className={cn(ds.typography.tiny, ds.textColors.tertiary, "mt-2")}>
                      Changed by: {item.changed_by}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
