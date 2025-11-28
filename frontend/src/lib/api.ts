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
  ProposalStats,
  TopValueProposal,
  DailyBriefing,
  IntelligenceSuggestionsResponse,
  IntelligenceDecisionRequest,
  IntelligenceDecisionResponse,
  RecentPaymentsResponse,
  ProjectedInvoicesResponse,
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
    request<ProposalDetail>(`/api/proposals/by-code/${encodeURIComponent(projectCode)}`),

  getProposalHealth: (projectCode: string) =>
    request<ProposalHealth>(
      `/api/proposals/by-code/${encodeURIComponent(projectCode)}/health`
    ),

  getProposalTimeline: (projectCode: string) =>
    request<ProposalTimelineResponse>(
      `/api/proposals/by-code/${encodeURIComponent(projectCode)}/timeline`
    ),

  getDashboardAnalytics: () =>
    request<AnalyticsDashboard>("/api/analytics/dashboard"),

  getDashboardStats: () =>
    request<DashboardStats>("/api/dashboard/stats"),

  getProposalStats: () =>
    request<ProposalStats>("/api/proposals/stats"),

  getDailyBriefing: () =>
    request<DailyBriefing>("/api/briefing/daily"),

  executeQuery: (question: string) =>
    request<QueryResponse>("/api/query/ask", {
      method: "POST",
      body: JSON.stringify({ question, use_ai: true }),
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
    request<ProposalBriefing>(
      `/api/proposals/by-code/${encodeURIComponent(projectCode)}/briefing`
    ),

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
};
