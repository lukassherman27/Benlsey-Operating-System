"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TrendingDown, TrendingUp, Zap, Clock, Loader2 } from "lucide-react";
import { formatCurrency } from "@/lib/utils";
import { useQuery } from "@tanstack/react-query";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ClientPaymentData {
  project_code: string;
  project_name: string;
  invoice_count: number;
  total_invoiced: number;
  total_paid: number;
  outstanding: number;
  avg_days_to_pay: number | null;
  payment_speed: "Fast" | "Normal" | "Slow" | "Unknown";
}

interface RevenueTrendData {
  month: string;
  avg_days_to_pay: number | null;
}

/**
 * Payment Velocity Widget
 * Shows how quickly invoices are getting paid and trends
 */
export function PaymentVelocityWidget() {
  // Fetch client payment behavior data
  const { data: clientData, isLoading: clientLoading } = useQuery({
    queryKey: ["client-payment-behavior"],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/api/invoices/client-payment-behavior?limit=10`);
      if (!res.ok) throw new Error("Failed to fetch client payment behavior");
      return res.json();
    },
  });

  // Fetch revenue trends for average days to pay over time
  const { data: trendsData, isLoading: trendsLoading } = useQuery({
    queryKey: ["revenue-trends"],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/api/invoices/revenue-trends?months=6`);
      if (!res.ok) throw new Error("Failed to fetch revenue trends");
      return res.json();
    },
  });

  const isLoading = clientLoading || trendsLoading;

  // Calculate velocity metrics from real data
  const clients: ClientPaymentData[] = clientData?.data || [];
  const trends: RevenueTrendData[] = trendsData?.data || [];

  // Calculate average days to pay from recent trends
  const recentTrends = trends.filter((t) => t.avg_days_to_pay != null);
  const currentAvg = recentTrends.length > 0
    ? Math.round(recentTrends[recentTrends.length - 1]?.avg_days_to_pay || 0)
    : 0;
  const previousAvg = recentTrends.length > 1
    ? Math.round(recentTrends[recentTrends.length - 2]?.avg_days_to_pay || 0)
    : currentAvg;

  // Split clients into fast and slow payers
  const fastestPayingClients = clients
    .filter((c) => c.avg_days_to_pay != null && c.avg_days_to_pay > 0)
    .sort((a, b) => (a.avg_days_to_pay || 999) - (b.avg_days_to_pay || 999))
    .slice(0, 3)
    .map((c) => ({
      name: c.project_name || c.project_code,
      avgDays: Math.round(c.avg_days_to_pay || 0),
      totalPaid: c.total_paid,
    }));

  const slowestPayingClients = clients
    .filter((c) => c.outstanding > 0)
    .sort((a, b) => (b.avg_days_to_pay || 0) - (a.avg_days_to_pay || 0))
    .slice(0, 2)
    .map((c) => ({
      name: c.project_name || c.project_code,
      avgDays: Math.round(c.avg_days_to_pay || 0),
      outstanding: c.outstanding,
    }));

  const trend = currentAvg - previousAvg;
  const trendLabel = trend <= 0 ? "Faster" : "Slower";
  const TrendIcon = trend <= 0 ? TrendingDown : TrendingUp;

  if (isLoading) {
    return (
      <Card className="overflow-hidden">
        <CardHeader className="bg-gradient-to-r from-purple-50 to-pink-50 border-b">
          <CardTitle className="text-lg flex items-center gap-2">
            <div className="p-2 bg-white rounded-lg shadow-sm">
              <Zap className="h-4 w-4 text-purple-600" />
            </div>
            Payment Velocity
          </CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-purple-600" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="overflow-hidden">
      <CardHeader className="bg-gradient-to-r from-purple-50 to-pink-50 border-b">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg flex items-center gap-2">
              <div className="p-2 bg-white rounded-lg shadow-sm">
                <Zap className="h-4 w-4 text-purple-600" />
              </div>
              Payment Velocity
            </CardTitle>
            <p className="text-xs text-muted-foreground mt-1">
              How quickly invoices are getting paid
            </p>
          </div>
          {currentAvg > 0 && (
            <Badge
              variant={trend <= 0 ? "default" : "destructive"}
              className="gap-1"
            >
              <TrendIcon className="h-3 w-3" />
              {trendLabel}
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-6 pt-6">
        {/* Average Days to Pay - Hero Stat */}
        <div className="relative overflow-hidden rounded-xl bg-gradient-to-br from-purple-500 to-pink-600 text-white p-6 shadow-lg">
          <div className="relative z-10">
            <p className="text-purple-100 text-sm font-medium mb-1">
              Average Days to Payment
            </p>
            <div className="flex items-baseline gap-4">
              <p className="text-5xl font-bold">{currentAvg || "—"}</p>
              {previousAvg > 0 && currentAvg > 0 && (
                <div className="flex items-center gap-1 text-sm">
                  <TrendIcon className={`h-4 w-4 ${trend <= 0 ? 'text-green-300' : 'text-red-300'}`} />
                  <span className="font-semibold">
                    {Math.abs(trend)} days vs last period
                  </span>
                </div>
              )}
            </div>
            <p className="text-purple-200 text-sm mt-2">
              {trend <= 0 ? "Collections are improving!" : "Collections need attention"}
            </p>
          </div>

          {/* Decorative elements */}
          <div className="absolute top-0 right-0 -mr-12 -mt-12 h-48 w-48 rounded-full bg-white/10 blur-3xl" />
          <Clock className="absolute bottom-4 right-4 h-24 w-24 text-white/10" />
        </div>

        {/* Fastest Paying Clients */}
        {fastestPayingClients.length > 0 && (
          <section className="space-y-3">
            <h3 className="text-sm font-semibold flex items-center gap-2">
              <div className="p-1.5 bg-green-100 rounded-md">
                <TrendingUp className="h-4 w-4 text-green-600" />
              </div>
              Fastest Paying Clients
            </h3>
            <div className="space-y-2">
              {fastestPayingClients.map((client, idx) => (
                <div
                  key={idx}
                  className="flex justify-between items-center p-3 bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-lg hover:shadow-md transition-all duration-200"
                >
                  <div>
                    <p className="font-semibold text-sm">{client.name}</p>
                    <p className="text-xs text-muted-foreground">
                      Avg {client.avgDays} days • {formatCurrency(client.totalPaid)} paid
                    </p>
                  </div>
                  <Badge variant="outline" className="bg-green-100 text-green-700 border-green-300">
                    {client.avgDays}d
                  </Badge>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Slowest Paying Clients */}
        {slowestPayingClients.length > 0 && (
          <section className="space-y-3">
            <h3 className="text-sm font-semibold flex items-center gap-2">
              <div className="p-1.5 bg-orange-100 rounded-md">
                <Clock className="h-4 w-4 text-orange-600" />
              </div>
              Needs Follow-up
            </h3>
            <div className="space-y-2">
              {slowestPayingClients.map((client, idx) => (
                <div
                  key={idx}
                  className="flex justify-between items-center p-3 bg-gradient-to-r from-orange-50 to-red-50 border border-orange-200 rounded-lg hover:shadow-md transition-all duration-200"
                >
                  <div>
                    <p className="font-semibold text-sm">{client.name}</p>
                    <p className="text-xs text-muted-foreground">
                      Avg {client.avgDays} days • {formatCurrency(client.outstanding)} outstanding
                    </p>
                  </div>
                  <Badge variant="outline" className="bg-red-100 text-red-700 border-red-300">
                    {client.avgDays}d
                  </Badge>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Insights Box */}
        {currentAvg > 0 && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <Zap className="h-5 w-5 text-blue-600 mt-0.5" />
              <div>
                <p className="font-semibold text-blue-900 text-sm">Quick Insight</p>
                <p className="text-sm text-blue-700 mt-1">
                  {trend <= 0
                    ? `Your average collection time improved by ${Math.abs(trend)} days this period. Focus on the slow-paying clients to improve cash flow further.`
                    : `Collection time increased by ${Math.abs(trend)} days. Consider following up with clients who have outstanding balances.`
                  }
                </p>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
