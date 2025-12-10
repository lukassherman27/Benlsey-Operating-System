"use client";

import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { ds } from "@/lib/design-system";
import { TrendingUp, TrendingDown } from "lucide-react";

export type KPIVariant = "default" | "success" | "warning" | "danger";

interface KPICardProps {
  label: string;
  value: string | number;
  subtitle?: string;
  trend?: {
    direction: "up" | "down";
    value: number;
    label: string;
  };
  variant?: KPIVariant;
  icon?: React.ReactNode;
}

export function KPICard({
  label,
  value,
  subtitle,
  trend,
  variant = "default",
  icon,
}: KPICardProps) {
  const variantStyles = {
    default: "border-slate-200 bg-white",
    success: "border-emerald-200 bg-emerald-50/50",
    warning: "border-amber-200 bg-amber-50/50",
    danger: "border-red-200 bg-red-50/50",
  };

  const iconBgStyles = {
    default: "bg-slate-100 text-slate-600",
    success: "bg-emerald-100 text-emerald-600",
    warning: "bg-amber-100 text-amber-600",
    danger: "bg-red-100 text-red-600",
  };

  // Determine if trend is positive (up is good) or negative
  const isTrendPositive = trend?.direction === "up";
  const trendColor = isTrendPositive ? "text-emerald-600" : "text-red-600";

  return (
    <Card className={cn(ds.borderRadius.cardLarge, "border", variantStyles[variant])}>
      <CardContent className="p-6">
        <div className="flex items-start justify-between mb-3">
          {icon && (
            <div className={cn("p-2.5 rounded-lg", iconBgStyles[variant])}>
              {icon}
            </div>
          )}
          {trend && (
            <div className={cn("flex items-center gap-1 text-sm font-medium", trendColor)}>
              {trend.direction === "up" ? (
                <TrendingUp className="h-4 w-4" />
              ) : (
                <TrendingDown className="h-4 w-4" />
              )}
              <span>{trend.label}</span>
            </div>
          )}
        </div>

        <div className="space-y-1">
          <p className={cn(ds.typography.label, "text-slate-500")}>{label}</p>
          <p className={cn(ds.typography.metricValue, "text-slate-900 font-bold")}>
            {value}
          </p>
          {subtitle && (
            <p className={cn(ds.typography.caption, "text-slate-500")}>
              {subtitle}
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Format number as currency with M/K abbreviations
 */
export function formatLargeNumber(num: number): string {
  if (num >= 1_000_000) {
    return `$${(num / 1_000_000).toFixed(1)}M`;
  }
  if (num >= 1_000) {
    return `$${(num / 1_000).toFixed(0)}K`;
  }
  return `$${num.toLocaleString()}`;
}
