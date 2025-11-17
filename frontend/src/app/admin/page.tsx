"use client";

import { useQuery } from "@tanstack/react-query";
import { format } from "date-fns";
import Link from "next/link";
import { api } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { RefreshCw } from "lucide-react";

export default function AdminPage() {
  const overridesQuery = useQuery({
    queryKey: ["manual-overrides", "admin"],
    queryFn: () => api.getManualOverrides({ per_page: 50 }),
    refetchInterval: 1000 * 60 * 5,
  });

  const systemHealthQuery = useQuery({
    queryKey: ["system-health"],
    queryFn: api.getSystemHealth,
    refetchInterval: 1000 * 60 * 5,
  });

  const overrides = overridesQuery.data?.data ?? [];
  const overrideMeta = overridesQuery.data?.pagination;
  const systemHealth = systemHealthQuery.data;

  return (
    <div className="space-y-8 p-6 pb-12 md:p-10">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold text-slate-900">
            Internal Controls
          </h1>
          <p className="text-sm text-muted-foreground">
            Manual overrides log + backend/system telemetry for Lukas.
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            overridesQuery.refetch();
            systemHealthQuery.refetch();
          }}
        >
          <RefreshCw className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between gap-3">
            <div>
              <CardTitle>Manual Overrides</CardTitle>
              <CardDescription>
                {overrideMeta
                  ? `${overrideMeta.total} total · showing ${overrides.length}`
                  : "Loading latest directives…"}
              </CardDescription>
            </div>
            <Button asChild variant="secondary">
              <Link href="/(dashboard)">Back to dashboard</Link>
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {overridesQuery.isLoading ? (
            <p className="text-sm text-muted-foreground">Loading overrides…</p>
          ) : overrides.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No overrides recorded yet.
            </p>
          ) : (
            <div className="space-y-3">
              {overrides.map((override) => (
                <div
                  key={override.override_id}
                  className="rounded-2xl border border-slate-200/80 p-4"
                >
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold text-slate-900">
                        {override.project_code ?? "Global Override"}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Scope: {override.scope} · Author: {override.author}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge
                        variant={
                          override.urgency === "urgent" ? "destructive" : "outline"
                        }
                      >
                        {override.urgency}
                      </Badge>
                      <Badge
                        variant={
                          override.status === "active" ? "default" : "secondary"
                        }
                      >
                        {override.status}
                      </Badge>
                    </div>
                  </div>
                  <p className="mt-3 text-sm text-slate-700">
                    {override.instruction}
                  </p>
                  <div className="mt-3 text-xs text-muted-foreground">
                    Created {format(new Date(override.created_at), "PPpp")}
                    {override.applied_at
                      ? ` · Applied ${format(
                          new Date(override.applied_at),
                          "PPpp"
                        )}`
                      : null}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>System Health</CardTitle>
          <CardDescription>
            Backend processing + model metrics (internal only).
          </CardDescription>
        </CardHeader>
        <CardContent>
          {systemHealthQuery.isLoading ? (
            <p className="text-sm text-muted-foreground">Loading telemetry…</p>
          ) : !systemHealth ? (
            <p className="text-sm text-muted-foreground">
              Unable to load system health right now.
            </p>
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
              <div className="rounded-2xl border border-slate-200 p-4">
                <p className="text-xs uppercase text-muted-foreground">
                  Email processing
                </p>
                <p className="mt-2 text-2xl font-semibold text-slate-900">
                  {systemHealth.email_processing.categorized_percent.toFixed(1)}%
                </p>
                <p className="text-sm text-muted-foreground">
                  {systemHealth.email_processing.processed}/
                  {systemHealth.email_processing.total_emails} processed (
                  {systemHealth.email_processing.processing_rate})
                </p>
              </div>
              <div className="rounded-2xl border border-slate-200 p-4">
                <p className="text-xs uppercase text-muted-foreground">
                  Model training
                </p>
                <p className="mt-2 text-2xl font-semibold text-slate-900">
                  {systemHealth.model_training.completion_percent.toFixed(1)}%
                </p>
                <p className="text-sm text-muted-foreground">
                  {systemHealth.model_training.training_samples}/
                  {systemHealth.model_training.target_samples} samples · accuracy{" "}
                  {(systemHealth.model_training.model_accuracy * 100).toFixed(1)}%
                </p>
              </div>
              <div className="rounded-2xl border border-slate-200 p-4">
                <p className="text-xs uppercase text-muted-foreground">Database</p>
                <p className="mt-2 text-2xl font-semibold text-slate-900">
                  {systemHealth.database.total_proposals} proposals
                </p>
                <p className="text-sm text-muted-foreground">
                  {systemHealth.database.active_projects} active · last sync{" "}
                  {format(new Date(systemHealth.database.last_sync), "PPpp")}
                </p>
              </div>
              <div className="rounded-2xl border border-slate-200 p-4">
                <p className="text-xs uppercase text-muted-foreground">API</p>
                <p className="mt-2 text-2xl font-semibold text-slate-900">
                  {systemHealth.api_health.avg_response_time_ms} ms
                </p>
                <p className="text-sm text-muted-foreground">
                  {systemHealth.api_health.requests_last_hour} req/hr · uptime{" "}
                  {(systemHealth.api_health.uptime_seconds / 3600).toFixed(1)} h
                </p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
