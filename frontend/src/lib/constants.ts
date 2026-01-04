/**
 * Shared constants for the Bensley Operating System
 * These values match the database exactly - do not modify without updating backend
 */

// Re-export ProposalStatus from types.ts (single source of truth)
export { type ProposalStatus } from "./types";
import type { ProposalStatus } from "./types";

// Status colors for UI components (workflow order)
export const STATUS_COLORS: Record<ProposalStatus, string> = {
  "First Contact": "bg-blue-100 text-blue-800 border-blue-200",
  "Meeting Held": "bg-sky-100 text-sky-800 border-sky-200",
  "NDA Signed": "bg-indigo-100 text-indigo-800 border-indigo-200",
  "Proposal Prep": "bg-yellow-100 text-yellow-800 border-yellow-200",
  "Proposal Sent": "bg-amber-100 text-amber-800 border-amber-200",
  "Negotiation": "bg-purple-100 text-purple-800 border-purple-200",
  "MOU Signed": "bg-teal-100 text-teal-800 border-teal-200",
  "On Hold": "bg-gray-100 text-gray-700 border-gray-200",
  "Contract Signed": "bg-emerald-100 text-emerald-800 border-emerald-200",
  "Lost": "bg-red-100 text-red-700 border-red-200",
  "Declined": "bg-rose-100 text-rose-700 border-rose-200",
  "Dormant": "bg-slate-100 text-slate-600 border-slate-200",
};

// Aging buckets for invoice tracking
export const AGING_BUCKETS = {
  current: {
    label: "Current (0-30)",
    color: {
      bg: "bg-emerald-50",
      border: "border-emerald-200",
      text: "text-emerald-700",
      bar: "bg-emerald-500",
    },
  },
  warning: {
    label: "31-60 days",
    color: {
      bg: "bg-yellow-50",
      border: "border-yellow-200",
      text: "text-yellow-700",
      bar: "bg-yellow-500",
    },
  },
  overdue: {
    label: "61-90 days",
    color: {
      bg: "bg-orange-50",
      border: "border-orange-200",
      text: "text-orange-700",
      bar: "bg-orange-500",
    },
  },
  critical: {
    label: "90+ days",
    color: {
      bg: "bg-red-50",
      border: "border-red-200",
      text: "text-red-700",
      bar: "bg-red-500",
    },
  },
};

// Sentiment colors for email/contact analysis
export const SENTIMENT_COLORS: Record<string, string> = {
  positive: "bg-emerald-100 text-emerald-700",
  neutral: "bg-slate-100 text-slate-600",
  negative: "bg-red-100 text-red-700",
  urgent: "bg-amber-100 text-amber-700",
};
