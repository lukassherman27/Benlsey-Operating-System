"use client"

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { DollarSign } from 'lucide-react'

export function AllInvoicesList() {
  const [selectedProject, setSelectedProject] = useState<string | null>(null)

  const { data: projects } = useQuery({
    queryKey: ['active-projects-list'],
    queryFn: api.getActiveProjects
  })

  const { data, isLoading } = useQuery({
    queryKey: ['all-outstanding-invoices', selectedProject],
    queryFn: () => api.getOutstandingInvoicesFiltered(
      selectedProject ? { project_code: selectedProject } : undefined
    )
  })

  const invoices = data?.invoices || []
  const totalOutstanding = data?.total_outstanding || 0

  const getAgingColor = (color: string) => {
    const colorMap: Record<string, string> = {
      green: 'bg-green-100 text-green-800 border-green-300',
      yellow: 'bg-yellow-100 text-yellow-800 border-yellow-300',
      orange: 'bg-orange-100 text-orange-800 border-orange-300',
      red: 'bg-red-100 text-red-800 border-red-300'
    }
    return colorMap[color] || 'bg-gray-100 text-gray-800'
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <DollarSign className="h-5 w-5" />
            All Outstanding Invoices
          </CardTitle>
          <div className="flex items-center gap-4">
            <div className="text-sm">
              <span className="text-muted-foreground">Total: </span>
              <span className="font-bold">${(totalOutstanding / 1000000).toFixed(2)}M</span>
              <span className="text-muted-foreground ml-2">({invoices.length} invoices)</span>
            </div>
            <Select value={selectedProject || "all"} onValueChange={(val) => setSelectedProject(val === "all" ? null : val)}>
              <SelectTrigger className="w-[250px]">
                <SelectValue placeholder="All projects" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Projects</SelectItem>
                {projects?.data?.map((p: any) => (
                  <SelectItem key={p.project_code} value={p.project_code}>
                    {p.project_code} - {p.project_title?.substring(0, 30)}...
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[600px]">
          <div className="space-y-2">
            {isLoading ? (
              <p className="text-sm text-muted-foreground">Loading invoices...</p>
            ) : invoices.length === 0 ? (
              <p className="text-sm text-muted-foreground">No outstanding invoices found</p>
            ) : (
              invoices.map((inv: any, i: number) => (
                <div key={i} className="flex items-center justify-between p-3 rounded-lg border hover:bg-gray-50">
                  <div className="flex-1 min-w-0 space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold">{inv.invoice_number}</span>
                      <Badge className={getAgingColor(inv.aging_category.color)} variant="outline">
                        {inv.days_outstanding} days
                      </Badge>
                    </div>
                    <div>
                      <span className="text-sm font-medium text-gray-700">{inv.project_code}</span>
                      <span className="text-xs text-muted-foreground block">{inv.project_name}</span>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {inv.phase}
                    </div>
                    <div className="text-xs text-gray-500">
                      Invoice Date: {new Date(inv.invoice_date).toLocaleDateString()}
                    </div>
                  </div>
                  <div className="text-right ml-4 space-y-1">
                    <div className="text-sm text-muted-foreground">Invoiced</div>
                    <div className="font-semibold">
                      ${inv.invoice_amount.toLocaleString()}
                    </div>
                    {inv.payment_amount > 0 && (
                      <>
                        <div className="text-xs text-green-600">
                          Paid: ${inv.payment_amount.toLocaleString()}
                        </div>
                        <div className="text-sm font-bold text-orange-600">
                          Due: ${inv.outstanding.toLocaleString()}
                        </div>
                      </>
                    )}
                    {inv.payment_amount === 0 && (
                      <div className="text-sm font-bold text-red-600">
                        Outstanding: ${inv.outstanding.toLocaleString()}
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  )
}
