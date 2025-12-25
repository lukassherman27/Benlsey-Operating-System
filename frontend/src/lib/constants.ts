/**
 * Shared Constants - Single source of truth for business logic constants
 * Eliminates duplication across components
 * Issue #119: Synced statuses with database values
 */

export type ProposalStatus =
  | "First Contact"
  | "Proposal Prep"
  | "Proposal Sent"
  | "Negotiation"
  | "On Hold"
  | "Contract Signed"
  | "Lost"
  | "Declined"
  | "Dormant";

// Proposal Status Colors (used in tracker, timeline, widgets)
export const STATUS_COLORS: Record<ProposalStatus, string> = {
  "First Contact": "bg-blue-100 text-blue-700 border-blue-200",
  "Proposal Prep": "bg-yellow-100 text-yellow-700 border-yellow-200",
  "Proposal Sent": "bg-amber-100 text-amber-700 border-amber-200",
  "Negotiation": "bg-purple-100 text-purple-700 border-purple-200",
  "On Hold": "bg-slate-100 text-slate-700 border-slate-200",
  "Contract Signed": "bg-green-100 text-green-700 border-green-200",
  "Lost": "bg-red-100 text-red-700 border-red-200",
  "Declined": "bg-rose-100 text-rose-700 border-rose-200",
  "Dormant": "bg-gray-100 text-gray-700 border-gray-200",
};

// Status Priority (for sorting - lower = earlier in pipeline)
export const STATUS_PRIORITY: Record<ProposalStatus, number> = {
  "First Contact": 1,
  "Proposal Prep": 2,
  "Proposal Sent": 3,
  "Negotiation": 4,
  "On Hold": 5,
  "Contract Signed": 6,
  "Lost": 7,
  "Declined": 8,
  "Dormant": 9,
};

// Invoice Aging Buckets
export const AGING_BUCKETS = {
  current: {
    label: "Current (0-30 days)",
    threshold: 30,
    color: {
      bg: "bg-green-50",
      border: "border-green-200",
      text: "text-green-700",
      bar: "bg-green-500",
    },
  },
  warning: {
    label: "31-60 days",
    threshold: 60,
    color: {
      bg: "bg-yellow-50",
      border: "border-yellow-200",
      text: "text-yellow-700",
      bar: "bg-yellow-500",
    },
  },
  overdue: {
    label: "61-90 days",
    threshold: 90,
    color: {
      bg: "bg-orange-50",
      border: "border-orange-200",
      text: "text-orange-700",
      bar: "bg-orange-500",
    },
  },
  critical: {
    label: "90+ days",
    threshold: Infinity,
    color: {
      bg: "bg-red-50",
      border: "border-red-200",
      text: "text-red-700",
      bar: "bg-red-500",
    },
  },
} as const;

// Email Sentiment Colors
export const SENTIMENT_COLORS = {
  positive: "bg-green-100 text-green-700 border-green-200",
  neutral: "bg-slate-100 text-slate-700 border-slate-200",
  negative: "bg-red-100 text-red-700 border-red-200",
  urgent: "bg-amber-100 text-amber-700 border-amber-200",
} as const;

// Project Health Thresholds
export const HEALTH_THRESHOLDS = {
  critical: 30,  // < 30 days = critical
  warning: 70,   // < 70 days = warning
  healthy: 100,  // >= 70 days = healthy
} as const;
