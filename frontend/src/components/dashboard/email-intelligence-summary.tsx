"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Mail, Calendar, TrendingUp, AlertCircle, Sparkles } from "lucide-react";

interface EmailIntelligenceSummaryProps {
  projectCode: string;
}

export function EmailIntelligenceSummary({ projectCode }: EmailIntelligenceSummaryProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["email-summary", projectCode],
    queryFn: () => api.getProjectEmailSummary(projectCode, true),
    refetchInterval: 1000 * 60 * 10, // Refresh every 10 minutes
  });

  if (isLoading) {
    return (
      <Card className="border-purple-200 bg-gradient-to-br from-purple-50 to-indigo-50">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-purple-600" />
            <CardTitle className="text-lg text-purple-900">Email Intelligence</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="animate-pulse">
                <div className="h-4 bg-purple-200 rounded w-3/4 mb-2"></div>
                <div className="h-3 bg-purple-100 rounded w-1/2"></div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="border-red-200 bg-red-50">
        <CardHeader>
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-red-600" />
            <CardTitle className="text-lg text-red-900">Email Intelligence</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-red-700">
            Failed to load email summary: {error instanceof Error ? error.message : "Unknown error"}
          </p>
        </CardContent>
      </Card>
    );
  }

  if (!data || data.total_emails === 0) {
    return (
      <Card className="border-slate-200 bg-slate-50">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Mail className="h-5 w-5 text-slate-400" />
            <CardTitle className="text-lg text-slate-600">Email Intelligence</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-slate-500">No emails found for this project.</p>
        </CardContent>
      </Card>
    );
  }

  const hasAISummary = data.ai_summary && !data.ai_summary.error;
  const emailGroups = data.email_groups || {};
  const topThreads = Object.entries(emailGroups)
    .sort(([, a], [, b]) => (b as number) - (a as number))
    .slice(0, 5);

  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric"
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <Card className="border-purple-200 bg-gradient-to-br from-purple-50 to-indigo-50">
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-purple-600" />
            <CardTitle className="text-lg text-purple-900">
              Email Intelligence Summary
            </CardTitle>
          </div>
          <Badge className="bg-purple-100 text-purple-700 border-purple-300">
            AI-Powered
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Email Statistics */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {/* Total Emails */}
          <div className="bg-white rounded-lg p-4 border border-purple-100 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-purple-600 font-medium uppercase tracking-wide">
                  Total Emails
                </p>
                <p className="text-2xl font-bold text-purple-900 mt-1">
                  {data.total_emails}
                </p>
              </div>
              <Mail className="h-8 w-8 text-purple-300" />
            </div>
          </div>

          {/* Date Range */}
          {data.date_range && (
            <div className="bg-white rounded-lg p-4 border border-indigo-100 shadow-sm sm:col-span-2">
              <div className="flex items-start gap-3">
                <Calendar className="h-5 w-5 text-indigo-600 mt-0.5 flex-shrink-0" />
                <div className="min-w-0 flex-1">
                  <p className="text-xs text-indigo-600 font-medium uppercase tracking-wide">
                    Communication Period
                  </p>
                  <p className="text-sm text-indigo-900 mt-1">
                    {formatDate(data.date_range.first)} → {formatDate(data.date_range.last)}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* AI Summary or Key Threads */}
        {hasAISummary ? (
          <div className="bg-white rounded-lg p-5 border border-purple-200 shadow-sm">
            <div className="flex items-start gap-3 mb-3">
              <TrendingUp className="h-5 w-5 text-purple-600 mt-0.5 flex-shrink-0" />
              <div className="min-w-0 flex-1">
                <h4 className="text-sm font-semibold text-purple-900 mb-2">
                  Executive Summary
                </h4>
                <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
                  {data.ai_summary?.executive_summary}
                </p>
              </div>
            </div>

            {/* Key Points */}
            {data.key_points && data.key_points.length > 0 && (
              <div className="mt-4 pt-4 border-t border-purple-100">
                <h5 className="text-xs font-semibold text-purple-900 mb-2 uppercase tracking-wide">
                  Key Insights
                </h5>
                <ul className="space-y-2">
                  {data.key_points.map((point: string, idx: number) => (
                    <li key={idx} className="flex items-start gap-2 text-sm text-slate-700">
                      <span className="text-purple-500 mt-0.5">•</span>
                      <span>{point}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ) : (
          <div className="bg-white rounded-lg p-5 border border-amber-200 shadow-sm">
            <div className="flex items-start gap-3 mb-4">
              <AlertCircle className="h-5 w-5 text-amber-600 mt-0.5 flex-shrink-0" />
              <div className="min-w-0 flex-1">
                <h4 className="text-sm font-semibold text-amber-900 mb-1">
                  AI Summary Unavailable
                </h4>
                <p className="text-xs text-amber-700">
                  {data.ai_summary?.error || "Could not generate AI summary for this email chain."}
                </p>
              </div>
            </div>

            {/* Show top email threads as fallback */}
            {topThreads.length > 0 && (
              <div>
                <h5 className="text-xs font-semibold text-slate-700 mb-3 uppercase tracking-wide">
                  Top Email Threads
                </h5>
                <div className="space-y-2">
                  {topThreads.map(([subject, count], idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between gap-3 p-2 bg-slate-50 rounded border border-slate-200"
                    >
                      <span className="text-xs text-slate-700 truncate flex-1">
                        {subject}
                      </span>
                      <Badge variant="secondary" className="text-xs flex-shrink-0">
                        {count} {count === 1 ? "email" : "emails"}
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Timeline */}
        {data.timeline && data.timeline.length > 0 && (
          <div className="bg-white rounded-lg p-5 border border-indigo-100 shadow-sm">
            <h4 className="text-sm font-semibold text-indigo-900 mb-3">
              Key Timeline Events
            </h4>
            <div className="space-y-3">
              {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
              {data.timeline.slice(0, 5).map((event: any, idx: number) => (
                <div key={idx} className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-16 text-xs text-slate-500">
                    {event.date ? formatDate(event.date) : "—"}
                  </div>
                  <div className="flex-1 text-sm text-slate-700">
                    {event.event || event.description || "Event"}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Action Button */}
        <div className="flex justify-center pt-2">
          <Button
            variant="outline"
            size="sm"
            className="border-purple-300 text-purple-700 hover:bg-purple-50"
          >
            View All {data.total_emails} Emails
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
