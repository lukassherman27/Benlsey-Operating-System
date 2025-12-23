"use client";

import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  DollarSign,
  FileQuestion,
  ChevronDown,
  ChevronUp,
  ExternalLink,
} from "lucide-react";
import { useState } from "react";

export type HealthStatus = "critical" | "at_risk" | "attention" | "healthy";

interface Issue {
  type: "invoice" | "rfi" | "communication" | "deliverable" | "other";
  severity: "critical" | "warning" | "info";
  title: string;
  detail: string;
  action?: {
    label: string;
    href?: string;
    onClick?: () => void;
  };
}

interface ProjectHealthBannerProps {
  status: HealthStatus;
  issues: Issue[];
  projectName?: string;
  className?: string;
}

const statusConfig: Record<
  HealthStatus,
  {
    label: string;
    bgColor: string;
    borderColor: string;
    textColor: string;
    icon: typeof AlertTriangle | typeof CheckCircle2;
    iconColor: string;
  }
> = {
  critical: {
    label: "Critical Issues",
    bgColor: "bg-red-50",
    borderColor: "border-red-300",
    textColor: "text-red-900",
    icon: AlertTriangle,
    iconColor: "text-red-600",
  },
  at_risk: {
    label: "At Risk",
    bgColor: "bg-amber-50",
    borderColor: "border-amber-300",
    textColor: "text-amber-900",
    icon: AlertTriangle,
    iconColor: "text-amber-600",
  },
  attention: {
    label: "Needs Attention",
    bgColor: "bg-yellow-50",
    borderColor: "border-yellow-300",
    textColor: "text-yellow-900",
    icon: Clock,
    iconColor: "text-yellow-600",
  },
  healthy: {
    label: "Healthy",
    bgColor: "bg-emerald-50",
    borderColor: "border-emerald-300",
    textColor: "text-emerald-900",
    icon: CheckCircle2,
    iconColor: "text-emerald-600",
  },
};

const issueIcons: Record<Issue["type"], typeof DollarSign> = {
  invoice: DollarSign,
  rfi: FileQuestion,
  communication: Clock,
  deliverable: Clock,
  other: AlertTriangle,
};

const severityColors: Record<Issue["severity"], string> = {
  critical: "bg-red-100 text-red-800 border-red-200",
  warning: "bg-amber-100 text-amber-800 border-amber-200",
  info: "bg-blue-100 text-blue-800 border-blue-200",
};

export function ProjectHealthBanner({
  status,
  issues,
  projectName: _projectName,
  className,
}: ProjectHealthBannerProps) {
  const [expanded, setExpanded] = useState(status !== "healthy");
  const config = statusConfig[status];
  const Icon = config.icon;

  // If healthy with no issues, show minimal banner
  if (status === "healthy" && issues.length === 0) {
    return (
      <div
        className={cn(
          "rounded-lg border px-4 py-3 flex items-center gap-3",
          config.bgColor,
          config.borderColor,
          className
        )}
      >
        <CheckCircle2 className={cn("h-5 w-5", config.iconColor)} />
        <div className="flex-1">
          <span className={cn("font-medium text-sm", config.textColor)}>
            All Systems Healthy
          </span>
          <span className="text-sm text-slate-500 ml-2">
            No outstanding issues
          </span>
        </div>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "rounded-xl border-2 overflow-hidden",
        config.bgColor,
        config.borderColor,
        className
      )}
    >
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className={cn(
          "w-full px-4 py-3 flex items-center gap-3",
          "hover:bg-white/30 transition-colors"
        )}
      >
        <Icon className={cn("h-5 w-5 shrink-0", config.iconColor)} />
        <div className="flex-1 text-left">
          <span className={cn("font-semibold text-sm", config.textColor)}>
            {config.label}
          </span>
          <Badge
            variant="outline"
            className={cn("ml-2 text-xs", config.textColor, config.borderColor)}
          >
            {issues.length} {issues.length === 1 ? "issue" : "issues"}
          </Badge>
        </div>
        {expanded ? (
          <ChevronUp className="h-4 w-4 text-slate-400" />
        ) : (
          <ChevronDown className="h-4 w-4 text-slate-400" />
        )}
      </button>

      {/* Expanded Issue List */}
      {expanded && issues.length > 0 && (
        <div className="px-4 pb-4 space-y-2">
          {issues.map((issue, index) => {
            const IssueIcon = issueIcons[issue.type];
            return (
              <div
                key={index}
                className={cn(
                  "p-3 rounded-lg border bg-white flex items-start gap-3",
                  "hover:shadow-sm transition-shadow"
                )}
              >
                <div
                  className={cn(
                    "p-1.5 rounded-lg shrink-0",
                    severityColors[issue.severity]
                  )}
                >
                  <IssueIcon className="h-4 w-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-medium text-sm text-slate-800">
                      {issue.title}
                    </span>
                    <Badge
                      variant="outline"
                      className={cn("text-xs", severityColors[issue.severity])}
                    >
                      {issue.severity}
                    </Badge>
                  </div>
                  <p className="text-xs text-slate-600 mt-0.5">{issue.detail}</p>
                </div>
                {issue.action && (
                  <Button
                    size="sm"
                    variant="ghost"
                    className="shrink-0 text-xs h-7"
                    onClick={issue.action.onClick}
                    asChild={!!issue.action.href}
                  >
                    {issue.action.href ? (
                      <a href={issue.action.href}>
                        {issue.action.label}
                        <ExternalLink className="h-3 w-3 ml-1" />
                      </a>
                    ) : (
                      <>
                        {issue.action.label}
                        <ExternalLink className="h-3 w-3 ml-1" />
                      </>
                    )}
                  </Button>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// Helper function to calculate project health from data
export function calculateProjectHealth(project: {
  overdue_invoices_count?: number;
  overdue_invoices_amount?: number;
  open_rfis_count?: number;
  days_since_activity?: number;
  overdue_deliverables_count?: number;
}): {
  status: HealthStatus;
  issues: Issue[];
} {
  const issues: Issue[] = [];
  let criticalCount = 0;
  let warningCount = 0;

  // Check overdue invoices
  const overdueCount = project.overdue_invoices_count ?? 0;
  const overdueAmount = project.overdue_invoices_amount ?? 0;
  if (overdueCount > 0) {
    const severity = overdueAmount > 100000 ? "critical" : "warning";
    if (severity === "critical") criticalCount++;
    else warningCount++;
    issues.push({
      type: "invoice",
      severity,
      title: `${overdueCount} Overdue Invoice${overdueCount > 1 ? "s" : ""}`,
      detail: `$${(overdueAmount / 1000).toFixed(0)}K outstanding over 30 days`,
      action: {
        label: "View Invoices",
        href: "#invoices",
      },
    });
  }

  // Check open RFIs
  const openRfis = project.open_rfis_count ?? 0;
  if (openRfis > 0) {
    const severity = openRfis > 3 ? "warning" : "info";
    if (severity === "warning") warningCount++;
    issues.push({
      type: "rfi",
      severity,
      title: `${openRfis} Open RFI${openRfis > 1 ? "s" : ""}`,
      detail: "Awaiting response",
      action: {
        label: "View RFIs",
        href: "#rfis",
      },
    });
  }

  // Check communication staleness
  const daysSilent = project.days_since_activity ?? 0;
  if (daysSilent > 14) {
    const severity = daysSilent > 30 ? "warning" : "info";
    if (severity === "warning") warningCount++;
    issues.push({
      type: "communication",
      severity,
      title: "Communication Gap",
      detail: `${daysSilent} days since last activity`,
      action: {
        label: "Send Update",
      },
    });
  }

  // Check overdue deliverables
  const overdueDeliverables = project.overdue_deliverables_count ?? 0;
  if (overdueDeliverables > 0) {
    const severity = overdueDeliverables > 1 ? "critical" : "warning";
    if (severity === "critical") criticalCount++;
    else warningCount++;
    issues.push({
      type: "deliverable",
      severity,
      title: `${overdueDeliverables} Overdue Deliverable${overdueDeliverables > 1 ? "s" : ""}`,
      detail: "Past due date",
      action: {
        label: "View",
        href: "#deliverables",
      },
    });
  }

  // Determine overall status
  let status: HealthStatus = "healthy";
  if (criticalCount > 0) {
    status = "critical";
  } else if (warningCount >= 2) {
    status = "at_risk";
  } else if (warningCount > 0 || issues.length > 0) {
    status = "attention";
  }

  return { status, issues };
}
