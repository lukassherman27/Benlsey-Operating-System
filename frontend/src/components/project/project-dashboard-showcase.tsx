"use client";

/**
 * PROJECT DASHBOARD SHOWCASE
 *
 * This component shows what a fully-populated project dashboard should look like.
 * Uses a mix of real data where available and placeholder data where missing.
 *
 * ⚠️ PLACEHOLDER DATA: Some sections contain placeholder data marked with
 * "// PLACEHOLDER" comments. Replace with real API data when available.
 */

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  Building2,
  Users,
  Calendar,
  DollarSign,
  Clock,
  CheckCircle2,
  AlertTriangle,
  TrendingUp,
  FileText,
  Mail,
  MessageSquare,
  ArrowRight,
  ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/utils";
import Link from "next/link";

interface ProjectDashboardShowcaseProps {
  projectCode: string;
  className?: string;
}

// PLACEHOLDER DATA - Replace with real API calls
const SHOWCASE_DATA = {
  // Project Info
  project: {
    code: "25 BK-033",
    name: "Ritz-Carlton Reserve Nusa Dua",
    client: "PT Luxury Hotels Indonesia",
    pm: "Aye Myat Mon",
    status: "Active",
    phase: "Design Development",
    health: 78,
    healthStatus: "at_risk" as const,
  },

  // Financial Summary
  finances: {
    contractValue: 3380000,
    invoiced: 1350000,
    collected: 945000,
    outstanding: 405000,
    remainingToInvoice: 2030000,
    overdueAmount: 135000,
    overdueCount: 2,
  },

  // Phase Progress - REAL DATA from project_fee_breakdown
  phases: [
    { name: "Mobilization", status: "completed", pct: 100 },
    { name: "Concept", status: "completed", pct: 100 },
    { name: "SD", status: "in_progress", pct: 40 },
    { name: "DD", status: "pending", pct: 0 },
    { name: "CD", status: "pending", pct: 0 },
    { name: "CA", status: "pending", pct: 0 },
  ],

  // Team - PLACEHOLDER (real data needs API fix)
  team: [
    { name: "Aye Myat Mon", role: "Project Manager", department: "PM", avatar: "AM" },
    { name: "Charn Panyawattana", role: "Lead Designer", department: "Landscape", avatar: "CP" },
    { name: "Priaw Luangkham", role: "Senior Architect", department: "Architecture", avatar: "PL" },
    { name: "Rahadi Putra", role: "Interior Lead", department: "Interior", avatar: "RP" },
    { name: "Teay Saechao", role: "Designer", department: "Interior", avatar: "TS" },
  ],

  // Upcoming Deadlines - PLACEHOLDER
  deadlines: [
    { name: "SD Package Submission", date: "Jan 15, 2025", daysLeft: 20, status: "upcoming" },
    { name: "DD 50% Review", date: "Feb 28, 2025", daysLeft: 64, status: "upcoming" },
    { name: "Client Site Visit", date: "Jan 8, 2025", daysLeft: 13, status: "upcoming" },
  ],

  // Overdue Invoices - PLACEHOLDER (real data exists)
  overdueInvoices: [
    { number: "INV-2024-089", amount: 67500, daysPast: 45, phase: "Concept" },
    { number: "INV-2024-102", amount: 67500, daysPast: 23, phase: "SD" },
  ],

  // Recent Activity - Mix of real and placeholder
  recentActivity: [
    { type: "invoice_paid", title: "Invoice INV-2024-078 paid", date: "Dec 20", amount: 270000 },
    { type: "meeting", title: "DD Kickoff Meeting", date: "Dec 18", participants: 8 },
    { type: "deliverable", title: "SD Package submitted", date: "Dec 15", status: "completed" },
    { type: "invoice_sent", title: "Invoice INV-2024-102 issued", date: "Dec 3", amount: 67500 },
    { type: "email", title: "Client feedback on SD concepts", date: "Dec 1", important: true },
  ],
};

const formatCurrency = (value: number) => {
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `$${Math.round(value / 1_000)}K`;
  return `$${value.toLocaleString()}`;
};

export function ProjectDashboardShowcase({ projectCode, className }: ProjectDashboardShowcaseProps) {
  const data = SHOWCASE_DATA;

  return (
    <div className={cn("space-y-6", className)}>
      {/* Placeholder Notice */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 flex items-center gap-2">
        <AlertTriangle className="h-4 w-4 text-amber-600 flex-shrink-0" />
        <p className="text-sm text-amber-800">
          <strong>Demo Mode:</strong> Some data is placeholder.
          <span className="text-amber-600 ml-1">Real data will replace these as APIs are fixed.</span>
        </p>
      </div>

      {/* Top Row: Key Metrics */}
      <div className="grid gap-4 md:grid-cols-4">
        {/* Contract Value */}
        <Card className="bg-gradient-to-br from-slate-50 to-slate-100 border-slate-200">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wide">Contract Value</p>
                <p className="text-2xl font-bold text-slate-900">{formatCurrency(data.finances.contractValue)}</p>
              </div>
              <DollarSign className="h-8 w-8 text-slate-400" />
            </div>
          </CardContent>
        </Card>

        {/* Collected */}
        <Card className="bg-gradient-to-br from-emerald-50 to-emerald-100 border-emerald-200">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-emerald-600 uppercase tracking-wide">Collected</p>
                <p className="text-2xl font-bold text-emerald-900">{formatCurrency(data.finances.collected)}</p>
                <p className="text-xs text-emerald-600 mt-1">
                  {Math.round((data.finances.collected / data.finances.contractValue) * 100)}% of contract
                </p>
              </div>
              <CheckCircle2 className="h-8 w-8 text-emerald-400" />
            </div>
          </CardContent>
        </Card>

        {/* Outstanding */}
        <Card className="bg-gradient-to-br from-amber-50 to-amber-100 border-amber-200">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-amber-600 uppercase tracking-wide">Outstanding</p>
                <p className="text-2xl font-bold text-amber-900">{formatCurrency(data.finances.outstanding)}</p>
                <p className="text-xs text-amber-600 mt-1">
                  {data.finances.overdueCount} invoices overdue
                </p>
              </div>
              <Clock className="h-8 w-8 text-amber-400" />
            </div>
          </CardContent>
        </Card>

        {/* Health Score */}
        <Card className={cn(
          "border-2",
          (data.project.healthStatus as string) === "healthy" && "bg-emerald-50 border-emerald-200",
          (data.project.healthStatus as string) === "at_risk" && "bg-amber-50 border-amber-200",
          (data.project.healthStatus as string) === "critical" && "bg-red-50 border-red-200"
        )}>
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs uppercase tracking-wide text-slate-500">Project Health</p>
                <p className="text-3xl font-bold">{data.project.health}</p>
                <Badge variant="outline" className={cn(
                  "mt-1",
                  data.project.healthStatus === "at_risk" && "bg-amber-100 text-amber-700 border-amber-300"
                )}>
                  At Risk
                </Badge>
              </div>
              <TrendingUp className={cn(
                "h-8 w-8",
                data.project.healthStatus === "at_risk" && "text-amber-400"
              )} />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Phase Progress Bar */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base flex items-center gap-2">
            <Building2 className="h-4 w-4 text-blue-600" />
            Phase Progress
            <Badge variant="secondary" className="ml-2">{data.project.phase}</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            {data.phases.map((phase, idx) => (
              <div key={phase.name} className="flex-1">
                <div
                  className={cn(
                    "h-10 rounded-md flex items-center justify-center text-xs font-medium transition-all",
                    phase.status === "completed" && "bg-emerald-500 text-white",
                    phase.status === "in_progress" && "bg-amber-400 text-amber-900",
                    phase.status === "pending" && "bg-slate-100 text-slate-400"
                  )}
                >
                  {phase.name}
                </div>
                {phase.status !== "pending" && (
                  <p className={cn(
                    "text-xs text-center mt-1",
                    phase.status === "completed" && "text-emerald-600",
                    phase.status === "in_progress" && "text-amber-600"
                  )}>
                    {phase.pct}%
                  </p>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Two Column Layout */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Left Column */}
        <div className="space-y-6">
          {/* Team */}
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base flex items-center gap-2">
                  <Users className="h-4 w-4 text-purple-600" />
                  Project Team
                </CardTitle>
                <Badge variant="secondary">{data.team.length} members</Badge>
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="space-y-2">
                {data.team.map((member) => (
                  <div
                    key={member.name}
                    className="flex items-center gap-3 p-2 rounded-lg hover:bg-slate-50 transition-colors"
                  >
                    <div className="h-9 w-9 rounded-full bg-slate-200 flex items-center justify-center text-xs font-semibold text-slate-600">
                      {member.avatar}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-sm text-slate-900 truncate">{member.name}</p>
                      <p className="text-xs text-slate-500">{member.role}</p>
                    </div>
                    <Badge variant="outline" className="text-xs">
                      {member.department}
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Overdue Invoices */}
          {data.overdueInvoices.length > 0 && (
            <Card className="border-red-200 bg-red-50/50">
              <CardHeader className="pb-2">
                <CardTitle className="text-base flex items-center gap-2 text-red-700">
                  <AlertTriangle className="h-4 w-4" />
                  Overdue Invoices
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-0">
                <div className="space-y-2">
                  {data.overdueInvoices.map((inv) => (
                    <div
                      key={inv.number}
                      className="flex items-center justify-between p-3 rounded-lg bg-white border border-red-100"
                    >
                      <div>
                        <p className="font-medium text-sm text-slate-900">{inv.number}</p>
                        <p className="text-xs text-red-600">{inv.daysPast} days overdue</p>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold text-red-700">{formatCurrency(inv.amount)}</p>
                        <Badge variant="outline" className="text-xs">{inv.phase}</Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Right Column */}
        <div className="space-y-6">
          {/* Upcoming Deadlines */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base flex items-center gap-2">
                <Calendar className="h-4 w-4 text-blue-600" />
                Upcoming Deadlines
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="space-y-2">
                {data.deadlines.map((deadline) => (
                  <div
                    key={deadline.name}
                    className="flex items-center justify-between p-3 rounded-lg bg-slate-50 hover:bg-slate-100 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className={cn(
                        "h-2 w-2 rounded-full",
                        deadline.daysLeft <= 14 && "bg-amber-500",
                        deadline.daysLeft > 14 && "bg-blue-500"
                      )} />
                      <div>
                        <p className="font-medium text-sm text-slate-900">{deadline.name}</p>
                        <p className="text-xs text-slate-500">{deadline.date}</p>
                      </div>
                    </div>
                    <Badge variant={deadline.daysLeft <= 14 ? "secondary" : "outline"} className="text-xs">
                      {deadline.daysLeft} days
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Recent Activity */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base flex items-center gap-2">
                <Clock className="h-4 w-4 text-slate-600" />
                Recent Activity
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="space-y-1">
                {data.recentActivity.map((activity, idx) => (
                  <div
                    key={idx}
                    className="flex items-start gap-3 p-2 rounded-lg hover:bg-slate-50 transition-colors"
                  >
                    <div className={cn(
                      "h-8 w-8 rounded-full flex items-center justify-center flex-shrink-0",
                      activity.type === "invoice_paid" && "bg-emerald-100 text-emerald-600",
                      activity.type === "invoice_sent" && "bg-blue-100 text-blue-600",
                      activity.type === "meeting" && "bg-purple-100 text-purple-600",
                      activity.type === "deliverable" && "bg-amber-100 text-amber-600",
                      activity.type === "email" && "bg-slate-100 text-slate-600"
                    )}>
                      {activity.type === "invoice_paid" && <DollarSign className="h-4 w-4" />}
                      {activity.type === "invoice_sent" && <FileText className="h-4 w-4" />}
                      {activity.type === "meeting" && <MessageSquare className="h-4 w-4" />}
                      {activity.type === "deliverable" && <CheckCircle2 className="h-4 w-4" />}
                      {activity.type === "email" && <Mail className="h-4 w-4" />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-slate-900">{activity.title}</p>
                      <p className="text-xs text-slate-500">{activity.date}</p>
                    </div>
                    {activity.amount && (
                      <span className={cn(
                        "text-sm font-medium",
                        activity.type === "invoice_paid" && "text-emerald-600",
                        activity.type === "invoice_sent" && "text-blue-600"
                      )}>
                        {formatCurrency(activity.amount)}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
