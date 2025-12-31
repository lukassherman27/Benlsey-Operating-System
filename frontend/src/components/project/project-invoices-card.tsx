"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Receipt, ChevronRight, AlertCircle, CheckCircle, Clock } from "lucide-react";
import { format, formatDistanceToNow, isPast, parseISO } from "date-fns";
import { ds } from "@/lib/design-system";
import { cn } from "@/lib/utils";

interface ProjectInvoicesCardProps {
  projectCode: string;
  limit?: number;
  onViewAll?: () => void;
}

interface Invoice {
  invoice_id: number;
  invoice_number: string;
  invoice_amount: number;
  payment_amount?: number;
  status: string;
  invoice_date: string;
  due_date?: string;
  discipline?: string;
  phase?: string;
}

const formatCurrency = (value?: number | null) => {
  if (value == null) return "$0";
  return `$${value.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
};

const getStatusBadge = (invoice: Invoice) => {
  const status = invoice.status?.toLowerCase() || "";
  const isPaid = status === "paid" || (invoice.payment_amount && invoice.payment_amount >= invoice.invoice_amount);
  const isOverdue = invoice.due_date && isPast(parseISO(invoice.due_date)) && !isPaid;

  if (isPaid) {
    return (
      <Badge className="bg-emerald-100 text-emerald-700 border-emerald-200 text-xs gap-1">
        <CheckCircle className="h-3 w-3" />
        Paid
      </Badge>
    );
  }

  if (isOverdue) {
    return (
      <Badge className="bg-red-100 text-red-700 border-red-200 text-xs gap-1">
        <AlertCircle className="h-3 w-3" />
        Overdue
      </Badge>
    );
  }

  return (
    <Badge className="bg-amber-100 text-amber-700 border-amber-200 text-xs gap-1">
      <Clock className="h-3 w-3" />
      Pending
    </Badge>
  );
};

export function ProjectInvoicesCard({ projectCode, limit = 5, onViewAll }: ProjectInvoicesCardProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["project", projectCode, "invoices"],
    queryFn: () => api.getInvoicesByProject(projectCode),
    staleTime: 1000 * 60 * 5,
  });

  const allInvoices: Invoice[] = (data?.invoices ?? []) as Invoice[];
  const invoices = allInvoices.slice(0, limit);
  const totalCount = allInvoices.length;

  // Calculate summary stats
  const totalInvoiced = allInvoices.reduce((sum, inv) => sum + (inv.invoice_amount || 0), 0);
  const totalPaid = allInvoices.reduce((sum, inv) => sum + (inv.payment_amount || 0), 0);
  const overdueCount = allInvoices.filter(inv => {
    const isPaid = inv.status?.toLowerCase() === "paid" || (inv.payment_amount && inv.payment_amount >= inv.invoice_amount);
    return inv.due_date && isPast(parseISO(inv.due_date)) && !isPaid;
  }).length;

  const formatDate = (dateStr: string | null | undefined) => {
    if (!dateStr) return "";
    try {
      const date = parseISO(dateStr);
      return format(date, "MMM d, yyyy");
    } catch {
      return dateStr;
    }
  };

  if (isLoading) {
    return (
      <Card className={ds.cards.default}>
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-base">
            <Receipt className="h-4 w-4 text-emerald-600" />
            Invoices
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-12 bg-slate-100 rounded-lg" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error || invoices.length === 0) {
    return (
      <Card className={ds.cards.default}>
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-base">
            <Receipt className="h-4 w-4 text-emerald-600" />
            Invoices
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-slate-500">No invoices found for this project.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={ds.cards.default}>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center justify-between text-base">
          <div className="flex items-center gap-2">
            <Receipt className="h-4 w-4 text-emerald-600" />
            Invoices
            <Badge variant="secondary">{totalCount}</Badge>
            {overdueCount > 0 && (
              <Badge className="bg-red-100 text-red-700 border-red-200 text-xs">
                {overdueCount} overdue
              </Badge>
            )}
          </div>
          {onViewAll && (
            <Button variant="ghost" size="sm" className="text-xs gap-1" onClick={onViewAll}>
              View All
              <ChevronRight className="h-3 w-3" />
            </Button>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        {/* Summary row */}
        <div className="flex gap-4 mb-3 p-2 bg-slate-50 rounded-lg text-xs">
          <div>
            <span className="text-slate-500">Invoiced:</span>
            <span className="ml-1 font-medium">{formatCurrency(totalInvoiced)}</span>
          </div>
          <div>
            <span className="text-slate-500">Collected:</span>
            <span className="ml-1 font-medium text-emerald-600">{formatCurrency(totalPaid)}</span>
          </div>
          <div>
            <span className="text-slate-500">Outstanding:</span>
            <span className={cn(
              "ml-1 font-medium",
              (totalInvoiced - totalPaid) > 0 ? "text-amber-600" : "text-slate-600"
            )}>
              {formatCurrency(Math.max(0, totalInvoiced - totalPaid))}
            </span>
          </div>
        </div>

        {/* Invoice list */}
        <div className="space-y-1">
          {invoices.map((invoice) => (
            <div
              key={invoice.invoice_id}
              className="p-2 rounded-lg hover:bg-slate-50 transition-colors"
            >
              <div className="flex items-center justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-sm text-slate-900">
                      {invoice.invoice_number || `INV-${invoice.invoice_id}`}
                    </span>
                    {getStatusBadge(invoice)}
                  </div>
                  <div className="flex items-center gap-2 text-xs text-slate-500 mt-0.5">
                    <span>{formatDate(invoice.invoice_date)}</span>
                    {invoice.discipline && (
                      <>
                        <span className="text-slate-300">|</span>
                        <span>{invoice.discipline}</span>
                      </>
                    )}
                    {invoice.phase && (
                      <>
                        <span className="text-slate-300">|</span>
                        <span>{invoice.phase}</span>
                      </>
                    )}
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-semibold text-sm">{formatCurrency(invoice.invoice_amount)}</p>
                  {invoice.payment_amount && invoice.payment_amount > 0 && invoice.payment_amount < invoice.invoice_amount && (
                    <p className="text-xs text-emerald-600">
                      {formatCurrency(invoice.payment_amount)} paid
                    </p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        {totalCount > limit && onViewAll && (
          <div className="mt-3 pt-3 border-t">
            <Button variant="outline" size="sm" className="w-full text-xs" onClick={onViewAll}>
              View all {totalCount} invoices
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
