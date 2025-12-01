"use client";

import { useState } from "react";
import { useMutation, useQueryClient, useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { ds, bensleyVoice, getLoadingMessage } from "@/lib/design-system";
import {
  DollarSign,
  Plus,
  Save,
  Trash2,
  ChevronRight,
  CheckCircle2,
  AlertTriangle,
  Eye,
  FileText,
} from "lucide-react";
import { toast } from "sonner";
import type { FeeBreakdown } from "@/lib/api";

interface PhaseEntry {
  id: string;
  discipline: string;
  phase: string;
  phase_fee_usd: number;
  percentage_of_total: number;
}

interface InvoiceEntry {
  id: string;
  breakdown_id: string;
  invoice_number: string;
  invoice_date: string;
  invoice_amount: number;
  payment_date?: string;
  payment_amount?: number;
  status: string;
}

// Loading skeleton for breakdowns
function BreakdownsSkeleton() {
  return (
    <div className="space-y-4">
      <p className={cn(ds.typography.caption, ds.textColors.tertiary, "text-center mb-4")}>
        {getLoadingMessage()}
      </p>
      <div className="grid grid-cols-4 gap-3">
        {[...Array(4)].map((_, i) => (
          <Skeleton key={i} className="h-20 w-full rounded-lg" />
        ))}
      </div>
      <Skeleton className="h-48 w-full rounded-lg" />
    </div>
  );
}

export default function FinancialEntryPage() {
  const queryClient = useQueryClient();

  // Edit Mode State
  const [editMode, setEditMode] = useState(false);
  const [selectedProjectCode, setSelectedProjectCode] = useState<string | null>(null);

  // Project Info State
  const [projectCode, setProjectCode] = useState("");
  const [projectTitle, setProjectTitle] = useState("");
  const [totalFee, setTotalFee] = useState("");
  const [country, setCountry] = useState("");
  const [city, setCity] = useState("");

  // Phase Breakdown State
  const [phases, setPhases] = useState<PhaseEntry[]>([]);
  const [currentPhase, setCurrentPhase] = useState({
    discipline: "Landscape",
    phase: "Mobilization",
    phase_fee_usd: "",
  });

  // Invoice State
  const [invoices, setInvoices] = useState<InvoiceEntry[]>([]);
  const [currentInvoice, setCurrentInvoice] = useState({
    breakdown_id: "",
    invoice_number: "",
    invoice_date: "",
    invoice_amount: "",
    payment_date: "",
    payment_amount: "",
    status: "Outstanding",
  });

  const [activeStep, setActiveStep] = useState(1);

  // Load projects list for edit mode
  const { data: projectsList } = useQuery({
    queryKey: ["projects-list"],
    queryFn: () => api.getProjectsForLinking(1000),
  });

  // Fetch existing breakdowns for the selected project
  const {
    data: existingBreakdowns,
    isLoading: breakdownsLoading,
    refetch: refetchBreakdowns
  } = useQuery({
    queryKey: ["project-breakdowns", selectedProjectCode],
    queryFn: () => selectedProjectCode ? api.getProjectFeeBreakdowns(selectedProjectCode) : null,
    enabled: !!selectedProjectCode,
  });

  // State for showing existing breakdowns
  const [showExistingBreakdowns, setShowExistingBreakdowns] = useState(true);

  // Load function for edit mode
  const loadProject = async (code: string) => {
    if (!code) {
      clearForm();
      return;
    }

    setEditMode(true);
    setSelectedProjectCode(code);

    try {
      const projectData = await api.getProjectData(code);

      setProjectCode(code);
      setProjectTitle(projectData.project.project_title || "");
      setTotalFee(projectData.project.total_fee_usd?.toString() || "");
      setCountry(projectData.project.country || "");
      setCity(projectData.project.city || "");

      setPhases(projectData.phases.map((p: any) => ({
        id: p.breakdown_id.toString(),
        discipline: p.discipline,
        phase: p.phase,
        phase_fee_usd: p.phase_fee_usd,
        percentage_of_total: p.percentage_of_total || 0,
      })));

      setInvoices(projectData.invoices.map((inv: any) => ({
        id: inv.invoice_id.toString(),
        breakdown_id: inv.breakdown_id || "",
        invoice_number: inv.invoice_number,
        invoice_date: inv.invoice_date,
        invoice_amount: inv.invoice_amount,
        payment_date: inv.payment_date || "",
        payment_amount: inv.payment_amount || 0,
        status: inv.status,
      })));

      toast.success(`Loaded ${code}. ${bensleyVoice.successMessages.default}`);
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);
      toast.error(`Failed to load project: ${errorMsg}`);
      console.error("Load error:", error);
      setEditMode(false);
      setSelectedProjectCode(null);
    }
  };

  // Clear form function
  const clearForm = () => {
    setSelectedProjectCode(null);
    setEditMode(false);
    setProjectCode("");
    setProjectTitle("");
    setTotalFee("");
    setCountry("");
    setCity("");
    setPhases([]);
    setInvoices([]);
    setActiveStep(1);
  };

  // Calculate percentage for phase
  const calculatePercentage = (phaseFee: number) => {
    const total = parseFloat(totalFee) || 0;
    if (total === 0) return 0;
    return (phaseFee / total) * 100;
  };

  // Add Phase with duplicate checking
  const addPhase = async () => {
    if (!currentPhase.discipline || !currentPhase.phase || !currentPhase.phase_fee_usd) {
      toast.error("Please fill all phase fields");
      return;
    }

    const localDuplicate = phases.find(
      p => p.discipline === currentPhase.discipline && p.phase === currentPhase.phase
    );
    if (localDuplicate) {
      toast.error(`Duplicate: ${currentPhase.discipline} - ${currentPhase.phase} already added locally`);
      return;
    }

    if (existingBreakdowns?.breakdowns) {
      const dbDuplicate = existingBreakdowns.breakdowns.find(
        b => b.discipline === currentPhase.discipline && b.phase === currentPhase.phase
      );
      if (dbDuplicate) {
        toast.error(
          `Duplicate: ${currentPhase.discipline} - ${currentPhase.phase} already exists in database ($${dbDuplicate.phase_fee_usd.toLocaleString()})`
        );
        return;
      }
    }

    const phaseFee = parseFloat(currentPhase.phase_fee_usd);
    const newPhase: PhaseEntry = {
      id: `phase-${Date.now()}`,
      discipline: currentPhase.discipline,
      phase: currentPhase.phase,
      phase_fee_usd: phaseFee,
      percentage_of_total: calculatePercentage(phaseFee),
    };

    setPhases([...phases, newPhase]);
    setCurrentPhase({
      discipline: "Landscape",
      phase: "",
      phase_fee_usd: "",
    });
    toast.success("Phase added");
  };

  // Remove Phase
  const removePhase = (id: string) => {
    setPhases(phases.filter(p => p.id !== id));
    toast.success("Phase removed");
  };

  // Add Invoice
  const addInvoice = () => {
    if (!currentInvoice.invoice_number || !currentInvoice.invoice_date || !currentInvoice.invoice_amount) {
      toast.error("Please fill required invoice fields");
      return;
    }

    if (!currentInvoice.breakdown_id) {
      toast.error("Please select a phase/discipline for this invoice");
      return;
    }

    const newInvoice: InvoiceEntry = {
      id: `invoice-${Date.now()}`,
      breakdown_id: currentInvoice.breakdown_id,
      invoice_number: currentInvoice.invoice_number,
      invoice_date: currentInvoice.invoice_date,
      invoice_amount: parseFloat(currentInvoice.invoice_amount),
      payment_date: currentInvoice.payment_date || undefined,
      payment_amount: currentInvoice.payment_amount ? parseFloat(currentInvoice.payment_amount) : undefined,
      status: currentInvoice.status,
    };

    setInvoices([...invoices, newInvoice]);
    setCurrentInvoice({
      breakdown_id: "",
      invoice_number: "",
      invoice_date: "",
      invoice_amount: "",
      payment_date: "",
      payment_amount: "",
      status: "Outstanding",
    });
    toast.success("Invoice added");
  };

  // Remove Invoice
  const removeInvoice = (id: string) => {
    setInvoices(invoices.filter(i => i.id !== id));
    toast.success("Invoice removed");
  };

  // Save All Data
  const saveAllMutation = useMutation({
    mutationFn: async () => {
      if (editMode) {
        await api.updateProject(projectCode, {
          project_title: projectTitle,
          total_fee_usd: parseFloat(totalFee),
          country: country || "Unknown",
          city: city || "Unknown",
        });

        for (const phase of phases) {
          if (phase.id.startsWith('phase-')) {
            await api.createFeeBreakdown({
              project_code: projectCode,
              discipline: phase.discipline,
              phase: phase.phase,
              phase_fee_usd: phase.phase_fee_usd,
              percentage_of_total: phase.percentage_of_total,
            });
          } else {
            await api.updatePhaseFee(phase.id, {
              phase_fee_usd: phase.phase_fee_usd,
              percentage_of_total: phase.percentage_of_total,
            });
          }
        }

        for (const invoice of invoices) {
          if (invoice.id.startsWith('invoice-')) {
            await api.createInvoice({
              project_code: projectCode,
              breakdown_id: invoice.breakdown_id,
              invoice_number: invoice.invoice_number,
              invoice_date: invoice.invoice_date,
              invoice_amount: invoice.invoice_amount,
              payment_date: invoice.payment_date,
              payment_amount: invoice.payment_amount,
              status: invoice.status,
            });
          } else {
            await api.updateInvoice(invoice.invoice_number, {
              breakdown_id: invoice.breakdown_id,
              invoice_date: invoice.invoice_date,
              invoice_amount: invoice.invoice_amount,
              payment_date: invoice.payment_date,
              payment_amount: invoice.payment_amount,
              status: invoice.status,
            });
          }
        }
      } else {
        const projectResponse = await api.createProject({
          project_code: projectCode,
          project_title: projectTitle,
          total_fee_usd: parseFloat(totalFee),
          country: country || "Unknown",
          city: city || "Unknown",
          status: "active",
        });

        for (const phase of phases) {
          await api.createFeeBreakdown({
            project_code: projectCode,
            discipline: phase.discipline,
            phase: phase.phase,
            phase_fee_usd: phase.phase_fee_usd,
            percentage_of_total: phase.percentage_of_total,
          });
        }

        for (const invoice of invoices) {
          await api.createInvoice({
            project_code: projectCode,
            breakdown_id: invoice.breakdown_id,
            invoice_number: invoice.invoice_number,
            invoice_date: invoice.invoice_date,
            invoice_amount: invoice.invoice_amount,
            payment_date: invoice.payment_date,
            payment_amount: invoice.payment_amount,
            status: invoice.status,
          });
        }
      }
    },
    onSuccess: () => {
      toast.success(editMode ? "Project updated! " + bensleyVoice.successMessages.saved : bensleyVoice.successMessages.saved);
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      queryClient.invalidateQueries({ queryKey: ["invoices"] });
      queryClient.invalidateQueries({ queryKey: ["projects-list"] });
      clearForm();
    },
    onError: (error) => {
      toast.error(`Error saving data: ${error}`);
    },
  });

  // Calculate totals
  const totalPhases = phases.reduce((sum, p) => sum + p.phase_fee_usd, 0);
  const totalInvoices = invoices.reduce((sum, i) => sum + i.invoice_amount, 0);
  const totalPayments = invoices.reduce((sum, i) => sum + (i.payment_amount || 0), 0);

  const disciplines = ["Landscape", "Architecture", "Interior", "Other"];
  const commonPhases = [
    "Mobilization",
    "Concept Design",
    "Design Development",
    "Construction Documentation",
    "Construction Administration"
  ];
  const invoiceStatuses = ["Outstanding", "Paid", "Partial", "Overdue"];

  // Get status badge for invoices
  const getInvoiceStatusBadge = (status: string) => {
    switch (status) {
      case "Paid":
        return <Badge className={ds.badges.success}>{status}</Badge>;
      case "Partial":
        return <Badge className={ds.badges.info}>{status}</Badge>;
      case "Overdue":
        return <Badge className={ds.badges.danger}>{status}</Badge>;
      default:
        return <Badge className={ds.badges.warning}>{status}</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className={cn(ds.typography.heading1, ds.textColors.primary, "flex items-center gap-3")}>
            <DollarSign className="h-8 w-8 text-emerald-600" />
            {editMode ? `Edit Project: ${projectCode}` : "Manual Financial Data Entry"}
          </h1>
          <p className={cn(ds.typography.body, ds.textColors.secondary, "mt-1")}>
            {editMode ? "Update existing project data" : "Enter project financials manually without importing"}
          </p>
        </div>
        <Button
          onClick={() => saveAllMutation.mutate()}
          disabled={!projectCode || !projectTitle || saveAllMutation.isPending}
          size="lg"
          className={cn(ds.buttons.primary, "gap-2")}
        >
          <Save className="h-5 w-5" />
          {saveAllMutation.isPending ? "Saving..." : (editMode ? "Update Project" : "Save All Data")}
        </Button>
      </div>

      {/* Project Selector for Edit Mode */}
      <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <Label className={cn(ds.typography.caption, ds.textColors.secondary)}>
                Load Existing Project
              </Label>
              <select
                className={cn(ds.inputs.default, "w-full h-10 mt-1")}
                value={selectedProjectCode || ""}
                onChange={(e) => loadProject(e.target.value)}
              >
                <option value="">-- Create New Project --</option>
                {projectsList?.projects.map((p: any) => (
                  <option key={p.code} value={p.code}>
                    {p.code} - {p.name}
                  </option>
                ))}
              </select>
            </div>
            {editMode && (
              <Button className={ds.buttons.secondary} onClick={clearForm}>
                Create New Instead
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Progress Steps */}
      <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            {[
              { num: 1, label: "Project Info" },
              { num: 2, label: "Phase Breakdown" },
              { num: 3, label: "Invoices" },
            ].map((step, idx) => (
              <div key={step.num} className="flex items-center gap-2">
                <button
                  onClick={() => setActiveStep(step.num)}
                  className={cn(
                    "flex items-center justify-center w-10 h-10 rounded-full font-bold transition-all",
                    activeStep === step.num
                      ? "bg-teal-600 text-white scale-110"
                      : activeStep > step.num
                      ? "bg-emerald-600 text-white"
                      : "bg-slate-200 text-slate-600"
                  )}
                >
                  {activeStep > step.num ? <CheckCircle2 className="h-5 w-5" /> : step.num}
                </button>
                <span className={cn(ds.typography.bodyBold, ds.textColors.primary)}>
                  {step.label}
                </span>
                {idx < 2 && (
                  <ChevronRight className="h-5 w-5 text-slate-400 mx-2" />
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Step 1: Project Info */}
      {activeStep === 1 && (
        <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
          <CardHeader>
            <CardTitle className={cn(ds.typography.heading3, ds.textColors.primary)}>
              Step 1: Project Information
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className={cn(ds.typography.caption, ds.textColors.secondary)}>
                  Project Code <span className="text-red-500">*</span>
                </Label>
                <Input
                  placeholder="e.g., 25-BK-001"
                  value={projectCode}
                  onChange={(e) => setProjectCode(e.target.value)}
                  disabled={editMode}
                  className={cn(ds.inputs.default, "mt-1", editMode && "bg-slate-100")}
                />
                {editMode && (
                  <p className={cn(ds.typography.tiny, ds.textColors.muted, "mt-1")}>
                    Project code cannot be changed
                  </p>
                )}
              </div>
              <div>
                <Label className={cn(ds.typography.caption, ds.textColors.secondary)}>
                  Project Name <span className="text-red-500">*</span>
                </Label>
                <Input
                  placeholder="e.g., Rosewood Phuket"
                  value={projectTitle}
                  onChange={(e) => setProjectTitle(e.target.value)}
                  className={cn(ds.inputs.default, "mt-1")}
                />
              </div>
              <div>
                <Label className={cn(ds.typography.caption, ds.textColors.secondary)}>
                  Total Contract Fee (USD) <span className="text-red-500">*</span>
                </Label>
                <Input
                  type="number"
                  placeholder="e.g., 475000"
                  value={totalFee}
                  onChange={(e) => setTotalFee(e.target.value)}
                  className={cn(ds.inputs.default, "mt-1")}
                />
              </div>
              <div>
                <Label className={cn(ds.typography.caption, ds.textColors.secondary)}>
                  Country
                </Label>
                <Input
                  placeholder="e.g., Thailand"
                  value={country}
                  onChange={(e) => setCountry(e.target.value)}
                  className={cn(ds.inputs.default, "mt-1")}
                />
              </div>
              <div>
                <Label className={cn(ds.typography.caption, ds.textColors.secondary)}>
                  City
                </Label>
                <Input
                  placeholder="e.g., Phuket"
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                  className={cn(ds.inputs.default, "mt-1")}
                />
              </div>
            </div>

            <div className="flex justify-end">
              <Button
                onClick={() => setActiveStep(2)}
                disabled={!projectCode || !projectTitle || (!totalFee && !editMode)}
                className={ds.buttons.primary}
              >
                Continue to Phase Breakdown
                <ChevronRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 2: Phase Breakdown */}
      {activeStep === 2 && (
        <div className="space-y-4">
          {/* View Existing Breakdowns Section - Only show in edit mode */}
          {editMode && selectedProjectCode && (
            <Card className={cn(ds.borderRadius.card, "border-blue-200 bg-blue-50/30")}>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className={cn(ds.typography.heading3, "text-blue-900 flex items-center gap-2")}>
                    <Eye className="h-5 w-5" />
                    Existing Fee Breakdowns
                  </CardTitle>
                  <Button
                    className={ds.buttons.secondary}
                    onClick={() => setShowExistingBreakdowns(!showExistingBreakdowns)}
                  >
                    {showExistingBreakdowns ? "Hide" : "Show"}
                  </Button>
                </div>
              </CardHeader>
              {showExistingBreakdowns && (
                <CardContent>
                  {breakdownsLoading ? (
                    <BreakdownsSkeleton />
                  ) : existingBreakdowns?.breakdowns && existingBreakdowns.breakdowns.length > 0 ? (
                    <div className="space-y-4">
                      {/* Summary */}
                      <div className="grid grid-cols-4 gap-3">
                        <div className={cn("bg-white rounded-lg p-3 border", ds.borderRadius.card)}>
                          <p className={cn(ds.typography.caption, ds.textColors.muted)}>Contract Value</p>
                          <p className={cn(ds.typography.bodyBold, ds.textColors.primary)}>
                            ${existingBreakdowns.contract_value?.toLocaleString() || 0}
                          </p>
                        </div>
                        <div className={cn("bg-white rounded-lg p-3 border", ds.borderRadius.card)}>
                          <p className={cn(ds.typography.caption, ds.textColors.muted)}>Total Breakdown Fee</p>
                          <p className={cn(ds.typography.bodyBold, ds.textColors.primary)}>
                            ${existingBreakdowns.summary.total_breakdown_fee.toLocaleString()}
                          </p>
                        </div>
                        <div className={cn("bg-white rounded-lg p-3 border", ds.borderRadius.card)}>
                          <p className={cn(ds.typography.caption, ds.textColors.muted)}>Total Invoiced</p>
                          <p className={cn(ds.typography.bodyBold, "text-blue-600")}>
                            ${existingBreakdowns.summary.total_invoiced.toLocaleString()}
                          </p>
                        </div>
                        <div className={cn("bg-white rounded-lg p-3 border", ds.borderRadius.card)}>
                          <p className={cn(ds.typography.caption, ds.textColors.muted)}>Total Paid</p>
                          <p className={cn(ds.typography.bodyBold, "text-emerald-600")}>
                            ${existingBreakdowns.summary.total_paid.toLocaleString()}
                          </p>
                        </div>
                      </div>

                      {/* Breakdown Table */}
                      <div className="overflow-x-auto rounded-lg border bg-white">
                        <table className="min-w-full divide-y divide-slate-200">
                          <thead className={ds.tables.header}>
                            <tr>
                              <th className={ds.tables.headerCell}>Scope</th>
                              <th className={ds.tables.headerCell}>Discipline</th>
                              <th className={ds.tables.headerCell}>Phase</th>
                              <th className={ds.tables.headerCellRight}>Fee</th>
                              <th className={ds.tables.headerCellRight}>Invoiced</th>
                              <th className={ds.tables.headerCellRight}>Paid</th>
                            </tr>
                          </thead>
                          <tbody className={cn("bg-white", ds.tables.divider)}>
                            {existingBreakdowns.breakdowns.map((breakdown) => (
                              <tr key={breakdown.breakdown_id} className={ds.tables.row}>
                                <td className={ds.tables.cell}>{breakdown.scope || '-'}</td>
                                <td className={ds.tables.cell}>
                                  <Badge className={ds.badges.default}>{breakdown.discipline}</Badge>
                                </td>
                                <td className={cn(ds.tables.cell, "font-medium")}>{breakdown.phase}</td>
                                <td className={ds.tables.cellNumber}>${breakdown.phase_fee_usd.toLocaleString()}</td>
                                <td className={ds.tables.cellNumber}>
                                  <span className="text-blue-600">${breakdown.total_invoiced.toLocaleString()}</span>
                                  <span className={cn(ds.typography.tiny, ds.textColors.muted, "ml-1")}>
                                    ({breakdown.percentage_invoiced}%)
                                  </span>
                                </td>
                                <td className={ds.tables.cellNumber}>
                                  <span className="text-emerald-600">${breakdown.total_paid.toLocaleString()}</span>
                                  <span className={cn(ds.typography.tiny, ds.textColors.muted, "ml-1")}>
                                    ({breakdown.percentage_paid}%)
                                  </span>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>

                      <div className={cn("flex items-center gap-2 p-3 rounded-lg", ds.status.warning.bg, ds.status.warning.border, ds.typography.caption, ds.status.warning.text)}>
                        <AlertTriangle className="h-4 w-4" />
                        <span>Adding a duplicate discipline/phase combination will be prevented to avoid data conflicts.</span>
                      </div>
                    </div>
                  ) : (
                    <div className={cn("text-center py-8", ds.textColors.muted)}>
                      <p className={ds.typography.body}>No existing breakdowns for this project.</p>
                      <p className={ds.typography.caption}>Add phases below to create the fee breakdown structure.</p>
                    </div>
                  )}
                </CardContent>
              )}
            </Card>
          )}

          <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
            <CardHeader>
              <CardTitle className={cn(ds.typography.heading3, ds.textColors.primary)}>
                Step 2: Add Phase Breakdown
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-4 gap-4">
                <div>
                  <Label className={cn(ds.typography.caption, ds.textColors.secondary)}>Discipline</Label>
                  <select
                    className={cn(ds.inputs.default, "w-full h-10 mt-1")}
                    value={currentPhase.discipline}
                    onChange={(e) =>
                      setCurrentPhase({ ...currentPhase, discipline: e.target.value })
                    }
                  >
                    {disciplines.map((d) => (
                      <option key={d} value={d}>
                        {d}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <Label className={cn(ds.typography.caption, ds.textColors.secondary)}>Phase</Label>
                  <select
                    className={cn(ds.inputs.default, "w-full h-10 mt-1")}
                    value={currentPhase.phase}
                    onChange={(e) =>
                      setCurrentPhase({ ...currentPhase, phase: e.target.value })
                    }
                  >
                    <option value="">Select phase...</option>
                    {commonPhases.map((p) => (
                      <option key={p} value={p}>
                        {p}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <Label className={cn(ds.typography.caption, ds.textColors.secondary)}>Phase Fee (USD)</Label>
                  <Input
                    type="number"
                    placeholder="e.g., 71250"
                    value={currentPhase.phase_fee_usd}
                    onChange={(e) =>
                      setCurrentPhase({ ...currentPhase, phase_fee_usd: e.target.value })
                    }
                    className={cn(ds.inputs.default, "mt-1")}
                  />
                </div>
                <div className="flex items-end">
                  <Button onClick={addPhase} className={cn(ds.buttons.primary, "w-full gap-2")}>
                    <Plus className="h-4 w-4" />
                    Add Phase
                  </Button>
                </div>
              </div>

              {/* Phase List */}
              {phases.length > 0 && (
                <div className="space-y-2 mt-4">
                  <h3 className={cn(ds.typography.bodyBold, ds.textColors.primary)}>
                    Added Phases ({phases.length})
                  </h3>
                  {phases.map((phase) => (
                    <div
                      key={phase.id}
                      className={cn("flex items-center justify-between p-3 rounded-lg border", ds.status.neutral.bg)}
                    >
                      <div className="flex items-center gap-4">
                        <Badge className={ds.badges.default}>{phase.discipline}</Badge>
                        <span className={cn(ds.typography.bodyBold, ds.textColors.primary)}>{phase.phase}</span>
                        <span className={cn(ds.typography.body, ds.textColors.secondary)}>
                          ${phase.phase_fee_usd.toLocaleString()}
                        </span>
                        <Badge className={ds.badges.info}>{phase.percentage_of_total.toFixed(1)}%</Badge>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removePhase(phase.id)}
                      >
                        <Trash2 className="h-4 w-4 text-red-600" />
                      </Button>
                    </div>
                  ))}

                  {/* Totals */}
                  <div className={cn("flex justify-between items-center p-3 rounded-lg", ds.status.info.bg, ds.status.info.border, ds.typography.bodyBold)}>
                    <span>Total Phases:</span>
                    <span>${totalPhases.toLocaleString()} USD</span>
                  </div>
                  {totalFee && Math.abs(totalPhases - parseFloat(totalFee)) > 0.01 && (
                    <p className={cn(ds.typography.caption, ds.status.warning.text)}>
                      Phase total (${totalPhases.toLocaleString()}) does not match project total (${parseFloat(totalFee).toLocaleString()})
                    </p>
                  )}
                </div>
              )}

              <div className="flex justify-between mt-6">
                <Button className={ds.buttons.secondary} onClick={() => setActiveStep(1)}>
                  Back to Project Info
                </Button>
                <Button onClick={() => setActiveStep(3)} className={ds.buttons.primary}>
                  Continue to Invoices
                  <ChevronRight className="ml-2 h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Step 3: Invoices */}
      {activeStep === 3 && (
        <div className="space-y-4">
          <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
            <CardHeader>
              <CardTitle className={cn(ds.typography.heading3, ds.textColors.primary)}>
                Step 3: Add Invoices & Payments
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {phases.length === 0 && (
                <div className={cn("p-3 rounded-md", ds.status.warning.bg, ds.status.warning.border, ds.typography.caption, ds.status.warning.text)}>
                  Please add at least one phase/discipline in Step 2 before adding invoices
                </div>
              )}
              <div className="grid grid-cols-3 gap-4">
                <div className="col-span-3">
                  <Label className={cn(ds.typography.caption, ds.textColors.secondary)}>
                    Phase/Discipline <span className="text-red-500">*</span>
                  </Label>
                  <select
                    className={cn(ds.inputs.default, "w-full h-10 mt-1")}
                    value={currentInvoice.breakdown_id}
                    onChange={(e) =>
                      setCurrentInvoice({ ...currentInvoice, breakdown_id: e.target.value })
                    }
                  >
                    <option value="">Select which phase/discipline this invoice is for...</option>
                    {phases.map((phase) => (
                      <option key={phase.id} value={phase.id}>
                        {phase.discipline} - {phase.phase} (${phase.phase_fee_usd.toLocaleString()})
                      </option>
                    ))}
                  </select>
                  <p className={cn(ds.typography.tiny, ds.textColors.muted, "mt-1")}>
                    Select the specific phase and discipline that this invoice entry is billing for
                  </p>
                </div>
                <div>
                  <Label className={cn(ds.typography.caption, ds.textColors.secondary)}>Invoice Number</Label>
                  <Input
                    placeholder="e.g., I25-001"
                    value={currentInvoice.invoice_number}
                    onChange={(e) =>
                      setCurrentInvoice({ ...currentInvoice, invoice_number: e.target.value })
                    }
                    className={cn(ds.inputs.default, "mt-1")}
                  />
                </div>
                <div>
                  <Label className={cn(ds.typography.caption, ds.textColors.secondary)}>Invoice Date</Label>
                  <Input
                    type="date"
                    value={currentInvoice.invoice_date}
                    onChange={(e) =>
                      setCurrentInvoice({ ...currentInvoice, invoice_date: e.target.value })
                    }
                    className={cn(ds.inputs.default, "mt-1")}
                  />
                </div>
                <div>
                  <Label className={cn(ds.typography.caption, ds.textColors.secondary)}>Invoice Amount (USD)</Label>
                  <Input
                    type="number"
                    placeholder="e.g., 71250"
                    value={currentInvoice.invoice_amount}
                    onChange={(e) =>
                      setCurrentInvoice({ ...currentInvoice, invoice_amount: e.target.value })
                    }
                    className={cn(ds.inputs.default, "mt-1")}
                  />
                </div>
                <div>
                  <Label className={cn(ds.typography.caption, ds.textColors.secondary)}>Payment Date (if paid)</Label>
                  <Input
                    type="date"
                    value={currentInvoice.payment_date}
                    onChange={(e) =>
                      setCurrentInvoice({ ...currentInvoice, payment_date: e.target.value })
                    }
                    className={cn(ds.inputs.default, "mt-1")}
                  />
                </div>
                <div>
                  <Label className={cn(ds.typography.caption, ds.textColors.secondary)}>Payment Amount</Label>
                  <Input
                    type="number"
                    placeholder="e.g., 71250"
                    value={currentInvoice.payment_amount}
                    onChange={(e) =>
                      setCurrentInvoice({ ...currentInvoice, payment_amount: e.target.value })
                    }
                    className={cn(ds.inputs.default, "mt-1")}
                  />
                </div>
                <div>
                  <Label className={cn(ds.typography.caption, ds.textColors.secondary)}>Status</Label>
                  <select
                    className={cn(ds.inputs.default, "w-full h-10 mt-1")}
                    value={currentInvoice.status}
                    onChange={(e) =>
                      setCurrentInvoice({ ...currentInvoice, status: e.target.value })
                    }
                  >
                    {invoiceStatuses.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <Button onClick={addInvoice} className={cn(ds.buttons.primary, "w-full gap-2")}>
                <Plus className="h-4 w-4" />
                Add Invoice
              </Button>

              {/* Invoice List */}
              {invoices.length > 0 && (
                <div className="space-y-2 mt-4">
                  <h3 className={cn(ds.typography.bodyBold, ds.textColors.primary)}>
                    Added Invoices ({invoices.length})
                  </h3>
                  {invoices.map((invoice) => {
                    const linkedPhase = phases.find(p => p.id === invoice.breakdown_id);

                    return (
                      <div
                        key={invoice.id}
                        className={cn("flex items-center justify-between p-3 rounded-lg border", ds.status.neutral.bg)}
                      >
                        <div className="flex flex-col gap-1">
                          <div className="flex items-center gap-4">
                            <FileText className="h-4 w-4 text-slate-600" />
                            <span className={cn(ds.typography.bodyBold, ds.textColors.primary)}>
                              {invoice.invoice_number}
                            </span>
                            <span className={cn(ds.typography.body, ds.textColors.secondary)}>
                              {new Date(invoice.invoice_date).toLocaleDateString()}
                            </span>
                            <span className={cn(ds.typography.bodyBold, ds.textColors.primary)}>
                              ${invoice.invoice_amount.toLocaleString()}
                            </span>
                            {getInvoiceStatusBadge(invoice.status)}
                            {invoice.payment_date && (
                              <span className={cn(ds.typography.tiny, "text-emerald-600")}>
                                Paid: {new Date(invoice.payment_date).toLocaleDateString()}
                              </span>
                            )}
                          </div>
                          {linkedPhase && (
                            <div className="flex items-center gap-2 ml-8">
                              <Badge className={ds.badges.info}>
                                {linkedPhase.discipline} - {linkedPhase.phase}
                              </Badge>
                            </div>
                          )}
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => removeInvoice(invoice.id)}
                        >
                          <Trash2 className="h-4 w-4 text-red-600" />
                        </Button>
                      </div>
                    );
                  })}

                  {/* Totals */}
                  <div className="space-y-2">
                    <div className={cn("flex justify-between items-center p-3 rounded-lg", ds.status.info.bg, ds.status.info.border)}>
                      <span className={cn(ds.typography.bodyBold, ds.status.info.text)}>Total Invoiced:</span>
                      <span className={cn(ds.typography.bodyBold, ds.status.info.text)}>${totalInvoices.toLocaleString()} USD</span>
                    </div>
                    <div className={cn("flex justify-between items-center p-3 rounded-lg", ds.status.success.bg, ds.status.success.border)}>
                      <span className={cn(ds.typography.bodyBold, ds.status.success.text)}>Total Paid:</span>
                      <span className={cn(ds.typography.bodyBold, ds.status.success.text)}>${totalPayments.toLocaleString()} USD</span>
                    </div>
                    <div className={cn("flex justify-between items-center p-3 rounded-lg", ds.status.warning.bg, ds.status.warning.border)}>
                      <span className={cn(ds.typography.bodyBold, ds.status.warning.text)}>Outstanding:</span>
                      <span className={cn(ds.typography.bodyBold, ds.status.warning.text)}>${(totalInvoices - totalPayments).toLocaleString()} USD</span>
                    </div>
                  </div>
                </div>
              )}

              <div className="flex justify-between mt-6">
                <Button className={ds.buttons.secondary} onClick={() => setActiveStep(2)}>
                  Back to Phases
                </Button>
                <Button
                  onClick={() => saveAllMutation.mutate()}
                  disabled={saveAllMutation.isPending}
                  size="lg"
                  className={cn(ds.buttons.primary, "gap-2")}
                >
                  <Save className="h-5 w-5" />
                  {saveAllMutation.isPending ? "Saving..." : "Save All Data"}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Summary Card (always visible) */}
      <Card className={cn(ds.borderRadius.card, "bg-gradient-to-br from-slate-50 to-blue-50 border-slate-200")}>
        <CardHeader>
          <CardTitle className={cn(ds.typography.heading3, ds.textColors.primary)}>
            Entry Summary
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div>
              <p className={cn(ds.typography.caption, ds.textColors.muted)}>Project Code</p>
              <p className={cn(ds.typography.bodyBold, ds.textColors.primary)}>{projectCode || "—"}</p>
            </div>
            <div>
              <p className={cn(ds.typography.caption, ds.textColors.muted)}>Project Name</p>
              <p className={cn(ds.typography.bodyBold, ds.textColors.primary)}>{projectTitle || "—"}</p>
            </div>
            <div>
              <p className={cn(ds.typography.caption, ds.textColors.muted)}>Contract Value</p>
              <p className={cn(ds.typography.bodyBold, ds.textColors.primary)}>
                ${totalFee ? parseFloat(totalFee).toLocaleString() : "0"}
              </p>
            </div>
            <div>
              <p className={cn(ds.typography.caption, ds.textColors.muted)}>Phases Added</p>
              <p className={cn(ds.typography.bodyBold, ds.textColors.primary)}>{phases.length}</p>
            </div>
            <div>
              <p className={cn(ds.typography.caption, ds.textColors.muted)}>Invoices Added</p>
              <p className={cn(ds.typography.bodyBold, ds.textColors.primary)}>{invoices.length}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
