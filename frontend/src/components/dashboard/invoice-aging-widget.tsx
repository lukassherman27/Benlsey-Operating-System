"use client"

import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts"
import { DollarSign, AlertTriangle } from "lucide-react"
import { FeedbackButtons } from "@/components/ui/feedback-buttons"

interface InvoiceAgingWidgetProps {
  compact?: boolean
}

export function InvoiceAgingWidget({ compact: _compact = false }: InvoiceAgingWidgetProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["invoice-aging"],
    queryFn: api.getInvoiceAging,
    refetchInterval: 5 * 60 * 1000, // Refresh every 5 minutes
  })

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Invoice Aging</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">Loading aging data...</p>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Invoice Aging</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-destructive">Error loading aging data</p>
        </CardContent>
      </Card>
    )
  }

  // Handle both response formats: data.data.aging and data.aging
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const rawData = data as any
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const breakdown = (rawData?.data?.aging || rawData?.aging || rawData?.data?.aging_breakdown || {}) as any

  // Calculate totals from aging buckets if no summary provided
  const buckets = ['0_to_10', '10_to_30', '30_to_90', 'over_90']
  const totalOutstanding = buckets.reduce((sum, bucket) => sum + (breakdown[bucket]?.amount || 0), 0)
  const totalInvoices = buckets.reduce((sum, bucket) => sum + (breakdown[bucket]?.count || 0), 0)

  // Prepare data for bar chart with Bill's requested buckets
  const chartData = [
    {
      bucket: "0-10 days",
      amount: breakdown["0_to_10"]?.amount || 0,
      count: breakdown["0_to_10"]?.count || 0,
      color: "#22c55e", // green
    },
    {
      bucket: "10-30 days",
      amount: breakdown["10_to_30"]?.amount || 0,
      count: breakdown["10_to_30"]?.count || 0,
      color: "#eab308", // yellow
    },
    {
      bucket: "30-90 days",
      amount: breakdown["30_to_90"]?.amount || 0,
      count: breakdown["30_to_90"]?.count || 0,
      color: "#f97316", // orange
    },
    {
      bucket: "90+ days",
      amount: breakdown["over_90"]?.amount || 0,
      count: breakdown["over_90"]?.count || 0,
      color: "#ef4444", // red
    },
  ]

  // Flag if too many invoices are aging (>30 days)
  const oldInvoices = (breakdown["30_to_90"]?.count || 0) + (breakdown["over_90"]?.count || 0)
  const isAging = oldInvoices > totalInvoices * 0.3 // More than 30% old

  // Calculate dynamic Y-axis scale based on max value (0.5M increments)
  const maxAmount = Math.max(...chartData.map(d => d.amount), 0)
  const scaleMax = Math.max(Math.ceil(maxAmount / 500000) * 500000, 500000) // At least 0.5M
  const tickCount = Math.min(Math.ceil(scaleMax / 500000) + 1, 6) // Max 6 ticks
  const dynamicTicks = Array.from({ length: tickCount }, (_, i) => i * 500000)

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <DollarSign className="h-5 w-5" />
            Invoice Aging
          </CardTitle>
          <div className="flex items-center gap-2">
            {isAging && (
              <Badge variant="destructive" className="gap-1">
                <AlertTriangle className="h-3 w-3" />
                Aging
              </Badge>
            )}
            <FeedbackButtons
              featureType="kpi_invoice_aging"
              featureId="dashboard"
              currentValue={totalOutstanding}
              compact={true}
            />
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Summary */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-muted-foreground">Total Outstanding</p>
            <p className="text-2xl font-bold">
              ${(totalOutstanding / 1000000).toFixed(2)}M
            </p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Total Invoices</p>
            <p className="text-2xl font-bold">{totalInvoices}</p>
          </div>
        </div>

        {/* Bar Chart */}
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="bucket"
              tick={{ fontSize: 12 }}
              angle={-15}
              textAnchor="end"
              height={60}
            />
            <YAxis
              domain={[0, scaleMax]}
              ticks={dynamicTicks}
              tick={{ fontSize: 12 }}
              tickFormatter={(value) => `$${(value / 1000000).toFixed(1)}M`}
            />
            <Tooltip
              formatter={(value: number) => [`$${value.toLocaleString()}`, "Amount"]}
              labelFormatter={(label) => `Aging: ${label}`}
            />
            <Bar dataKey="amount" radius={[8, 8, 0, 0]}>
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>

        {/* Breakdown Table */}
        <div className="space-y-2">
          {chartData.map((bucket, i) => (
            <div
              key={i}
              className="flex items-center justify-between p-2 rounded-lg hover:bg-gray-50"
              style={{ borderLeft: `4px solid ${bucket.color}` }}
            >
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">{bucket.bucket}</span>
                <Badge variant="outline" className="text-xs">
                  {bucket.count} invoices
                </Badge>
              </div>
              <span className="text-sm font-semibold">
                ${(bucket.amount / 1000000).toFixed(2)}M
              </span>
            </div>
          ))}
        </div>

        {/* Warning for 90+ days */}
        {breakdown["over_90"]?.count > 0 && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-start gap-2">
              <AlertTriangle className="h-4 w-4 text-red-600 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-red-900">
                  {breakdown["over_90"].count} invoice
                  {breakdown["over_90"].count > 1 ? "s" : ""} overdue 90+ days
                </p>
                <p className="text-xs text-red-700 mt-1">
                  Total: ${(breakdown["over_90"].amount / 1000000).toFixed(2)}M - Follow up required
                </p>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
