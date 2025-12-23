"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  AlertTriangle,
  DollarSign,
  TrendingUp,
  Clock,
  Download,
  ArrowUpRight,
  CheckCircle2,
  Circle
} from "lucide-react";
import { formatCurrency } from "@/lib/utils";

// The actual API response shape (backend returns aging buckets)
interface AgingBucket {
  count: number;
  amount: number;
}

interface AgingApiResponse {
  "0_to_10"?: AgingBucket;
  "10_to_30"?: AgingBucket;
  "30_to_90"?: AgingBucket;
  over_90?: AgingBucket;
}

interface PaidInvoice {
  invoice_id?: number;
  invoice_number: string;
  project_code: string;
  project_name?: string;
  payment_amount: number;
  payment_date: string;
}

interface OutstandingInvoice {
  invoice_id?: number;
  invoice_number: string;
  project_code: string;
  project_title?: string;
  invoice_amount: number;
  days_overdue: number;
  discipline?: string;
  scope?: string;
  phase?: string;
  description?: string;
}

interface InvoiceAgingWidgetProps {
  compact?: boolean;
  showExport?: boolean;
}

// Transformed aging data shape for the widget
interface TransformedAgingData {
  aging_breakdown: {
    under_30: AgingBucket;
    "30_to_90": AgingBucket;
    over_90: AgingBucket;
  };
  summary: {
    total_outstanding_amount: number;
    total_outstanding_count: number;
  };
  recent_paid?: PaidInvoice[];
  largest_outstanding?: OutstandingInvoice[];
}

export function InvoiceAgingWidgetEnhanced({ compact = false, showExport = true }: InvoiceAgingWidgetProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["invoice-aging"],
    queryFn: api.getInvoiceAging,
    refetchInterval: 1000 * 60 * 5,
  });

  // Transform API response to widget format
  // API returns: { data: { aging: { "0_to_10", "10_to_30", "30_to_90", "over_90" } }, aging: {...} }
  // Widget expects: { aging_breakdown: { under_30, "30_to_90", over_90 }, summary: {...} }
  const apiData = data as unknown as { data?: { aging?: AgingApiResponse }; aging?: AgingApiResponse; recent_paid?: PaidInvoice[]; largest_outstanding?: OutstandingInvoice[] } | undefined;
  const rawAging = apiData?.data?.aging || apiData?.aging;
  const agingData: TransformedAgingData | null = rawAging ? (() => {
    const under30Amt = (rawAging["0_to_10"]?.amount || 0) + (rawAging["10_to_30"]?.amount || 0);
    const under30Cnt = (rawAging["0_to_10"]?.count || 0) + (rawAging["10_to_30"]?.count || 0);
    const mid90Amt = rawAging["30_to_90"]?.amount || 0;
    const mid90Cnt = rawAging["30_to_90"]?.count || 0;
    const over90Amt = rawAging["over_90"]?.amount || 0;
    const over90Cnt = rawAging["over_90"]?.count || 0;
    return {
      aging_breakdown: {
        under_30: { count: under30Cnt, amount: under30Amt },
        "30_to_90": { count: mid90Cnt, amount: mid90Amt },
        over_90: { count: over90Cnt, amount: over90Amt },
      },
      summary: {
        total_outstanding_amount: under30Amt + mid90Amt + over90Amt,
        total_outstanding_count: under30Cnt + mid90Cnt + over90Cnt,
      },
      recent_paid: apiData?.recent_paid,
      largest_outstanding: apiData?.largest_outstanding,
    };
  })() : null;

  // Loading skeleton with smooth animations
  if (isLoading) {
    return (
      <Card className="overflow-hidden">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="space-y-2">
              <div className="h-4 w-32 bg-gray-200 rounded animate-pulse" />
              <div className="h-6 w-48 bg-gray-200 rounded animate-pulse" />
            </div>
            <div className="h-6 w-20 bg-gray-200 rounded-full animate-pulse" />
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 bg-gray-100 rounded-lg animate-pulse" />
          ))}
        </CardContent>
      </Card>
    );
  }

  if (error || !agingData) {
    return (
      <Card className="border-red-200 bg-red-50">
        <CardContent className="pt-6">
          <div className="flex items-center gap-3 text-red-700">
            <AlertTriangle className="h-5 w-5" />
            <p className="text-sm font-medium">
              {error ? "Failed to load invoice data" : "No data available"}
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const breakdown = agingData.aging_breakdown;
  const totalOutstanding = agingData.summary.total_outstanding_amount;
  const totalCount = agingData.summary.total_outstanding_count;

  // Calculate health score (0-100)
  const healthScore = calculateHealthScore(breakdown, totalOutstanding);

  // Compact mode - more visual and condensed
  if (compact) {
    return (
      <Card className="hover:shadow-lg transition-shadow duration-200">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base font-semibold flex items-center gap-2">
              <DollarSign className="h-4 w-4" />
              Outstanding Invoices
            </CardTitle>
            <HealthBadge score={healthScore} />
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex justify-between items-baseline">
            <span className="text-2xl font-bold">{formatCurrency(totalOutstanding)}</span>
            <Badge variant={breakdown.over_90.count > 0 ? "destructive" : "secondary"}>
              {totalCount} total
            </Badge>
          </div>

          {/* Mini progress bar */}
          <div className="space-y-1">
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>Aging Distribution</span>
              <span>{breakdown.over_90.count} critical</span>
            </div>
            <div className="flex h-2 w-full overflow-hidden rounded-full bg-gray-200">
              <div
                className="bg-green-500 transition-all duration-500"
                style={{ width: `${totalOutstanding > 0 ? (breakdown.under_30.amount / totalOutstanding) * 100 : 0}%` }}
              />
              <div
                className="bg-yellow-500 transition-all duration-500"
                style={{ width: `${totalOutstanding > 0 ? (breakdown["30_to_90"].amount / totalOutstanding) * 100 : 0}%` }}
              />
              <div
                className="bg-red-500 transition-all duration-500"
                style={{ width: `${totalOutstanding > 0 ? (breakdown.over_90.amount / totalOutstanding) * 100 : 0}%` }}
              />
            </div>
          </div>

          {/* Quick stats */}
          <div className="grid grid-cols-3 gap-2 text-xs pt-2 border-t">
            <div className="text-center">
              <p className="font-semibold text-green-600">{breakdown.under_30.count}</p>
              <p className="text-muted-foreground">&lt;30d</p>
            </div>
            <div className="text-center">
              <p className="font-semibold text-yellow-600">{breakdown["30_to_90"].count}</p>
              <p className="text-muted-foreground">30-90d</p>
            </div>
            <div className="text-center">
              <p className="font-semibold text-red-600">{breakdown.over_90.count}</p>
              <p className="text-muted-foreground">&gt;90d</p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Full mode with enhanced visuals
  return (
    <Card className="overflow-hidden">
      <CardHeader className="bg-gradient-to-r from-blue-50 to-indigo-50 border-b">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-xl flex items-center gap-2 mb-1">
              <div className="p-2 bg-white rounded-lg shadow-sm">
                <DollarSign className="h-5 w-5 text-blue-600" />
              </div>
              Invoice Aging Analysis
            </CardTitle>
            <p className="text-sm text-muted-foreground">
              Real-time tracking of {totalCount} outstanding invoices
            </p>
          </div>
          <div className="flex items-center gap-2">
            <HealthBadge score={healthScore} large />
            {showExport && (
              <Button variant="outline" size="sm" onClick={() => exportToCSV(agingData)}>
                <Download className="h-4 w-4 mr-2" />
                Export
              </Button>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6 pt-6">
        {/* Hero Stats Card with Gradient */}
        <div className="relative overflow-hidden rounded-xl bg-gradient-to-br from-blue-500 via-blue-600 to-indigo-600 text-white p-6 shadow-lg">
          <div className="relative z-10">
            <div className="flex items-center justify-between mb-4">
              <div>
                <p className="text-blue-100 text-sm font-medium mb-1">Total Outstanding</p>
                <p className="text-4xl font-bold tracking-tight">{formatCurrency(totalOutstanding)}</p>
                <p className="text-blue-200 text-sm mt-1">{totalCount} invoices pending payment</p>
              </div>
              <div className="bg-white/20 backdrop-blur-sm rounded-full p-4">
                <Clock className="h-10 w-10 text-white" />
              </div>
            </div>

            {/* Mini trend indicator */}
            <div className="flex items-center gap-2 text-sm">
              <TrendingUp className="h-4 w-4" />
              <span>Track aging across {breakdown.under_30.count + breakdown["30_to_90"].count + breakdown.over_90.count} categories</span>
            </div>
          </div>

          {/* Decorative background pattern */}
          <div className="absolute top-0 right-0 -mr-12 -mt-12 h-48 w-48 rounded-full bg-white/10 blur-3xl" />
          <div className="absolute bottom-0 left-0 -ml-12 -mb-12 h-48 w-48 rounded-full bg-indigo-400/20 blur-3xl" />
        </div>

        {/* Recently Paid - Enhanced with status icons */}
        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold flex items-center gap-2">
              <div className="p-1.5 bg-green-100 rounded-md">
                <CheckCircle2 className="h-4 w-4 text-green-600" />
              </div>
              Recently Paid
            </h3>
            <Button variant="ghost" size="sm" className="text-xs">
              View All <ArrowUpRight className="h-3 w-3 ml-1" />
            </Button>
          </div>

          <div className="space-y-2">
            {(agingData.recent_paid || []).slice(0, 5).map((invoice, idx) => (
              <div
                key={invoice.invoice_number}
                className="group relative flex justify-between items-center p-3.5 bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-lg hover:shadow-md hover:border-green-300 transition-all duration-200 cursor-pointer"
                style={{ animationDelay: `${idx * 50}ms` }}
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-white rounded-full shadow-sm">
                    <CheckCircle2 className="h-4 w-4 text-green-600" />
                  </div>
                  <div>
                    <p className="font-semibold text-sm text-gray-900">{invoice.invoice_number}</p>
                    <p className="text-xs text-gray-600">
                      {invoice.project_code || "No Project"} • Paid {new Date(invoice.payment_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-bold text-green-700">
                    {formatCurrency(invoice.payment_amount)}
                  </span>
                  <ArrowUpRight className="h-4 w-4 text-green-600 opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Largest Outstanding - Enhanced with priority badges */}
        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold flex items-center gap-2">
              <div className="p-1.5 bg-orange-100 rounded-md">
                <AlertTriangle className="h-4 w-4 text-orange-600" />
              </div>
              Largest Outstanding
            </h3>
            <Badge variant="outline" className="text-xs">
              Top 10 by amount
            </Badge>
          </div>

          <div className="space-y-2">
            {(agingData.largest_outstanding || []).slice(0, 10).map((invoice, idx) => {
              const isOverdue = invoice.days_overdue > 0;
              const isExtremelyCritical = invoice.days_overdue > 600; // 600+ days - RED bold
              const isVeryCritical = invoice.days_overdue > 365 && invoice.days_overdue <= 600; // 365-600 days
              const isCritical = invoice.days_overdue > 90 && invoice.days_overdue <= 365;
              const isWarning = invoice.days_overdue > 30 && invoice.days_overdue <= 90;

              // Build phase/scope string
              const phaseInfo = [
                invoice.discipline,
                invoice.scope,
                invoice.phase
              ].filter(Boolean).join(' / ') || invoice.description || 'General';

              return (
                <div
                  key={invoice.invoice_number}
                  className={`group relative flex justify-between items-center p-3.5 rounded-lg border transition-all duration-200 cursor-pointer ${
                    isExtremelyCritical
                      ? "bg-gradient-to-r from-red-100 to-red-50 border-red-400 hover:shadow-md hover:border-red-500"
                      : isVeryCritical
                      ? "bg-gradient-to-r from-red-50 to-orange-50 border-red-300 hover:shadow-md hover:border-red-400"
                      : isCritical
                      ? "bg-gradient-to-r from-red-50 to-pink-50 border-red-200 hover:shadow-md hover:border-red-300"
                      : isWarning
                      ? "bg-gradient-to-r from-yellow-50 to-amber-50 border-yellow-200 hover:shadow-md hover:border-yellow-300"
                      : "bg-gradient-to-r from-gray-50 to-slate-50 border-gray-200 hover:shadow-md hover:border-gray-300"
                  }`}
                  style={{ animationDelay: `${idx * 50}ms` }}
                >
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-full shadow-sm ${
                      isExtremelyCritical ? "bg-red-200" :
                      isVeryCritical ? "bg-red-100" :
                      isCritical ? "bg-red-100" : isWarning ? "bg-yellow-100" : "bg-gray-100"
                    }`}>
                      <Circle className={`h-4 w-4 ${
                        isExtremelyCritical ? "text-red-700 fill-red-700" :
                        isVeryCritical ? "text-red-600 fill-red-600" :
                        isCritical ? "text-red-600 fill-red-600" :
                        isWarning ? "text-yellow-600 fill-yellow-600" :
                        "text-gray-600"
                      }`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="font-medium text-sm text-gray-900 truncate">
                          {invoice.project_title || invoice.project_code || "No Project"}
                        </p>
                        {isExtremelyCritical && (
                          <Badge variant="destructive" className="text-xs px-1.5 py-0 bg-red-600">
                            {invoice.days_overdue}d OVERDUE
                          </Badge>
                        )}
                        {isVeryCritical && !isExtremelyCritical && (
                          <Badge variant="destructive" className="text-xs px-1.5 py-0">
                            {invoice.days_overdue}d
                          </Badge>
                        )}
                      </div>
                      <p className={`text-xs mt-0.5 ${isExtremelyCritical ? "text-red-700 font-semibold" : "text-gray-500"}`}>
                        {phaseInfo}
                      </p>
                      <p className="text-xs text-gray-400 mt-0.5">
                        <span className="text-[10px]">{invoice.invoice_number}</span>
                        {isOverdue && !isExtremelyCritical && !isVeryCritical && (
                          <span className={`ml-2 font-semibold ${
                            isCritical ? "text-red-600" : isWarning ? "text-yellow-700" : "text-gray-600"
                          }`}>
                            • {invoice.days_overdue} days overdue
                          </span>
                        )}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`font-bold ${
                      isExtremelyCritical ? "text-red-800 text-lg" :
                      isVeryCritical ? "text-red-700" :
                      isCritical ? "text-red-700" : isWarning ? "text-yellow-700" : "text-gray-700"
                    }`}>
                      {formatCurrency(invoice.invoice_amount)}
                    </span>
                    <ArrowUpRight className="h-4 w-4 opacity-0 group-hover:opacity-100 transition-opacity" />
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        {/* Aging Breakdown with enhanced visuals */}
        <section className="space-y-4">
          <h3 className="text-sm font-semibold">Aging Breakdown</h3>

          {/* Stacked bar chart */}
          <div className="space-y-3">
            <EnhancedAgingBar
              label="< 30 Days"
              sublabel="Current & On Track"
              count={breakdown.under_30.count}
              amount={breakdown.under_30.amount}
              color="green"
              percentage={safePercentage(breakdown.under_30.amount, totalOutstanding)}
            />
            <EnhancedAgingBar
              label="30-90 Days"
              sublabel="Needs Follow-up"
              count={breakdown["30_to_90"].count}
              amount={breakdown["30_to_90"].amount}
              color="yellow"
              percentage={safePercentage(breakdown["30_to_90"].amount, totalOutstanding)}
            />
            <EnhancedAgingBar
              label="> 90 Days"
              sublabel="Critical Action Required"
              count={breakdown.over_90.count}
              amount={breakdown.over_90.amount}
              color="red"
              percentage={safePercentage(breakdown.over_90.amount, totalOutstanding)}
            />
          </div>

          {/* Stats cards with hover effects */}
          <div className="grid grid-cols-3 gap-3 pt-2">
            <EnhancedAgingCard
              label="< 30 Days"
              count={breakdown.under_30.count}
              amount={breakdown.under_30.amount}
              color="green"
              icon={CheckCircle2}
            />
            <EnhancedAgingCard
              label="30-90 Days"
              count={breakdown["30_to_90"].count}
              amount={breakdown["30_to_90"].amount}
              color="yellow"
              icon={Clock}
            />
            <EnhancedAgingCard
              label="> 90 Days"
              count={breakdown.over_90.count}
              amount={breakdown.over_90.amount}
              color="red"
              icon={AlertTriangle}
            />
          </div>
        </section>

        {/* Critical Alert with action buttons */}
        {breakdown.over_90.count > 0 && (
          <div className="relative overflow-hidden bg-gradient-to-r from-red-50 to-pink-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-red-100 rounded-full">
                <AlertTriangle className="h-5 w-5 text-red-600" />
              </div>
              <div className="flex-1">
                <p className="font-semibold text-red-900 mb-1">Critical Attention Required</p>
                <p className="text-sm text-red-700 mb-3">
                  {formatCurrency(breakdown.over_90.amount)} in {breakdown.over_90.count} invoices are over 90
                  days old. Immediate follow-up recommended to prevent further aging.
                </p>
                <div className="flex gap-2">
                  <Button size="sm" variant="destructive">
                    View Critical Invoices
                  </Button>
                  <Button size="sm" variant="outline">
                    Send Reminders
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// Helper Components

function HealthBadge({ score, large = false }: { score: number; large?: boolean }) {
  const getHealthColor = (score: number) => {
    if (score >= 80) return { bg: "bg-green-100", text: "text-green-700", label: "Excellent" };
    if (score >= 60) return { bg: "bg-yellow-100", text: "text-yellow-700", label: "Good" };
    if (score >= 40) return { bg: "bg-orange-100", text: "text-orange-700", label: "Fair" };
    return { bg: "bg-red-100", text: "text-red-700", label: "Poor" };
  };

  const { bg, text, label } = getHealthColor(score);

  return (
    <div className={`flex items-center gap-2 ${bg} ${text} rounded-full ${large ? "px-4 py-2" : "px-3 py-1"}`}>
      <Circle className={`${large ? "h-2 w-2" : "h-1.5 w-1.5"} fill-current`} />
      <span className={`${large ? "text-sm" : "text-xs"} font-semibold`}>
        {label} {large && `(${score}%)`}
      </span>
    </div>
  );
}

function EnhancedAgingBar({
  label,
  sublabel,
  count,
  amount,
  color,
  percentage,
}: {
  label: string;
  sublabel: string;
  count: number;
  amount: number;
  color: "green" | "yellow" | "red";
  percentage: number;
}) {
  const colorClasses = {
    green: { bg: "bg-green-500", text: "text-green-700", light: "bg-green-100" },
    yellow: { bg: "bg-yellow-500", text: "text-yellow-700", light: "bg-yellow-100" },
    red: { bg: "bg-red-500", text: "text-red-700", light: "bg-red-100" },
  };

  const colors = colorClasses[color];

  return (
    <div className="space-y-2">
      <div className="flex justify-between items-center">
        <div>
          <p className={`text-sm font-semibold ${colors.text}`}>{label}</p>
          <p className="text-xs text-muted-foreground">{sublabel}</p>
        </div>
        <div className="text-right">
          <p className="text-sm font-bold">{formatCurrency(amount)}</p>
          <p className="text-xs text-muted-foreground">{count} invoices • {percentage.toFixed(1)}%</p>
        </div>
      </div>
      <div className="relative w-full bg-gray-200 rounded-full h-3 overflow-hidden">
        <div
          className={`h-full ${colors.bg} transition-all duration-700 ease-out relative`}
          style={{ width: `${percentage}%` }}
        >
          <div className="absolute inset-0 bg-white/20 animate-pulse" />
        </div>
      </div>
    </div>
  );
}

function EnhancedAgingCard({
  label,
  count,
  amount,
  color,
  icon: Icon,
}: {
  label: string;
  count: number;
  amount: number;
  color: "green" | "yellow" | "red";
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  icon: any;
}) {
  const colorClasses = {
    green: {
      bg: "bg-gradient-to-br from-green-50 to-emerald-50",
      border: "border-green-200",
      text: "text-green-700",
      icon: "text-green-600",
      iconBg: "bg-green-100",
    },
    yellow: {
      bg: "bg-gradient-to-br from-yellow-50 to-amber-50",
      border: "border-yellow-200",
      text: "text-yellow-700",
      icon: "text-yellow-600",
      iconBg: "bg-yellow-100",
    },
    red: {
      bg: "bg-gradient-to-br from-red-50 to-pink-50",
      border: "border-red-200",
      text: "text-red-700",
      icon: "text-red-600",
      iconBg: "bg-red-100",
    },
  };

  const classes = colorClasses[color];

  return (
    <div className={`${classes.bg} border ${classes.border} rounded-lg p-4 hover:shadow-md transition-all duration-200 cursor-pointer group`}>
      <div className="flex items-center justify-between mb-3">
        <div className={`p-2 ${classes.iconBg} rounded-lg`}>
          <Icon className={`h-4 w-4 ${classes.icon}`} />
        </div>
        <Badge variant="outline" className="text-xs">
          {count}
        </Badge>
      </div>
      <p className="text-xs text-muted-foreground mb-1">{label}</p>
      <p className={`text-lg font-bold ${classes.text} group-hover:scale-105 transition-transform`}>
        {formatCurrency(amount)}
      </p>
    </div>
  );
}

// Utility functions
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function calculateHealthScore(breakdown: any, total: number): number {
  if (!total || total === 0) return 100; // No outstanding = healthy
  const under30Percentage = (breakdown.under_30.amount / total) * 100;
  const over90Percentage = (breakdown.over_90.amount / total) * 100;

  // Score: Higher is better
  // 100% under 30 days = 100 score
  // 100% over 90 days = 0 score
  const score = under30Percentage - (over90Percentage * 2);
  return Math.max(0, Math.min(100, score));
}

// Safe percentage calculation to avoid NaN
function safePercentage(value: number, total: number): number {
  if (!total || total === 0) return 0;
  return (value / total) * 100;
}

function exportToCSV(data: TransformedAgingData) {
  // Create CSV content
  let csv = "Invoice Number,Amount,Status,Days Overdue,Project Code\n";

  (data.largest_outstanding || []).forEach((inv: OutstandingInvoice) => {
    csv += `${inv.invoice_number},${inv.invoice_amount},Outstanding,${inv.days_overdue},${inv.project_code || "N/A"}\n`;
  });

  // Trigger download
  const blob = new Blob([csv], { type: "text/csv" });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `invoice-aging-${new Date().toISOString().split('T')[0]}.csv`;
  a.click();
  window.URL.revokeObjectURL(url);
}
