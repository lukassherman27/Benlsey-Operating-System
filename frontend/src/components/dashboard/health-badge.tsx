import { Badge } from "@/components/ui/badge";

const labelMap: Record<string, string> = {
  healthy: "Healthy",
  at_risk: "At Risk",
  critical: "Critical",
};

const variants: Record<string, "default" | "secondary" | "destructive"> = {
  healthy: "default",
  at_risk: "secondary",
  critical: "destructive",
};

export function HealthBadge({ status }: { status?: string }) {
  if (!status) return null;
  const normalized = status.toLowerCase();
  return (
    <Badge variant={variants[normalized] ?? "secondary"} className="capitalize">
      {labelMap[normalized] ?? status}
    </Badge>
  );
}
