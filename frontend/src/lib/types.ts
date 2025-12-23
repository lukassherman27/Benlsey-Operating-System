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
  client_company?: string | null;
  next_steps?: string | null;
  // Ball in court tracking
  ball_in_court?: string | null;
  waiting_for?: string | null;
  // Value and contact info
  project_value?: number | null;
  primary_contact_name?: string | null;
  primary_contact_email?: string | null;
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

export interface ProposalFollowUp {
  proposal_id: number;
  project_code: string;
  project_name: string;
  status: string;
  client_company: string | null;
  contact_person: string | null;
  contact_email: string | null;
  project_value: number | null;
  last_email_date: string | null;
  our_last_email: string | null;
  client_last_email: string | null;
  email_count: number;
  last_sender: string | null;
  last_subject: string | null;
  days_since_contact: number;
  last_sender_type: 'us' | 'client';
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
  // Pipeline metrics (optional - may not be returned by all endpoints)
  total_pipeline_value?: number;
  active_proposals?: number;
  contracts_won?: number;
  contracts_won_value?: number;
  conversion_rate?: number;
  avg_days_to_close?: number;
  win_rate?: number;
  projects_at_risk?: number;
  avg_deal_size?: number;
  outstanding_invoices?: number;
  outstanding_value?: number;
  overdue_value?: number;
  revenue_this_month?: number;
  revenue_change_percent?: number;
  proposals_by_status?: Array<{ status: string; count: number; value: number }>;
  revenue_by_month?: Array<{ month: string; revenue: number }>;
  top_clients?: Array<{ client: string; value: number; count: number; projects?: number }>;
}

export interface DashboardStats {
  // Legacy stats (no role)
  proposals?: {
    total: number;
    active: number;
    at_risk: number;
    needs_follow_up: number;
  };
  revenue?: {
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
  // Role-based stats (role=bill)
  role?: string;
  pipeline_value?: number;
  active_projects_count?: number;
  outstanding_invoices_total?: number;
  overdue_invoices_count?: number;
  // Role-based stats (role=pm)
  my_projects_count?: number;
  deliverables_due_this_week?: number;
  open_rfis_count?: number;
  // Role-based stats (role=finance)
  total_outstanding?: number;
  overdue_30_days?: number;
  overdue_60_days?: number;
  overdue_90_plus?: number;
  recent_payments_7_days?: number;
}

export interface KPITrend {
  value: number;
  direction: "up" | "down" | "neutral";
  label: string;
}

export interface KPIValue {
  value: number;
  previous?: number;
  trend: KPITrend;
}

export interface DashboardKPIs {
  // Period info
  period?: string;
  period_label?: string;
  date_range?: {
    start: string | null;
    end: string | null;
  };
  // Core KPIs
  active_projects: KPIValue;
  active_proposals: KPIValue;
  remaining_contract_value: KPIValue;
  outstanding_invoices: KPIValue & {
    overdue_count?: number;
    overdue_amount?: number;
  };
  revenue_ytd: KPIValue;
  // Period-based KPIs
  contracts_signed?: KPIValue & { amount?: number };
  contracts_signed_2025?: KPIValue;
  paid_in_period?: KPIValue & { previous_value?: number };
  total_paid_to_date?: KPIValue;
  // Additional KPIs
  avg_days_to_payment?: number;
  largest_outstanding?: {
    amount: number;
    invoice_number: string | null;
  };
  win_rate?: number;
  pipeline_value?: number;
  // Meta
  timestamp?: string;
  currency?: string;
  trend_period_days: number;
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

export interface WeeklyChangeProposal {
  proposal_id: number;
  project_code: string;
  project_name: string;
  client_company: string;
  fee?: number;
  status?: string;
  created_date?: string;
}

export interface WeeklyChangeStatusChange {
  project_code: string;
  project_name: string;
  client_company: string;
  previous_status: string;
  new_status: string;
  changed_date: string;
}

export interface WeeklyChangeStalledProposal {
  proposal_id: number;
  project_code: string;
  project_name: string;
  client_company: string;
  days_since_contact: number;
  last_contact_date: string | null;
}

export interface WeeklyChangeWonProposal {
  proposal_id: number;
  project_code: string;
  project_name: string;
  client_company: string;
  fee: number;
  signed_date: string;
}

export interface ProposalWeeklyChanges {
  period: {
    start_date: string;
    end_date: string;
    days: number;
  };
  summary: {
    new_proposals: number;
    status_changes: number;
    stalled_proposals: number;
    won_proposals: number;
    total_pipeline_value: string;
  };
  new_proposals: WeeklyChangeProposal[];
  status_changes: WeeklyChangeStatusChange[];
  stalled_proposals: WeeklyChangeStalledProposal[];
  won_proposals: WeeklyChangeWonProposal[];
}

// Proposal Tracker Types
export type ProposalStatus =
  | "First Contact"
  | "Drafting"
  | "Proposal Sent"
  | "On Hold"
  | "Archived"
  | "Contract Signed";

export interface ProposalTrackerItem {
  id: number;
  project_code: string;
  project_name: string;
  project_value: number;
  country: string;
  current_status: ProposalStatus;
  last_week_status: ProposalStatus | null;
  status_changed_date: string | null;
  days_in_current_status: number;
  first_contact_date: string | null;
  proposal_sent_date: string | null;
  proposal_sent: number;
  current_remark: string | null;
  latest_email_context: string | null;
  waiting_on: string | null;
  next_steps: string | null;
  last_email_date: string | null;
  email_count?: number;
  first_email_date?: string | null;
  updated_at: string;
  // Ball in court tracking
  ball_in_court?: string | null;
  waiting_for?: string | null;
  // Optional contact/summary fields used in quick edit dialog
  contact_person?: string | null;
  contact_email?: string | null;
  contact_phone?: string | null;
  project_summary?: string | null;
}

export interface ProposalTrackerStats {
  total_proposals: number;
  total_pipeline_value: number;
  avg_days_in_status: number;
  status_breakdown: {
    current_status: ProposalStatus;
    count: number;
    total_value: number;
  }[];
  needs_followup: number;
}

export interface ProposalTrackerListResponse {
  success: boolean;
  proposals: ProposalTrackerItem[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface ProposalTrackerStatsResponse {
  success: boolean;
  stats: ProposalTrackerStats;
}

export interface ProposalTrackerDetailResponse {
  success: boolean;
  proposal: ProposalTrackerItem;
}

export interface ProposalStatusHistoryItem {
  id: number;
  project_code: string;
  old_status: ProposalStatus;
  new_status: ProposalStatus;
  changed_date: string;
  changed_by: string | null;
  source_email_id: number | null;
  notes: string | null;
}

export interface ProposalEmailIntelligence {
  id: number;
  email_id: number;
  project_code: string;
  status_update: string | null;
  key_information: string | null;
  action_items: string | null;
  client_sentiment: string | null;
  confidence_score: number | null;
  email_subject: string;
  email_date: string;
  email_from: string;
  email_to: string;
  email_snippet: string | null;
  processed_at: string;
}

export type DisciplineFilter = 'all' | 'landscape' | 'interior' | 'architect' | 'combined';

export interface ProposalTrackerQueryParams {
  status?: ProposalStatus;
  country?: string;
  search?: string;
  discipline?: DisciplineFilter;
  page?: number;
  per_page?: number;
}

export interface DisciplineStats {
  count: number;
  total_value: number;
}

export interface DisciplineStatsResponse {
  success: boolean;
  disciplines: {
    all: DisciplineStats;
    landscape: DisciplineStats;
    interior: DisciplineStats;
    architect: DisciplineStats;
    combined: DisciplineStats;
  };
}

export interface ProposalTrackerUpdateRequest {
  project_name?: string;
  project_value?: number;
  country?: string;
  current_status?: ProposalStatus;
  current_remark?: string;
  project_summary?: string;
  waiting_on?: string;
  next_steps?: string;
  proposal_sent_date?: string;
  first_contact_date?: string;
  proposal_sent?: number;
}

// Admin - Email Links types
export interface EmailLink {
  link_id: string;  // Composite key: "email_id-project_id"
  email_id: number;
  project_id: number;
  confidence_score: number;
  link_type: string;  // "auto" | "manual" | "ai" | "alias"
  match_reasons: string | null;
  created_at: string;
  subject: string;
  sender_email: string;
  email_date: string;
  snippet: string;
  category: string;
  project_code: string;
  project_name: string;
  project_status: string;
}

export interface EmailLinksResponse {
  links: EmailLink[];
  total: number;
  limit: number;
  offset: number;
}

export interface CreateEmailLinkRequest {
  email_id: number;
  proposal_id: number;
  user: string;
}

// Invoice Aging Types
export interface InvoiceBase {
  invoice_number: string;
  invoice_amount: number;
  invoice_date: string;
  project_code?: string;
  project_title?: string;
}

export interface PaidInvoice extends InvoiceBase {
  payment_amount: number;
  payment_date: string;
  status: 'paid';
  description?: string;
}

export interface OutstandingInvoice extends InvoiceBase {
  due_date?: string;
  days_overdue: number;
  status: 'outstanding';
  description?: string;
  discipline?: string;
  phase?: string;
  scope?: string;
}

export interface AgingCategory {
  count: number;
  amount: number;
}

export interface AgingBreakdown {
  under_30: AgingCategory;
  '30_to_90': AgingCategory;
  over_90: AgingCategory;
}

export interface InvoiceAgingSummary {
  total_outstanding_count: number;
  total_outstanding_amount: number;
}

export interface InvoiceAgingData {
  recent_paid: PaidInvoice[];
  largest_outstanding: OutstandingInvoice[];
  aging_breakdown: AgingBreakdown;
  summary: InvoiceAgingSummary;
}

export interface InvoiceAgingResponse {
  success: boolean;
  data: InvoiceAgingData;
}

export interface TopOutstandingInvoice {
  project_code: string;
  project_name?: string;
  project_title?: string;  // API sometimes uses this
  outstanding?: number;
  invoice_amount?: number;  // API uses this
  days_outstanding?: number;
  days_overdue?: number;  // API uses this
  invoice_count?: number;
  invoice_number?: string;
}

export interface FilteredOutstandingInvoice extends TopOutstandingInvoice {
  invoice_date?: string;
  due_date?: string;
  status?: string;
  invoice_amount?: number;
  payment_amount?: number;
  phase?: string;
  aging_category?: {
    color: string;
  };
}

export interface ApiPhaseBreakdown {
  breakdown_id: number;
  discipline: string;
  phase: string;
  phase_fee_usd: number;
  percentage_of_total?: number;
}

export interface ApiProjectInvoice {
  invoice_id: number;
  breakdown_id?: string;
  invoice_number: string;
  invoice_date: string;
  invoice_amount: number;
  payment_date?: string;
  payment_amount?: number;
  status: string;
}

// Project Types
export interface Project {
  project_id: number;
  project_code: string;
  project_title: string;
  client_name?: string;
  contract_value?: number;
  total_fee_usd?: number;
  status?: string;
  current_phase?: string;
  paid_to_date_usd?: number;
  outstanding_usd?: number;
  total_invoiced?: number;
  total_paid?: number;
  remaining_value?: number;
  payment_status?: 'outstanding' | 'paid' | 'pending';
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  last_invoice?: any;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  invoice_history?: any[];
  health_score?: number;
  project_type?: string;
  country?: string;
  city?: string;
  scope_summary?: string;
  [key: string]: unknown; // Index signature for flexibility
}

export interface ActiveProjectsResponse {
  data: Project[];
  count: number;
}

// Project Email Types (for email activity feed)
export interface ProjectEmail {
  email_id: number;
  subject: string;
  sender_email: string;
  sender_name?: string | null;
  date: string;
  date_normalized?: string | null;
  snippet?: string | null;
  body_preview?: string;
  has_attachments: number;
  category?: string | null;
  subcategory?: string | null;
  importance_score?: number | null;
  ai_summary?: string | null;
  confidence_score: number;
  project_title?: string;
}

export interface ProjectEmailsResponse {
  success: boolean;
  project_code: string;
  data: ProjectEmail[];
  count: number;
}

export interface ProjectEmailSummary {
  success: boolean;
  project_code: string;
  total_emails: number;
  date_range?: {
    first: string;
    last: string;
  };
  email_groups?: Record<string, number>;
  ai_summary?: {
    executive_summary: string;
    error?: string;
  };
  summary?: string;
  key_points?: string[];
  timeline?: Array<{
    date: string;
    event: string;
    [key: string]: unknown;
  }>;
  recent_emails?: ProjectEmail[];
}

// Project Financial Hierarchy Types
export interface PhaseInvoice {
  invoice_id: number;
  invoice_number: string;
  invoice_amount: number;
  payment_amount: number;
  amount_applied?: number;
  percentage_of_phase?: number;
  invoice_date: string;
  due_date: string | null;
  payment_date: string | null;
  status: string;
}

export interface ProjectPhase {
  breakdown_id: string;
  phase: string;
  phase_fee: number;
  total_invoiced: number;
  total_paid: number;
  remaining: number;
  invoices: PhaseInvoice[];
}

export interface DisciplineBreakdown {
  total_fee: number;
  total_invoiced: number;
  total_paid: number;
  remaining: number;
  phases: ProjectPhase[];
}

export interface ProjectHierarchy {
  success: boolean;
  project_code: string;
  project_name: string | null;
  total_contract_value: number;
  total_invoiced: number;
  total_paid: number;
  disciplines: Record<string, DisciplineBreakdown>;
}


// ============================================================================
// Enhanced Review UI Types
// ============================================================================

/**
 * Source content (email or transcript) for a suggestion
 */
export interface SourceContent {
  type: 'email' | 'transcript';
  id: number;
  subject?: string;
  sender?: string;
  recipient?: string;
  date: string;
  body: string;
  attachments?: { filename: string; size: number }[];
  thread_context?: string[];  // Previous emails in thread
}

/**
 * Detected entities from AI analysis
 */
export interface DetectedEntities {
  projects: string[];
  fees: { amount: number; currency: string }[];
  contacts: { name: string; email: string }[];
  dates: string[];
  keywords: string[];
}

/**
 * Pattern that will be learned from this action
 */
export interface PatternToLearn {
  type: 'sender_to_project' | 'domain_to_project' | 'keyword_to_project';
  pattern_key: string;
  target: string;
  confidence_boost: number;
}

/**
 * Suggested action that can be applied
 */
export interface SuggestedAction {
  id: string;
  type: 'link_email' | 'update_fee' | 'link_contact' | 'learn_pattern';
  description: string;
  enabled_by_default: boolean;
  data: Record<string, unknown>;
  database_change: string;  // Human-readable SQL description
}

/**
 * AI analysis of a suggestion
 */
export interface AIAnalysis {
  detected_entities: DetectedEntities;
  suggested_actions: SuggestedAction[];
  pattern_to_learn: PatternToLearn | null;
  overall_confidence: number;
}

/**
 * User context provided during review
 */
export interface UserContext {
  notes: string;
  tags: string[];
  contact_role?: string;
  priority?: string;
}

/**
 * Actions to apply when approving
 */
export interface ApprovalAction {
  type: 'link_email' | 'update_fee' | 'link_contact' | 'learn_pattern';
  enabled: boolean;
  data: Record<string, unknown>;
}

/**
 * Full context for reviewing a suggestion
 * Note: SuggestionItem and SuggestionPreviewResponse are defined in api.ts
 */
export interface SuggestionFullContext {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  suggestion: any; // SuggestionItem from api.ts
  source_content: SourceContent | null;
  ai_analysis: AIAnalysis;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  preview: any; // SuggestionPreviewResponse from api.ts
  existing_feedback?: {
    notes: string;
    tags: string[];
    contact_role?: string;
    priority?: string;
  };
}

/**
 * Request to approve with context
 */
export interface ApproveWithContextRequest {
  actions: ApprovalAction[];
  user_context: UserContext;
  create_sender_pattern?: boolean;
  create_domain_pattern?: boolean;
}

/**
 * Response from approve with context
 */
export interface ApproveWithContextResponse {
  success: boolean;
  message: string;
  data: {
    suggestion_id: number;
    actions_applied: string[];
    patterns_created: Array<{ type: string; key: string }>;
    feedback_saved: boolean;
  };
}

/**
 * Suggestion tag for autocomplete
 */
export interface SuggestionTag {
  tag_id: number;
  tag_name: string;
  tag_category: string;
  usage_count: number;
}

/**
 * Response with available tags
 */
export interface SuggestionTagsResponse {
  success: boolean;
  tags: SuggestionTag[];
}

/**
 * Validation suggestion for data corrections
 */
export interface ValidationSuggestion {
  suggestion_id: number;
  project_code: string;
  entity_name: string;
  field_name: string;
  current_value: string;
  suggested_value: string;
  evidence_source: string;
  evidence_email_subject?: string;
  evidence_snippet: string;
  reasoning: string;
  confidence_score: number;
  status: 'pending' | 'applied' | 'approved' | 'denied';
  reviewed_by?: string;
  reviewed_at?: string;
}

// ============================================================================
// My Day Types
// ============================================================================

export interface MyDayTask {
  task_id: number;
  title: string;
  description: string | null;
  task_type: string;
  priority: string;
  status: string;
  due_date: string | null;
  project_code: string | null;
  assignee: string | null;
  created_at: string;
}

export interface MyDayMeeting {
  meeting_id: number;
  meeting_title: string | null;
  meeting_type: string | null;
  meeting_date: string;
  start_time: string | null;
  end_time: string | null;
  location: string | null;
  project_code: string | null;
  status: string;
  attendees: string | null;
}

export interface MyDayProposal {
  proposal_id: number;
  project_code: string;
  project_name: string;
  client_name: string | null;
  status: string;
  ball_in_court: string | null;
  waiting_for: string | null;
  last_contact_date: string | null;
  next_followup_date: string | null;
  probability: number | null;
  urgency: 'overdue' | 'today' | 'upcoming';
  days_since_contact: number | null;
}

export interface MyDaySuggestion {
  suggestion_id: number;
  suggestion_type: string;
  title: string;
  description: string | null;
  priority: string;
  confidence_score: number | null;
  project_code: string | null;
  created_at: string;
}

export interface MyDayCommitment {
  commitment_id: number;
  commitment_type: 'our_commitment' | 'their_commitment';
  description: string;
  committed_by: string | null;
  due_date: string | null;
  fulfillment_status: string;
  project_code: string | null;
}

export interface MyDayDeliverable {
  deliverable_id: number;
  name: string;
  project_code: string | null;
  due_date: string | null;
  status: string;
}

export interface MyDayResponse {
  success: boolean;
  greeting: {
    text: string;
    name: string;
    date: string;
    day_of_week: string;
    formatted_date: string;
  };
  tasks: {
    today: MyDayTask[];
    overdue: MyDayTask[];
    today_count: number;
    overdue_count: number;
    total_active: number;
  };
  meetings: {
    today: MyDayMeeting[];
    count: number;
    has_virtual: boolean;
  };
  proposals: {
    needing_followup: MyDayProposal[];
    count: number;
    total_our_ball: number;
  };
  suggestions_queue: {
    top_suggestions: MyDaySuggestion[];
    total_pending: number;
    by_type: Record<string, number>;
  };
  week_ahead: {
    upcoming_deadlines: MyDayTask[];
    meetings_this_week: number;
    decision_dates: Array<{
      project_code: string;
      project_name: string;
      client_name: string | null;
      decision_date: string;
    }>;
    deliverables_due: MyDayDeliverable[];
  };
  commitments: {
    our_overdue: MyDayCommitment[];
    their_overdue: MyDayCommitment[];
    our_overdue_count: number;
    their_overdue_count: number;
  };
  generated_at: string;
}
