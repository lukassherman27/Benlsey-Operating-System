import {
  AnalyticsDashboard,
  ProposalsQueryParams,
  ProposalDetail,
  ProposalHealth,
  ProposalSummary,
  ProposalTimelineResponse,
  ProposalBriefing,
  DecisionTiles,
  SystemHealth,
  ManualOverride,
  ManualOverridesResponse,
  ManualOverrideCreateRequest,
  ManualOverrideUpdateRequest,
  QueryResponse,
  QuerySuggestionsResponse,
  EmailSummary,
  EmailCategoryCounts,
  EmailCategoryListResponse,
  EmailCategoryUpdateRequest,
  EmailCategoryUpdateResponse,
  Pagination,
  DashboardStats,
  DashboardKPIs,
  ProposalStats,
  TopValueProposal,
  DailyBriefing,
  IntelligenceSuggestionsResponse,
  IntelligenceDecisionRequest,
  IntelligenceDecisionResponse,
  RecentPaymentsResponse,
  ProjectedInvoicesResponse,
  ProposalWeeklyChanges,
  ProposalTrackerQueryParams,
  ProposalTrackerStatsResponse,
  ProposalTrackerListResponse,
  ProposalTrackerDetailResponse,
  ProposalTrackerUpdateRequest,
  ProposalStatusHistoryItem,
  ProposalEmailIntelligence,
  DisciplineStatsResponse,
  ValidationSuggestionsResponse,
  ValidationSuggestion,
  ApproveSuggestionRequest,
  DenySuggestionRequest,
  EmailLinksResponse,
  CreateEmailLinkRequest,
  InvoiceAgingResponse,
  InvoiceAgingData,
  Project,
  ActiveProjectsResponse,
  ProjectEmailsResponse,
  ProjectEmailSummary,
  ProjectHierarchy,
} from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

async function request<T>(
  path: string,
  init?: RequestInit,
  signal?: AbortSignal
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
    signal,
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const text = await response.text();
      if (text) {
        const maybeJson = JSON.parse(text);
        detail =
          maybeJson.detail ??
          maybeJson.message ??
          (typeof maybeJson === "string" ? maybeJson : JSON.stringify(maybeJson));
      }
    } catch {
      // Ignore JSON parse errors and keep fallback detail
    }

    throw new Error(
      detail || `API request failed (${response.status})`
    );
  }

  return (await response.json()) as T;
}

function buildQuery(params: Record<string, unknown>): string {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") return;
    searchParams.append(key, String(value));
  });
  const queryString = searchParams.toString();
  return queryString ? `?${queryString}` : "";
}

function normalizePaginationResponse<T>(raw: unknown): {
  data: T[];
  pagination: Pagination;
} {
  if (!raw || typeof raw !== "object") {
    return {
      data: [],
      pagination: { page: 1, per_page: 20, total: 0, total_pages: 0 },
    };
  }

  const payload = raw as Record<string, unknown>;

  const extractArray = (value: unknown): T[] | undefined =>
    Array.isArray(value) ? (value as T[]) : undefined;

  const data =
    extractArray(payload.data) ??
    extractArray(payload.items) ??
    ([] as T[]);

  const paginationSource =
    typeof payload.pagination === "object" && payload.pagination !== null
      ? (payload.pagination as Record<string, unknown>)
      : payload;

  const asNumber = (value: unknown, fallback: number): number =>
    typeof value === "number" ? value : fallback;

  const page = asNumber(paginationSource.page, 1);
  const perPageCandidate =
    asNumber(paginationSource.per_page, NaN) ||
    asNumber(paginationSource.perPage, NaN);
  const perPage = Number.isFinite(perPageCandidate)
    ? perPageCandidate
    : 20;
  const total = asNumber(paginationSource.total, 0);
  const totalPagesCandidate =
    asNumber(paginationSource.total_pages, NaN) ||
    asNumber(paginationSource.pages, NaN);
  const totalPages = Number.isFinite(totalPagesCandidate)
    ? totalPagesCandidate
    : Math.ceil(total / perPage);

  return {
    data,
    pagination: {
      page,
      per_page: perPage,
      total,
      total_pages: totalPages,
    },
  };
}

export const api = {
  getProposals: (params: ProposalsQueryParams = {}) =>
    request<unknown>(
      `/api/proposals${buildQuery({
        per_page: params.per_page ?? 50,
        page: params.page ?? 1,
        sort_by: params.sort_by ?? "health_score",
        sort_order: params.sort_order ?? "ASC",
        status: params.status,
        is_active: params.is_active,
      })}`
    ).then((raw) => normalizePaginationResponse<ProposalSummary>(raw)),

  getProposalDetail: (projectCode: string) =>
    request<{ data: ProposalDetail }>(`/api/proposal-tracker/${encodeURIComponent(projectCode)}`)
      .then((res) => res.data),

  getProposalHealth: (projectCode: string) =>
    // Use intelligence context endpoint which has health/risk info
    request<ProposalHealth>(
      `/api/intelligence/proposals/${encodeURIComponent(projectCode)}/context`
    ).catch(() => ({
      health_score: null,
      health_status: 'unknown',
      factors: {},
      risks: [],
      recommendation: null,
    })),

  getProposalHistory: (projectCode: string) =>
    request<{
      data: Record<string, unknown>[];
      history: Record<string, unknown>[];
      current_status?: string;
    }>(
      `/api/proposal-tracker/${encodeURIComponent(projectCode)}/history`
    ),

  getProposalTimeline: (projectCode: string) =>
    // Combine history and emails for timeline
    Promise.all([
      request<{ data: unknown[] }>(`/api/proposal-tracker/${encodeURIComponent(projectCode)}/history`).catch(() => ({ data: [] })),
      request<{ data: unknown[] }>(`/api/proposal-tracker/${encodeURIComponent(projectCode)}/emails`).catch(() => ({ data: [] })),
    ]).then(([historyRes, emailsRes]) => ({
      proposal: { project_code: projectCode, project_name: '', status: '' },
      emails: emailsRes.data || [],
      documents: [],
      timeline: historyRes.data || [],
      stats: {
        total_emails: (emailsRes.data || []).length,
        total_documents: 0,
        timeline_events: (historyRes.data || []).length,
      },
    } as unknown as ProposalTimelineResponse)),

  getDashboardAnalytics: () =>
    request<AnalyticsDashboard>("/api/analytics/dashboard"),

  getDashboardStats: () =>
    request<DashboardStats>("/api/dashboard/stats"),

  getDashboardKPIs: (params?: { period?: string; start_date?: string; end_date?: string }) =>
    request<DashboardKPIs>(`/api/dashboard/kpis${buildQuery(params || {})}`),

  getProposalStats: () =>
    request<ProposalStats>("/api/proposals/stats"),

  getDailyBriefing: () =>
    request<DailyBriefing>("/api/briefing/daily"),

  executeQuery: (question: string) =>
    request<QueryResponse>("/api/query/ask", {
      method: "POST",
      body: JSON.stringify({ question, use_ai: true }),
    }),

  // Context-aware query with conversation history
  executeQueryWithContext: (
    question: string,
    conversationHistory: Array<{
      role: string;
      content: string;
      results_count?: number;
      sql?: string;
    }> = []
  ) =>
    request<QueryResponse>("/api/query/chat", {
      method: "POST",
      body: JSON.stringify({
        question,
        conversation_history: conversationHistory,
        use_ai: true,
      }),
    }),

  getQuerySuggestions: () =>
    request<QuerySuggestionsResponse>("/api/query/examples"),

  getEmails: (params: {
    category?: string;
    page?: number;
    per_page?: number;
    q?: string;
    sort_by?: "date" | "sender_email" | "subject";
    sort_order?: "ASC" | "DESC";
  } = {}) =>
    request<unknown>(
      `/api/emails${buildQuery({
        category: params.category,
        page: params.page ?? 1,
        per_page: params.per_page ?? 20,
        q: params.q,
        sort_by: params.sort_by,
        sort_order: params.sort_order,
      })}`
    ).then((raw) => normalizePaginationResponse<EmailSummary>(raw)),

  getEmailCategories: () =>
    request<EmailCategoryCounts>("/api/emails/categories"),

  getEmailCategoryList: () =>
    request<EmailCategoryListResponse>("/api/emails/categories/list"),

  updateEmailCategory: (emailId: number, body: EmailCategoryUpdateRequest) =>
    request<EmailCategoryUpdateResponse>(
      `/api/emails/${emailId}/category`,
      {
        method: "POST",
        body: JSON.stringify(body),
      }
    ),

  getProposalBriefing: (projectCode: string) =>
    // Use intelligence context endpoint for briefing data
    request<ProposalBriefing>(
      `/api/intelligence/proposals/${encodeURIComponent(projectCode)}/context`
    ).catch(() => (null as unknown as ProposalBriefing)),

  getDecisionTiles: () => request<DecisionTiles>("/api/dashboard/decision-tiles"),

  getTopValueProposals: (params: { limit?: number; page?: number } = {}) =>
    request<unknown>(
      `/api/proposals/top-value${buildQuery({
        limit: params.limit,
        page: params.page,
      })}`
    ).then((raw) => normalizePaginationResponse<TopValueProposal>(raw)),

  getSystemHealth: () => request<SystemHealth>("/api/admin/system-health"),

  getManualOverrides: (params: {
    project_code?: string;
    status?: string;
    scope?: string;
    author?: string;
    page?: number;
    per_page?: number;
  } = {}) =>
    request<ManualOverridesResponse>(
      `/api/manual-overrides${buildQuery({
        project_code: params.project_code,
        status: params.status,
        scope: params.scope,
        author: params.author,
        page: params.page,
        per_page: params.per_page,
      })}`
    ),

  getManualOverride: (id: number) =>
    request<ManualOverride>(`/api/manual-overrides/${id}`),

  createManualOverride: (body: ManualOverrideCreateRequest) =>
    request<ManualOverride>("/api/manual-overrides", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  updateManualOverride: (id: number, body: ManualOverrideUpdateRequest) =>
    request<ManualOverride>(`/api/manual-overrides/${id}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),

  applyManualOverride: (id: number, appliedBy?: string) =>
    request<ManualOverride>(
      `/api/manual-overrides/${id}/apply${buildQuery({
        applied_by: appliedBy,
      })}`,
      {
        method: "POST",
      }
    ),

  getIntelSuggestions: (
    params: { status?: string; group?: string; limit?: number } = {}
  ) =>
    request<IntelligenceSuggestionsResponse>(
      `/api/intel/suggestions${buildQuery({
        status: params.status ?? "pending",
        group: params.group,
        limit: params.limit,
      })}`
    ),

  postIntelDecision: (id: string, body: IntelligenceDecisionRequest) =>
    request<IntelligenceDecisionResponse>(
      `/api/intel/suggestions/${encodeURIComponent(id)}/decision`,
      {
        method: "POST",
        body: JSON.stringify({
          decision: body.decision,
          reason: body.reason,
          apply_now: body.apply_now ?? true,
          dry_run: body.dry_run ?? false,
          batch_ids: body.batch_ids,
        }),
      }
    ),

  getRecentPayments: (limit = 5) =>
    request<RecentPaymentsResponse>(
      `/api/finance/recent-payments${buildQuery({ limit })}`
    ),

  getProjectedInvoices: (limit = 5) =>
    request<ProjectedInvoicesResponse>(
      `/api/finance/projected-invoices${buildQuery({ limit })}`
    ),

  // New Financial Dashboard APIs (Migration 023)
  getDashboardFinancialMetrics: () =>
    request<{
      success: boolean;
      metrics: {
        total_contract_value: number;
        total_invoiced: number;
        total_paid: number;
        total_outstanding: number;
        total_overdue: number;
        total_remaining: number;
        active_project_count: number;
      };
    }>("/api/finance/dashboard-metrics"),

  getProjectsByOutstanding: (limit = 5) =>
    request<{
      success: boolean;
      projects: Record<string, unknown>[];
      count: number;
    }>(`/api/finance/projects-by-outstanding${buildQuery({ limit })}`),

  getOldestUnpaidInvoices: (limit = 5) =>
    request<{
      success: boolean;
      invoices: Record<string, unknown>[];
      count: number;
    }>(`/api/finance/oldest-unpaid-invoices${buildQuery({ limit })}`),

  getProjectsByRemaining: (limit = 5) =>
    request<{
      success: boolean;
      projects: Record<string, unknown>[];
      count: number;
    }>(`/api/finance/projects-by-remaining${buildQuery({ limit })}`),

  getProposalWeeklyChanges: (days = 7) =>
    request<ProposalWeeklyChanges>(
      `/api/proposals/weekly-changes${buildQuery({ days })}`
    ),

  // Projects API (older methods - kept for compatibility)
  getProjectDetail: (projectCode: string) =>
    request<Record<string, unknown>>(`/api/projects/${encodeURIComponent(projectCode)}/financial-summary`),

  getProjectTimeline: (projectCode: string) =>
    request<Record<string, unknown>>(`/api/projects/${encodeURIComponent(projectCode)}/timeline`),

  // Invoices API
  getInvoiceStats: () =>
    request<Record<string, unknown>>("/api/invoices/stats"),

  getOutstandingInvoices: () =>
    request<{ invoices: Record<string, unknown>[] }>("/api/invoices/outstanding"),

  getInvoicesByProject: (projectCode: string) =>
    request<{ invoices: Record<string, unknown>[] }>(`/api/invoices/by-project/${encodeURIComponent(projectCode)}`),

  // Milestones API
  getMilestones: (params: { upcoming?: boolean } = {}) =>
    request<{ milestones: Record<string, unknown>[] }>(
      `/api/milestones${buildQuery({ upcoming: params.upcoming })}`
    ),

  // Dashboard Meetings API
  getDashboardMeetings: () =>
    request<{ meetings: Record<string, unknown>[] }>("/api/dashboard/meetings"),

  // RFIs API
  getRfis: (params: { status?: string } = {}) =>
    request<{ rfis: Record<string, unknown>[] }>(
      `/api/rfis${buildQuery({ status: params.status })}`
    ),

  getProposalRfis: (proposalId: number) =>
    request<{ rfis: Record<string, unknown>[] }>(`/api/proposals/${proposalId}/rfis`),

  // Proposal Tracker API
  getProposalTrackerStats: () =>
    request<ProposalTrackerStatsResponse>("/api/proposal-tracker/stats"),

  getProposalTrackerList: (params: ProposalTrackerQueryParams = {}) =>
    request<ProposalTrackerListResponse>(
      `/api/proposal-tracker/list${buildQuery({
        status: params.status,
        country: params.country,
        search: params.search,
        discipline: params.discipline && params.discipline !== 'all' ? params.discipline : undefined,
        page: params.page ?? 1,
        per_page: params.per_page ?? 50,
      })}`
    ),

  getProposalTrackerDisciplines: () =>
    request<DisciplineStatsResponse>("/api/proposal-tracker/disciplines"),

  getProposalTrackerCountries: () =>
    request<{ success: boolean; countries: string[] }>(
      "/api/proposal-tracker/countries"
    ),

  getProposalTrackerDetail: (projectCode: string) =>
    request<ProposalTrackerDetailResponse>(
      `/api/proposal-tracker/${encodeURIComponent(projectCode)}`
    ),

  updateProposalTracker: (
    projectCode: string,
    updates: ProposalTrackerUpdateRequest
  ) =>
    request<{ success: boolean; message: string; updated_fields: string[] }>(
      `/api/proposal-tracker/${encodeURIComponent(projectCode)}`,
      {
        method: "PUT",
        body: JSON.stringify(updates),
      }
    ),

  getProposalStatusHistory: (projectCode: string) =>
    request<{ success: boolean; history: ProposalStatusHistoryItem[] }>(
      `/api/proposal-tracker/${encodeURIComponent(projectCode)}/history`
    ),

  getProposalEmailIntelligence: (projectCode: string) =>
    request<{ success: boolean; emails: ProposalEmailIntelligence[] }>(
      `/api/proposal-tracker/${encodeURIComponent(projectCode)}/emails`
    ),

  generateProposalPdf: () =>
    request<{ success: boolean; pdf_path?: string; message: string }>(
      "/api/proposal-tracker/generate-pdf",
      {
        method: "POST",
      }
    ),

  // Admin - Data Validation
  getValidationSuggestions: (status?: string) =>
    request<ValidationSuggestionsResponse>(
      `/api/admin/validation/suggestions${status ? `?status=${status}` : ""}`
    ),

  getValidationSuggestion: (id: number) =>
    request<ValidationSuggestion>(
      `/api/admin/validation/suggestions/${id}`
    ),

  approveSuggestion: (id: number, data: ApproveSuggestionRequest) =>
    request<{ success: boolean; message: string }>(
      `/api/admin/validation/suggestions/${id}/approve`,
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    ),

  denySuggestion: (id: number, data: DenySuggestionRequest) =>
    request<{ success: boolean; message: string }>(
      `/api/admin/validation/suggestions/${id}/deny`,
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    ),

  // Admin - Email Links
  getEmailLinks: (projectCode?: string) =>
    request<EmailLinksResponse>(
      `/api/admin/email-links${projectCode ? `?project_code=${projectCode}` : ""}`
    ),

  unlinkEmail: (linkId: string, user: string = "admin") =>
    request<{ success: boolean; message: string }>(
      `/api/admin/email-links/${encodeURIComponent(linkId)}?user=${encodeURIComponent(user)}`,
      {
        method: "DELETE",
      }
    ),

  createEmailLink: (data: CreateEmailLinkRequest) =>
    request<{ success: boolean; link_id: number; message: string }>(
      `/api/admin/email-links`,
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    ),

  // Invoice Aging
  getInvoiceAging: () =>
    request<InvoiceAgingResponse>(`/api/invoices/aging`),

  getRecentPaidInvoices: (limit: number = 5) =>
    request<{ success: boolean; data: InvoiceAgingData["recent_paid"]; count: number }>(
      `/api/invoices/recent-paid?limit=${limit}`
    ),

  getLargestOutstandingInvoices: (limit: number = 10) =>
    request<{ success: boolean; data: InvoiceAgingData["largest_outstanding"]; count: number }>(
      `/api/invoices/largest-outstanding?limit=${limit}`
    ),

  getAgingBreakdown: () =>
    request<{ success: boolean; data: InvoiceAgingData["aging_breakdown"] }>(
      `/api/invoices/aging-breakdown`
    ),

  getTopOutstandingInvoices: () =>
    request<{ success: boolean; invoices: any[] }>(
      `/api/invoices/top-outstanding`
    ),

  getOutstandingInvoicesFiltered: (params?: { project_code?: string; min_days?: number; max_days?: number }) =>
    request<{ success: boolean; invoices: any[]; total_outstanding: number; count: number }>(
      `/api/invoices/outstanding-filtered${params ? `?${buildQuery(params)}` : ''}`
    ),

  // Email API - New endpoints for Claude 1
  getRecentEmails: (limit: number = 10, days: number = 30) =>
    request<{ success: boolean; data: EmailSummary[]; count: number; days: number }>(
      `/api/emails/recent?limit=${limit}&days=${days}`
    ),

  getProposalEmails: (proposalId: number, limit: number = 20) =>
    request<{ success: boolean; proposal_id: number; data: EmailSummary[]; count: number }>(
      `/api/emails/proposal/${proposalId}?limit=${limit}`
    ),

  getEmailDetail: (emailId: number) =>
    request<EmailSummary & { body_full?: string; attachments?: unknown[]; linked_proposals?: unknown[] }>(
      `/api/emails/${emailId}`
    ),

  markEmailRead: (emailId: number) =>
    request<{ success: boolean; message: string }>(
      `/api/emails/${emailId}/read`,
      { method: "POST" }
    ),

  linkEmailToProject: (emailId: number, projectCode: string, confidence: number = 1.0) =>
    request<{ success: boolean; data: unknown; message: string }>(
      `/api/emails/${emailId}/link`,
      {
        method: "POST",
        body: JSON.stringify({ project_code: projectCode, confidence }),
      }
    ),

  // Projects API
  getActiveProjects: () =>
    request<ActiveProjectsResponse>(`/api/projects/active`),

  getProjectFinancialDetail: (projectCode: string) =>
    request<{ success: boolean; project_code: string; [key: string]: unknown }>(
      `/api/projects/${encodeURIComponent(projectCode)}/financial-detail`
    ),

  getProjectHierarchy: (projectCode: string) =>
    request<ProjectHierarchy>(
      `/api/projects/${encodeURIComponent(projectCode)}/hierarchy`
    ),

  // Project Emails API
  getProjectEmails: (projectCode: string, limit: number = 20) =>
    request<ProjectEmailsResponse>(
      `/api/emails/project/${encodeURIComponent(projectCode)}?limit=${limit}`
    ),

  getProjectEmailSummary: (projectCode: string, useAI: boolean = true) =>
    request<ProjectEmailSummary>(
      `/api/emails/project/${encodeURIComponent(projectCode)}/summary?use_ai=${useAI}`
    ),

  // Training Data / Feedback API (RLHF)
  logFeedback: (data: {
    feature_type: string;
    feature_id: string;
    helpful: boolean;
    issue_type?: string;
    feedback_text?: string;
    expected_value?: string;
    current_value?: string;
    context?: Record<string, unknown>;
  }) =>
    request<{ success: boolean; training_id: number; message: string }>(
      "/api/training/feedback",
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    ),

  getFeedbackStats: (feature?: string, days: number = 30) =>
    request<{ success: boolean; stats: unknown; period_days: number }>(
      `/api/training/feedback/stats${buildQuery({ feature, days })}`
    ),

  // Email Category Approval API (RLHF)
  approveEmailCategory: (emailId: number, approvedBy: string = 'bill') =>
    request<{ success: boolean; message: string; email_id: number; training_logged: boolean }>(
      `/api/emails/${emailId}/approve-category`,
      {
        method: 'POST',
        body: JSON.stringify({ approved_by: approvedBy }),
      }
    ),

  rejectEmailCategory: (emailId: number, newCategory: string, reason?: string, rejectedBy: string = 'bill') =>
    request<{ success: boolean; message: string; email_id: number; old_category: string | null; new_category: string; training_logged: boolean }>(
      `/api/emails/${emailId}/reject-category`,
      {
        method: 'POST',
        body: JSON.stringify({ new_category: newCategory, reason, rejected_by: rejectedBy }),
      }
    ),

  getEmailsPendingApproval: (limit: number = 50, category?: string) =>
    request<{
      success: boolean;
      emails: EmailPendingApproval[];
      count: number;
      total_pending: number;
    }>(`/api/emails/pending-approval${buildQuery({ limit, category })}`),

  getFeedbackCorrections: (feature?: string, limit: number = 50) =>
    request<{ success: boolean; corrections: unknown[]; count: number }>(
      `/api/training/feedback/corrections${buildQuery({ feature, limit })}`
    ),

  // Email Intelligence API (Claude 6)
  getEmailValidationQueue: (params: {
    status?: 'unlinked' | 'low_confidence' | 'all';
    priority?: 'high' | 'medium' | 'low' | 'all';
    limit?: number;
  } = {}) =>
    request<{
      success: boolean;
      counts: {
        unlinked: number;
        low_confidence: number;
        total_linked: number;
        returned: number;
      };
      emails: EmailValidationItem[];
    }>(`/api/emails/validation-queue${buildQuery({
      status: params.status,
      priority: params.priority,
      limit: params.limit ?? 50,
    })}`),

  getEmailDetails: (emailId: number) =>
    request<{
      success: boolean;
      email: EmailDetailsFull;
    }>(`/api/emails/${emailId}/details`),

  updateEmailLink: (emailId: number, data: {
    project_code: string;
    reason: string;
    updated_by?: string;
  }) =>
    request<{ success: boolean; message: string; training_logged: boolean }>(
      `/api/emails/${emailId}/link`,
      {
        method: 'PATCH',
        body: JSON.stringify(data),
      }
    ),

  confirmEmailLink: (emailId: number, confirmedBy: string = 'bill') =>
    request<{ success: boolean; message: string; training_logged: boolean }>(
      `/api/emails/${emailId}/confirm-link?confirmed_by=${encodeURIComponent(confirmedBy)}`,
      { method: 'POST' }
    ),

  unlinkEmailIntelligence: (emailId: number, reason: string, updatedBy: string = 'bill') =>
    request<{ success: boolean; message: string; training_logged: boolean }>(
      `/api/emails/${emailId}/link?reason=${encodeURIComponent(reason)}&updated_by=${encodeURIComponent(updatedBy)}`,
      { method: 'DELETE' }
    ),

  getProjectEmailTimeline: (projectCode: string, params: {
    include_attachments?: boolean;
    include_threads?: boolean;
  } = {}) =>
    request<{
      success: boolean;
      project: {
        code: string;
        name: string;
        project_value: number | null;
        status: string;
      };
      emails: ProjectTimelineEmail[];
      stats: {
        total_emails: number;
        total_attachments: number;
        contract_count: number;
        design_doc_count: number;
      };
    }>(`/api/projects/${encodeURIComponent(projectCode)}/emails${buildQuery({
      include_attachments: params.include_attachments ?? true,
      include_threads: params.include_threads ?? true,
    })}`),

  getProjectsForLinking: (limit: number = 500) =>
    request<{
      success: boolean;
      projects: Array<{
        code: string;
        name: string;
        status: string;
        is_active_project: number;
      }>;
    }>(`/api/projects/linking-list?limit=${limit}`),

  // Manual Data Entry API
  createProject: (data: {
    project_code: string;
    project_title: string;
    total_fee_usd: number;
    country?: string;
    city?: string;
    status?: string;
  }) =>
    request<{ success: boolean; project_id: number; message: string }>(
      "/api/projects",
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    ),

  createFeeBreakdown: (data: {
    project_code: string;
    scope?: string;
    discipline: string;
    phase: string;
    phase_fee_usd: number;
    percentage_of_total: number;
  }) =>
    request<{ success: boolean; breakdown_id: string; message: string }>(
      "/api/phase-fees",
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    ),

  // Get fee breakdowns for a project with full financial summary
  getProjectFeeBreakdowns: (projectCode: string) =>
    request<{
      success: boolean;
      project_code: string;
      project_title: string | null;
      contract_value: number | null;
      breakdowns: FeeBreakdown[];
      summary: {
        total_breakdown_fee: number;
        total_invoiced: number;
        total_paid: number;
        total_outstanding: number;
        remaining_to_invoice: number;
        percentage_invoiced: number;
        percentage_paid: number;
      };
      count: number;
    }>(`/api/projects/${encodeURIComponent(projectCode)}/fee-breakdown`),

  // Check for duplicate breakdown before creating
  checkDuplicateBreakdown: (projectCode: string, scope: string | null, discipline: string, phase: string) =>
    request<{ exists: boolean; existing_breakdown?: FeeBreakdown }>(
      `/api/projects/${encodeURIComponent(projectCode)}/fee-breakdown/check-duplicate${buildQuery({
        scope,
        discipline,
        phase
      })}`
    ),

  // Add a new fee breakdown phase to a project
  addFeeBreakdown: (projectCode: string, data: {
    discipline: string;
    phase: string;
    phase_fee_usd: number;
    scope?: string;
    percentage_of_total?: number;
  }) =>
    request<{ success: boolean; breakdown_id: string; message: string }>(
      `/api/projects/${encodeURIComponent(projectCode)}/fee-breakdown`,
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    ),

  createInvoice: (data: {
    project_code: string;
    breakdown_id?: string;
    invoice_number: string;
    invoice_date: string;
    invoice_amount: number;
    payment_date?: string;
    payment_amount?: number;
    status?: string;
  }) =>
    request<{ success: boolean; invoice_id: number; message: string }>(
      "/api/invoices",
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    ),

  // Load existing project data
  getProjectData: async (project_code: string) => {
    const [project, phases, invoices] = await Promise.all([
      request<{ project: any }>(`/api/projects/${project_code}`),
      request<{ breakdowns: any[] }>(`/api/projects/${project_code}/fee-breakdown`),
      request<{ invoices: any[] }>(`/api/invoices/by-project/${project_code}`),
    ]);
    return {
      project: project.project || {},
      phases: phases.breakdowns || [],
      invoices: invoices.invoices || []
    };
  },

  // Update existing data
  updateProject: (
    project_code: string,
    data: {
      project_title?: string;
      total_fee_usd?: number;
      country?: string;
      city?: string;
      status?: string;
      notes?: string;
      contract_term_months?: number;
      team_lead?: string;
      current_phase?: string;
      target_completion?: string;
      payment_due_days?: number;
      payment_terms?: string;
      late_payment_interest_rate?: number;
    }
  ) =>
    request<{ success: boolean; message: string }>(
      `/api/projects/${project_code}`,
      {
        method: "PUT",
        body: JSON.stringify(data),
      }
    ),

  updateInvoice: (
    invoice_number: string,
    data: {
      breakdown_id?: string;
      invoice_date?: string;
      invoice_amount?: number;
      payment_date?: string;
      payment_amount?: number;
      status?: string;
    }
  ) =>
    request<{ success: boolean; message: string }>(
      `/api/invoices/${invoice_number}`,
      {
        method: "PUT",
        body: JSON.stringify(data),
      }
    ),

  updatePhaseFee: (
    breakdown_id: string,
    data: {
      phase_fee_usd?: number;
      percentage_of_total?: number;
    }
  ) =>
    request<{ success: boolean; message: string }>(
      `/api/phase-fees/${breakdown_id}`,
      {
        method: "PUT",
        body: JSON.stringify(data),
      }
    ),

  // ============================================================================
  // DELIVERABLES & PM WORKLOAD
  // ============================================================================

  getDeliverables: (params?: {
    project_code?: string;
    status?: string;
    assigned_pm?: string;
    phase?: string;
  }) =>
    request<DeliverablesResponse>(`/api/deliverables${buildQuery(params || {})}`),

  getOverdueDeliverables: () =>
    request<OverdueDeliverablesResponse>("/api/deliverables/overdue"),

  getUpcomingDeliverables: (days: number = 14) =>
    request<UpcomingDeliverablesResponse>(`/api/deliverables/upcoming?days=${days}`),

  getDeliverableAlerts: () =>
    request<DeliverableAlertsResponse>("/api/deliverables/alerts"),

  createDeliverable: (data: {
    project_code: string;
    deliverable_name: string;
    due_date: string;
    phase?: string;
    deliverable_type?: string;
    assigned_pm?: string;
    description?: string;
    priority?: string;
  }) =>
    request<{ success: boolean; deliverable_id: number; message: string }>(
      "/api/deliverables",
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    ),

  updateDeliverableStatus: (
    deliverable_id: number,
    data: {
      status: string;
      notes?: string;
      submitted_date?: string;
    }
  ) =>
    request<{ success: boolean; message: string }>(
      `/api/deliverables/${deliverable_id}/status`,
      {
        method: "PUT",
        body: JSON.stringify(data),
      }
    ),

  addOverdueContext: (
    deliverable_id: number,
    data: {
      context: string;
      context_by: string;
    }
  ) =>
    request<{ success: boolean; message: string }>(
      `/api/deliverables/${deliverable_id}/context`,
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    ),

  getPMWorkload: (pm_name?: string) =>
    request<PMWorkloadResponse>(`/api/deliverables/pm-workload${pm_name ? `?pm_name=${encodeURIComponent(pm_name)}` : ''}`),

  getPMList: () =>
    request<PMListResponse>("/api/deliverables/pm-list"),

  getProjectPhaseStatus: (project_code: string) =>
    request<ProjectPhaseStatusResponse>(`/api/projects/${encodeURIComponent(project_code)}/phase-status`),

  getInferredPM: (project_code: string) =>
    request<{ success: boolean; project_code: string; inferred_pm: string | null }>(
      `/api/projects/${encodeURIComponent(project_code)}/inferred-pm`
    ),

  generateProjectMilestones: (data: {
    project_code: string;
    contract_start_date: string;
    disciplines?: string[];
    skip_schematic?: boolean;
  }) =>
    request<{ success: boolean; project_code: string; deliverables_created: number; deliverable_ids: number[] }>(
      `/api/projects/${encodeURIComponent(data.project_code)}/generate-milestones`,
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    ),

  seedDeliverablesFromMilestones: () =>
    request<{ success: boolean; milestones_found: number; deliverables_created: number; skipped: number }>(
      "/api/deliverables/seed-from-milestones",
      { method: "POST" }
    ),

  getLifecyclePhases: () =>
    request<LifecyclePhasesResponse>("/api/lifecycle-phases"),

  // AI Learning API
  getLearningStats: () =>
    request<LearningStatsResponse>("/api/learning/stats"),

  getLearningPatterns: (patternType?: string) =>
    request<LearnedPatternsResponse>(
      `/api/learning/patterns${patternType ? `?pattern_type=${patternType}` : ""}`
    ),

  getLearningPendingSuggestions: (suggestionType?: string, projectCode?: string, limit?: number) =>
    request<AISuggestionsResponse>(
      `/api/learning/suggestions${buildQuery({
        suggestion_type: suggestionType,
        project_code: projectCode,
        limit: limit ?? 50,
      })}`
    ),

  approveLearning: (suggestionId: number, reviewedBy: string, applyChanges: boolean = true) =>
    request<{ success: boolean; suggestion_id: number; applied: boolean }>(
      `/api/learning/suggestions/${suggestionId}/approve`,
      {
        method: "POST",
        body: JSON.stringify({ reviewed_by: reviewedBy, apply_changes: applyChanges }),
      }
    ),

  rejectLearning: (suggestionId: number, reviewedBy: string, reason?: string) =>
    request<{ success: boolean; suggestion_id: number }>(
      `/api/learning/suggestions/${suggestionId}/reject`,
      {
        method: "POST",
        body: JSON.stringify({ reviewed_by: reviewedBy, reason }),
      }
    ),

  generateRules: (minEvidence: number = 3) =>
    request<RuleGenerationResponse>(
      `/api/learning/generate-rules?min_evidence=${minEvidence}`,
      { method: "POST" }
    ),

  // Follow-up Agent API
  getFollowUpSummary: () =>
    request<FollowUpSummaryResponse>("/api/agent/follow-up/summary"),

  getFollowUpProposals: (daysThreshold?: number, limit?: number) =>
    request<FollowUpProposalsResponse>(
      `/api/agent/follow-up/proposals${buildQuery({
        days_threshold: daysThreshold ?? 14,
        include_analysis: true,
        limit: limit ?? 50,
      })}`
    ),

  draftFollowUpEmail: (proposalId: number, tone?: string) =>
    request<{ success: boolean; subject?: string; body?: string; error?: string }>(
      `/api/agent/follow-up/draft/${proposalId}?tone=${tone || "professional"}`,
      { method: "POST" }
    ),

  // Pattern-Enhanced Query API
  queryWithPatterns: (question: string, usePatterns: boolean = true) =>
    request<EnhancedQueryResponse>(
      `/api/query/ask-enhanced?question=${encodeURIComponent(question)}&use_patterns=${usePatterns}`,
      { method: "POST" }
    ),

  submitQueryFeedback: (
    question: string,
    originalSql: string,
    wasCorrect: boolean,
    correctedSql?: string,
    correctionReason?: string
  ) =>
    request<{ success: boolean; feedback_id?: number; message?: string }>(
      "/api/query/feedback",
      {
        method: "POST",
        body: JSON.stringify({
          question,
          original_sql: originalSql,
          was_correct: wasCorrect,
          corrected_sql: correctedSql,
          correction_reason: correctionReason,
        }),
      }
    ),

  getIntelligentQuerySuggestions: (partialQuery: string = "") =>
    request<{
      success: boolean;
      suggestions: QuerySuggestion[];
    }>(`/api/query/intelligent-suggestions?partial_query=${encodeURIComponent(partialQuery)}`),

  getQueryLearningStats: () =>
    request<{
      success: boolean;
      stats: QueryLearningStats;
    }>("/api/query/stats"),

  // ============================================================================
  // AI SUGGESTIONS QUEUE API
  // ============================================================================

  getSuggestions: (params: {
    status?: string;
    field_name?: string;
    data_table?: string;
    min_confidence?: number;
    limit?: number;
    offset?: number;
  } = {}) =>
    request<SuggestionsResponse>(
      `/api/suggestions${buildQuery({
        status: params.status ?? "pending",
        field_name: params.field_name,
        data_table: params.data_table,
        min_confidence: params.min_confidence,
        limit: params.limit ?? 50,
        offset: params.offset ?? 0,
      })}`
    ),

  getSuggestionsStats: () =>
    request<SuggestionsStatsResponse>("/api/suggestions/stats"),

  approveAISuggestion: (suggestionId: number, edits?: {
    name?: string;
    email?: string;
    company?: string;
    role?: string;
    related_project?: string;
    notes?: string;
  }) =>
    request<{ success: boolean; message: string; result?: Record<string, unknown> }>(
      `/api/suggestions/${suggestionId}/approve`,
      {
        method: "POST",
        body: edits ? JSON.stringify(edits) : undefined,
      }
    ),

  rejectAISuggestion: (suggestionId: number, reason?: string) =>
    request<{ success: boolean; message: string }>(
      `/api/suggestions/${suggestionId}/reject`,
      {
        method: "POST",
        body: JSON.stringify({ reason }),
      }
    ),

  bulkApproveAISuggestions: (minConfidence: number = 0.8) =>
    request<{ success: boolean; approved: number; skipped: number; errors: number }>(
      `/api/suggestions/bulk-approve`,
      {
        method: "POST",
        body: JSON.stringify({ min_confidence: minConfidence }),
      }
    ),

  bulkApproveByIds: (suggestionIds: number[]) =>
    request<{ success: boolean; approved: number; total: number; errors: Array<{ id: number; error: string }> }>(
      `/api/suggestions/bulk-approve-by-ids`,
      {
        method: "POST",
        body: JSON.stringify({ suggestion_ids: suggestionIds }),
      }
    ),

  bulkRejectByIds: (suggestionIds: number[], reason?: string) =>
    request<{ success: boolean; rejected: number; total: number; errors: Array<{ id: number; error: string }> }>(
      `/api/suggestions/bulk-reject`,
      {
        method: "POST",
        body: JSON.stringify({ suggestion_ids: suggestionIds, reason: reason || "batch_rejected" }),
      }
    ),

  // Suggestion Preview, Source, and Rollback
  getSuggestionPreview: (suggestionId: number) =>
    request<SuggestionPreviewResponse>(`/api/suggestions/${suggestionId}/preview`),

  getSuggestionSource: (suggestionId: number) =>
    request<SuggestionSourceResponse>(`/api/suggestions/${suggestionId}/source`),

  rollbackSuggestion: (suggestionId: number) =>
    request<{ success: boolean; message: string }>(
      `/api/suggestions/${suggestionId}/rollback`,
      { method: "POST" }
    ),

  getGroupedSuggestions: (params: {
    status?: string;
    min_confidence?: number;
  } = {}) =>
    request<GroupedSuggestionsResponse>(
      `/api/suggestions/grouped${buildQuery({
        status: params.status ?? "pending",
        min_confidence: params.min_confidence,
      })}`
    ),

  // Enhanced Feedback - Reject with Correction
  rejectWithCorrection: (suggestionId: number, data: {
    rejection_reason: string;
    correct_project_code?: string;
    correct_proposal_id?: number;
    correct_contact_id?: number;
    create_pattern?: boolean;
    pattern_notes?: string;
  }) =>
    request<{
      success: boolean;
      message: string;
      data?: {
        suggestion_id: number;
        rejection_reason: string;
        corrected: boolean;
        pattern_created: boolean;
        correct_link?: {
          email_id?: number;
          project_id?: number;
          project_code?: string;
        };
        pattern_key?: string;
      };
    }>(`/api/suggestions/${suggestionId}/reject-with-correction`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Enhanced Feedback - Approve with Context
  approveWithContext: (suggestionId: number, data: {
    create_sender_pattern?: boolean;
    create_domain_pattern?: boolean;
    contact_role?: string;
    pattern_notes?: string;
    contact_edits?: Record<string, unknown>;
  }) =>
    request<{
      success: boolean;
      message: string;
      data?: {
        suggestion_id: number;
        patterns_created: Array<{ type: string; key: string }>;
        contact_role_updated?: boolean;
      };
    }>(`/api/suggestions/${suggestionId}/approve-with-context`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Enhanced Review UI - Full Context
  getSuggestionFullContext: (suggestionId: number) =>
    request<{
      success: boolean;
      suggestion: SuggestionItem;
      source_content: {
        type: 'email' | 'transcript';
        id: number;
        subject?: string;
        sender?: string;
        recipient?: string;
        date: string;
        body: string;
      } | null;
      ai_analysis: {
        detected_entities: {
          projects: string[];
          fees: Array<{ amount: number; currency: string }>;
          contacts: Array<{ name: string; email: string }>;
          dates: string[];
          keywords: string[];
        };
        suggested_actions: Array<{
          id: string;
          type: string;
          description: string;
          enabled_by_default: boolean;
          data: Record<string, unknown>;
          database_change: string;
        }>;
        pattern_to_learn: {
          type: string;
          pattern_key: string;
          target: string;
          confidence_boost: number;
        } | null;
        overall_confidence: number;
      };
      preview: {
        is_actionable: boolean;
        action: string;
        table: string;
        summary: string;
        changes: Array<{
          field: string;
          old_value: string | null;
          new_value: string | null;
        }>;
      } | null;
      existing_feedback: {
        notes: string;
        tags: string[];
        contact_role?: string;
        priority?: string;
      } | null;
    }>(`/api/suggestions/${suggestionId}/full-context`),

  getSuggestionTags: () =>
    request<{
      success: boolean;
      tags: Array<{
        tag_id: number;
        tag_name: string;
        tag_category: string;
        usage_count: number;
      }>;
    }>("/api/suggestion-tags"),

  saveSuggestionFeedback: (suggestionId: number, data: {
    context_notes?: string;
    tags?: string[];
    contact_role?: string;
    priority?: string;
  }) =>
    request<{ success: boolean; message: string }>(
      `/api/suggestions/${suggestionId}/save-feedback`,
      {
        method: "POST",
        body: JSON.stringify({
          context_notes: data.context_notes,
          tags: JSON.stringify(data.tags || []),
          contact_role: data.contact_role,
          priority: data.priority,
        }),
      }
    ),

  // Pattern Management
  getPatterns: (params: {
    pattern_type?: string;
    target_code?: string;
    is_active?: boolean;
    limit?: number;
    offset?: number;
  } = {}) =>
    request<{
      success: boolean;
      patterns: Array<{
        pattern_id: number;
        pattern_type: string;
        pattern_key: string;
        target_type: string;
        target_id: number;
        target_code: string;
        target_name: string | null;
        confidence: number;
        times_used: number;
        times_correct: number;
        times_rejected: number;
        is_active: number;
        notes: string | null;
        created_at: string;
        updated_at: string;
        last_used_at: string | null;
      }>;
      total: number;
    }>(`/api/patterns${buildQuery(params)}`),

  getPatternStats: () =>
    request<{
      success: boolean;
      stats: {
        total_patterns: number;
        active_patterns: number;
        total_uses: number;
        total_correct: number;
        total_rejected: number;
        avg_confidence: number;
      };
      by_type: Record<string, { count: number; uses: number }>;
      top_patterns: Array<{
        pattern_id: number;
        pattern_type: string;
        pattern_key: string;
        target_code: string;
        times_used: number;
        times_correct: number;
        success_rate: number;
      }>;
    }>("/api/patterns/stats"),

  getPattern: (patternId: number) =>
    request<{
      success: boolean;
      pattern: {
        pattern_id: number;
        pattern_type: string;
        pattern_key: string;
        target_type: string;
        target_id: number;
        target_code: string;
        target_name: string | null;
        confidence: number;
        times_used: number;
        times_correct: number;
        times_rejected: number;
        is_active: number;
        notes: string | null;
        created_at: string;
        updated_at: string;
        last_used_at: string | null;
      };
      usage_history: Array<{
        log_id: number;
        suggestion_id: number | null;
        email_id: number | null;
        action: string;
        match_score: number | null;
        created_at: string;
      }>;
    }>(`/api/patterns/${patternId}`),

  createPattern: (data: {
    pattern_type: string;
    pattern_key: string;
    target_type: string;
    target_code: string;
    notes?: string;
  }) =>
    request<{ success: boolean; message: string; data?: { pattern_id: number } }>(
      "/api/patterns",
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    ),

  updatePattern: (patternId: number, data: {
    is_active?: boolean;
    notes?: string;
    confidence?: number;
  }) =>
    request<{ success: boolean; message: string }>(
      `/api/patterns/${patternId}`,
      {
        method: "PUT",
        body: JSON.stringify(data),
      }
    ),

  deletePattern: (patternId: number) =>
    request<{ success: boolean; message: string }>(
      `/api/patterns/${patternId}`,
      { method: "DELETE" }
    ),

  // Contacts API
  getContacts: (params: {
    search?: string;
    company?: string;
    role?: string;
    project_id?: number;
    limit?: number;
    offset?: number;
  } = {}) =>
    request<{
      success: boolean;
      contacts: Array<{
        contact_id: number;
        name: string | null;
        email: string | null;
        role: string | null;
        phone: string | null;
        company: string | null;
        position: string | null;
        context_notes: string | null;
        source: string | null;
        first_seen_date: string | null;
        notes: string | null;
        client_id: number | null;
      }>;
      total?: number;
    }>(`/api/contacts${buildQuery({
      search: params.search,
      company: params.company,
      role: params.role,
      project_id: params.project_id,
      limit: params.limit ?? 50,
      offset: params.offset ?? 0,
    })}`),

  getContactStats: () =>
    request<{
      success: boolean;
      stats: {
        total: number;
        by_company: Record<string, number>;
        with_email: number;
        with_phone: number;
      };
    }>("/api/contacts/stats"),

  getContact: (contactId: number) =>
    request<{
      success: boolean;
      contact: {
        contact_id: number;
        name: string | null;
        email: string | null;
        role: string | null;
        phone: string | null;
        company: string | null;
        position: string | null;
        context_notes: string | null;
        source: string | null;
        first_seen_date: string | null;
        notes: string | null;
        linked_projects: Array<{ project_code: string; project_title: string }>;
        recent_emails: Array<{ email_id: number; subject: string; date: string }>;
      };
    }>(`/api/contacts/${contactId}`),

  createContact: (contact: {
    name?: string;
    email: string;
    phone?: string;
    company?: string;
    position?: string;
    role?: string;
    context_notes?: string;
  }) =>
    request<{ success: boolean; contact_id: number }>("/api/contacts", {
      method: "POST",
      body: JSON.stringify(contact),
    }),

  updateContact: (contactId: number, updates: {
    name?: string;
    email?: string;
    phone?: string;
    company?: string;
    position?: string;
    role?: string;
    context_notes?: string;
  }) =>
    request<{ success: boolean; message: string }>(`/api/contacts/${contactId}`, {
      method: "PUT",
      body: JSON.stringify(updates),
    }),

  deleteContact: (contactId: number) =>
    request<{ success: boolean; message: string }>(`/api/contacts/${contactId}`, {
      method: "DELETE",
    }),

  // Meeting Transcripts API
  getMeetingTranscripts: (params: {
    project_id?: number;
    limit?: number;
    offset?: number;
  } = {}) =>
    request<{
      success: boolean;
      total: number;
      limit: number;
      offset: number;
      transcripts: Array<{
        id: number;
        audio_filename: string;
        audio_path: string;
        transcript: string;
        created_at: string;
        updated_at: string | null;
        ai_summary: string | null;
        project_id: number | null;
        proposal_id: number | null;
        meeting_title: string | null;
        meeting_date: string | null;
      }>;
    }>(`/api/meeting-transcripts${buildQuery({
      project_id: params.project_id,
      limit: params.limit ?? 50,
      offset: params.offset ?? 0,
    })}`),

  getTranscript: (transcriptId: number) =>
    request<{
      success: boolean;
      transcript: {
        id: number;
        audio_filename: string;
        audio_path: string;
        transcript: string;
        created_at: string;
        updated_at: string | null;
        ai_summary: string | null;
        project_id: number | null;
        proposal_id: number | null;
        meeting_title: string | null;
        meeting_date: string | null;
      };
    }>(`/api/meeting-transcripts/${transcriptId}`),

  updateTranscript: (transcriptId: number, updates: {
    project_id?: number;
    proposal_id?: number;
    meeting_title?: string;
    meeting_date?: string;
    ai_summary?: string;
  }) =>
    request<{ success: boolean; message: string }>(`/api/meeting-transcripts/${transcriptId}`, {
      method: "PUT",
      body: JSON.stringify(updates),
    }),

  getProjectTranscripts: (projectCode: string) =>
    request<{
      success: boolean;
      transcripts: Array<{
        id: number;
        audio_filename: string;
        transcript: string;
        meeting_title: string | null;
        meeting_date: string | null;
        ai_summary: string | null;
      }>;
    }>(`/api/projects/${encodeURIComponent(projectCode)}/transcripts`),

  // Unified Timeline API
  getUnifiedTimeline: (projectCode: string) =>
    request<{
      success: boolean;
      project_code: string;
      items: Array<{
        type: 'email' | 'transcript' | 'invoice' | 'rfi';
        date: string;
        title: string;
        description: string | null;
        data: Record<string, unknown>;
      }>;
    }>(`/api/projects/${encodeURIComponent(projectCode)}/unified-timeline`),

  // Email Link Suggestion API
  approveEmailLink: (suggestionId: number, projectCode?: string) =>
    request<{ success: boolean; message: string; link_id?: number }>(
      `/api/suggestions/${suggestionId}/approve-email-link`,
      {
        method: "POST",
        body: JSON.stringify({ project_code: projectCode }),
      }
    ),

  // ============ CONTRACTS API ============
  getContracts: (params: { project_code?: string; status?: string; limit?: number } = {}) =>
    request<{
      success: boolean;
      contracts: Array<{
        contract_id: number;
        project_code: string;
        contract_type: string;
        contract_value: number;
        signed_date: string | null;
        expiry_date: string | null;
        status: string;
      }>;
      total: number;
    }>(`/api/contracts${buildQuery(params)}`),

  getContractStats: () =>
    request<{
      success: boolean;
      stats: {
        total_contracts: number;
        total_value: number;
        active_contracts: number;
        expiring_soon: number;
      };
    }>("/api/contracts/stats"),

  getContractsByProject: (projectCode: string) =>
    request<{
      success: boolean;
      contracts: Array<Record<string, unknown>>;
    }>(`/api/contracts/by-project/${encodeURIComponent(projectCode)}`),

  getContractFeeBreakdown: (projectCode: string) =>
    request<{
      success: boolean;
      breakdowns: Array<Record<string, unknown>>;
    }>(`/api/contracts/by-project/${encodeURIComponent(projectCode)}/fee-breakdown`),

  // ============ DOCUMENTS API ============
  getDocuments: (params: { project_code?: string; document_type?: string; limit?: number } = {}) =>
    request<{
      success: boolean;
      documents: Array<{
        document_id: number;
        file_name: string;
        file_path: string;
        document_type: string;
        project_code: string | null;
        created_at: string;
        file_size: number | null;
      }>;
      total: number;
    }>(`/api/documents${buildQuery(params)}`),

  getDocumentsByProject: (projectCode: string) =>
    request<{
      success: boolean;
      documents: Array<Record<string, unknown>>;
    }>(`/api/documents/by-project/${encodeURIComponent(projectCode)}`),

  getDocumentStats: () =>
    request<{
      success: boolean;
      stats: {
        total_documents: number;
        by_type: Record<string, number>;
      };
    }>("/api/documents/stats"),

  getRecentDocuments: (limit: number = 10) =>
    request<{
      success: boolean;
      documents: Array<Record<string, unknown>>;
    }>(`/api/documents/recent?limit=${limit}`),

  // ============ MILESTONES API ============
  getMilestonesByProject: (projectCode: string) =>
    request<{
      success: boolean;
      milestones: Array<{
        milestone_id: number;
        milestone_name: string;
        expected_date: string | null;
        actual_date: string | null;
        status: string;
        responsible_party: string | null;
      }>;
    }>(`/api/milestones/by-project/${encodeURIComponent(projectCode)}`),

  getUpcomingMilestones: (days: number = 30) =>
    request<{
      success: boolean;
      milestones: Array<Record<string, unknown>>;
    }>(`/api/milestones/upcoming?days=${days}`),

  getOverdueMilestones: () =>
    request<{
      success: boolean;
      milestones: Array<Record<string, unknown>>;
    }>("/api/milestones/overdue"),

  // ============ RFIs API (extended) ============
  getRfisByProject: (projectCode: string) =>
    request<{
      success: boolean;
      rfis: Array<Record<string, unknown>>;
    }>(`/api/rfis/by-project/${encodeURIComponent(projectCode)}`),

  getRfiStats: () =>
    request<{
      success: boolean;
      stats: {
        total: number;
        open: number;
        closed: number;
        overdue: number;
      };
    }>("/api/rfis/stats"),

  getOverdueRfis: () =>
    request<{
      success: boolean;
      rfis: Array<Record<string, unknown>>;
    }>("/api/rfis/overdue"),

  createRfi: (data: {
    project_code: string;
    question: string;
    asked_by?: string;
    priority?: string;
    due_date?: string;
  }) =>
    request<{ success: boolean; rfi_id: number }>("/api/rfis", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  respondToRfi: (rfiId: number, response: string) =>
    request<{ success: boolean }>(`/api/rfis/${rfiId}/respond`, {
      method: "POST",
      body: JSON.stringify({ response }),
    }),

  closeRfi: (rfiId: number) =>
    request<{ success: boolean }>(`/api/rfis/${rfiId}/close`, {
      method: "POST",
    }),

  // ============ CONTEXT API ============
  getProjectContext: (projectCode: string) =>
    request<{
      success: boolean;
      context: Record<string, unknown>;
    }>(`/api/context/project/${encodeURIComponent(projectCode)}`),

  // ============ INTELLIGENCE API ============
  getProjectHealth: (projectCode: string) =>
    request<{
      success: boolean;
      health_score: number;
      health_status: string;
      factors: Record<string, unknown>;
    }>(`/api/intelligence/health/${encodeURIComponent(projectCode)}`),

  getProjectRisks: (projectCode: string) =>
    request<{
      success: boolean;
      risks: Array<{
        risk_type: string;
        severity: string;
        description: string;
      }>;
    }>(`/api/intelligence/risks/${encodeURIComponent(projectCode)}`),
};

// Email Intelligence Types
export interface EmailValidationItem {
  email_id: number;
  subject: string | null;
  sender_email: string | null;
  sender_name: string | null;
  date: string | null;
  date_normalized: string | null;
  has_attachments: number;
  category: string | null;
  snippet: string | null;
  ai_summary: string | null;
  sentiment: string | null;
  urgency_level: string | null;
  project_code?: string | null;
  project_name?: string | null;
  confidence?: number | null;
  link_method?: string | null;
  evidence?: string | null;
  attachment_count: number;
}

export interface EmailDetailsFull {
  email_id: number;
  message_id: string;
  thread_id: string | null;
  date: string | null;
  sender_email: string | null;
  sender_name: string | null;
  subject: string | null;
  snippet: string | null;
  body_preview: string | null;
  body_full: string | null;
  has_attachments: number;
  category: string | null;
  project_code?: string | null;
  project_name?: string | null;
  confidence?: number | null;
  link_method?: string | null;
  evidence?: string | null;
  ai_insights: {
    category: string | null;
    subcategory: string | null;
    key_points: string | null;
    sentiment: string | null;
    client_sentiment: string | null;
    urgency_level: string | null;
    action_required: number;
    ai_summary: string | null;
    importance_score: number | null;
    entities: string | null;
  } | null;
  attachments: Array<{
    attachment_id: number;
    filename: string;
    filesize: number | null;
    mime_type: string | null;
    document_type: string | null;
    is_signed: boolean;
    is_executed: boolean;
    ai_summary: string | null;
  }>;
  thread: {
    thread_id: number;
    subject_normalized: string | null;
    message_count: number;
    status: string | null;
    first_email_date: string | null;
    last_email_date: string | null;
  } | null;
}

export interface ProjectTimelineEmail {
  email_id: number;
  subject: string | null;
  sender_email: string | null;
  sender_name: string | null;
  date: string | null;
  date_normalized: string | null;
  snippet: string | null;
  thread_id: string | null;
  has_attachments: number;
  category: string | null;
  subcategory: string | null;
  ai_summary: string | null;
  key_points: string | null;
  sentiment: string | null;
  urgency_level: string | null;
  action_required: number;
  confidence: number | null;
  link_method: string | null;
  thread_position?: number;
  total_in_thread?: number;
  attachments?: Array<{
    attachment_id: number;
    email_id: number;
    filename: string;
    filesize: number | null;
    document_type: string | null;
    is_signed: boolean;
    is_executed: boolean;
  }>;
}

export interface EmailPendingApproval {
  email_id: number;
  subject: string | null;
  sender_email: string | null;
  sender_name: string | null;
  date: string | null;
  snippet: string | null;
  has_attachments: number;
  ai_category: string | null;
  subcategory: string | null;
  importance_score: number | null;
  sentiment: string | null;
  ai_summary: string | null;
  human_approved: number | null;
  project_code: string | null;
  project_name: string | null;
  link_confidence: number | null;
}

export interface FeeBreakdown {
  breakdown_id: string;
  project_code: string;
  scope: string | null;
  discipline: string;
  phase: string;
  phase_fee_usd: number;
  percentage_of_total: number | null;
  total_invoiced: number;
  total_paid: number;
  percentage_invoiced: number;
  percentage_paid: number;
  created_at: string | null;
  updated_at: string | null;
}

// ============================================================================
// DELIVERABLES & PM WORKLOAD TYPES
// ============================================================================

export interface Deliverable {
  deliverable_id: number;
  project_id: number | null;
  project_code: string | null;
  deliverable_name: string | null;
  deliverable_type: string | null;
  phase: string | null;
  due_date: string | null;
  submitted_date: string | null;
  approved_date: string | null;
  status: string;
  revision_number: number;
  notes: string | null;
  file_path: string | null;
  title: string | null;
  assigned_pm: string | null;
  description: string | null;
  priority: string;
  created_at: string;
  updated_at: string;
  project_title?: string | null;
  days_until_due?: number;
  is_overdue?: number;
  days_overdue?: number;
  urgency_level?: string;
}

export interface DeliverablesResponse {
  success: boolean;
  deliverables: Deliverable[];
  count: number;
}

export interface OverdueDeliverablesResponse {
  success: boolean;
  overdue_deliverables: Deliverable[];
  count: number;
}

export interface UpcomingDeliverablesResponse {
  success: boolean;
  upcoming_deliverables: Deliverable[];
  count: number;
  days_ahead: number;
}

export interface DeliverableAlert {
  type: 'day_of' | 'tomorrow' | 'this_week' | 'two_weeks' | 'overdue';
  priority: 'critical' | 'high' | 'medium' | 'low';
  deliverable_id: number;
  project_code: string;
  deliverable_name: string;
  message: string;
  assigned_pm?: string | null;
  days_overdue?: number;
  has_context?: boolean;
}

export interface DeliverableAlertsResponse {
  success: boolean;
  alerts: DeliverableAlert[];
  count: number;
  by_priority: {
    critical: DeliverableAlert[];
    high: DeliverableAlert[];
    medium: DeliverableAlert[];
    low: DeliverableAlert[];
  };
}

export interface PMWorkload {
  pm_name: string;
  total_deliverables: number;
  pending_count: number;
  in_progress_count: number;
  completed_count: number;
  overdue_count: number;
  due_this_week: number;
  due_two_weeks: number;
}

export interface PMWorkloadResponse {
  success: boolean;
  workload: PMWorkload[];
  pm_count: number;
}

export interface PM {
  member_id: number;
  full_name: string;
  discipline: string;
  office: string;
  is_team_lead: number;
}

export interface PMListResponse {
  success: boolean;
  pms: PM[];
  count: number;
}

export interface ProjectPhaseStatus {
  project_code: string;
  project_title: string | null;
  contract_date: string | null;
  months_since_contract: number;
  expected_phase: string;
  phases: {
    phase: string;
    total: number;
    completed: number;
    earliest_due: string | null;
    last_completed: string | null;
  }[];
  flags: {
    type: string;
    message: string;
    typical?: string;
    action?: string;
  }[];
}

export interface ProjectPhaseStatusResponse {
  success: boolean;
  project_code: string;
  project_title: string | null;
  contract_date: string | null;
  months_since_contract: number;
  expected_phase: string;
  phases: ProjectPhaseStatus['phases'];
  flags: ProjectPhaseStatus['flags'];
}

export interface LifecyclePhase {
  phase: string;
  phase_order: number;
  typical_duration_months: number;
  description: string;
  deliverables: string[];
  is_optional?: boolean;
}

export interface LifecyclePhasesResponse {
  success: boolean;
  phases: LifecyclePhase[];
  total_typical_months: number;
}

// AI Learning Types
export interface AISuggestion {
  suggestion_id: number;
  suggestion_type: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  confidence_score: number;
  source_type: string;
  source_id: number | null;
  source_reference: string;
  title: string;
  description: string | null;
  suggested_action: string | null;
  suggested_data: string | null;
  target_table: string | null;
  target_id: number | null;
  project_code: string | null;
  project_name: string | null;
  proposal_id: number | null;
  status: string;
  reviewed_by: string | null;
  reviewed_at: string | null;
  review_notes: string | null;
  correction_data: string | null;
  created_at: string;
}

export interface AISuggestionsResponse {
  success: boolean;
  suggestions: AISuggestion[];
  count: number;
}

export interface LearnedPattern {
  pattern_id: number;
  pattern_name: string;
  pattern_type: string;
  condition: Record<string, unknown>;
  action: Record<string, unknown>;
  confidence_score: number;
  evidence_count: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface LearnedPatternsResponse {
  success: boolean;
  patterns: LearnedPattern[];
  count: number;
}

export interface LearningStatsResponse {
  success: boolean;
  suggestions: Record<string, number>;
  feedback: Record<string, number>;
  active_patterns: number;
  approval_rate: number;
}

export interface RuleGenerationResponse {
  success: boolean;
  rules_created: number;
  rules_updated: number;
  patterns_found: string[];
}

// Follow-up Agent Types
export interface FollowUpProposal {
  proposal_id: number;
  project_code: string;
  project_name: string;
  client_company: string | null;
  contact_person: string | null;
  contact_email: string | null;
  status: string;
  last_contact_date: string | null;
  days_since_contact: number | null;
  next_action: string | null;
  next_action_date: string | null;
  project_value: number | null;
  win_probability: number | null;
  health_score: number | null;
  priority_score: number;
  urgency: string;
  communication_history?: {
    email_id: number;
    subject: string;
    date: string;
    folder: string;
  }[];
  last_email_sentiment?: string;
}

export interface FollowUpProposalsResponse {
  success: boolean;
  proposals: FollowUpProposal[];
  count: number;
}

export interface FollowUpSummaryResponse {
  success: boolean;
  total_active_proposals: number;
  needing_follow_up: number;
  by_urgency: Record<string, { count: number; value: number }>;
  value_at_risk: number;
  top_priority: {
    project_code: string;
    project_name: string;
    client: string | null;
    value: number;
    urgency: string;
    priority_score: number;
  }[];
  overdue_actions: {
    project_code: string;
    action: string | null;
    due_date: string | null;
  }[];
}

// Pattern-Enhanced Query Types
export interface EnhancedQueryResponse {
  success: boolean;
  question: string;
  results: Record<string, unknown>[];
  count: number;
  sql?: string;
  summary?: string;
  reasoning?: string;
  confidence?: number;
  patterns_used?: string[];
  method: "ai" | "pattern_enhanced" | "pattern_matching" | "ai_with_context";
  error?: string;
}

export interface QuerySuggestion {
  query: string;
  source: "learned_pattern" | "recent" | "default";
  pattern?: string;
  success_count?: number;
}

export interface QueryLearningStats {
  active_patterns: number;
  total_feedback?: number;
  correct_queries?: number;
  corrected_queries?: number;
  accuracy_rate?: number;
  error?: string;
}

// ============================================================================
// AI SUGGESTIONS QUEUE TYPES
// ============================================================================

export interface SuggestionItem {
  suggestion_id: number;
  suggestion_type: string;
  priority: string;
  confidence_score: number;
  source_type: string;
  source_id: number | null;
  source_reference: string | null;
  title: string;
  description: string;
  suggested_action: string;
  suggested_data: string | Record<string, unknown>; // JSON string or parsed object
  target_table: string | null;
  target_id: number | null;
  project_code: string | null;
  proposal_id: number | null;
  status: "pending" | "approved" | "rejected" | "applied";
  reviewed_by: string | null;
  reviewed_at: string | null;
  review_notes: string | null;
  correction_data: string | null;
  created_at: string;
  expires_at: string | null;
}

export interface NewContactSuggestion {
  name: string;
  email: string;
  company?: string;
  related_project?: string;
}

export interface ProjectAliasSuggestion {
  alias: string;
  project_code: string;
}

export interface SuggestionsResponse {
  success: boolean;
  suggestions: SuggestionItem[];
  total: number;
  returned: number;
}

export interface SuggestionsStatsResponse {
  success: boolean;
  by_status: Record<string, number>;
  pending_by_field: Record<string, number>;
  high_confidence_pending: number;
  avg_pending_confidence: number;
}

export interface GroupedSuggestion {
  project_code: string | null;
  project_name: string | null;
  suggestion_count: number;
  suggestions: SuggestionItem[];
}

export interface GroupedSuggestionsResponse {
  success: boolean;
  groups: GroupedSuggestion[];
  total: number;
  ungrouped_count: number;
}

export interface SuggestionPreviewResponse {
  success: boolean;
  is_actionable: boolean;
  action: 'insert' | 'update' | 'delete' | 'none';
  table: string | null;
  summary: string;
  changes: Array<{
    field: string;
    old_value: unknown;
    new_value: unknown;
  }>;
}

export interface SuggestionSourceResponse {
  success: boolean;
  source_type: 'email' | 'transcript' | 'pattern' | null;
  content: string | null;
  metadata: {
    email_id?: number;
    subject?: string;
    sender?: string;
    recipients?: string;
    date?: string;
    folder?: string;
    transcript_id?: number;
    title?: string;
    filename?: string;
    summary?: string;
    duration_seconds?: number;
    source_id?: number;
    source_reference?: string;
    note?: string;
  };
}
