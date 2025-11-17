export interface Pagination {
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
}

export interface ProposalSummary {
  proposal_id: number;
  project_code: string;
  project_name: string;
  client_name: string | null;
  status: string;
  is_active_project: number;
  health_score: number | null;
  health_calculated?: boolean;
  days_since_contact: number | null;
  last_contact_date: string | null;
  next_action: string | null;
  pm: string | null;
  email_count?: number;
  document_count?: number;
}

export interface ProposalListResponse {
  data: ProposalSummary[];
  pagination: Pagination;
}

export interface ProposalDetail extends ProposalSummary {
  phase?: string | null;
  win_probability?: number | null;
  created_date?: string | null;
  updated_date?: string | null;
}

export interface ProposalHealth {
  project_code: string;
  project_name: string;
  health_score: number | null;
  health_status: "healthy" | "at_risk" | "critical" | string;
  factors?: Record<string, string | number | null>;
  risks?: Array<{
    type: string;
    severity: string;
    description: string;
  }>;
  recommendation?: string | null;
}

export interface TimelineEvent {
  type: string;
  date: string;
  [key: string]: unknown;
}

export interface TimelineEmail {
  email_id: number;
  subject: string;
  sender_email: string;
  date: string;
  category?: string;
  subcategory?: string | null;
  importance_score?: number | null;
  action_required?: boolean | number;
  follow_up_date?: string | null;
}

export interface TimelineDocument {
  document_id: number;
  file_name: string;
  document_type: string;
  modified_date?: string;
  file_size?: number;
}

export interface ProposalTimelineResponse {
  proposal: {
    project_code: string;
    project_name: string;
    status: string;
  };
  timeline: TimelineEvent[];
  emails: TimelineEmail[];
  documents: TimelineDocument[];
  stats?: {
    total_emails: number;
    total_documents: number;
    timeline_events: number;
  };
}

export interface AnalyticsDashboard {
  proposals: {
    total_proposals: number;
    active_projects: number;
    healthy: number;
    at_risk: number;
    critical: number;
    active_last_week: number;
    need_followup: number;
  };
  emails: {
    total_emails: number;
    processed: number;
    unprocessed: number;
    with_full_body: number;
    linked_to_proposals: number;
  };
  documents: {
    total_documents: number;
    linked_to_proposals: number;
    total_size_bytes: number;
    most_common_type: string;
  };
  timestamp: string;
}

export interface DashboardStats {
  proposals: {
    total: number;
    active: number;
    at_risk: number;
    needs_follow_up: number;
  };
  revenue: {
    total_contracts: number;
    paid: number;
    outstanding: number;
    remaining: number;
  };
  total_emails?: number;
  categorized_emails?: number;
  needs_review?: number;
  total_attachments?: number;
  training_progress?: Record<string, unknown>;
}

export interface ProposalStats {
  total_proposals: number;
  active_projects: number;
  healthy: number;
  at_risk: number;
  critical: number;
  active_last_week?: number;
  need_followup: number;
  needs_attention?: number;
  avg_health_score?: number | null;
}

export interface BriefingAction {
  type: string;
  priority?: string;
  project_code?: string;
  project_name?: string;
  action: string;
  context?: string;
  detail?: string;
}

export interface BriefingWin {
  title?: string;
  project_code?: string;
  project_name?: string;
  description?: string;
  amount_usd?: number;
  date?: string;
}

export interface DailyBriefing {
  date: string;
  business_health: {
    status: string;
    summary: string;
  };
  urgent: BriefingAction[];
  needs_attention: BriefingAction[];
  insights: string[];
  wins: BriefingWin[];
  metrics: {
    total_projects: number;
    at_risk: number;
    revenue: number;
    outstanding: number;
    [key: string]: number;
  };
}

export interface TopValueProposal {
  project_code: string;
  project_name: string;
  client_name?: string;
  status?: string;
  phase?: string;
  pm?: string;
  total_fee_usd: number;
  currency?: string;
}

export interface QueryResponse {
  success: boolean;
  question: string;
  results: Array<Record<string, unknown>>;
  count: number;
  sql?: string;
  params?: unknown[];
  error?: string;
  summary?: string; // AI-generated natural language summary
  reasoning?: string; // AI's reasoning for the query
  confidence?: number; // AI confidence score (0-100)
  method?: 'ai' | 'pattern_matching'; // Method used to generate query
}

export interface QuerySuggestionsResponse {
  examples: string[]; // Example queries from API
  ai_enabled: boolean; // Whether AI queries are available
  suggestions?: string[]; // Legacy field for backward compatibility
  types?: Array<{
    type: string;
    description: string;
    examples: string[];
    filters?: string[];
  }>;
}

export interface ProposalBriefing {
  client: {
    name: string;
    contact: string;
    email: string;
    last_contact_date: string | null;
    days_since_contact: number;
    next_action: string;
  };
  project: {
    code: string;
    name: string;
    phase: string;
    status: string;
    win_probability: number;
    health_score: number;
    health_status: string;
    pm: string;
  };
  submissions: Array<{
    title?: string;
    submitted_date?: string;
    description?: string;
    link?: string;
  }>;
  financials: {
    total_contract_value: number;
    currency: string;
    initial_payment_received: number;
    outstanding_balance: number;
    next_payment: string | null;
    overdue_amount: number;
  };
  milestones: Array<{
    milestone_name: string;
    expected_date: string;
    actual_date?: string | null;
    status: string;
    responsible_party: string;
  }>;
  open_issues: {
    rfis: Array<Record<string, unknown>>;
    blockers: Array<Record<string, unknown>>;
    internal_tasks: Array<Record<string, unknown>>;
  };
  recent_emails: Array<{
    date: string;
    subject: string;
    sender: string;
    category: string;
    snippet: string;
  }>;
  documents_breakdown: {
    total: number;
    by_type: {
      contracts: number;
      presentations: number;
      drawings: number;
      renderings: number;
      [key: string]: number;
    };
  };
}

export interface OutreachTileItem {
  proposal_id?: number;
  project_code: string;
  project_name: string;
  days_since_contact?: number;
}

export interface RfiTileItem {
  rfi_id: number;
  proposal_id: number;
  rfi_number: string;
  question: string;
  asked_by?: string;
  asked_date?: string;
  priority?: string;
  status?: string;
  days_waiting?: number;
  project_code: string;
  project_name: string;
  client_company?: string;
}

export interface MeetingTileItem {
  meeting_id: number;
  proposal_id: number;
  meeting_type?: string;
  meeting_title?: string;
  scheduled_date?: string;
  location?: string;
  meeting_url?: string;
  status?: string;
  project_code: string;
  project_name: string;
  client_company?: string;
}

export interface MilestoneTileItem {
  milestone_id: number;
  project_id?: number;
  project_code: string;
  project_name: string;
  milestone_name?: string;
  milestone_type?: string;
  planned_date?: string;
  actual_date?: string;
  status?: string;
  notes?: string;
}

export interface PaymentTileItem {
  financial_id: number;
  proposal_id?: number;
  project_code: string;
  project_name: string;
  due_date?: string;
  amount?: number;
  currency?: string;
  status?: string;
  invoice_number?: string;
  days_outstanding?: number;
}

export interface DecisionTileGroup<T> {
  count: number;
  items: T[];
}

export interface DecisionTiles {
  proposals_needing_outreach: DecisionTileGroup<OutreachTileItem>;
  unanswered_rfis: DecisionTileGroup<RfiTileItem>;
  upcoming_meetings: DecisionTileGroup<MeetingTileItem>;
  overdue_milestones: DecisionTileGroup<MilestoneTileItem>;
  overdue_payments: DecisionTileGroup<PaymentTileItem>;
}

export interface IntelligenceSuggestionEvidence {
  root_cause?: string;
  signals?: Array<{ label: string; value: string }>;
  supporting_files?: Array<{ type: string; reference: string }>;
  detection_logic?: string;
  [key: string]: unknown;
}

export interface IntelligenceSuggestionImpact {
  type?: string | null;
  value_usd?: number | null;
  summary?: string | null;
  severity?: string | null;
}

export interface IntelligenceSuggestion {
  id: string;
  project_code: string;
  project_name?: string;
  is_active_project?: number;
  suggestion_type: string;
  summary?: string;
  proposed_fix: Record<string, unknown>;
  impact?: IntelligenceSuggestionImpact;
  impact_type?: string;
  impact_value_usd?: number;
  impact_summary?: string;
  confidence: number;
  severity?: string;
  bucket?: string;
  pattern_id?: string;
  pattern_label?: string;
  auto_apply_candidate?: boolean;
  status?: string;
  created_at?: string;
  snooze_until?: string | null;
  evidence?: IntelligenceSuggestionEvidence;
}

export interface IntelligenceSuggestionGroup {
  bucket: string;
  label: string;
  description?: string;
  items: IntelligenceSuggestion[];
}

export interface IntelligenceSuggestionsResponse {
  group: string;
  items: IntelligenceSuggestion[];
  generated_at?: string;
}

export interface FinancePayment {
  invoice_id?: number;
  invoice_number?: string;
  project_code: string;
  project_name: string;
  discipline?: string;
  amount_usd: number;
  paid_on: string;
}

export interface RecentPaymentsResponse {
  payments: FinancePayment[];
  count: number;
}

export interface ProjectedInvoice {
  project_code: string;
  project_name: string;
  phase: string;
  presentation_date: string;
  projected_fee_usd: number;
  scope?: string;
  status?: string;
}

export interface ProjectedInvoicesResponse {
  invoices: ProjectedInvoice[];
  count: number;
  total_projected_usd: number;
}

export interface SystemHealth {
  email_processing: {
    total_emails: number;
    processed: number;
    unprocessed: number;
    categorized_percent: number;
    processing_rate: string;
  };
  model_training: {
    training_samples: number;
    target_samples: number;
    completion_percent: number;
    model_accuracy: number;
  };
  database: {
    total_proposals: number;
    active_projects: number;
    total_documents: number;
    last_sync: string;
  };
  api_health: {
    uptime_seconds: number;
    requests_last_hour: number;
    avg_response_time_ms: number;
  };
}

export interface ManualOverride {
  override_id: number;
  proposal_id?: number;
  project_code?: string;
  scope: "emails" | "documents" | "billing" | "rfis" | "scheduling" | "general";
  instruction: string;
  author: string;
  source?: string;
  urgency: "informational" | "urgent";
  status: "active" | "applied" | "archived";
  applied_by?: string;
  applied_at?: string;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface ManualOverridesResponse {
  data: ManualOverride[];
  pagination: Pagination;
}

export interface ManualOverrideCreateRequest {
  project_code?: string;
  scope: ManualOverride["scope"];
  instruction: string;
  author: string;
  source?: string;
  urgency: ManualOverride["urgency"];
  tags?: string[];
}

export interface ManualOverrideUpdateRequest {
  project_code?: string | null;
  scope?: ManualOverride["scope"];
  instruction?: string;
  author?: string;
  urgency?: ManualOverride["urgency"];
  status?: ManualOverride["status"];
  applied_by?: string | null;
  applied_at?: string | null;
  tags?: string[];
}

export interface ProposalsQueryParams {
  status?: string;
  is_active?: boolean;
  page?: number;
  per_page?: number;
  sort_by?: string;
  sort_order?: "ASC" | "DESC";
}

export interface EmailSummary {
  email_id: number;
  subject: string;
  sender_email: string;
  date: string;
  snippet?: string;
  category?: string | null;
  subcategory?: string | null;
  importance_score?: number | null;
  ai_summary?: string | null;
  project_code?: string | null;
  is_active_project?: number | null;
}

export interface EmailListResponse {
  data: EmailSummary[];
  pagination: Pagination;
}

export type EmailCategoryCounts = Record<string, number>;

export interface EmailCategoryListItem {
  value: string;
  label: string;
  count: number;
}

export interface EmailCategoryListResponse {
  categories: EmailCategoryListItem[];
}

export interface EmailCategoryUpdateRequest {
  category: string;
  subcategory?: string | null;
  feedback?: string;
}

export interface EmailCategoryUpdateResponse {
  message: string;
  data: {
    email_id: number;
    subject: string;
    sender_email: string;
    category: string;
    subcategory?: string | null;
    previous_category?: string | null;
    feedback?: string | null;
  };
}

export interface IntelligenceDecisionRequest {
  decision: "approved" | "rejected" | "snoozed";
  reason?: string;
  apply_now?: boolean;
  dry_run?: boolean;
  batch_ids?: string[];
}

export type IntelligenceDecisionResponse =
  | {
      updated: number;
      applied: Array<{ project_code: string; changes: Record<string, unknown> }>;
      decisions_logged: number;
    }
  | {
      would_update: number;
      preview: unknown[];
      conflicts: unknown[];
      applied: boolean;
    };
