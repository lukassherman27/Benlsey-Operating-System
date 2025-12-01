"use client";

import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Mail,
  Inbox,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  TrendingUp,
  Calendar,
} from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api";

interface ImportStats {
  today: {
    imported: number;
    categorized: number;
    need_review: number;
  };
  this_week: {
    total_imports: number;
    categorized: number;
    uncategorized: number;
  };
  trend: {
    direction: "up" | "down" | "stable";
    percentage: number;
  };
}

interface ImportSummaryWidgetProps {
  compact?: boolean;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export function ImportSummaryWidget({ compact = false }: ImportSummaryWidgetProps) {
  const { data, isLoading, error } = useQuery<ImportStats>({
    queryKey: ["import-stats"],
    queryFn: async () => {
      // Try to fetch from API, fallback to computed values from existing endpoints
      try {
        const res = await fetch(`${API_BASE_URL}/api/emails/import-stats`);
        if (res.ok) {
          return res.json();
        }
      } catch {
        // API not available, compute from existing data
      }

      // Fallback: compute from existing endpoints
      const [pendingRes, recentRes] = await Promise.all([
        api.getEmailsPendingApproval(100),
        api.getRecentEmails(100, 7),
      ]);

      const pendingCount = pendingRes?.total_pending || 0;
      const recentEmails = recentRes?.data || [];
      const totalThisWeek = recentEmails.length;
      const categorizedThisWeek = recentEmails.filter((e) => e.category && e.category !== "uncategorized").length;

      // Estimate today's stats (last 24h subset)
      const yesterday = new Date();
      yesterday.setDate(yesterday.getDate() - 1);
      const todayEmails = recentEmails.filter((e) => e.date && new Date(e.date) > yesterday);
      const todayImported = todayEmails.length;
      const todayCategorized = todayEmails.filter((e) => e.category && e.category !== "uncategorized").length;

      return {
        today: {
          imported: todayImported,
          categorized: todayCategorized,
          need_review: pendingCount > 0 ? Math.min(pendingCount, todayImported - todayCategorized) : 0,
        },
        this_week: {
          total_imports: totalThisWeek,
          categorized: categorizedThisWeek,
          uncategorized: totalThisWeek - categorizedThisWeek,
        },
        trend: {
          direction: totalThisWeek > 50 ? "up" : totalThisWeek > 20 ? "stable" : "down",
          percentage: totalThisWeek > 0 ? Math.round((categorizedThisWeek / totalThisWeek) * 100) : 0,
        },
      };
    },
    staleTime: 60 * 1000, // 1 minute
    retry: 1,
  });

  if (isLoading) {
    return (
      <Card className={cn(compact && "shadow-sm")}>
        <CardHeader className={cn("pb-2", compact && "py-3")}>
          <Skeleton className="h-5 w-32" />
        </CardHeader>
        <CardContent className={cn(compact && "py-2")}>
          <div className="space-y-3">
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-8 w-3/4" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error || !data) {
    return (
      <Card className={cn(compact && "shadow-sm", "border-amber-200 bg-amber-50/50")}>
        <CardContent className={cn("pt-4", compact && "py-3")}>
          <div className="flex items-center gap-2 text-amber-700 text-sm">
            <AlertCircle className="h-4 w-4" />
            <span>Import stats unavailable</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  const needsReview = data.today.need_review > 0 || data.this_week.uncategorized > 0;

  return (
    <Card className={cn(compact && "shadow-sm")}>
      <CardHeader className={cn("pb-2", compact && "py-3 px-4")}>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-base font-semibold">
            <Inbox className="h-5 w-5 text-blue-600" />
            Email Import Summary
          </div>
          {data.trend?.direction && data.trend.direction !== "stable" && (
            <Badge
              variant="secondary"
              className={cn(
                "text-xs",
                data.trend.direction === "up" && "bg-emerald-100 text-emerald-700",
                data.trend.direction === "down" && "bg-slate-100 text-slate-600"
              )}
            >
              <TrendingUp
                className={cn(
                  "h-3 w-3 mr-1",
                  data.trend.direction === "down" && "rotate-180"
                )}
              />
              {data.trend.percentage}% categorized
            </Badge>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className={cn(compact && "px-4 pb-3")}>
        {/* Today's Stats */}
        <div className="flex items-center gap-4 py-3 border-b">
          <div className="p-2 rounded-lg bg-blue-100">
            <Calendar className="h-5 w-5 text-blue-600" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-medium text-slate-700">Today</p>
            <div className="flex items-center gap-3 mt-1 text-sm text-slate-500">
              <span className="flex items-center gap-1">
                <Mail className="h-3.5 w-3.5" />
                {data.today.imported} imported
              </span>
              <span className="flex items-center gap-1 text-emerald-600">
                <CheckCircle2 className="h-3.5 w-3.5" />
                {data.today.categorized} categorized
              </span>
              {data.today.need_review > 0 && (
                <span className="flex items-center gap-1 text-amber-600">
                  <AlertCircle className="h-3.5 w-3.5" />
                  {data.today.need_review} need review
                </span>
              )}
            </div>
          </div>
        </div>

        {/* This Week Stats */}
        <div className="flex items-center gap-4 py-3">
          <div className="p-2 rounded-lg bg-purple-100">
            <TrendingUp className="h-5 w-5 text-purple-600" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-medium text-slate-700">This Week</p>
            <div className="flex items-center gap-3 mt-1 text-sm text-slate-500">
              <span>{data.this_week.total_imports} total imports</span>
              <span className="text-slate-300">|</span>
              <span className="text-emerald-600">{data.this_week.categorized} categorized</span>
              {data.this_week.uncategorized > 0 && (
                <>
                  <span className="text-slate-300">|</span>
                  <span className="text-amber-600">{data.this_week.uncategorized} uncategorized</span>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Action Link */}
        {needsReview && (
          <div className="mt-2 pt-3 border-t">
            <Link href="/admin/email-categories">
              <Button variant="outline" size="sm" className="w-full group">
                <AlertCircle className="h-4 w-4 mr-2 text-amber-500" />
                Review Uncategorized Emails
                <ArrowRight className="h-4 w-4 ml-auto group-hover:translate-x-1 transition-transform" />
              </Button>
            </Link>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
