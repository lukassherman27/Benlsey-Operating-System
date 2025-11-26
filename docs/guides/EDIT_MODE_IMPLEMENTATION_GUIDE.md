# Edit Mode Implementation Guide

## Goal
Add ability to **load and edit existing projects** in the financial entry page.

---

## Backend Endpoints (Already Exist ✅)

### GET Endpoints:
```
GET /api/projects/linking-list          → List all projects
GET /api/projects/{project_code}/fee-breakdown  → Get phases
GET /api/invoices/by-project/{project_code}     → Get invoices
```

### UPDATE Endpoints:
```
PUT /api/projects/{project_code}         → Update project info
PUT /api/invoices/{invoice_number}       → Update invoice
PUT /api/phase-fees/{breakdown_id}       → Update phase fee
```

---

## Frontend Changes Needed

### 1. Add Project Selector (Top of Page)

```tsx
// Add new state
const [selectedProjectCode, setSelectedProjectCode] = useState<string | null>(null);
const [editMode, setEditMode] = useState(false);

// Add query to load projects list
const { data: projectsList } = useQuery({
  queryKey: ["projects-list"],
  queryFn: () => api.getProjectsLinkingList(1000),
});

// Add query to load project data when selected
const { data: projectData } = useQuery({
  queryKey: ["project-data", selectedProjectCode],
  queryFn: () => api.getProjectData(selectedProjectCode!),
  enabled: !!selectedProjectCode,
});
```

### 2. Add Project Search Component

```tsx
<Card>
  <CardContent className="pt-6">
    <div className="flex items-center gap-4">
      <div className="flex-1">
        <Label>Load Existing Project</Label>
        <select
          className="w-full h-10 px-3 rounded-md border"
          value={selectedProjectCode || ""}
          onChange={(e) => loadProject(e.target.value)}
        >
          <option value="">-- Create New Project --</option>
          {projectsList?.projects.map((p) => (
            <option key={p.project_code} value={p.project_code}>
              {p.project_code} - {p.project_title}
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
```

### 3. Add Load Function

```tsx
const loadProject = async (code: string) => {
  if (!code) {
    clearForm();
    return;
  }

  setEditMode(true);
  setSelectedProjectCode(code);

  try {
    // Fetch project data
    const [projectInfo, phasesData, invoicesData] = await Promise.all([
      api.getProject(code),
      api.getFeeBreakdown(code),
      api.getInvoicesByProject(code),
    ]);

    // Populate form
    setProjectCode(projectInfo.project_code);
    setProjectTitle(projectInfo.project_title);
    setTotalFee(projectInfo.total_fee_usd?.toString() || "");
    setCountry(projectInfo.country || "");
    setCity(projectInfo.city || "");

    // Load phases
    setPhases(phasesData.map(p => ({
      id: p.breakdown_id,
      discipline: p.discipline,
      phase: p.phase,
      phase_fee_usd: p.phase_fee_usd,
      percentage_of_total: p.percentage_of_total || 0,
    })));

    // Load invoices
    setInvoices(invoicesData.map(inv => ({
      id: inv.invoice_id.toString(),
      phase_id: "",
      invoice_number: inv.invoice_number,
      invoice_date: inv.invoice_date,
      invoice_amount: inv.invoice_amount,
      payment_date: inv.payment_date,
      payment_amount: inv.payment_amount,
      status: inv.status,
    })));

    toast.success(`Loaded ${code}`);
  } catch (error) {
    toast.error(`Failed to load project: ${error}`);
  }
};
```

### 4. Update Save Mutation

```tsx
const saveAllMutation = useMutation({
  mutationFn: async () => {
    if (editMode) {
      // UPDATE MODE
      await api.updateProject(projectCode, {
        project_title: projectTitle,
        total_fee_usd: parseFloat(totalFee),
        country,
        city,
      });

      // Update phases
      for (const phase of phases) {
        if (phase.id.startsWith('phase-')) {
          // New phase, create it
          await api.createPhaseFee({ ... });
        } else {
          // Existing phase, update it
          await api.updatePhaseFee(phase.id, { ... });
        }
      }

      // Update invoices
      for (const invoice of invoices) {
        if (invoice.id.startsWith('invoice-')) {
          // New invoice, create it
          await api.createInvoice({ ... });
        } else {
          // Existing invoice, update it
          await api.updateInvoice(invoice.invoice_number, { ... });
        }
      }
    } else {
      // CREATE MODE (existing code)
      // ... keep current create logic
    }
  },
  onSuccess: () => {
    toast.success(editMode ? "Project updated!" : "Project created!");
    clearForm();
  },
});
```

### 5. Add Clear Function

```tsx
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
```

### 6. Add Missing API Functions

In `frontend/src/lib/api.ts`:

```ts
// Add these functions:
getProjectsLinkingList: (limit: number = 500) =>
  request(`/api/projects/linking-list?limit=${limit}`),

getProject: (project_code: string) =>
  request(`/api/projects/${project_code}`),

getFeeBreakdown: (project_code: string) =>
  request(`/api/projects/${project_code}/fee-breakdown`),

getInvoicesByProject: (project_code: string) =>
  request(`/api/invoices/by-project/${project_code}`),

updateProject: (project_code: string, data: UpdateProjectRequest) =>
  request(`/api/projects/${project_code}`, {
    method: "PUT",
    body: JSON.stringify(data),
  }),

updateInvoice: (invoice_number: string, data: UpdateInvoiceRequest) =>
  request(`/api/invoices/${invoice_number}`, {
    method: "PUT",
    body: JSON.stringify(data),
  }),

updatePhaseFee: (breakdown_id: string, data: UpdatePhaseFeeRequest) =>
  request(`/api/phase-fees/${breakdown_id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  }),
```

---

## UI Changes

### Header
Change "Manual Financial Data Entry" to show mode:
```tsx
<h1>
  {editMode ? `Edit Project: ${projectCode}` : "Manual Financial Data Entry"}
</h1>
```

### Save Button
Change label based on mode:
```tsx
<Button onClick={() => saveAllMutation.mutate()}>
  {editMode ? "Update Project" : "Create Project"}
</Button>
```

---

## Testing Checklist

- [ ] Can load existing project from dropdown
- [ ] Project data populates correctly
- [ ] Can edit project info and save
- [ ] Can add new phases to existing project
- [ ] Can edit existing phases
- [ ] Can add new invoices to existing project
- [ ] Can edit existing invoices
- [ ] Can switch from edit mode back to create mode
- [ ] Can create new project after loading existing one

---

## Estimated Time: 30-45 minutes
