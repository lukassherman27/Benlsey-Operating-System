"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertTriangle, Clock } from "lucide-react";
import { formatCurrency, cn } from "@/lib/utils";
import { type ProposalStatus } from "@/lib/constants";

interface StatusBreakdown {
  current_status: string;
  count: number;
  total_value: number;
}

interface PipelineStats {
  status_breakdown?: StatusBreakdown[];
  overdue_count?: number;
  needs_followup?: number;
}

interface ProposalPipelineFunnelProps {
  stats: PipelineStats | null;
  statusFilter: ProposalStatus | "all";
  onStatusClick: (status: ProposalStatus | "all") => void;
}

// Pipeline stage configuration
const PIPELINE_STAGES = [
  { status: "First Contact", color: "bg-slate-400", textColor: "text-slate-700", label: "First Contact" },
  { status: "Proposal Prep", color: "bg-blue-400", textColor: "text-blue-700", label: "Preparing Proposal" },
  { status: "Proposal Sent", color: "bg-amber-500", textColor: "text-amber-700", label: "Proposal Sent" },
  { status: "Negotiation", color: "bg-emerald-500", textColor: "text-emerald-700", label: "Negotiation" },
  { status: "On Hold", color: "bg-orange-400", textColor: "text-orange-700", label: "On Hold (Paused)" },
] as const;

export function ProposalPipelineFunnel({ stats, statusFilter, onStatusClick }: ProposalPipelineFunnelProps) {
  if (!stats || !stats.status_breakdown?.length) return null;

  const maxCount = Math.max(...(stats.status_breakdown?.map((s) => s.count) || [1]));

  return (
    <Card className="border-slate-200">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium text-slate-600">
            Pipeline Stages
          </CardTitle>
          <div className="flex items-center gap-4 text-xs text-slate-500">
            {(stats.overdue_count ?? 0) > 0 && (
              <span className="flex items-center gap-1 text-red-600 font-semibold">
                <AlertTriangle className="h-3 w-3" />
                {stats.overdue_count} overdue
              </span>
            )}
            <span className="flex items-center gap-1">
              <Clock className="h-3 w-3 text-amber-500" />
              {stats.needs_followup} need follow-up
            </span>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-2">
        {PIPELINE_STAGES.map(({ status, color, textColor, label }) => {
          const data = stats.status_breakdown?.find((s) => s.current_status === status);
          const count = data?.count || 0;
          const value = data?.total_value || 0;
          const widthPercent = maxCount > 0 ? Math.max((count / maxCount) * 100, 8) : 8;

          return (
            <div
              key={status}
              className={cn(
                "flex items-center gap-3 cursor-pointer p-2 rounded hover:bg-slate-50 transition-colors",
                statusFilter === status && "bg-slate-100 ring-1 ring-slate-300"
              )}
              onClick={() => onStatusClick(statusFilter === status ? "all" : status as ProposalStatus)}
            >
              {/* Stage label */}
              <span className={cn("w-36 text-sm font-medium", textColor)}>
                {label}
              </span>

              {/* Bar */}
              <div className="flex-1 h-6 bg-slate-100 rounded overflow-hidden">
                <div
                  className={cn(color, "h-full flex items-center justify-end pr-2 transition-all")}
                  style={{ width: `${widthPercent}%` }}
                >
                  {count > 0 && (
                    <span className="text-white text-xs font-bold">{count}</span>
                  )}
                </div>
              </div>

              {/* Value */}
              <span className="w-24 text-right text-sm font-medium text-slate-600">
                {formatCurrency(value)}
              </span>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
