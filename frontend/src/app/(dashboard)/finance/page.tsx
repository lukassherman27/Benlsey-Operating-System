"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { InvoiceAgingWidgetEnhanced } from "@/components/dashboard/invoice-aging-widget-enhanced";
import { PaymentVelocityWidget } from "@/components/dashboard/payment-velocity-widget";
import { InvoiceQuickActions } from "@/components/dashboard/invoice-quick-actions";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { DollarSign, TrendingUp, Calendar, Download, AlertTriangle, Clock } from "lucide-react";

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

      {/* Bottom Section - Additional Charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <PlaceholderChart
          title="Revenue Trends"
          description="Monthly collections over time"
        />
        <PlaceholderChart
          title="Client Payment Behavior"
          description="Top clients by payment speed"
        />
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

function PlaceholderChart({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="rounded-lg border border-gray-200 p-6 bg-gradient-to-br from-gray-50 to-slate-50">
      <h3 className="text-lg font-semibold mb-1">{title}</h3>
      <p className="text-sm text-muted-foreground mb-4">{description}</p>
      <div className="h-48 bg-gray-100 rounded-lg flex items-center justify-center">
        <p className="text-sm text-muted-foreground">Chart coming soon...</p>
      </div>
    </div>
  );
}
