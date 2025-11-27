"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Activity, AlertCircle, TrendingUp, TrendingDown, Minus } from "lucide-react";

interface ProjectHealthScore {
  projectCode: string;
  projectName: string;
  overallHealth: number; // 0-100
  healthStatus: "healthy" | "warning" | "critical";
  factors: {
    financial: number;
    communication: number;
    schedule: number;
  };
  risks: Array<{
    type: string;
    severity: "low" | "medium" | "high";
    description: string;
  }>;
  trend: "improving" | "stable" | "declining";
}

interface ProjectHealthDashboardProps {
  projectCode?: string;
}

export function ProjectHealthDashboard({ projectCode }: ProjectHealthDashboardProps) {
  // Mock data - Will be replaced with real API data once health scoring is implemented
  const mockHealthData: ProjectHealthScore[] = [
    {
      projectCode: "BK-033",
      projectName: "The Ritz Carlton Reserve, Nusa Dua",
      overallHealth: 85,
      healthStatus: "healthy",
      factors: {
        financial: 90,
        communication: 85,
        schedule: 80,
      },
      risks: [],
      trend: "stable",
    },
    {
      projectCode: "BK-036",
      projectName: "Sunny Lagoons Maldives",
      overallHealth: 65,
      healthStatus: "warning",
      factors: {
        financial: 70,
        communication: 55,
        schedule: 70,
      },
      risks: [
        {
          type: "Communication",
          severity: "medium",
          description: "No client contact in 21 days",
        },
      ],
      trend: "declining",
    },
    {
      projectCode: "BK-015",
      projectName: "Ultra Luxury Beach Resort",
      overallHealth: 40,
      healthStatus: "critical",
      factors: {
        financial: 30,
        communication: 45,
        schedule: 45,
      },
      risks: [
        {
          type: "Financial",
          severity: "high",
          description: "Invoice >90 days overdue ($245K)",
        },
        {
          type: "Communication",
          severity: "high",
          description: "No response to last 3 emails",
        },
      ],
      trend: "declining",
    },
  ];

  const getHealthColor = (status: string) => {
    if (status === "healthy") return "text-green-700 bg-green-50 border-green-200";
    if (status === "warning") return "text-amber-700 bg-amber-50 border-amber-200";
    return "text-red-700 bg-red-50 border-red-200";
  };

  const getHealthIcon = (status: string) => {
    if (status === "healthy") return "bg-green-500";
    if (status === "warning") return "bg-amber-500";
    return "bg-red-500";
  };

  const getTrendIcon = (trend: string) => {
    if (trend === "improving") return <TrendingUp className="h-4 w-4 text-green-600" />;
    if (trend === "declining") return <TrendingDown className="h-4 w-4 text-red-600" />;
    return <Minus className="h-4 w-4 text-slate-500" />;
  };

  const filteredData = projectCode
    ? mockHealthData.filter((p) => p.projectCode === projectCode)
    : mockHealthData;

  return (
    <Card className="border-slate-200 bg-gradient-to-br from-slate-50 to-blue-50">
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-blue-600" />
            <CardTitle className="text-lg text-slate-900">Project Health</CardTitle>
          </div>
          <Badge className="bg-amber-100 text-amber-700 border-amber-300">
            Coming Soon
          </Badge>
        </div>
        <p className="text-sm text-slate-600 mt-1">
          Real-time project health monitoring (placeholder with mock data)
        </p>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Info Banner */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-semibold text-blue-900 mb-1">
                Health Scoring Coming Soon
              </p>
              <p className="text-xs text-blue-800">
                Once project data is fully populated, the system will automatically calculate
                health scores based on financial status, communication frequency, and schedule
                adherence. Below is a preview with sample data.
              </p>
            </div>
          </div>
        </div>

        {/* Project Health Cards */}
        <div className="space-y-3">
          {filteredData.map((project, idx) => (
            <div
              key={idx}
              className={`border-2 rounded-lg p-4 ${getHealthColor(project.healthStatus)}`}
            >
              {/* Project Header */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-mono text-sm font-semibold text-slate-900">
                      {project.projectCode}
                    </span>
                    <Badge variant="outline" className="text-xs">
                      {project.healthStatus.toUpperCase()}
                    </Badge>
                  </div>
                  <h4 className="text-sm font-medium text-slate-900 truncate">
                    {project.projectName}
                  </h4>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0 ml-4">
                  {getTrendIcon(project.trend)}
                  <div className="text-right">
                    <div className="text-2xl font-bold text-slate-900">
                      {project.overallHealth}
                    </div>
                    <div className="text-xs text-slate-600">Health</div>
                  </div>
                </div>
              </div>

              {/* Health Factors */}
              <div className="grid grid-cols-3 gap-3 mb-3">
                <div className="bg-white/60 rounded p-2">
                  <div className="text-xs text-slate-600 mb-1">Financial</div>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-2 bg-slate-200 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${project.factors.financial >= 70 ? "bg-green-500" : project.factors.financial >= 40 ? "bg-amber-500" : "bg-red-500"}`}
                        style={{ width: `${project.factors.financial}%` }}
                      />
                    </div>
                    <span className="text-xs font-semibold">{project.factors.financial}</span>
                  </div>
                </div>

                <div className="bg-white/60 rounded p-2">
                  <div className="text-xs text-slate-600 mb-1">Comms</div>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-2 bg-slate-200 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${project.factors.communication >= 70 ? "bg-green-500" : project.factors.communication >= 40 ? "bg-amber-500" : "bg-red-500"}`}
                        style={{ width: `${project.factors.communication}%` }}
                      />
                    </div>
                    <span className="text-xs font-semibold">{project.factors.communication}</span>
                  </div>
                </div>

                <div className="bg-white/60 rounded p-2">
                  <div className="text-xs text-slate-600 mb-1">Schedule</div>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-2 bg-slate-200 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${project.factors.schedule >= 70 ? "bg-green-500" : project.factors.schedule >= 40 ? "bg-amber-500" : "bg-red-500"}`}
                        style={{ width: `${project.factors.schedule}%` }}
                      />
                    </div>
                    <span className="text-xs font-semibold">{project.factors.schedule}</span>
                  </div>
                </div>
              </div>

              {/* Risks */}
              {project.risks.length > 0 && (
                <div className="space-y-1.5">
                  {project.risks.map((risk, riskIdx) => (
                    <div
                      key={riskIdx}
                      className="flex items-start gap-2 text-xs bg-white/60 rounded p-2"
                    >
                      <AlertCircle
                        className={`h-3.5 w-3.5 flex-shrink-0 mt-0.5 ${
                          risk.severity === "high"
                            ? "text-red-600"
                            : risk.severity === "medium"
                            ? "text-amber-600"
                            : "text-slate-600"
                        }`}
                      />
                      <div className="flex-1">
                        <span className="font-semibold">{risk.type}:</span> {risk.description}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
