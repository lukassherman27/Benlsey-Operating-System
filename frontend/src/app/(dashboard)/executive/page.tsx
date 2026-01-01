import { ExecutiveDashboard } from "@/components/executive/executive-dashboard";

export const metadata = {
  title: "Executive Dashboard | BDS Operations",
  description: "Executive view of pipeline, projects, and action items",
};

export default function ExecutivePage() {
  return <ExecutiveDashboard />;
}
