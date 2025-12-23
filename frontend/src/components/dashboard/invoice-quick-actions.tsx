"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Send,
  FileText,
  DollarSign,
  BarChart3,
  Download,
  AlertCircle,
  CheckCircle2,
  Loader2,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

interface InvoiceAgingData {
  aging: {
    current: number;
    "30_days": number;
    "60_days": number;
    "90_days": number;
    over_90_days: number;
  };
}

/**
 * Invoice Quick Actions Widget
 * Provides one-click access to common invoice operations
 */
export function InvoiceQuickActions() {
  const router = useRouter();

  // Fetch real aging data
  const { data: agingData, isLoading: agingLoading } = useQuery({
    queryKey: ["invoice-aging"],
    queryFn: async () => {
      const res = await fetch(`${API_BASE_URL}/api/invoices/aging`);
      if (!res.ok) throw new Error("Failed to fetch aging data");
      return res.json();
    },
  });

  // Fetch outstanding invoices to get counts
  const { isLoading: outstandingLoading } = useQuery({
    queryKey: ["outstanding-invoices"],
    queryFn: async () => {
      const res = await fetch(`${API_BASE_URL}/api/invoices/outstanding?per_page=200`);
      if (!res.ok) throw new Error("Failed to fetch outstanding invoices");
      return res.json();
    },
  });

  const isLoading = agingLoading || outstandingLoading;

  // Calculate real stats from data
  const aging: InvoiceAgingData["aging"] = agingData?.aging || {
    current: 0,
    "30_days": 0,
    "60_days": 0,
    "90_days": 0,
    over_90_days: 0,
  };

  // Calculate action-based counts
  const overdueCount = aging["30_days"] + aging["60_days"] + aging["90_days"] + aging.over_90_days;
  const criticalCount = aging["90_days"] + aging.over_90_days; // 90+ days need urgent attention
  const recentCount = aging.current + aging["30_days"]; // Current and 30-day invoices

  const quickStats = {
    actionRequired: criticalCount, // 90+ days overdue
    reviewNeeded: aging["30_days"] + aging["60_days"], // 30-60 days - need review
    readyToClose: recentCount, // Current invoices - on track
  };

  const actions = [
    {
      id: "send-reminders",
      label: "Send Reminders",
      description: `${overdueCount} overdue invoices`,
      icon: Send,
      color: "blue",
      count: overdueCount,
      action: () => {
        // Navigate to invoices page filtered to overdue
        router.push("/finance?tab=outstanding");
      },
    },
    {
      id: "generate-report",
      label: "Generate Report",
      description: "Aging & collections",
      icon: FileText,
      color: "purple",
      action: () => {
        // Open aging report in new tab
        window.open(`${API_BASE_URL}/api/invoices/aging-breakdown`, "_blank");
      },
    },
    {
      id: "export-data",
      label: "Export Data",
      description: "View all invoices",
      icon: Download,
      color: "green",
      action: () => {
        // Navigate to full invoice list
        router.push("/finance?view=all");
      },
    },
    {
      id: "view-analytics",
      label: "View Analytics",
      description: "Trends & insights",
      icon: BarChart3,
      color: "orange",
      action: () => {
        // Navigate to analytics section
        router.push("/finance?tab=analytics");
      },
    },
  ];

  if (isLoading) {
    return (
      <Card>
        <CardHeader className="pb-4">
          <CardTitle className="text-lg">Quick Actions</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Quick Actions</CardTitle>
          <Badge variant="outline" className="text-xs">
            {quickStats.actionRequired} need attention
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Action Items Summary */}
        <div className="grid grid-cols-3 gap-2 mb-4">
          <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-center">
            <div className="flex items-center justify-center mb-1">
              <AlertCircle className="h-4 w-4 text-red-600" />
            </div>
            <p className="text-2xl font-bold text-red-700">{quickStats.actionRequired}</p>
            <p className="text-xs text-muted-foreground">90+ Days</p>
          </div>
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 text-center">
            <div className="flex items-center justify-center mb-1">
              <FileText className="h-4 w-4 text-yellow-600" />
            </div>
            <p className="text-2xl font-bold text-yellow-700">{quickStats.reviewNeeded}</p>
            <p className="text-xs text-muted-foreground">30-90 Days</p>
          </div>
          <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-center">
            <div className="flex items-center justify-center mb-1">
              <CheckCircle2 className="h-4 w-4 text-green-600" />
            </div>
            <p className="text-2xl font-bold text-green-700">{quickStats.readyToClose}</p>
            <p className="text-xs text-muted-foreground">On Track</p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="space-y-2">
          {actions.map((action) => {
            const colorClasses = {
              blue: "bg-blue-50 hover:bg-blue-100 border-blue-200 text-blue-700",
              purple: "bg-purple-50 hover:bg-purple-100 border-purple-200 text-purple-700",
              green: "bg-green-50 hover:bg-green-100 border-green-200 text-green-700",
              orange: "bg-orange-50 hover:bg-orange-100 border-orange-200 text-orange-700",
            };

            const iconColorClasses = {
              blue: "text-blue-600 bg-blue-100",
              purple: "text-purple-600 bg-purple-100",
              green: "text-green-600 bg-green-100",
              orange: "text-orange-600 bg-orange-100",
            };

            return (
              <button
                key={action.id}
                onClick={action.action}
                className={`w-full flex items-center gap-3 p-3 rounded-lg border transition-all duration-200 ${
                  colorClasses[action.color as keyof typeof colorClasses]
                }`}
              >
                <div className={`p-2 rounded-lg ${iconColorClasses[action.color as keyof typeof iconColorClasses]}`}>
                  <action.icon className="h-4 w-4" />
                </div>
                <div className="flex-1 text-left">
                  <p className="font-semibold text-sm">{action.label}</p>
                  <p className="text-xs opacity-75">{action.description}</p>
                </div>
                {action.count !== undefined && action.count > 0 && (
                  <Badge variant="secondary" className="text-xs">
                    {action.count}
                  </Badge>
                )}
              </button>
            );
          })}
        </div>

        {/* Quick Links */}
        <div className="pt-4 border-t space-y-2">
          <p className="text-xs font-semibold text-muted-foreground mb-2">QUICK LINKS</p>
          <div className="grid grid-cols-2 gap-2">
            <Button
              variant="outline"
              size="sm"
              className="w-full justify-start text-xs"
              onClick={() => router.push("/finance?action=record-payment")}
            >
              <DollarSign className="h-3 w-3 mr-2" />
              Record Payment
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="w-full justify-start text-xs"
              onClick={() => router.push("/finance?action=create-invoice")}
            >
              <FileText className="h-3 w-3 mr-2" />
              Create Invoice
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
