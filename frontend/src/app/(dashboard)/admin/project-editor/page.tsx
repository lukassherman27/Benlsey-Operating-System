"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Building2,
  DollarSign,
  FileText,
  Users,
  AlertCircle,
  CheckCircle2,
  Loader2,
  Save,
  RefreshCw,
  Eye,
  Edit,
  Plus,
  Briefcase,
} from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { ds } from "@/lib/design-system";

interface ProjectData {
  project_id: number;
  project_code: string;
  project_title: string;
  client_name?: string;
  total_fee_usd?: number;
  status?: string;
  current_phase?: string;
  country?: string;
  city?: string;
  scope_summary?: string;
}

interface FeeBreakdown {
  breakdown_id: string;
  discipline: string;
  phase: string;
  phase_fee_usd: number;
  total_invoiced: number;
  total_paid: number;
  scope?: string | null;
}

interface InvoiceData {
  invoice_id: number;
  invoice_number: string;
  invoice_amount: number;
  payment_amount?: number;
  invoice_date: string;
  due_date?: string;
  payment_date?: string;
  status: string;
  breakdown_id?: string;
}

export default function ProjectEditorPage() {
  const queryClient = useQueryClient();
  const [selectedProject, setSelectedProject] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [activeTab, setActiveTab] = useState("overview");

  // Form state for project details
  const [projectForm, setProjectForm] = useState<Partial<ProjectData>>({});
  const [newPhase, setNewPhase] = useState({
    discipline: "Landscape",
    phase: "Mobilization",
    phase_fee_usd: "",
    scope: "",
  });

  // Load projects list
  const { data: projectsList, isLoading: loadingProjects } = useQuery({
    queryKey: ["projects-list-editor"],
    queryFn: () => api.getProjectsForLinking(500),
  });

  // Load selected project data
  const { data: projectData, isLoading: loadingProject, refetch: refetchProject } = useQuery({
    queryKey: ["project-editor-data", selectedProject],
    queryFn: async () => {
      if (!selectedProject) return null;
      const data = await api.getProjectData(selectedProject);
      return data;
    },
    enabled: !!selectedProject,
  });

  // Load fee breakdowns
  const { data: breakdownsData, isLoading: loadingBreakdowns } = useQuery({
    queryKey: ["project-breakdowns-editor", selectedProject],
    queryFn: () => selectedProject ? api.getProjectFeeBreakdowns(selectedProject) : null,
    enabled: !!selectedProject,
  });

  // Update project mutation
  const updateMutation = useMutation({
    mutationFn: async (data: { project_code: string; updates: Partial<ProjectData> }) => {
      return api.updateProject(data.project_code, data.updates);
    },
    onSuccess: () => {
      toast.success("Project updated successfully");
      queryClient.invalidateQueries({ queryKey: ["project-editor-data", selectedProject] });
      setIsEditing(false);
    },
    onError: (error) => {
      toast.error(`Failed to update project: ${error.message}`);
    },
  });

  // Add fee breakdown mutation
  const addBreakdownMutation = useMutation({
    mutationFn: async (data: { project_code: string; breakdown: typeof newPhase }) => {
      return api.addFeeBreakdown(data.project_code, {
        discipline: data.breakdown.discipline,
        phase: data.breakdown.phase,
        phase_fee_usd: parseFloat(data.breakdown.phase_fee_usd) || 0,
        scope: data.breakdown.scope,
      });
    },
    onSuccess: () => {
      toast.success("Phase added successfully");
      queryClient.invalidateQueries({ queryKey: ["project-breakdowns-editor", selectedProject] });
      setNewPhase({ discipline: "Landscape", phase: "Mobilization", phase_fee_usd: "", scope: "" });
    },
    onError: (error) => {
      toast.error(`Failed to add phase: ${error.message}`);
    },
  });

  // Update form when project data loads
  useEffect(() => {
    if (projectData?.project) {
      setProjectForm({
        project_code: projectData.project.project_code,
        project_title: projectData.project.project_title || "",
        client_name: projectData.project.client_name || "",
        total_fee_usd: projectData.project.total_fee_usd,
        status: projectData.project.status || "",
        current_phase: projectData.project.current_phase || "",
        country: projectData.project.country || "",
        city: projectData.project.city || "",
        scope_summary: projectData.project.scope_summary || "",
      });
    }
  }, [projectData]);

  const handleSave = () => {
    if (!selectedProject || !projectForm) return;
    updateMutation.mutate({
      project_code: selectedProject,
      updates: projectForm,
    });
  };

  const handleAddPhase = () => {
    if (!selectedProject || !newPhase.phase_fee_usd) {
      toast.error("Please enter a fee amount");
      return;
    }
    addBreakdownMutation.mutate({
      project_code: selectedProject,
      breakdown: newPhase,
    });
  };

  const formatCurrency = (value: number | undefined) => {
    if (!value) return "$0";
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 0,
    }).format(value);
  };

  // Calculate data quality score
  const calculateQualityScore = () => {
    if (!projectData?.project) return 0;
    let score = 0;
    const checks = [
      !!projectData.project.total_fee_usd,
      (breakdownsData?.breakdowns?.length ?? 0) > 0,
      (projectData.invoices?.length ?? 0) > 0,
      !!projectData.project.country,
      !!projectData.project.current_phase,
    ];
    score = checks.filter(Boolean).length / checks.length * 100;
    return Math.round(score);
  };

  return (
    <div className={cn("min-h-screen", ds.spacing.spacious)}>
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className={cn(ds.typography.heading1, ds.textColors.primary)}>
              Project Editor
            </h1>
            <p className={cn(ds.typography.body, ds.textColors.secondary)}>
              View and edit all database fields for any project
            </p>
          </div>
        </div>

        {/* Project Selector */}
        <Card className={ds.borderRadius.card}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Building2 className="h-5 w-5" />
              Select Project
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Select
              value={selectedProject || ""}
              onValueChange={(value) => {
                setSelectedProject(value);
                setIsEditing(false);
              }}
            >
              <SelectTrigger className="w-full max-w-md">
                <SelectValue placeholder="Choose a project to edit..." />
              </SelectTrigger>
              <SelectContent>
                {loadingProjects ? (
                  <SelectItem value="_loading" disabled>Loading...</SelectItem>
                ) : (
                  projectsList?.projects?.map((project: { code: string; name: string }) => (
                    <SelectItem key={project.code} value={project.code}>
                      {project.code} - {project.name || "Untitled"}
                    </SelectItem>
                  ))
                )}
              </SelectContent>
            </Select>
          </CardContent>
        </Card>

        {/* Loading State */}
        {loadingProject && selectedProject && (
          <Card className={ds.borderRadius.card}>
            <CardContent className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </CardContent>
          </Card>
        )}

        {/* Project Data */}
        {projectData && !loadingProject && (
          <>
            {/* Data Quality Score */}
            <Card className={cn(ds.borderRadius.card, "border-l-4",
              calculateQualityScore() >= 60 ? "border-l-green-500" :
              calculateQualityScore() >= 30 ? "border-l-amber-500" : "border-l-red-500"
            )}>
              <CardContent className="py-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {calculateQualityScore() >= 60 ? (
                      <CheckCircle2 className="h-6 w-6 text-green-600" />
                    ) : (
                      <AlertCircle className="h-6 w-6 text-amber-600" />
                    )}
                    <div>
                      <p className={cn(ds.typography.bodyBold, ds.textColors.primary)}>
                        Data Quality: {calculateQualityScore()}%
                      </p>
                      <p className={cn(ds.typography.caption, ds.textColors.secondary)}>
                        {calculateQualityScore() < 60 ? "Missing: " + getMissingFields().join(", ") : "All key fields present"}
                      </p>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => refetchProject()}
                    >
                      <RefreshCw className="h-4 w-4 mr-2" />
                      Refresh
                    </Button>
                    <Button
                      variant={isEditing ? "default" : "outline"}
                      size="sm"
                      onClick={() => setIsEditing(!isEditing)}
                    >
                      {isEditing ? <Eye className="h-4 w-4 mr-2" /> : <Edit className="h-4 w-4 mr-2" />}
                      {isEditing ? "View Mode" : "Edit Mode"}
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Tabs */}
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="overview">
                  <Briefcase className="h-4 w-4 mr-2" />
                  Overview
                </TabsTrigger>
                <TabsTrigger value="phases">
                  <DollarSign className="h-4 w-4 mr-2" />
                  Fee Breakdown
                </TabsTrigger>
                <TabsTrigger value="invoices">
                  <FileText className="h-4 w-4 mr-2" />
                  Invoices
                </TabsTrigger>
                <TabsTrigger value="contacts">
                  <Users className="h-4 w-4 mr-2" />
                  Contacts
                </TabsTrigger>
              </TabsList>

              {/* Overview Tab */}
              <TabsContent value="overview" className="space-y-4">
                <Card className={ds.borderRadius.card}>
                  <CardHeader>
                    <CardTitle>Project Information</CardTitle>
                    <CardDescription>Basic project details and metadata</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="project_code">Project Code</Label>
                        <Input
                          id="project_code"
                          value={projectForm.project_code || ""}
                          disabled
                          className="bg-muted"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="project_title">Project Title</Label>
                        <Input
                          id="project_title"
                          value={projectForm.project_title || ""}
                          onChange={(e) => setProjectForm({ ...projectForm, project_title: e.target.value })}
                          disabled={!isEditing}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="client_name">Client Name</Label>
                        <Input
                          id="client_name"
                          value={projectForm.client_name || ""}
                          onChange={(e) => setProjectForm({ ...projectForm, client_name: e.target.value })}
                          disabled={!isEditing}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="total_fee_usd">Total Contract Value (USD)</Label>
                        <Input
                          id="total_fee_usd"
                          type="number"
                          value={projectForm.total_fee_usd || ""}
                          onChange={(e) => setProjectForm({ ...projectForm, total_fee_usd: parseFloat(e.target.value) })}
                          disabled={!isEditing}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="status">Status</Label>
                        <Select
                          value={projectForm.status || ""}
                          onValueChange={(value) => setProjectForm({ ...projectForm, status: value })}
                          disabled={!isEditing}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Select status" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="active">Active</SelectItem>
                            <SelectItem value="completed">Completed</SelectItem>
                            <SelectItem value="on_hold">On Hold</SelectItem>
                            <SelectItem value="cancelled">Cancelled</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="current_phase">Current Phase</Label>
                        <Select
                          value={projectForm.current_phase || ""}
                          onValueChange={(value) => setProjectForm({ ...projectForm, current_phase: value })}
                          disabled={!isEditing}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Select phase" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="Mobilization">Mobilization</SelectItem>
                            <SelectItem value="Concept Design">Concept Design</SelectItem>
                            <SelectItem value="Schematic Design">Schematic Design</SelectItem>
                            <SelectItem value="Design Development">Design Development</SelectItem>
                            <SelectItem value="Construction Documents">Construction Documents</SelectItem>
                            <SelectItem value="Construction Observation">Construction Observation</SelectItem>
                            <SelectItem value="Completed">Completed</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="country">Country</Label>
                        <Input
                          id="country"
                          value={projectForm.country || ""}
                          onChange={(e) => setProjectForm({ ...projectForm, country: e.target.value })}
                          disabled={!isEditing}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="city">City</Label>
                        <Input
                          id="city"
                          value={projectForm.city || ""}
                          onChange={(e) => setProjectForm({ ...projectForm, city: e.target.value })}
                          disabled={!isEditing}
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="scope_summary">Scope of Work</Label>
                      <textarea
                        id="scope_summary"
                        className="w-full min-h-[100px] rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                        value={projectForm.scope_summary || ""}
                        onChange={(e) => setProjectForm({ ...projectForm, scope_summary: e.target.value })}
                        disabled={!isEditing}
                        placeholder="Describe the scope of work..."
                      />
                    </div>

                    {isEditing && (
                      <div className="flex justify-end gap-2 pt-4 border-t">
                        <Button variant="outline" onClick={() => setIsEditing(false)}>
                          Cancel
                        </Button>
                        <Button onClick={handleSave} disabled={updateMutation.isPending}>
                          {updateMutation.isPending ? (
                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          ) : (
                            <Save className="h-4 w-4 mr-2" />
                          )}
                          Save Changes
                        </Button>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Fee Breakdown Tab */}
              <TabsContent value="phases" className="space-y-4">
                <Card className={ds.borderRadius.card}>
                  <CardHeader>
                    <CardTitle>Fee Breakdown by Phase</CardTitle>
                    <CardDescription>
                      Phase-by-phase fee structure and payment status
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {loadingBreakdowns ? (
                      <div className="flex justify-center py-8">
                        <Loader2 className="h-6 w-6 animate-spin" />
                      </div>
                    ) : (breakdownsData?.breakdowns?.length ?? 0) > 0 ? (
                      <div className="space-y-4">
                        <table className="w-full">
                          <thead>
                            <tr className="border-b">
                              <th className="text-left py-2">Discipline</th>
                              <th className="text-left py-2">Phase</th>
                              <th className="text-right py-2">Fee</th>
                              <th className="text-right py-2">Invoiced</th>
                              <th className="text-right py-2">Paid</th>
                              <th className="text-right py-2">Progress</th>
                            </tr>
                          </thead>
                          <tbody>
                            {breakdownsData?.breakdowns?.map((bd: FeeBreakdown) => (
                              <tr key={bd.breakdown_id} className="border-b last:border-0">
                                <td className="py-3">{bd.discipline || "General"}</td>
                                <td className="py-3">
                                  {bd.phase}
                                  {bd.scope && (
                                    <span className="text-muted-foreground text-sm ml-2">({bd.scope})</span>
                                  )}
                                </td>
                                <td className="py-3 text-right font-medium">
                                  {formatCurrency(bd.phase_fee_usd)}
                                </td>
                                <td className="py-3 text-right">
                                  {formatCurrency(bd.total_invoiced)}
                                </td>
                                <td className="py-3 text-right">
                                  {formatCurrency(bd.total_paid)}
                                </td>
                                <td className="py-3 text-right">
                                  <Badge variant={
                                    bd.total_paid >= bd.phase_fee_usd ? "default" :
                                    bd.total_invoiced > 0 ? "secondary" : "outline"
                                  }>
                                    {bd.phase_fee_usd > 0
                                      ? Math.round((bd.total_paid / bd.phase_fee_usd) * 100)
                                      : 0}% paid
                                  </Badge>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>

                        {/* Summary */}
                        <div className="flex justify-end pt-4 border-t">
                          <div className="text-right">
                            <p className={cn(ds.typography.caption, ds.textColors.secondary)}>
                              Total Contract Value
                            </p>
                            <p className={cn(ds.typography.heading2, ds.textColors.primary)}>
                              {formatCurrency(
                                breakdownsData?.breakdowns?.reduce(
                                  (sum: number, bd: FeeBreakdown) => sum + (bd.phase_fee_usd || 0),
                                  0
                                ) ?? 0
                              )}
                            </p>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="text-center py-8 text-muted-foreground">
                        <DollarSign className="h-12 w-12 mx-auto mb-4 opacity-50" />
                        <p>No fee breakdown data available</p>
                        <p className="text-sm mt-2">Add phases below to build the fee structure</p>
                      </div>
                    )}

                    {/* Add New Phase */}
                    {isEditing && (
                      <div className="mt-6 pt-6 border-t">
                        <h4 className={cn(ds.typography.bodyBold, "mb-4")}>Add New Phase</h4>
                        <div className="grid grid-cols-4 gap-4">
                          <div>
                            <Label>Discipline</Label>
                            <Select
                              value={newPhase.discipline}
                              onValueChange={(v) => setNewPhase({ ...newPhase, discipline: v })}
                            >
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="Landscape">Landscape</SelectItem>
                                <SelectItem value="Interior">Interior</SelectItem>
                                <SelectItem value="Architecture">Architecture</SelectItem>
                                <SelectItem value="Combined">Combined</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                          <div>
                            <Label>Phase</Label>
                            <Select
                              value={newPhase.phase}
                              onValueChange={(v) => setNewPhase({ ...newPhase, phase: v })}
                            >
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="Mobilization">Mobilization</SelectItem>
                                <SelectItem value="Concept Design">Concept Design</SelectItem>
                                <SelectItem value="Schematic Design">Schematic Design</SelectItem>
                                <SelectItem value="Design Development">Design Development</SelectItem>
                                <SelectItem value="Construction Documents">Construction Documents</SelectItem>
                                <SelectItem value="Construction Observation">Construction Observation</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                          <div>
                            <Label>Fee (USD)</Label>
                            <Input
                              type="number"
                              value={newPhase.phase_fee_usd}
                              onChange={(e) => setNewPhase({ ...newPhase, phase_fee_usd: e.target.value })}
                              placeholder="0"
                            />
                          </div>
                          <div className="flex items-end">
                            <Button onClick={handleAddPhase} disabled={addBreakdownMutation.isPending}>
                              <Plus className="h-4 w-4 mr-2" />
                              Add Phase
                            </Button>
                          </div>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Invoices Tab */}
              <TabsContent value="invoices" className="space-y-4">
                <Card className={ds.borderRadius.card}>
                  <CardHeader>
                    <CardTitle>Invoice History</CardTitle>
                    <CardDescription>
                      All invoices and payments for this project
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {(projectData.invoices?.length ?? 0) > 0 ? (
                      <table className="w-full">
                        <thead>
                          <tr className="border-b">
                            <th className="text-left py-2">Invoice #</th>
                            <th className="text-left py-2">Date</th>
                            <th className="text-right py-2">Amount</th>
                            <th className="text-right py-2">Paid</th>
                            <th className="text-center py-2">Status</th>
                          </tr>
                        </thead>
                        <tbody>
                          {projectData.invoices.map((inv: InvoiceData) => (
                            <tr key={inv.invoice_id} className="border-b last:border-0">
                              <td className="py-3 font-medium">{inv.invoice_number}</td>
                              <td className="py-3">
                                {inv.invoice_date ? new Date(inv.invoice_date).toLocaleDateString() : "-"}
                              </td>
                              <td className="py-3 text-right">{formatCurrency(inv.invoice_amount)}</td>
                              <td className="py-3 text-right">{formatCurrency(inv.payment_amount || 0)}</td>
                              <td className="py-3 text-center">
                                <Badge variant={
                                  inv.status === "Paid" ? "default" :
                                  inv.status === "Outstanding" ? "destructive" : "secondary"
                                }>
                                  {inv.status}
                                </Badge>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    ) : (
                      <div className="text-center py-8 text-muted-foreground">
                        <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                        <p>No invoices recorded</p>
                        <p className="text-sm mt-2">Use Financial Entry to add invoices</p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Contacts Tab */}
              <TabsContent value="contacts" className="space-y-4">
                <Card className={ds.borderRadius.card}>
                  <CardHeader>
                    <CardTitle>Project Contacts</CardTitle>
                    <CardDescription>
                      People associated with this project
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="text-center py-8 text-muted-foreground">
                      <Users className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <p>Contact linking coming soon</p>
                      <p className="text-sm mt-2">Use AI Suggestions to link contacts from emails</p>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </>
        )}
      </div>
    </div>
  );

  function getMissingFields(): string[] {
    const missing: string[] = [];
    if (!projectData?.project) return missing;

    if (!projectData.project.total_fee_usd) missing.push("contract value");
    if (!breakdownsData?.breakdowns?.length) missing.push("fee breakdown");
    if (!projectData.invoices?.length) missing.push("invoices");
    if (!projectData.project.country) missing.push("location");
    if (!projectData.project.current_phase) missing.push("current phase");

    return missing;
  }
}
