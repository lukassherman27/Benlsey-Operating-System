"use client";

import { useState } from "react";
import { useMutation, useQueryClient, useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  DollarSign,
  Plus,
  Save,
  Trash2,
  Calendar,
  FileText,
  ChevronRight,
  CheckCircle2,
  AlertTriangle,
  Eye,
  Loader2
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
  breakdown_id: string;  // Links to specific phase/discipline from project_fee_breakdown
  invoice_number: string;
  invoice_date: string;
  invoice_amount: number;
  payment_date?: string;
  payment_amount?: number;
  status: string;
}

/**
 * Manual Financial Data Entry Page
 * Allows manual input of:
 * - Project code & name
 * - Total project fee
 * - Phase/Discipline breakdown
 * - Individual invoices and payments
 */
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
      // Fetch project data (includes project info, phases, and invoices)
      const projectData = await api.getProjectData(code);

      // Populate form with project info
      setProjectCode(code);
      setProjectTitle(projectData.project.project_title || "");
      setTotalFee(projectData.project.total_fee_usd?.toString() || "");
      setCountry(projectData.project.country || "");
      setCity(projectData.project.city || "");

      // Load phases
      setPhases(projectData.phases.map((p: any) => ({
        id: p.breakdown_id.toString(),
        discipline: p.discipline,
        phase: p.phase,
        phase_fee_usd: p.phase_fee_usd,
        percentage_of_total: p.percentage_of_total || 0,
      })));

      // Load invoices
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

      toast.success(`Loaded ${code}`);
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);
      toast.error(`Failed to load project: ${errorMsg}`);
      console.error("Load error:", error);
      // Reset to create mode on error
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

    // Check for duplicate in local phases list
    const localDuplicate = phases.find(
      p => p.discipline === currentPhase.discipline && p.phase === currentPhase.phase
    );
    if (localDuplicate) {
      toast.error(`Duplicate: ${currentPhase.discipline} - ${currentPhase.phase} already added locally`);
      return;
    }

    // Check for duplicate in existing breakdowns (from database)
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
        // UPDATE MODE
        await api.updateProject(projectCode, {
          project_title: projectTitle,
          total_fee_usd: parseFloat(totalFee),
          country: country || "Unknown",
          city: city || "Unknown",
        });

        // Update phases
        for (const phase of phases) {
          if (phase.id.startsWith('phase-')) {
            // New phase, create it
            await api.createFeeBreakdown({
              project_code: projectCode,
              discipline: phase.discipline,
              phase: phase.phase,
              phase_fee_usd: phase.phase_fee_usd,
              percentage_of_total: phase.percentage_of_total,
            });
          } else {
            // Existing phase, update it (can only change fee amounts, not discipline/phase)
            await api.updatePhaseFee(phase.id, {
              phase_fee_usd: phase.phase_fee_usd,
              percentage_of_total: phase.percentage_of_total,
            });
          }
        }

        // Update invoices
        for (const invoice of invoices) {
          if (invoice.id.startsWith('invoice-')) {
            // New invoice, create it
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
            // Existing invoice, update it
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
        // CREATE MODE (existing code)
        const projectResponse = await api.createProject({
          project_code: projectCode,
          project_title: projectTitle,
          total_fee_usd: parseFloat(totalFee),
          country: country || "Unknown",
          city: city || "Unknown",
          status: "active",
        });

        // Then save phases
        for (const phase of phases) {
          await api.createFeeBreakdown({
            project_code: projectCode,
            discipline: phase.discipline,
            phase: phase.phase,
            phase_fee_usd: phase.phase_fee_usd,
            percentage_of_total: phase.percentage_of_total,
          });
        }

        // Finally save invoices
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
      toast.success(editMode ? "Project updated!" : "All data saved successfully!");
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      queryClient.invalidateQueries({ queryKey: ["invoices"] });
      queryClient.invalidateQueries({ queryKey: ["projects-list"] });

      // Reset form
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

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <DollarSign className="h-8 w-8 text-green-600" />
            {editMode ? `Edit Project: ${projectCode}` : "Manual Financial Data Entry"}
          </h1>
          <p className="text-muted-foreground mt-1">
            {editMode ? "Update existing project data" : "Enter project financials manually without importing"}
          </p>
        </div>
        <Button
          onClick={() => saveAllMutation.mutate()}
          disabled={!projectCode || !projectTitle || saveAllMutation.isPending}
          size="lg"
          className="gap-2"
        >
          <Save className="h-5 w-5" />
          {saveAllMutation.isPending ? "Saving..." : (editMode ? "Update Project" : "Save All Data")}
        </Button>
      </div>

      {/* Project Selector for Edit Mode */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <Label>Load Existing Project</Label>
              <select
                className="w-full h-10 px-3 rounded-md border border-gray-300"
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
              <Button variant="outline" onClick={clearForm}>
                Create New Instead
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Progress Steps */}
      <Card>
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
                  className={`flex items-center justify-center w-10 h-10 rounded-full font-bold transition-all ${
                    activeStep === step.num
                      ? "bg-blue-600 text-white scale-110"
                      : activeStep > step.num
                      ? "bg-green-600 text-white"
                      : "bg-gray-200 text-gray-600"
                  }`}
                >
                  {activeStep > step.num ? <CheckCircle2 className="h-5 w-5" /> : step.num}
                </button>
                <span className="text-sm font-medium">{step.label}</span>
                {idx < 2 && (
                  <ChevronRight className="h-5 w-5 text-gray-400 mx-2" />
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Step 1: Project Info */}
      {activeStep === 1 && (
        <Card>
          <CardHeader>
            <CardTitle>Step 1: Project Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="projectCode">
                  Project Code <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="projectCode"
                  placeholder="e.g., 25-BK-001"
                  value={projectCode}
                  onChange={(e) => setProjectCode(e.target.value)}
                  disabled={editMode}
                  className={editMode ? "bg-gray-100" : ""}
                />
                {editMode && (
                  <p className="text-xs text-gray-500 mt-1">Project code cannot be changed</p>
                )}
              </div>
              <div>
                <Label htmlFor="projectTitle">
                  Project Name <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="projectTitle"
                  placeholder="e.g., Rosewood Phuket"
                  value={projectTitle}
                  onChange={(e) => setProjectTitle(e.target.value)}
                />
              </div>
              <div>
                <Label htmlFor="totalFee">
                  Total Contract Fee (USD) <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="totalFee"
                  type="number"
                  placeholder="e.g., 475000"
                  value={totalFee}
                  onChange={(e) => setTotalFee(e.target.value)}
                />
              </div>
              <div>
                <Label htmlFor="country">Country</Label>
                <Input
                  id="country"
                  placeholder="e.g., Thailand"
                  value={country}
                  onChange={(e) => setCountry(e.target.value)}
                />
              </div>
              <div>
                <Label htmlFor="city">City</Label>
                <Input
                  id="city"
                  placeholder="e.g., Phuket"
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                />
              </div>
            </div>

            <div className="flex justify-end">
              <Button
                onClick={() => setActiveStep(2)}
                disabled={!projectCode || !projectTitle || (!totalFee && !editMode)}
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
            <Card className="border-blue-200 bg-blue-50/30">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-blue-900">
                    <Eye className="h-5 w-5" />
                    Existing Fee Breakdowns
                  </CardTitle>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowExistingBreakdowns(!showExistingBreakdowns)}
                  >
                    {showExistingBreakdowns ? "Hide" : "Show"}
                  </Button>
                </div>
              </CardHeader>
              {showExistingBreakdowns && (
                <CardContent>
                  {breakdownsLoading ? (
                    <div className="flex items-center justify-center py-8">
                      <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
                      <span className="ml-2 text-sm text-gray-600">Loading existing breakdowns...</span>
                    </div>
                  ) : existingBreakdowns?.breakdowns && existingBreakdowns.breakdowns.length > 0 ? (
                    <div className="space-y-4">
                      {/* Summary */}
                      <div className="grid grid-cols-4 gap-3 text-sm">
                        <div className="bg-white rounded-lg p-3 border">
                          <p className="text-gray-500">Contract Value</p>
                          <p className="font-bold text-lg">${existingBreakdowns.contract_value?.toLocaleString() || 0}</p>
                        </div>
                        <div className="bg-white rounded-lg p-3 border">
                          <p className="text-gray-500">Total Breakdown Fee</p>
                          <p className="font-bold text-lg">${existingBreakdowns.summary.total_breakdown_fee.toLocaleString()}</p>
                        </div>
                        <div className="bg-white rounded-lg p-3 border">
                          <p className="text-gray-500">Total Invoiced</p>
                          <p className="font-bold text-lg text-blue-600">${existingBreakdowns.summary.total_invoiced.toLocaleString()}</p>
                        </div>
                        <div className="bg-white rounded-lg p-3 border">
                          <p className="text-gray-500">Total Paid</p>
                          <p className="font-bold text-lg text-green-600">${existingBreakdowns.summary.total_paid.toLocaleString()}</p>
                        </div>
                      </div>

                      {/* Breakdown Table */}
                      <div className="overflow-x-auto rounded-lg border bg-white">
                        <table className="min-w-full divide-y divide-gray-200">
                          <thead className="bg-gray-50">
                            <tr>
                              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Scope</th>
                              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Discipline</th>
                              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Phase</th>
                              <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Fee</th>
                              <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Invoiced</th>
                              <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Paid</th>
                            </tr>
                          </thead>
                          <tbody className="bg-white divide-y divide-gray-200">
                            {existingBreakdowns.breakdowns.map((breakdown) => (
                              <tr key={breakdown.breakdown_id} className="hover:bg-gray-50">
                                <td className="px-4 py-2 text-sm text-gray-900">{breakdown.scope || '-'}</td>
                                <td className="px-4 py-2 text-sm">
                                  <Badge variant="outline">{breakdown.discipline}</Badge>
                                </td>
                                <td className="px-4 py-2 text-sm font-medium text-gray-900">{breakdown.phase}</td>
                                <td className="px-4 py-2 text-sm text-right font-medium">${breakdown.phase_fee_usd.toLocaleString()}</td>
                                <td className="px-4 py-2 text-sm text-right">
                                  <span className="text-blue-600">${breakdown.total_invoiced.toLocaleString()}</span>
                                  <span className="text-gray-400 text-xs ml-1">({breakdown.percentage_invoiced}%)</span>
                                </td>
                                <td className="px-4 py-2 text-sm text-right">
                                  <span className="text-green-600">${breakdown.total_paid.toLocaleString()}</span>
                                  <span className="text-gray-400 text-xs ml-1">({breakdown.percentage_paid}%)</span>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>

                      <div className="flex items-center gap-2 p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-sm text-yellow-800">
                        <AlertTriangle className="h-4 w-4" />
                        <span>Adding a duplicate discipline/phase combination will be prevented to avoid data conflicts.</span>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-8 text-gray-500">
                      <p>No existing breakdowns for this project.</p>
                      <p className="text-sm">Add phases below to create the fee breakdown structure.</p>
                    </div>
                  )}
                </CardContent>
              )}
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle>Step 2: Add Phase Breakdown</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-4 gap-4">
                <div>
                  <Label>Discipline</Label>
                  <select
                    className="w-full h-10 px-3 rounded-md border border-gray-300"
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
                  <Label>Phase</Label>
                  <select
                    className="w-full h-10 px-3 rounded-md border border-gray-300"
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
                  <Label>Phase Fee (USD)</Label>
                  <Input
                    type="number"
                    placeholder="e.g., 71250"
                    value={currentPhase.phase_fee_usd}
                    onChange={(e) =>
                      setCurrentPhase({ ...currentPhase, phase_fee_usd: e.target.value })
                    }
                  />
                </div>
                <div className="flex items-end">
                  <Button onClick={addPhase} className="w-full gap-2">
                    <Plus className="h-4 w-4" />
                    Add Phase
                  </Button>
                </div>
              </div>

              {/* Phase List */}
              {phases.length > 0 && (
                <div className="space-y-2 mt-4">
                  <h3 className="font-semibold">Added Phases ({phases.length})</h3>
                  {phases.map((phase) => (
                    <div
                      key={phase.id}
                      className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border"
                    >
                      <div className="flex items-center gap-4">
                        <Badge variant="outline">{phase.discipline}</Badge>
                        <span className="font-medium">{phase.phase}</span>
                        <span className="text-sm text-gray-600">
                          ${phase.phase_fee_usd.toLocaleString()}
                        </span>
                        <Badge>{phase.percentage_of_total.toFixed(1)}%</Badge>
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
                  <div className="flex justify-between items-center p-3 bg-blue-50 rounded-lg border border-blue-200 font-semibold">
                    <span>Total Phases:</span>
                    <span>${totalPhases.toLocaleString()} USD</span>
                  </div>
                  {totalFee && Math.abs(totalPhases - parseFloat(totalFee)) > 0.01 && (
                    <p className="text-sm text-orange-600">
                      ⚠️ Phase total (${totalPhases.toLocaleString()}) doesn&apos;t match project total (${parseFloat(totalFee).toLocaleString()})
                    </p>
                  )}
                </div>
              )}

              <div className="flex justify-between mt-6">
                <Button variant="outline" onClick={() => setActiveStep(1)}>
                  Back to Project Info
                </Button>
                <Button onClick={() => setActiveStep(3)}>
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
          <Card>
            <CardHeader>
              <CardTitle>Step 3: Add Invoices & Payments</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {phases.length === 0 && (
                <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-md text-sm text-yellow-800">
                  ⚠️ Please add at least one phase/discipline in Step 2 before adding invoices
                </div>
              )}
              <div className="grid grid-cols-3 gap-4">
                <div className="col-span-3">
                  <Label>
                    Phase/Discipline <span className="text-red-500">*</span>
                  </Label>
                  <select
                    className="w-full h-10 px-3 rounded-md border border-gray-300"
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
                  <p className="text-xs text-gray-500 mt-1">
                    Select the specific phase and discipline that this invoice entry is billing for
                  </p>
                </div>
                <div>
                  <Label>Invoice Number</Label>
                  <Input
                    placeholder="e.g., I25-001"
                    value={currentInvoice.invoice_number}
                    onChange={(e) =>
                      setCurrentInvoice({ ...currentInvoice, invoice_number: e.target.value })
                    }
                  />
                </div>
                <div>
                  <Label>Invoice Date</Label>
                  <Input
                    type="date"
                    value={currentInvoice.invoice_date}
                    onChange={(e) =>
                      setCurrentInvoice({ ...currentInvoice, invoice_date: e.target.value })
                    }
                  />
                </div>
                <div>
                  <Label>Invoice Amount (USD)</Label>
                  <Input
                    type="number"
                    placeholder="e.g., 71250"
                    value={currentInvoice.invoice_amount}
                    onChange={(e) =>
                      setCurrentInvoice({ ...currentInvoice, invoice_amount: e.target.value })
                    }
                  />
                </div>
                <div>
                  <Label>Payment Date (if paid)</Label>
                  <Input
                    type="date"
                    value={currentInvoice.payment_date}
                    onChange={(e) =>
                      setCurrentInvoice({ ...currentInvoice, payment_date: e.target.value })
                    }
                  />
                </div>
                <div>
                  <Label>Payment Amount</Label>
                  <Input
                    type="number"
                    placeholder="e.g., 71250"
                    value={currentInvoice.payment_amount}
                    onChange={(e) =>
                      setCurrentInvoice({ ...currentInvoice, payment_amount: e.target.value })
                    }
                  />
                </div>
                <div>
                  <Label>Status</Label>
                  <select
                    className="w-full h-10 px-3 rounded-md border border-gray-300"
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

              <Button onClick={addInvoice} className="w-full gap-2">
                <Plus className="h-4 w-4" />
                Add Invoice
              </Button>

              {/* Invoice List */}
              {invoices.length > 0 && (
                <div className="space-y-2 mt-4">
                  <h3 className="font-semibold">Added Invoices ({invoices.length})</h3>
                  {invoices.map((invoice) => {
                    // Find the corresponding phase/discipline
                    const linkedPhase = phases.find(p => p.id === invoice.breakdown_id);

                    return (
                      <div
                        key={invoice.id}
                        className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border"
                      >
                        <div className="flex flex-col gap-1">
                          <div className="flex items-center gap-4">
                            <FileText className="h-4 w-4 text-gray-600" />
                            <span className="font-medium">{invoice.invoice_number}</span>
                            <span className="text-sm text-gray-600">
                              {new Date(invoice.invoice_date).toLocaleDateString()}
                            </span>
                            <span className="font-semibold">
                              ${invoice.invoice_amount.toLocaleString()}
                            </span>
                            <Badge
                              variant={invoice.status === "Paid" ? "default" : "secondary"}
                            >
                              {invoice.status}
                            </Badge>
                            {invoice.payment_date && (
                              <span className="text-xs text-green-600">
                                Paid: {new Date(invoice.payment_date).toLocaleDateString()}
                              </span>
                            )}
                          </div>
                          {linkedPhase && (
                            <div className="flex items-center gap-2 ml-8 text-sm text-gray-600">
                              <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
                                {linkedPhase.discipline} - {linkedPhase.phase}
                              </span>
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
                    <div className="flex justify-between items-center p-3 bg-blue-50 rounded-lg border border-blue-200">
                      <span className="font-semibold">Total Invoiced:</span>
                      <span className="font-semibold">${totalInvoices.toLocaleString()} USD</span>
                    </div>
                    <div className="flex justify-between items-center p-3 bg-green-50 rounded-lg border border-green-200">
                      <span className="font-semibold">Total Paid:</span>
                      <span className="font-semibold">${totalPayments.toLocaleString()} USD</span>
                    </div>
                    <div className="flex justify-between items-center p-3 bg-orange-50 rounded-lg border border-orange-200">
                      <span className="font-semibold">Outstanding:</span>
                      <span className="font-semibold">${(totalInvoices - totalPayments).toLocaleString()} USD</span>
                    </div>
                  </div>
                </div>
              )}

              <div className="flex justify-between mt-6">
                <Button variant="outline" onClick={() => setActiveStep(2)}>
                  Back to Phases
                </Button>
                <Button
                  onClick={() => saveAllMutation.mutate()}
                  disabled={saveAllMutation.isPending}
                  size="lg"
                  className="gap-2"
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
      <Card className="bg-gradient-to-br from-slate-50 to-blue-50">
        <CardHeader>
          <CardTitle>Entry Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div>
              <p className="text-sm text-gray-600">Project Code</p>
              <p className="font-semibold">{projectCode || "—"}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Project Name</p>
              <p className="font-semibold">{projectTitle || "—"}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Contract Value</p>
              <p className="font-semibold">
                ${totalFee ? parseFloat(totalFee).toLocaleString() : "0"}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Phases Added</p>
              <p className="font-semibold">{phases.length}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Invoices Added</p>
              <p className="font-semibold">{invoices.length}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
