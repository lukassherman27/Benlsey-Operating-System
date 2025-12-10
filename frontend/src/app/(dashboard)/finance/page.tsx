"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { InvoiceAgingWidgetEnhanced } from "@/components/dashboard/invoice-aging-widget-enhanced";
import { PaymentVelocityWidget } from "@/components/dashboard/payment-velocity-widget";
import { InvoiceQuickActions } from "@/components/dashboard/invoice-quick-actions";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DollarSign, TrendingUp, Calendar, Download, AlertTriangle, Clock, Zap, Timer, ArrowRight } from "lucide-react";
import Link from "next/link";

/**
 * Finance Dashboard Page
 * Comprehensive view of all financial metrics and invoice aging
 */
export default function FinancePage() {
  // Fetch real financial metrics
  const { data: metricsData, isLoading: metricsLoading } = useQuery({
    queryKey: ["finance-dashboard-metrics"],
    queryFn: api.getDashboardFinancialMetrics,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });

  // Fetch invoice aging data
  const { data: agingData, isLoading: agingLoading } = useQuery({
    queryKey: ["invoice-aging-finance"],
    queryFn: api.getInvoiceAging,
    staleTime: 1000 * 60 * 5,
  });

  const metrics = metricsData?.metrics;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const aging = (agingData as any)?.aging || (agingData as any)?.data?.aging;

  // Calculate derived metrics
  const totalOutstanding = metrics?.total_outstanding || 0;
  const totalPaid = metrics?.total_paid || 0;
  const totalInvoiced = metrics?.total_invoiced || 0;
  const criticalCount = aging?.over_90?.count || 0;
  const collectionRate = totalInvoiced > 0 ? (totalPaid / totalInvoiced) * 100 : 0;

  // Format currency
  const formatCurrency = (amount: number) => {
    if (amount >= 1000000) {
      return `$${(amount / 1000000).toFixed(2)}M`;
    }
    return `$${(amount / 1000).toFixed(0)}K`;
  };

  const isLoading = metricsLoading || agingLoading;

  return (
    <div className="space-y-6 w-full max-w-full overflow-x-hidden">
      {/* Page Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <DollarSign className="h-8 w-8 text-blue-600" />
            Financial Dashboard
          </h1>
          <p className="text-muted-foreground mt-1">
            Real-time invoice tracking and collections management
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant="outline" className="gap-1">
            <Calendar className="h-3 w-3" />
            Last updated: Just now
          </Badge>
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Export All
          </Button>
        </div>
      </div>

      {/* KPI Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {isLoading ? (
          <>
            <Skeleton className="h-24 rounded-lg" />
            <Skeleton className="h-24 rounded-lg" />
            <Skeleton className="h-24 rounded-lg" />
            <Skeleton className="h-24 rounded-lg" />
          </>
        ) : (
          <>
            <KPICard
              title="Total Outstanding"
              value={formatCurrency(totalOutstanding)}
              subtitle={`of ${formatCurrency(totalInvoiced)} invoiced`}
              icon={DollarSign}
              color="blue"
            />
            <KPICard
              title="Total Paid"
              value={formatCurrency(totalPaid)}
              subtitle={`${metrics?.active_project_count || 0} active projects`}
              icon={TrendingUp}
              color="green"
            />
            <KPICard
              title="Critical (>90d)"
              value={String(criticalCount)}
              subtitle={aging?.over_90?.amount ? formatCurrency(aging.over_90.amount) : "$0"}
              icon={AlertTriangle}
              color="red"
            />
            <KPICard
              title="Collection Rate"
              value={`${collectionRate.toFixed(1)}%`}
              subtitle="of invoiced amount"
              icon={Clock}
              color="purple"
            />
          </>
        )}
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Main Widget (2/3 width) */}
        <div className="lg:col-span-2 space-y-6">
          <InvoiceAgingWidgetEnhanced showExport={true} />
        </div>

        {/* Right Column - Sidebar Widgets (1/3 width) */}
        <div className="space-y-6">
          <InvoiceQuickActions />
          <PaymentVelocityWidget />
        </div>
      </div>

      {/* Bottom Section - Real Charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <RevenueTrendsChart />
        <ClientPaymentBehaviorChart />
      </div>
    </div>
  );
}

// Helper Components

function KPICard({
  title,
  value,
  subtitle,
  icon: Icon,
  color,
}: {
  title: string;
  value: string;
  subtitle: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  icon: any;
  color: "blue" | "green" | "red" | "purple";
}) {
  const colorClasses = {
    blue: "bg-blue-50 border-blue-200 text-blue-700",
    green: "bg-green-50 border-green-200 text-green-700",
    red: "bg-red-50 border-red-200 text-red-700",
    purple: "bg-purple-50 border-purple-200 text-purple-700",
  };

  return (
    <div
      className={`rounded-lg border p-4 transition-all duration-200 hover:shadow-md ${
        colorClasses[color]
      }`}
    >
      <div className="flex items-center justify-between mb-2">
        <p className="text-xs font-medium opacity-75">{title}</p>
        <Icon className="h-4 w-4 opacity-75" />
      </div>
      <p className="text-2xl font-bold">{value}</p>
      <p className="text-xs opacity-75 mt-1">{subtitle}</p>
    </div>
  );
}

function RevenueTrendsChart() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["revenue-trends"],
    queryFn: () => api.getRevenueTrends(12),
    staleTime: 1000 * 60 * 10,
  });

  const formatCurrency = (value: number) => {
    if (value >= 1000000) return `$${(value / 1000000).toFixed(1)}M`;
    if (value >= 1000) return `$${(value / 1000).toFixed(0)}K`;
    return `$${value.toFixed(0)}`;
  };

  const formatMonth = (month: string) => {
    const [year, m] = month.split("-");
    const date = new Date(parseInt(year), parseInt(m) - 1);
    return date.toLocaleDateString("en-US", { month: "short", year: "2-digit" });
  };

  if (isLoading) {
    return (
      <Card className="border-gray-200 bg-gradient-to-br from-gray-50 to-slate-50">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-blue-600" />
            Revenue Trends
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-48 flex items-center justify-center">
            <Skeleton className="h-full w-full rounded-lg" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (isError || !data?.data) {
    return (
      <Card className="border-gray-200 bg-gradient-to-br from-gray-50 to-slate-50">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-blue-600" />
            Revenue Trends
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-48 flex items-center justify-center text-muted-foreground">
            Unable to load revenue data
          </div>
        </CardContent>
      </Card>
    );
  }

  const trends = data.data;
  const maxPaid = Math.max(...trends.map(t => t.total_paid), 1);

  return (
    <Card className="border-gray-200 bg-gradient-to-br from-gray-50 to-slate-50">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-blue-600" />
            Revenue Trends
          </CardTitle>
          <Badge variant="outline" className="text-xs">
            Last {trends.length} months
          </Badge>
        </div>
        <p className="text-sm text-muted-foreground">Monthly collections over time</p>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {trends.slice(-6).map((month, idx) => (
            <div key={month.month} className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className="font-medium">{formatMonth(month.month)}</span>
                <span className="text-muted-foreground">
                  {formatCurrency(month.total_paid)} collected
                </span>
              </div>
              <div className="h-6 bg-gray-100 rounded-full overflow-hidden relative">
                <div
                  className="h-full bg-gradient-to-r from-emerald-400 to-emerald-600 rounded-full transition-all duration-500"
                  style={{ width: `${(month.total_paid / maxPaid) * 100}%` }}
                />
                {month.collection_rate > 0 && (
                  <span className="absolute right-2 top-1/2 -translate-y-1/2 text-[10px] font-medium text-gray-600">
                    {month.collection_rate}% rate
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
        <div className="mt-4 pt-3 border-t flex items-center justify-between text-sm">
          <div>
            <span className="text-muted-foreground">Total: </span>
            <span className="font-semibold text-emerald-700">
              {formatCurrency(trends.reduce((sum, t) => sum + t.total_paid, 0))}
            </span>
          </div>
          <div>
            <span className="text-muted-foreground">Avg/month: </span>
            <span className="font-semibold">
              {formatCurrency(trends.reduce((sum, t) => sum + t.total_paid, 0) / trends.length)}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function ClientPaymentBehaviorChart() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["client-payment-behavior"],
    queryFn: () => api.getClientPaymentBehavior(8),
    staleTime: 1000 * 60 * 10,
  });

  const formatCurrency = (value: number) => {
    if (value >= 1000000) return `$${(value / 1000000).toFixed(1)}M`;
    if (value >= 1000) return `$${(value / 1000).toFixed(0)}K`;
    return `$${value.toFixed(0)}`;
  };

  const getSpeedColor = (speed: string) => {
    switch (speed) {
      case "Fast": return "bg-emerald-100 text-emerald-700 border-emerald-200";
      case "Normal": return "bg-blue-100 text-blue-700 border-blue-200";
      case "Slow": return "bg-amber-100 text-amber-700 border-amber-200";
      default: return "bg-gray-100 text-gray-600 border-gray-200";
    }
  };

  const getSpeedIcon = (speed: string) => {
    switch (speed) {
      case "Fast": return <Zap className="h-3 w-3" />;
      case "Normal": return <Clock className="h-3 w-3" />;
      case "Slow": return <Timer className="h-3 w-3" />;
      default: return null;
    }
  };

  if (isLoading) {
    return (
      <Card className="border-gray-200 bg-gradient-to-br from-gray-50 to-slate-50">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <DollarSign className="h-5 w-5 text-green-600" />
            Client Payment Behavior
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <Skeleton key={i} className="h-12 w-full rounded-lg" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (isError || !data?.data) {
    return (
      <Card className="border-gray-200 bg-gradient-to-br from-gray-50 to-slate-50">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <DollarSign className="h-5 w-5 text-green-600" />
            Client Payment Behavior
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-48 flex items-center justify-center text-muted-foreground">
            Unable to load payment data
          </div>
        </CardContent>
      </Card>
    );
  }

  const clients = data.data;

  return (
    <Card className="border-gray-200 bg-gradient-to-br from-gray-50 to-slate-50">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <DollarSign className="h-5 w-5 text-green-600" />
            Client Payment Behavior
          </CardTitle>
          <Badge variant="outline" className="text-xs">
            Top {clients.length} clients
          </Badge>
        </div>
        <p className="text-sm text-muted-foreground">By total payments received</p>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {clients.slice(0, 6).map((client) => (
            <Link
              key={client.project_code}
              href={`/projects/${client.project_code}`}
              className="block"
            >
              <div className="flex items-center justify-between p-2 rounded-lg hover:bg-white/50 transition-colors border border-transparent hover:border-gray-200 cursor-pointer group">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate group-hover:text-blue-600">
                    {client.project_name}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {client.invoice_count} invoices • {formatCurrency(client.total_paid)} paid
                  </p>
                </div>
                <div className="flex items-center gap-2 ml-2">
                  <Badge
                    variant="outline"
                    className={`text-[10px] px-2 py-0.5 flex items-center gap-1 ${getSpeedColor(client.payment_speed)}`}
                  >
                    {getSpeedIcon(client.payment_speed)}
                    {client.avg_days_to_pay ? `${client.avg_days_to_pay}d` : "N/A"}
                  </Badge>
                  <ArrowRight className="h-3 w-3 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
              </div>
            </Link>
          ))}
        </div>
        <div className="mt-3 pt-3 border-t grid grid-cols-3 gap-4 text-center text-xs">
          <div>
            <p className="text-muted-foreground">Fast (&lt;30d)</p>
            <p className="font-semibold text-emerald-700">
              {clients.filter(c => c.payment_speed === "Fast").length}
            </p>
          </div>
          <div>
            <p className="text-muted-foreground">Normal (30-60d)</p>
            <p className="font-semibold text-blue-700">
              {clients.filter(c => c.payment_speed === "Normal").length}
            </p>
          </div>
          <div>
            <p className="text-muted-foreground">Slow (&gt;60d)</p>
            <p className="font-semibold text-amber-700">
              {clients.filter(c => c.payment_speed === "Slow").length}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
