import { Badge } from "@/components/ui/badge";

const labelMap: Record<string, string> = {
  healthy: "Healthy",
  at_risk: "At Risk",
  critical: "Critical",
};

// Use semantic status variants for proper color coding
const variants: Record<string, "success" | "warning" | "danger"> = {
  healthy: "success",    // Green - good state
  at_risk: "warning",    // Amber - needs attention
  critical: "danger",    // Red - urgent
};

export function HealthBadge({ status }: { status?: string }) {
  if (!status) return null;
  const normalized = status.toLowerCase();
  return (
    <Badge variant={variants[normalized] ?? "warning"} className="capitalize">
      {labelMap[normalized] ?? status}
    </Badge>
  );
}
