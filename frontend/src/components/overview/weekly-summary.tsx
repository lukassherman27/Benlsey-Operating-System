"use client";

import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { formatCurrency, cn } from "@/lib/utils";
import {
  Plus,
  Trophy,
  TrendingUp,
  AlertTriangle,
  ArrowRight,
} from "lucide-react";

interface WeeklySummaryProps {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  weeklyData: any;
  isLoading: boolean;
}

export function WeeklySummary({ weeklyData, isLoading }: WeeklySummaryProps) {
  const router = useRouter();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
        <Skeleton className="h-64" />
        <Skeleton className="h-64" />
      </div>
    );
  }

  const data = weeklyData || {};
  const newProposals = data.new_proposals || [];
  const wonProposals = data.won_proposals || [];
  const statusChanges = data.status_changes || [];
  const stalledProposals = data.stalled_proposals || [];

  return (
    <div className="space-y-6">
      {/* Summary Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border-blue-200 bg-blue-50/30">
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 mb-1">
              <Plus className="h-4 w-4 text-blue-500" />
              <span className="text-xs font-medium text-blue-600 uppercase">New</span>
            </div>
            <p className="text-2xl font-bold text-blue-700">{newProposals.length}</p>
          </CardContent>
        </Card>

        <Card className="border-emerald-200 bg-emerald-50/30">
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 mb-1">
              <Trophy className="h-4 w-4 text-emerald-500" />
              <span className="text-xs font-medium text-emerald-600 uppercase">Won</span>
            </div>
            <p className="text-2xl font-bold text-emerald-700">{wonProposals.length}</p>
          </CardContent>
        </Card>

        <Card className="border-purple-200 bg-purple-50/30">
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 mb-1">
              <TrendingUp className="h-4 w-4 text-purple-500" />
              <span className="text-xs font-medium text-purple-600 uppercase">Advanced</span>
            </div>
            <p className="text-2xl font-bold text-purple-700">{statusChanges.length}</p>
          </CardContent>
        </Card>

        <Card className="border-red-200 bg-red-50/30">
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 mb-1">
              <AlertTriangle className="h-4 w-4 text-red-500" />
              <span className="text-xs font-medium text-red-600 uppercase">Stalled</span>
            </div>
            <p className="text-2xl font-bold text-red-700">{stalledProposals.length}</p>
          </CardContent>
        </Card>
      </div>

      {/* New Proposals This Week */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-slate-600 flex items-center gap-2">
            <Plus className="h-4 w-4 text-blue-500" />
            New Proposals This Week
          </CardTitle>
        </CardHeader>
        <CardContent>
          {newProposals.length === 0 ? (
            <p className="text-sm text-slate-400 py-4 text-center">
              No new proposals this week
            </p>
          ) : (
            <div className="space-y-2">
              {newProposals.map((p: { project_code: string; project_name: string; project_value: number; created_at: string }) => (
                <div
                  key={p.project_code}
                  className="flex items-center justify-between py-2 border-b border-slate-100 last:border-0 cursor-pointer hover:bg-slate-50 rounded px-2 -mx-2"
                  onClick={() => router.push(`/proposals/${encodeURIComponent(p.project_code)}`)}
                >
                  <div>
                    <p className="text-sm font-medium text-slate-900">
                      {p.project_code} | {p.project_name}
                    </p>
                    <p className="text-xs text-slate-500">
                      {new Date(p.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                    </p>
                  </div>
                  <span className="text-sm font-semibold text-slate-600">
                    {formatCurrency(p.project_value)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Status Changes */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-slate-600 flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-purple-500" />
            Status Changes
          </CardTitle>
        </CardHeader>
        <CardContent>
          {statusChanges.length === 0 ? (
            <p className="text-sm text-slate-400 py-4 text-center">
              No status changes this week
            </p>
          ) : (
            <div className="space-y-2">
              {statusChanges.map((change: { project_code: string; project_name: string; old_status: string; new_status: string; changed_at: string }) => (
                <div
                  key={`${change.project_code}-${change.changed_at}`}
                  className="flex items-center justify-between py-2 border-b border-slate-100 last:border-0 cursor-pointer hover:bg-slate-50 rounded px-2 -mx-2"
                  onClick={() => router.push(`/proposals/${encodeURIComponent(change.project_code)}`)}
                >
                  <div>
                    <p className="text-sm font-medium text-slate-900">
                      {change.project_name}
                    </p>
                    <div className="flex items-center gap-1 text-xs">
                      <span className="text-slate-400">{change.old_status}</span>
                      <ArrowRight className="h-3 w-3 text-slate-300" />
                      <span className={cn(
                        "font-medium",
                        change.new_status === "Contract Signed" ? "text-emerald-600" :
                        change.new_status === "Negotiation" ? "text-purple-600" :
                        "text-blue-600"
                      )}>
                        {change.new_status}
                      </span>
                    </div>
                  </div>
                  <span className="text-xs text-slate-400">
                    {new Date(change.changed_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                  </span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Stalled Proposals */}
      {stalledProposals.length > 0 && (
        <Card className="border-red-200">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-red-600 flex items-center gap-2">
              <AlertTriangle className="h-4 w-4" />
              Stalled (14+ days no activity)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {stalledProposals.map((p: { project_code: string; project_name: string; days_stalled: number; last_activity: string }) => (
                <div
                  key={p.project_code}
                  className="flex items-center justify-between py-2 border-b border-slate-100 last:border-0 cursor-pointer hover:bg-red-50 rounded px-2 -mx-2"
                  onClick={() => router.push(`/proposals/${encodeURIComponent(p.project_code)}`)}
                >
                  <div>
                    <p className="text-sm font-medium text-slate-900">
                      {p.project_name}
                    </p>
                    <p className="text-xs text-red-600">
                      {p.days_stalled} days stalled
                    </p>
                  </div>
                  <span className="text-xs text-slate-400">
                    Last: {new Date(p.last_activity).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
