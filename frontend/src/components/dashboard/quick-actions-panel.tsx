"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Mail,
  FileText,
  Download,
  BarChart3,
  Send,
  DollarSign,
  Clock,
  CheckCircle,
} from "lucide-react";
import { useState } from "react";

interface QuickAction {
  id: string;
  label: string;
  icon: React.ReactNode;
  color: string;
  bgColor: string;
  hoverColor: string;
  count?: number;
  disabled?: boolean;
}

interface QuickActionsPanelProps {
  projectCode?: string;
  variant?: "full" | "compact";
}

export function QuickActionsPanel({ projectCode, variant = "full" }: QuickActionsPanelProps) {
  const [processing, setProcessing] = useState<string | null>(null);

  const handleAction = async (actionId: string) => {
    setProcessing(actionId);

    // Simulate action processing
    setTimeout(() => {
      setProcessing(null);
    }, 1500);
  };

  const actions: QuickAction[] = [
    {
      id: "send-reminders",
      label: "Send Payment Reminders",
      icon: <Send className="h-4 w-4" />,
      color: "text-blue-700",
      bgColor: "bg-blue-50",
      hoverColor: "hover:bg-blue-100",
      count: 15,
    },
    {
      id: "generate-report",
      label: "Generate Project Report",
      icon: <FileText className="h-4 w-4" />,
      color: "text-purple-700",
      bgColor: "bg-purple-50",
      hoverColor: "hover:bg-purple-100",
    },
    {
      id: "export-data",
      label: "Export to Excel",
      icon: <Download className="h-4 w-4" />,
      color: "text-green-700",
      bgColor: "bg-green-50",
      hoverColor: "hover:bg-green-100",
    },
    {
      id: "view-analytics",
      label: "View Analytics",
      icon: <BarChart3 className="h-4 w-4" />,
      color: "text-orange-700",
      bgColor: "bg-orange-50",
      hoverColor: "hover:bg-orange-100",
    },
    {
      id: "invoice-preview",
      label: "Preview Next Invoice",
      icon: <DollarSign className="h-4 w-4" />,
      color: "text-emerald-700",
      bgColor: "bg-emerald-50",
      hoverColor: "hover:bg-emerald-100",
    },
    {
      id: "update-status",
      label: "Update Project Status",
      icon: <CheckCircle className="h-4 w-4" />,
      color: "text-indigo-700",
      bgColor: "bg-indigo-50",
      hoverColor: "hover:bg-indigo-100",
    },
  ];

  // Quick stats for context
  const stats = [
    {
      label: "Action Required",
      value: 15,
      color: "bg-red-100 text-red-700",
      icon: <Clock className="h-4 w-4" />,
    },
    {
      label: "Review Needed",
      value: 8,
      color: "bg-amber-100 text-amber-700",
      icon: <FileText className="h-4 w-4" />,
    },
    {
      label: "Ready to Close",
      value: 23,
      color: "bg-green-100 text-green-700",
      icon: <CheckCircle className="h-4 w-4" />,
    },
  ];

  if (variant === "compact") {
    return (
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Quick Actions</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {actions.slice(0, 4).map((action) => (
            <Button
              key={action.id}
              variant="outline"
              size="sm"
              className={`w-full justify-start ${action.bgColor} ${action.hoverColor} border-none`}
              onClick={() => handleAction(action.id)}
              disabled={processing === action.id}
            >
              <span className={action.color}>{action.icon}</span>
              <span className={`ml-2 text-sm ${action.color}`}>
                {action.label}
              </span>
              {action.count && (
                <Badge variant="secondary" className="ml-auto text-xs">
                  {action.count}
                </Badge>
              )}
            </Button>
          ))}
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-slate-200 bg-gradient-to-br from-slate-50 to-white">
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg text-slate-900">Quick Actions</CardTitle>
          {projectCode && (
            <Badge variant="outline" className="text-xs">
              {projectCode}
            </Badge>
          )}
        </div>
        <p className="text-sm text-slate-600 mt-1">
          One-click access to common operations
        </p>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Quick Stats */}
        <div className="grid grid-cols-3 gap-3">
          {stats.map((stat, idx) => (
            <div
              key={idx}
              className={`rounded-lg p-3 ${stat.color} border border-current/20`}
            >
              <div className="flex items-center gap-2 mb-1">
                {stat.icon}
                <span className="text-xs font-medium uppercase tracking-wide">
                  {stat.label}
                </span>
              </div>
              <p className="text-2xl font-bold">{stat.value}</p>
            </div>
          ))}
        </div>

        {/* Action Buttons Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {actions.map((action) => (
            <Button
              key={action.id}
              variant="outline"
              size="lg"
              className={`
                justify-start h-auto py-4 px-4
                ${action.bgColor} ${action.hoverColor}
                border-2 border-current/10
                transition-all duration-200
                ${processing === action.id ? "opacity-50 cursor-wait" : "hover:scale-105"}
              `}
              onClick={() => handleAction(action.id)}
              disabled={processing === action.id || action.disabled}
            >
              <div className="flex items-center gap-3 w-full">
                <div className={`p-2 rounded-lg ${action.bgColor} ${action.color}`}>
                  {action.icon}
                </div>
                <div className="flex-1 text-left">
                  <div className={`text-sm font-medium ${action.color}`}>
                    {action.label}
                  </div>
                  {action.count && (
                    <div className="text-xs text-slate-500 mt-0.5">
                      {action.count} items pending
                    </div>
                  )}
                </div>
                {processing === action.id && (
                  <div className="animate-spin h-4 w-4 border-2 border-current border-t-transparent rounded-full" />
                )}
              </div>
            </Button>
          ))}
        </div>

        {/* Pro Tip */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <Mail className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="text-sm font-semibold text-blue-900 mb-1">
                Pro Tip
              </h4>
              <p className="text-xs text-blue-800">
                Payment reminders are automatically sent for invoices over 60 days old.
                You can manually trigger reminders for invoices 30-60 days old.
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
