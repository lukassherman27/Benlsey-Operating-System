"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { AnalyticsTrends } from "@/lib/types";
import { cn } from "@/lib/utils";
import { ds } from "@/lib/design-system";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { TrendingUp, TrendingDown, Clock, Target, DollarSign, Percent } from "lucide-react";

interface AnalyticsChartsProps {
  data?: AnalyticsTrends;
  isLoading?: boolean;
}

// Format large numbers as $XXM or $XXXK
function formatValue(value: number): string {
  if (value >= 1000000) {
    return `$${(value / 1000000).toFixed(1)}M`;
  } else if (value >= 1000) {
    return `$${(value / 1000).toFixed(0)}K`;
  }
  return `$${value.toFixed(0)}`;
}

// Format month as "Jan", "Feb", etc.
function formatMonth(month: string): string {
  const [, m] = month.split("-");
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  return months[parseInt(m, 10) - 1] || month;
}

// Status colors for funnel
const statusColors: Record<string, string> = {
  "First Contact": "#93c5fd",
  "Meeting Scheduled": "#60a5fa",
  "Design Brief Received": "#3b82f6",
  "Proposal Prep": "#2563eb",
  "Proposal Sent": "#1d4ed8",
  "Negotiation": "#1e40af",
  "Verbal Agreement": "#1e3a8a",
  Dormant: "#94a3b8",
  "On Hold": "#64748b",
};

export function AnalyticsCharts({ data, isLoading }: AnalyticsChartsProps) {
  if (isLoading) {
    return (
      <div className="grid gap-6 md:grid-cols-2">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i}>
            <CardHeader>
              <Skeleton className="h-5 w-32" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-[200px] w-full" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (!data) {
    return (
      <div className="text-center py-12">
        <p className={cn(ds.typography.body, ds.textColors.secondary)}>
          No analytics data available
        </p>
      </div>
    );
  }

  // Prepare pipeline data for chart
  const pipelineData = data.pipeline_by_month.map((item) => ({
    month: formatMonth(item.month),
    value: item.value,
    displayValue: formatValue(item.value),
  }));

  // Prepare win rate data
  const winRateData = data.win_rate_by_month
    .filter((item) => item.win_rate !== null)
    .map((item) => ({
      month: formatMonth(item.month),
      rate: item.win_rate,
      won: item.won,
      lost: item.lost,
    }));

  // Prepare funnel data (sorted by count descending for display)
  const funnelData = data.pipeline_by_status.map((item) => ({
    ...item,
    displayValue: formatValue(item.value),
    color: statusColors[item.status] || "#6366f1",
  }));

  // Calculate summary metrics
  const currentPipeline = data.summary.total_pipeline;
  const weightedPipeline = data.summary.weighted_pipeline;
  const avgDaysToWin = data.summary.avg_days_to_win;

  // Calculate trend (compare last month to previous)
  const lastMonthValue = data.pipeline_by_month[data.pipeline_by_month.length - 1]?.value || 0;
  const prevMonthValue = data.pipeline_by_month[data.pipeline_by_month.length - 2]?.value || 0;
  const pipelineTrend = prevMonthValue > 0
    ? ((lastMonthValue - prevMonthValue) / prevMonthValue) * 100
    : 0;

  // Calculate average win rate from non-null values
  const winRates = data.win_rate_by_month.filter((w) => w.win_rate !== null);
  const avgWinRate = winRates.length > 0
    ? winRates.reduce((acc, w) => acc + (w.win_rate || 0), 0) / winRates.length
    : null;

  return (
    <div className="space-y-6">
      {/* Summary Metrics */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className={cn(ds.typography.caption, ds.textColors.secondary)}>
                  Total Pipeline
                </p>
                <p className={cn(ds.typography.heading2, ds.textColors.primary)}>
                  {formatValue(currentPipeline)}
                </p>
              </div>
              <DollarSign className="h-8 w-8 text-blue-500 opacity-50" />
            </div>
            {pipelineTrend !== 0 && (
              <div className={cn("flex items-center gap-1 mt-2", pipelineTrend > 0 ? "text-green-600" : "text-red-600")}>
                {pipelineTrend > 0 ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
                <span className="text-sm">{Math.abs(pipelineTrend).toFixed(1)}% vs last month</span>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className={cn(ds.typography.caption, ds.textColors.secondary)}>
                  Weighted Pipeline
                </p>
                <p className={cn(ds.typography.heading2, ds.textColors.primary)}>
                  {formatValue(weightedPipeline)}
                </p>
              </div>
              <Target className="h-8 w-8 text-green-500 opacity-50" />
            </div>
            <p className={cn(ds.typography.caption, ds.textColors.tertiary, "mt-2")}>
              Based on win probability
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className={cn(ds.typography.caption, ds.textColors.secondary)}>
                  Avg Win Rate
                </p>
                <p className={cn(ds.typography.heading2, ds.textColors.primary)}>
                  {avgWinRate !== null ? `${avgWinRate.toFixed(0)}%` : "—"}
                </p>
              </div>
              <Percent className="h-8 w-8 text-purple-500 opacity-50" />
            </div>
            <p className={cn(ds.typography.caption, ds.textColors.tertiary, "mt-2")}>
              Last 12 months
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className={cn(ds.typography.caption, ds.textColors.secondary)}>
                  Avg Days to Win
                </p>
                <p className={cn(ds.typography.heading2, ds.textColors.primary)}>
                  {avgDaysToWin !== null ? `${Math.round(avgDaysToWin)}` : "—"}
                </p>
              </div>
              <Clock className="h-8 w-8 text-orange-500 opacity-50" />
            </div>
            <p className={cn(ds.typography.caption, ds.textColors.tertiary, "mt-2")}>
              First contact to signed
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Pipeline Over Time */}
        <Card>
          <CardHeader>
            <CardTitle className={ds.typography.heading3}>Pipeline Value Trend</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[250px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={pipelineData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis
                    dataKey="month"
                    tick={{ fontSize: 12 }}
                    stroke="#64748b"
                  />
                  <YAxis
                    tickFormatter={(value) => formatValue(value)}
                    tick={{ fontSize: 12 }}
                    stroke="#64748b"
                    width={60}
                  />
                  <Tooltip
                    formatter={(value: number) => [formatValue(value), "Pipeline"]}
                    labelStyle={{ color: "#1e293b" }}
                    contentStyle={{ borderRadius: "8px", border: "1px solid #e2e8f0" }}
                  />
                  <Line
                    type="monotone"
                    dataKey="value"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    dot={{ fill: "#3b82f6", strokeWidth: 2, r: 4 }}
                    activeDot={{ r: 6 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Win Rate Trend */}
        <Card>
          <CardHeader>
            <CardTitle className={ds.typography.heading3}>Win Rate Trend</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[250px]">
              {winRateData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={winRateData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis
                      dataKey="month"
                      tick={{ fontSize: 12 }}
                      stroke="#64748b"
                    />
                    <YAxis
                      domain={[0, 100]}
                      tickFormatter={(value) => `${value}%`}
                      tick={{ fontSize: 12 }}
                      stroke="#64748b"
                      width={45}
                    />
                    <Tooltip
                      formatter={(value: number, name: string) => {
                        if (name === "rate") return [`${value}%`, "Win Rate"];
                        return [value, name];
                      }}
                      labelStyle={{ color: "#1e293b" }}
                      contentStyle={{ borderRadius: "8px", border: "1px solid #e2e8f0" }}
                    />
                    <Line
                      type="monotone"
                      dataKey="rate"
                      stroke="#22c55e"
                      strokeWidth={2}
                      dot={{ fill: "#22c55e", strokeWidth: 2, r: 4 }}
                      activeDot={{ r: 6 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-full">
                  <p className={cn(ds.typography.body, ds.textColors.tertiary)}>
                    Not enough data to show win rate trend
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Pipeline Funnel */}
        <Card>
          <CardHeader>
            <CardTitle className={ds.typography.heading3}>Pipeline by Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[250px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={funnelData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
                  <XAxis
                    type="number"
                    tickFormatter={(value) => formatValue(value)}
                    tick={{ fontSize: 12 }}
                    stroke="#64748b"
                  />
                  <YAxis
                    type="category"
                    dataKey="status"
                    tick={{ fontSize: 11 }}
                    stroke="#64748b"
                    width={100}
                  />
                  <Tooltip
                    formatter={(value: number) => [formatValue(value), "Value"]}
                    labelStyle={{ color: "#1e293b" }}
                    contentStyle={{ borderRadius: "8px", border: "1px solid #e2e8f0" }}
                  />
                  <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                    {funnelData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Win Rate by Value */}
        <Card>
          <CardHeader>
            <CardTitle className={ds.typography.heading3}>Win Rate by Deal Size</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[250px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.win_rate_by_value.filter((d) => d.win_rate !== null)}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis
                    dataKey="bracket"
                    tick={{ fontSize: 12 }}
                    stroke="#64748b"
                  />
                  <YAxis
                    domain={[0, 100]}
                    tickFormatter={(value) => `${value}%`}
                    tick={{ fontSize: 12 }}
                    stroke="#64748b"
                    width={45}
                  />
                  <Tooltip
                    formatter={(value: number, name: string) => {
                      if (name === "win_rate") return [`${value}%`, "Win Rate"];
                      return [value, name];
                    }}
                    content={({ active, payload, label }) => {
                      if (!active || !payload || payload.length === 0) return null;
                      const data = payload[0].payload;
                      return (
                        <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-sm">
                          <p className="font-medium text-slate-900">{label}</p>
                          <p className="text-sm text-slate-600">
                            Win Rate: <span className="font-semibold">{data.win_rate}%</span>
                          </p>
                          <p className="text-sm text-slate-500">
                            Won: {data.won} | Lost: {data.lost}
                          </p>
                        </div>
                      );
                    }}
                  />
                  <Bar dataKey="win_rate" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Stage Durations */}
      <Card>
        <CardHeader>
          <CardTitle className={ds.typography.heading3}>Average Time in Stage</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-6">
            {data.stage_durations.map((stage) => (
              <div
                key={stage.status}
                className="p-4 bg-slate-50 rounded-lg text-center"
              >
                <p className={cn(ds.typography.caption, ds.textColors.secondary, "mb-1")}>
                  {stage.status}
                </p>
                <p className={cn(ds.typography.heading2, ds.textColors.primary)}>
                  {Math.round(stage.avg_days)}d
                </p>
                <p className={cn(ds.typography.caption, ds.textColors.tertiary)}>
                  {stage.count} proposals
                </p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
