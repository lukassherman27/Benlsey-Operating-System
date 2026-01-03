"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  FileText,
  AlertTriangle,
  CheckCircle2,
  Clock,
  DollarSign,
  Users,
  Calendar,
  ArrowRight,
  TrendingUp,
  Circle,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { format, differenceInDays } from "date-fns";

interface ProjectInsightsProps {
  projectCode: string;
  projectDetail: Record<string, unknown>;
  invoices: Array<Record<string, unknown>>;
}

interface ActionItem {
  type: "invoice" | "rfi" | "deliverable" | "task" | "meeting";
  priority: "high" | "medium" | "low";
  title: string;
  description: string;
  dueDate?: string;
  amount?: number;
}

export function ProjectInsights({ projectCode, projectDetail, invoices }: ProjectInsightsProps) {
  // Fetch schedule team
  const teamQuery = useQuery({
    queryKey: ["project-schedule-team", projectCode],
    queryFn: async () => {
      const res = await fetch(`/api/projects/${encodeURIComponent(projectCode)}/schedule-team`);
      if (!res.ok) return { team: [] };
      return res.json();
    },
    staleTime: 1000 * 60 * 5,
  });

  // Calculate health score
  const calculateHealth = () => {
    let score = 100;
    const risks: string[] = [];

    // Check overdue invoices
    const overdueInvoices = invoices.filter((inv) => {
      if (inv.status === "paid") return false;
      if (!inv.due_date) return false;
      return new Date(inv.due_date as string) < new Date();
    });

    if (overdueInvoices.length > 0) {
      const totalOverdue = overdueInvoices.reduce(
        (sum, inv) => sum + ((inv.invoice_amount as number) || 0),
        0
      );
      score -= Math.min(30, overdueInvoices.length * 10);
      risks.push(`${overdueInvoices.length} overdue invoice${overdueInvoices.length > 1 ? "s" : ""} ($${(totalOverdue / 1000).toFixed(0)}K)`);
    }

    // Check RFIs
    const openRfis = (projectDetail?.open_rfis_count as number) || 0;
    if (openRfis > 3) {
      score -= 15;
      risks.push(`${openRfis} open RFIs need attention`);
    } else if (openRfis > 0) {
      score -= 5;
    }

    // Check deliverables
    const overdueDeliverables = (projectDetail?.overdue_deliverables_count as number) || 0;
    if (overdueDeliverables > 0) {
      score -= overdueDeliverables * 10;
      risks.push(`${overdueDeliverables} overdue deliverable${overdueDeliverables > 1 ? "s" : ""}`);
    }

    // Check team coverage
    const teamCount = teamQuery.data?.team?.length || 0;
    if (teamCount === 0) {
      score -= 10;
      risks.push("No team members scheduled this week");
    }

    // Check payment progress
    const contractValue = (projectDetail?.contract_value_usd as number) || (projectDetail?.total_fee_usd as number) || 0;
    const paidToDate = (projectDetail?.paid_to_date_usd as number) || 0;
    const invoicedAmount = (projectDetail?.total_invoiced as number) || 0;

    if (contractValue > 0) {
      const paymentRatio = paidToDate / invoicedAmount;
      if (invoicedAmount > 0 && paymentRatio < 0.5) {
        score -= 10;
        risks.push("Less than 50% of invoiced amount collected");
      }
    }

    return {
      score: Math.max(0, Math.min(100, score)),
      risks,
    };
  };

  // Generate action items
  const generateActionItems = (): ActionItem[] => {
    const items: ActionItem[] = [];

    // Overdue invoices
    invoices
      .filter((inv) => {
        if (inv.status === "paid") return false;
        if (!inv.due_date) return false;
        return new Date(inv.due_date as string) < new Date();
      })
      .forEach((inv) => {
        const daysOverdue = differenceInDays(new Date(), new Date(inv.due_date as string));
        items.push({
          type: "invoice",
          priority: daysOverdue > 30 ? "high" : "medium",
          title: `Follow up on Invoice ${inv.invoice_number || inv.invoice_id}`,
          description: `$${((inv.invoice_amount as number) / 1000).toFixed(0)}K overdue by ${daysOverdue} days`,
          dueDate: inv.due_date as string,
          amount: inv.invoice_amount as number,
        });
      });

    // Open RFIs
    const rfis = (projectDetail?.rfis as Array<Record<string, unknown>>) || [];
    rfis
      .filter((rfi) => rfi.status === "open")
      .slice(0, 3)
      .forEach((rfi) => {
        items.push({
          type: "rfi",
          priority: (rfi.days_open as number) > 14 ? "high" : "medium",
          title: `Respond to RFI: ${rfi.subject || rfi.rfi_number}`,
          description: `Open for ${rfi.days_open || "?"} days`,
        });
      });

    // Overdue deliverables
    const deliverables = (projectDetail?.deliverables as Array<Record<string, unknown>>) || [];
    deliverables
      .filter((d) => {
        if (d.status === "delivered" || d.status === "approved") return false;
        if (!d.due_date) return false;
        return new Date(d.due_date as string) < new Date();
      })
      .slice(0, 3)
      .forEach((d) => {
        items.push({
          type: "deliverable",
          priority: "high",
          title: `Complete: ${d.name}`,
          description: `Due ${format(new Date(d.due_date as string), "MMM d")}`,
          dueDate: d.due_date as string,
        });
      });

    // Sort by priority
    const priorityOrder = { high: 0, medium: 1, low: 2 };
    items.sort((a, b) => priorityOrder[a.priority] - priorityOrder[b.priority]);

    return items.slice(0, 5);
  };

  const health = calculateHealth();
  const actionItems = generateActionItems();
  const team = teamQuery.data?.team || [];

  // Health config
  const getHealthConfig = (score: number) => {
    if (score >= 80) return { label: "Healthy", color: "text-emerald-600", bg: "bg-emerald-50", border: "border-emerald-200", bar: "bg-emerald-500" };
    if (score >= 60) return { label: "Good", color: "text-emerald-600", bg: "bg-emerald-50", border: "border-emerald-200", bar: "bg-emerald-400" };
    if (score >= 40) return { label: "Needs Attention", color: "text-amber-600", bg: "bg-amber-50", border: "border-amber-200", bar: "bg-amber-500" };
    return { label: "At Risk", color: "text-red-600", bg: "bg-red-50", border: "border-red-200", bar: "bg-red-500" };
  };

  const healthConfig = getHealthConfig(health.score);

  // Generate executive summary
  const generateSummary = () => {
    const projectName = (projectDetail?.project_name as string) || (projectDetail?.project_title as string) || projectCode;
    const phase = (projectDetail?.current_phase as string) || (projectDetail?.phase as string) || "Unknown";
    const contractValue = (projectDetail?.contract_value_usd as number) || (projectDetail?.total_fee_usd as number) || 0;
    const paidToDate = (projectDetail?.paid_to_date_usd as number) || 0;
    const paidPct = contractValue > 0 ? Math.round((paidToDate / contractValue) * 100) : 0;

    let summary = `${projectName} is currently in ${phase} phase. `;

    if (contractValue > 0) {
      summary += `The project has a contract value of $${(contractValue / 1000000).toFixed(2)}M with ${paidPct}% collected to date. `;
    }

    if (team.length > 0) {
      summary += `${team.length} team members are currently assigned. `;
    }

    if (health.risks.length > 0) {
      summary += `Key issues: ${health.risks.slice(0, 2).join("; ")}.`;
    } else {
      summary += "No critical issues identified.";
    }

    return summary;
  };

  return (
    <div className="space-y-6">
      {/* Executive Summary */}
      <Card className="border-2 border-slate-200 bg-gradient-to-br from-slate-50 to-white">
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-lg">
            <FileText className="h-5 w-5 text-slate-600" />
            Project Overview
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-slate-700 leading-relaxed">{generateSummary()}</p>

          {/* Quick Stats */}
          <div className="mt-4 pt-4 border-t grid grid-cols-3 gap-4">
            <div className="text-center">
              <div className="flex items-center justify-center gap-1 text-slate-500 text-xs mb-1">
                <Users className="h-3 w-3" />
                Team
              </div>
              <p className="text-lg font-bold text-slate-900">{team.length}</p>
            </div>
            <div className="text-center">
              <div className="flex items-center justify-center gap-1 text-slate-500 text-xs mb-1">
                <DollarSign className="h-3 w-3" />
                Collected
              </div>
              <p className="text-lg font-bold text-slate-900">
                {Math.round(
                  ((projectDetail?.paid_to_date_usd as number) || 0) /
                    (((projectDetail?.contract_value_usd as number) || (projectDetail?.total_fee_usd as number) || 1)) *
                    100
                )}%
              </p>
            </div>
            <div className="text-center">
              <div className="flex items-center justify-center gap-1 text-slate-500 text-xs mb-1">
                <AlertTriangle className="h-3 w-3" />
                Issues
              </div>
              <p className="text-lg font-bold text-slate-900">{health.risks.length}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Two Column: Health + Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Health Score */}
        <Card className={cn("border", healthConfig.bg, healthConfig.border)}>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center justify-between text-base">
              <div className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-slate-600" />
                Project Health
              </div>
              <Badge variant="outline" className={healthConfig.color}>
                {healthConfig.label}
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {/* Score Bar */}
            <div className="mb-4">
              <div className="h-3 bg-slate-200 rounded-full overflow-hidden">
                <div
                  className={cn("h-full rounded-full transition-all", healthConfig.bar)}
                  style={{ width: `${health.score}%` }}
                />
              </div>
              <div className="flex justify-between mt-1">
                <span className={cn("text-2xl font-bold", healthConfig.color)}>{health.score}</span>
                <span className="text-xs text-slate-400">/100</span>
              </div>
            </div>

            {/* Risks */}
            {health.risks.length > 0 ? (
              <div className="space-y-2">
                <p className="text-xs font-medium uppercase text-slate-500">Issues</p>
                {health.risks.map((risk, i) => (
                  <div key={i} className="flex items-start gap-2 text-sm text-slate-600">
                    <AlertTriangle className="h-3.5 w-3.5 text-amber-500 mt-0.5 shrink-0" />
                    <span>{risk}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex items-center gap-2 text-sm text-emerald-600">
                <CheckCircle2 className="h-4 w-4" />
                <span>No critical issues</span>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Action Items */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-base">
              <Zap className="h-4 w-4 text-amber-600" />
              Action Items
              {actionItems.length > 0 && (
                <Badge variant="secondary" className="ml-auto">
                  {actionItems.length}
                </Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {actionItems.length === 0 ? (
              <div className="flex items-center gap-2 text-sm text-emerald-600 py-4">
                <CheckCircle2 className="h-4 w-4" />
                <span>No pending actions</span>
              </div>
            ) : (
              <div className="space-y-2">
                {actionItems.map((item, i) => (
                  <div key={i} className="flex items-start gap-2 p-2 rounded-lg hover:bg-slate-50">
                    <Circle
                      className={cn(
                        "h-4 w-4 mt-0.5 shrink-0",
                        item.priority === "high"
                          ? "text-red-400"
                          : item.priority === "medium"
                          ? "text-amber-400"
                          : "text-slate-300"
                      )}
                    />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-slate-700">{item.title}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-xs text-slate-400">{item.description}</span>
                        <Badge
                          variant="outline"
                          className={cn(
                            "text-xs",
                            item.type === "invoice" && "border-emerald-300 text-emerald-600",
                            item.type === "rfi" && "border-blue-300 text-blue-600",
                            item.type === "deliverable" && "border-purple-300 text-purple-600"
                          )}
                        >
                          {item.type}
                        </Badge>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Team This Week */}
      {team.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-base">
              <Calendar className="h-4 w-4 text-blue-600" />
              Team This Week
              <Badge variant="secondary" className="ml-auto">{team.length} people</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {team.slice(0, 10).map((member: Record<string, unknown>, i: number) => (
                <div
                  key={i}
                  className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-100 text-sm"
                >
                  <div className="h-6 w-6 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 font-medium text-xs">
                    {(member.full_name as string)?.charAt(0) || "?"}
                  </div>
                  <span className="text-slate-700">{member.full_name as string}</span>
                  {member.phase != null && (
                    <Badge variant="outline" className="text-xs">
                      {member.phase as React.ReactNode}
                    </Badge>
                  )}
                </div>
              ))}
              {team.length > 10 && (
                <div className="flex items-center px-3 py-1.5 text-sm text-slate-500">
                  +{team.length - 10} more
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
