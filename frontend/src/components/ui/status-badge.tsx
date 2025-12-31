"use client";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

type StatusType = "success" | "warning" | "danger" | "info" | "neutral";

interface StatusBadgeProps {
  status: StatusType;
  label: string;
  className?: string;
  size?: "sm" | "default";
}

/**
 * StatusBadge - Consistent status indicators across the app
 *
 * Uses semantic colors from the design system:
 * - success: Green (emerald) - completed, healthy, paid
 * - warning: Amber - needs attention, at risk, aging
 * - danger: Red - critical, overdue, error
 * - info: Blue - informational, in progress
 * - neutral: Gray - inactive, on hold
 */
export function StatusBadge({
  status,
  label,
  className,
  size = "default"
}: StatusBadgeProps) {
  const sizeClasses = size === "sm" ? "text-[10px] px-1.5 py-0" : "";

  return (
    <Badge
      variant={status === "neutral" ? "secondary" : status}
      className={cn(sizeClasses, className)}
    >
      {label}
    </Badge>
  );
}

// Helper function to determine status from common patterns
export function getStatusFromValue(
  value: number | string | null | undefined,
  thresholds?: { good: number; warning: number }
): StatusType {
  if (value === null || value === undefined) return "neutral";

  if (typeof value === "number") {
    const { good = 70, warning = 50 } = thresholds || {};
    if (value >= good) return "success";
    if (value >= warning) return "warning";
    return "danger";
  }

  // String status mapping
  const normalized = String(value).toLowerCase().replace(/[_-]/g, "");

  const statusMap: Record<string, StatusType> = {
    // Success states
    healthy: "success",
    completed: "success",
    paid: "success",
    active: "success",
    approved: "success",
    won: "success",

    // Warning states
    atrisk: "warning",
    pending: "warning",
    aging: "warning",
    needsattention: "warning",
    review: "warning",

    // Danger states
    critical: "danger",
    overdue: "danger",
    failed: "danger",
    lost: "danger",
    rejected: "danger",

    // Info states
    inprogress: "info",
    open: "info",
    new: "info",

    // Neutral states
    onhold: "neutral",
    inactive: "neutral",
    draft: "neutral",
    cancelled: "neutral",
  };

  return statusMap[normalized] || "neutral";
}

// Common status badge presets
export function ProposalStatusBadge({ status }: { status?: string }) {
  if (!status) return null;
  const normalized = status.toLowerCase().replace(/[_-]/g, " ");
  const statusType = getStatusFromValue(status);

  return (
    <StatusBadge
      status={statusType}
      label={normalized.charAt(0).toUpperCase() + normalized.slice(1)}
    />
  );
}

export function InvoiceStatusBadge({ status, daysOverdue }: { status?: string; daysOverdue?: number }) {
  if (!status) return null;

  let statusType: StatusType = "neutral";
  if (status.toLowerCase() === "paid") {
    statusType = "success";
  } else if (daysOverdue && daysOverdue > 60) {
    statusType = "danger";
  } else if (daysOverdue && daysOverdue > 30) {
    statusType = "warning";
  } else {
    statusType = "info";
  }

  return <StatusBadge status={statusType} label={status} />;
}
