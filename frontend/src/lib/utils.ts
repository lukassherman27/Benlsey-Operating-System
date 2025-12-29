import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { STATUS_COLORS, AGING_BUCKETS, SENTIMENT_COLORS, type ProposalStatus } from "./constants";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(value: number | null | undefined): string {
  if (value == null) return "$0";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

/**
 * Get status color classes for a proposal status
 * Replaces inline color logic and prevents duplication
 */
export function getStatusColor(status: ProposalStatus): string {
  return STATUS_COLORS[status] || STATUS_COLORS["First Contact"];
}

/**
 * Get aging bucket color based on days outstanding
 * Prevents Tailwind class concatenation issues
 */
export function getAgingBucketColor(daysOutstanding: number): {
  bg: string;
  border: string;
  text: string;
  bar: string;
  label: string;
} {
  if (daysOutstanding <= 30) return { ...AGING_BUCKETS.current.color, label: AGING_BUCKETS.current.label };
  if (daysOutstanding <= 60) return { ...AGING_BUCKETS.warning.color, label: AGING_BUCKETS.warning.label };
  if (daysOutstanding <= 90) return { ...AGING_BUCKETS.overdue.color, label: AGING_BUCKETS.overdue.label };
  return { ...AGING_BUCKETS.critical.color, label: AGING_BUCKETS.critical.label };
}

/**
 * Get sentiment color classes
 */
export function getSentimentColor(sentiment: "positive" | "neutral" | "negative" | "urgent"): string {
  return SENTIMENT_COLORS[sentiment] || SENTIMENT_COLORS.neutral;
}
