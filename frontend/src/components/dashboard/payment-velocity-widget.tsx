"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TrendingDown, TrendingUp, Zap, Clock } from "lucide-react";
import { formatCurrency } from "@/lib/utils";

/**
 * Payment Velocity Widget
 * Shows how quickly invoices are getting paid and trends
 */
export function PaymentVelocityWidget() {
  // TODO: Hook this up to real API endpoint
  // For now, using mock data to show the design
  const velocityData = {
    averageDaysToPay: 42,
    previousPeriodAverage: 47,
    fastestPayingClients: [
      { name: "Ultra Luxury Beach Resort", avgDays: 18, totalPaid: 850000 },
      { name: "Mandarin Oriental Bali", avgDays: 22, totalPaid: 720000 },
      { name: "Tel Aviv High Rise", avgDays: 28, totalPaid: 560000 },
    ],
    slowestPayingClients: [
      { name: "43 Dang Thai Mai Project", avgDays: 82, outstanding: 789525 },
      { name: "Hanoi Development Co", avgDays: 67, outstanding: 450000 },
    ],
    paymentTrend: "improving", // improving, declining, stable
  };

  const trend = velocityData.averageDaysToPay - velocityData.previousPeriodAverage;
  const trendLabel = trend < 0 ? "Faster" : "Slower";
  const TrendIcon = trend < 0 ? TrendingDown : TrendingUp;
  const trendColor = trend < 0 ? "text-green-600" : "text-red-600";

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
          <Badge
            variant={trend < 0 ? "default" : "destructive"}
            className="gap-1"
          >
            <TrendIcon className="h-3 w-3" />
            {trendLabel}
          </Badge>
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
              <p className="text-5xl font-bold">{velocityData.averageDaysToPay}</p>
              <div className="flex items-center gap-1 text-sm">
                <TrendIcon className={`h-4 w-4 ${trend < 0 ? 'text-green-300' : 'text-red-300'}`} />
                <span className="font-semibold">
                  {Math.abs(trend)} days vs last period
                </span>
              </div>
            </div>
            <p className="text-purple-200 text-sm mt-2">
              {trend < 0 ? "Collections are improving!" : "Collections need attention"}
            </p>
          </div>

          {/* Decorative elements */}
          <div className="absolute top-0 right-0 -mr-12 -mt-12 h-48 w-48 rounded-full bg-white/10 blur-3xl" />
          <Clock className="absolute bottom-4 right-4 h-24 w-24 text-white/10" />
        </div>

        {/* Fastest Paying Clients */}
        <section className="space-y-3">
          <h3 className="text-sm font-semibold flex items-center gap-2">
            <div className="p-1.5 bg-green-100 rounded-md">
              <TrendingUp className="h-4 w-4 text-green-600" />
            </div>
            Fastest Paying Clients
          </h3>
          <div className="space-y-2">
            {velocityData.fastestPayingClients.map((client, idx) => (
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

        {/* Slowest Paying Clients */}
        <section className="space-y-3">
          <h3 className="text-sm font-semibold flex items-center gap-2">
            <div className="p-1.5 bg-orange-100 rounded-md">
              <Clock className="h-4 w-4 text-orange-600" />
            </div>
            Needs Follow-up
          </h3>
          <div className="space-y-2">
            {velocityData.slowestPayingClients.map((client, idx) => (
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

        {/* Insights Box */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <Zap className="h-5 w-5 text-blue-600 mt-0.5" />
            <div>
              <p className="font-semibold text-blue-900 text-sm">Quick Insight</p>
              <p className="text-sm text-blue-700 mt-1">
                Your average collection time improved by {Math.abs(trend)} days this period.
                Focus on the slow-paying clients to improve cash flow further.
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
