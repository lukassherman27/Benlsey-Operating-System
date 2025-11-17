"use client";

import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

type Props = {
  series?: Array<{ name: string; data: number[] }>;
  categories?: string[];
  hideCard?: boolean;
  className?: string;
};

export default function RevenueBar({
  series = [
    { name: "Revenue", data: [320, 380, 420, 510, 560, 610] },
    { name: "Cost", data: [180, 210, 240, 320, 340, 360] },
  ],
  categories = ["Aug", "Sep", "Oct", "Nov", "Dec", "Jan"],
  hideCard = false,
  className,
}: Props) {
  const chart = (
    <BarChart series={series} categories={categories} />
  );

  if (hideCard) {
    return <div className={className}>{chart}</div>;
  }

  return (
    <Card className={cn("rounded-3xl border border-slate-200/80 shadow-sm", className)}>
      <CardContent className="p-4">{chart}</CardContent>
    </Card>
  );
}

function BarChart({
  series,
  categories,
}: {
  series: Array<{ name: string; data: number[] }>;
  categories: string[];
}) {
  const colors = ["#0f172a", "#94a3b8"];
  const revenue = series[0]?.data ?? [];
  const costs = series[1]?.data ?? [];
  const maxPoint = Math.max(...revenue, ...costs, 1);

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-4 text-xs uppercase tracking-[0.3em] text-slate-400">
        {series.map((entry, index) => (
          <div key={entry.name} className="flex items-center gap-2">
            <span
              className="h-1 w-8 rounded-full"
              style={{ backgroundColor: colors[index] ?? colors[0] }}
            />
            <span>{entry.name}</span>
          </div>
        ))}
      </div>
      <div className="flex items-end gap-3 rounded-3xl bg-slate-900/5 px-4 py-6">
        {categories.map((label, index) => {
          const revenueHeight = (revenue[index] ?? 0) / maxPoint;
          const costHeight = (costs[index] ?? 0) / maxPoint;
          return (
            <div key={label} className="flex flex-1 flex-col items-center gap-1 text-xs text-slate-500">
              <div className="flex w-full items-end gap-1">
                <div
                  className="flex-1 rounded-sm bg-gradient-to-t from-[#0f172a] to-[#2b3b60]"
                  style={{ height: `${Math.max(revenueHeight * 160, 4)}px` }}
                  title={`Revenue ${revenue[index] ?? 0}K`}
                />
                <div
                  className="flex-1 rounded-sm bg-gradient-to-t from-[#94a3b8] to-white"
                  style={{ height: `${Math.max(costHeight * 160, 4)}px` }}
                  title={`Cost ${costs[index] ?? 0}K`}
                />
              </div>
              <span>{label}</span>
            </div>
          );
        })}
      </div>
      <div className="flex justify-between text-xs uppercase tracking-[0.3em] text-slate-400">
        {categories.map((label) => (
          <span key={label}>{label}</span>
        ))}
      </div>
    </div>
  );
}
