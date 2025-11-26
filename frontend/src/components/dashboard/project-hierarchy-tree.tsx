"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { ProjectHierarchy, DisciplineBreakdown, ProjectPhase, PhaseInvoice } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { ChevronRight, ChevronDown, DollarSign, FileText, CheckCircle, Clock } from "lucide-react";
import { useState } from "react";

interface ProjectHierarchyTreeProps {
  projectCode: string;
}

function formatCurrency(amount: number | null | undefined): string {
  if (amount === null || amount === undefined) return "$0";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
}

function formatDate(date: string | null | undefined): string {
  if (!date) return "N/A";
  return new Date(date).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function InvoiceBadge({ invoice }: { invoice: PhaseInvoice }) {
  const isPaid = invoice.status === "paid";
  const isPartial = invoice.payment_amount > 0 && invoice.payment_amount < invoice.invoice_amount;

  return (
    <div className="flex items-center gap-2 p-2 rounded-md bg-muted/50 text-sm">
      {isPaid ? (
        <CheckCircle className="h-4 w-4 text-green-600" />
      ) : isPartial ? (
        <Clock className="h-4 w-4 text-yellow-600" />
      ) : (
        <Clock className="h-4 w-4 text-gray-400" />
      )}
      <div className="flex-1">
        <div className="font-medium">{invoice.invoice_number}</div>
        <div className="text-xs text-muted-foreground">
          {formatDate(invoice.invoice_date)}
        </div>
      </div>
      <div className="text-right">
        <div className="font-medium">{formatCurrency(invoice.invoice_amount)}</div>
        {invoice.payment_amount > 0 && (
          <div className="text-xs text-green-600">
            Paid: {formatCurrency(invoice.payment_amount)}
          </div>
        )}
      </div>
      <Badge
        variant={isPaid ? "default" : isPartial ? "secondary" : "outline"}
        className={
          isPaid
            ? "bg-green-100 text-green-800"
            : isPartial
            ? "bg-yellow-100 text-yellow-800"
            : ""
        }
      >
        {invoice.status}
      </Badge>
    </div>
  );
}

function PhaseRow({ phase }: { phase: ProjectPhase }) {
  const [isOpen, setIsOpen] = useState(false);
  const hasInvoices = phase.invoices && phase.invoices.length > 0;
  const percentComplete = phase.phase_fee > 0
    ? Math.round((phase.total_invoiced / phase.phase_fee) * 100)
    : 0;

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <CollapsibleTrigger className="w-full">
        <div className="flex items-center gap-2 p-3 hover:bg-muted/50 rounded-md transition-colors">
          <div className="text-muted-foreground">
            {hasInvoices ? (
              isOpen ? (
                <ChevronDown className="h-4 w-4" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              )
            ) : (
              <div className="w-4" />
            )}
          </div>
          <FileText className="h-4 w-4 text-blue-600" />
          <div className="flex-1 text-left">
            <div className="font-medium text-sm">{phase.phase}</div>
            <div className="flex items-center gap-4 mt-1">
              <div className="text-xs text-muted-foreground">
                Fee: {formatCurrency(phase.phase_fee)}
              </div>
              <div className="flex-1 max-w-xs">
                <Progress value={percentComplete} className="h-2" />
              </div>
              <div className="text-xs font-medium">{percentComplete}%</div>
            </div>
          </div>
          <div className="text-right">
            <div className="text-sm font-medium text-green-600">
              {formatCurrency(phase.total_invoiced)}
            </div>
            <div className="text-xs text-muted-foreground">
              Remaining: {formatCurrency(phase.remaining)}
            </div>
          </div>
        </div>
      </CollapsibleTrigger>
      {hasInvoices && (
        <CollapsibleContent>
          <div className="ml-10 mt-2 space-y-2">
            {phase.invoices.map((invoice) => (
              <InvoiceBadge key={invoice.invoice_id} invoice={invoice} />
            ))}
          </div>
        </CollapsibleContent>
      )}
    </Collapsible>
  );
}

function DisciplineSection({
  name,
  breakdown,
}: {
  name: string;
  breakdown: DisciplineBreakdown;
}) {
  const [isOpen, setIsOpen] = useState(true);
  const percentComplete = breakdown.total_fee > 0
    ? Math.round((breakdown.total_invoiced / breakdown.total_fee) * 100)
    : 0;

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <CollapsibleTrigger className="w-full">
        <div className="flex items-center gap-3 p-4 bg-muted/30 hover:bg-muted/50 rounded-lg transition-colors">
          {isOpen ? (
            <ChevronDown className="h-5 w-5 text-muted-foreground" />
          ) : (
            <ChevronRight className="h-5 w-5 text-muted-foreground" />
          )}
          <DollarSign className="h-5 w-5 text-primary" />
          <div className="flex-1 text-left">
            <div className="font-semibold text-base">{name}</div>
            <div className="flex items-center gap-4 mt-1">
              <div className="text-sm text-muted-foreground">
                Total: {formatCurrency(breakdown.total_fee)}
              </div>
              <div className="flex-1 max-w-md">
                <Progress value={percentComplete} className="h-2.5" />
              </div>
              <div className="text-sm font-medium">{percentComplete}% invoiced</div>
            </div>
          </div>
          <div className="text-right">
            <div className="text-base font-semibold text-green-600">
              {formatCurrency(breakdown.total_invoiced)}
            </div>
            <div className="text-sm text-muted-foreground">
              {breakdown.phases.length} phases
            </div>
          </div>
        </div>
      </CollapsibleTrigger>
      <CollapsibleContent>
        <div className="ml-6 mt-2 space-y-1">
          {breakdown.phases.map((phase) => (
            <PhaseRow key={phase.breakdown_id} phase={phase} />
          ))}
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
}

export function ProjectHierarchyTree({ projectCode }: ProjectHierarchyTreeProps) {
  const { data, isLoading, error } = useQuery<ProjectHierarchy>({
    queryKey: ["projectHierarchy", projectCode],
    queryFn: () => api.getProjectHierarchy(projectCode),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Financial Breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8 text-muted-foreground">
            Loading hierarchy...
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error || !data?.success) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Financial Breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8 text-red-600">
            Failed to load financial hierarchy
          </div>
        </CardContent>
      </Card>
    );
  }

  const totalPercentInvoiced = data.total_contract_value > 0
    ? Math.round((data.total_invoiced / data.total_contract_value) * 100)
    : 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Financial Breakdown</CardTitle>
        <div className="mt-2 text-sm text-muted-foreground">
          {data.project_name || data.project_code}
        </div>
      </CardHeader>
      <CardContent>
        {/* Project Summary */}
        <div className="mb-6 p-4 bg-primary/5 rounded-lg border border-primary/20">
          <div className="flex items-center justify-between mb-3">
            <div>
              <div className="text-sm text-muted-foreground">Total Contract Value</div>
              <div className="text-2xl font-bold">
                {formatCurrency(data.total_contract_value)}
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm text-muted-foreground">Invoiced</div>
              <div className="text-xl font-semibold text-green-600">
                {formatCurrency(data.total_invoiced)}
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm text-muted-foreground">Paid</div>
              <div className="text-xl font-semibold text-blue-600">
                {formatCurrency(data.total_paid)}
              </div>
            </div>
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Progress</span>
              <span className="font-medium">{totalPercentInvoiced}% invoiced</span>
            </div>
            <Progress value={totalPercentInvoiced} className="h-3" />
          </div>
        </div>

        {/* Discipline Breakdown */}
        <div className="space-y-3">
          {Object.entries(data.disciplines).map(([name, breakdown]) => (
            <DisciplineSection key={name} name={name} breakdown={breakdown} />
          ))}
        </div>

        {Object.keys(data.disciplines).length === 0 && (
          <div className="text-center py-8 text-muted-foreground">
            No financial breakdown available for this project
          </div>
        )}
      </CardContent>
    </Card>
  );
}
