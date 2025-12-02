"use client"

import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { DollarSign } from 'lucide-react'

export function TopOutstandingInvoicesWidget() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['top-outstanding-invoices'],
    queryFn: api.getTopOutstandingInvoices,
    refetchInterval: 5 * 60 * 1000
  })

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Top 10 Outstanding Invoices</CardTitle>
        </CardHeader>
        <CardContent>Loading...</CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Top 10 Outstanding Invoices</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-destructive">Error loading data</p>
        </CardContent>
      </Card>
    )
  }

  const invoices = data?.invoices || []

  const getAgingBadge = (aging: any) => {
    const colorMap: Record<string, string> = {
      green: 'bg-green-100 text-green-800 border-green-300',
      yellow: 'bg-yellow-100 text-yellow-800 border-yellow-300',
      orange: 'bg-orange-100 text-orange-800 border-orange-300',
      red: 'bg-red-100 text-red-800 border-red-300'
    }
    return (
      <Badge className={colorMap[aging.color]} variant="outline">
        {aging.bucket}
      </Badge>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <DollarSign className="h-5 w-5" />
          Top 10 Outstanding Invoices
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {invoices.map((inv: any, i: number) => (
            <div key={i} className="flex items-center justify-between p-3 rounded-lg border hover:bg-gray-50">
              <div className="flex-1 min-w-0">
                <div className="font-semibold text-lg">{inv.project_name}</div>
                <div className="mt-1">
                  <span className="text-sm text-red-600">
                    ${inv.outstanding.toLocaleString()} overdue
                    {inv.days_outstanding && ` • ${inv.days_outstanding} days`}
                  </span>
                </div>
                <div className="text-xs text-gray-400">
                  {inv.project_code} • Invoice {inv.invoice_number}
                </div>
              </div>
              <div className="text-right ml-4">
                <div className="font-bold text-lg">
                  ${(inv.outstanding / 1000).toFixed(1)}K
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
