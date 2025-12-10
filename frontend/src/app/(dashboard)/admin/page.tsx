"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { ds, bensleyVoice, getLoadingMessage } from "@/lib/design-system";
import {
  Link2,
  DollarSign,
  Edit3,
  ArrowRight,
  AlertCircle,
  Clock,
  Sparkles,
  Activity,
} from "lucide-react";

interface AdminTool {
  href: string;
  label: string;
  description: string;
  icon: React.ElementType;
  color: "emerald" | "blue" | "amber" | "violet" | "slate" | "rose";
  stat?: {
    value: number | string;
    label: string;
    highlight?: boolean;
  };
}

function StatsSkeleton() {
  return (
    <div className="grid grid-cols-4 gap-4">
      {[...Array(4)].map((_, i) => (
        <Skeleton key={i} className="h-24 w-full rounded-xl" />
      ))}
    </div>
  );
}

function ToolCardSkeleton() {
  return (
    <div className="grid grid-cols-3 gap-4">
      {[...Array(6)].map((_, i) => (
        <Skeleton key={i} className="h-32 w-full rounded-xl" />
      ))}
    </div>
  );
}

export default function AdminOverviewPage() {
  // Fetch learning stats
  const { data: learningStats, isLoading: loadingLearning } = useQuery({
    queryKey: ["admin-learning-stats"],
    queryFn: () => api.getLearningStats(),
  });

  // Fetch suggestions stats
  const { data: suggestionsStats, isLoading: loadingSuggestions } = useQuery({
    queryKey: ["admin-suggestions-stats"],
    queryFn: () => api.getSuggestionsStats(),
  });

  // Fetch email links for unlinked count
  const { data: emailLinksData, isLoading: loadingEmailLinks } = useQuery({
    queryKey: ["admin-email-links"],
    queryFn: () => api.getEmailValidationQueue({ status: "unlinked", limit: 1 }),
  });

  const isLoading = loadingLearning || loadingSuggestions || loadingEmailLinks;

  // Calculate stats
  const pendingLearning = learningStats?.suggestions?.pending || 0;
  const pendingSuggestions = suggestionsStats?.by_status?.pending || 0;
  const unlinkedEmails = emailLinksData?.counts?.unlinked || 0;
  const totalPending = pendingLearning + pendingSuggestions;

  // Color helper for each tool
  const colorClasses = {
    emerald: {
      bg: "bg-emerald-50/50",
      border: "border-emerald-200",
      text: "text-emerald-700",
      icon: "bg-emerald-100 text-emerald-600",
      hover: "hover:bg-emerald-50 hover:border-emerald-300",
    },
    blue: {
      bg: "bg-blue-50/50",
      border: "border-blue-200",
      text: "text-blue-700",
      icon: "bg-blue-100 text-blue-600",
      hover: "hover:bg-blue-50 hover:border-blue-300",
    },
    amber: {
      bg: "bg-amber-50/50",
      border: "border-amber-200",
      text: "text-amber-700",
      icon: "bg-amber-100 text-amber-600",
      hover: "hover:bg-amber-50 hover:border-amber-300",
    },
    violet: {
      bg: "bg-violet-50/50",
      border: "border-violet-200",
      text: "text-violet-700",
      icon: "bg-violet-100 text-violet-600",
      hover: "hover:bg-violet-50 hover:border-violet-300",
    },
    slate: {
      bg: "bg-slate-50/50",
      border: "border-slate-200",
      text: "text-slate-700",
      icon: "bg-slate-100 text-slate-600",
      hover: "hover:bg-slate-100 hover:border-slate-300",
    },
    rose: {
      bg: "bg-rose-50/50",
      border: "border-rose-200",
      text: "text-rose-700",
      icon: "bg-rose-100 text-rose-600",
      hover: "hover:bg-rose-50 hover:border-rose-300",
    },
  };

  const adminTools: AdminTool[] = [
    {
      href: "/admin/suggestions",
      label: "AI Suggestions",
      description: "Review email links and contact suggestions",
      icon: Sparkles,
      color: "emerald",
      stat: {
        value: pendingSuggestions,
        label: "pending",
        highlight: pendingSuggestions > 0,
      },
    },
    {
      href: "/admin/email-links",
      label: "Email Links",
      description: "Manage email-project connections",
      icon: Link2,
      color: "blue",
      stat: {
        value: unlinkedEmails,
        label: "unlinked",
        highlight: unlinkedEmails > 50,
      },
    },
    {
      href: "/admin/financial-entry",
      label: "Financial Entry",
      description: "Manual project & invoice data entry",
      icon: DollarSign,
      color: "amber",
    },
    {
      href: "/admin/project-editor",
      label: "Project Editor",
      description: "View and edit all project fields",
      icon: Edit3,
      color: "slate",
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className={cn(ds.typography.heading1, ds.textColors.primary)}>
          Admin Dashboard
        </h1>
        <p className={cn(ds.typography.body, ds.textColors.secondary, "mt-1")}>
          {bensleyVoice.sectionHeaders.suggestions} - Manage data, review suggestions, and monitor system activity.
        </p>
      </div>

      {/* Quick Stats */}
      {isLoading ? (
        <StatsSkeleton />
      ) : (
        <div className="grid grid-cols-4 gap-4">
          <Card className={cn(ds.borderRadius.card, "border-amber-200 bg-amber-50/30")}>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-amber-100">
                  <Clock className="h-5 w-5 text-amber-700" />
                </div>
                <div>
                  <p className={cn(ds.typography.caption, "text-amber-700")}>Total Pending</p>
                  <p className={cn(ds.typography.heading2, "text-amber-800")}>
                    {totalPending}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className={cn(ds.borderRadius.card, "border-blue-200 bg-blue-50/30")}>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-blue-100">
                  <Link2 className="h-5 w-5 text-blue-700" />
                </div>
                <div>
                  <p className={cn(ds.typography.caption, "text-blue-700")}>Unlinked Emails</p>
                  <p className={cn(ds.typography.heading2, "text-blue-800")}>
                    {unlinkedEmails}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className={cn(ds.borderRadius.card, "border-violet-200 bg-violet-50/30")}>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-violet-100">
                  <Sparkles className="h-5 w-5 text-violet-700" />
                </div>
                <div>
                  <p className={cn(ds.typography.caption, "text-violet-700")}>Active Patterns</p>
                  <p className={cn(ds.typography.heading2, "text-violet-800")}>
                    {learningStats?.active_patterns || 0}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className={cn(ds.borderRadius.card, "border-emerald-200 bg-emerald-50/30")}>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-emerald-100">
                  <Activity className="h-5 w-5 text-emerald-700" />
                </div>
                <div>
                  <p className={cn(ds.typography.caption, "text-emerald-700")}>Approval Rate</p>
                  <p className={cn(ds.typography.heading2, "text-emerald-800")}>
                    {learningStats?.approval_rate
                      ? `${(learningStats.approval_rate * 100).toFixed(0)}%`
                      : "N/A"}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Admin Tools Grid */}
      <div>
        <h2 className={cn(ds.typography.heading3, ds.textColors.primary, "mb-4")}>
          Admin Tools
        </h2>
        {isLoading ? (
          <ToolCardSkeleton />
        ) : (
          <div className="grid grid-cols-3 gap-4">
            {adminTools.map((tool) => {
              const Icon = tool.icon;
              const colors = colorClasses[tool.color];

              return (
                <Link key={tool.href} href={tool.href}>
                  <Card
                    className={cn(
                      ds.borderRadius.card,
                      "border transition-all duration-200 cursor-pointer group",
                      colors.bg,
                      colors.border,
                      colors.hover
                    )}
                  >
                    <CardContent className="p-5">
                      <div className="flex items-start justify-between mb-3">
                        <div className={cn("p-2 rounded-lg", colors.icon)}>
                          <Icon className="h-5 w-5" />
                        </div>
                        {tool.stat && (
                          <Badge
                            className={cn(
                              tool.stat.highlight
                                ? ds.badges.warning
                                : ds.badges.neutral
                            )}
                          >
                            {tool.stat.value} {tool.stat.label}
                          </Badge>
                        )}
                      </div>
                      <h3 className={cn(ds.typography.bodyBold, ds.textColors.primary, "mb-1")}>
                        {tool.label}
                      </h3>
                      <p className={cn(ds.typography.caption, ds.textColors.tertiary)}>
                        {tool.description}
                      </p>
                      <div
                        className={cn(
                          "flex items-center gap-1 mt-3 text-sm font-medium transition-transform duration-200",
                          colors.text,
                          "group-hover:translate-x-1"
                        )}
                      >
                        Open
                        <ArrowRight className="h-4 w-4" />
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              );
            })}
          </div>
        )}
      </div>

      {/* Alerts Section */}
      {totalPending > 10 && (
        <Card className={cn(ds.borderRadius.card, ds.status.warning.bg, ds.status.warning.border)}>
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <AlertCircle className={cn("h-5 w-5", ds.status.warning.icon)} />
              <div>
                <p className={cn(ds.typography.bodyBold, ds.status.warning.text)}>
                  Action Required
                </p>
                <p className={cn(ds.typography.caption, ds.status.warning.text)}>
                  You have {totalPending} items pending review. The AI is waiting for your wisdom.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
