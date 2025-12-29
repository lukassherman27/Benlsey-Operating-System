/**
 * Dashboard Intelligence Engine
 *
 * Calculates the overall health state of the business and determines
 * which dashboard sections should be prominently displayed.
 */

export type HealthState = "critical" | "needs_attention" | "healthy";

export interface HealthFactors {
  // Proposals
  ballWithUsOver7Days: number;
  overdueFollowUps: number;
  stalledProposals: number;

  // Financial
  overdueInvoices30: number;
  overdueInvoices60: number;
  overdueInvoices90: number;
  totalOverdueAmount: number;

  // Operations
  openRFIs: number;
  overdueDeliverables: number;

  // Communication
  silentProjects: number; // Projects with no activity for 14+ days
}

export interface HealthAssessment {
  state: HealthState;
  score: number;
  primaryConcerns: string[];
  sectionPriority: SectionPriority[];
}

export type DashboardSection =
  | "briefing"
  | "proposal_alerts"
  | "financial_alerts"
  | "kpis"
  | "hot_items"
  | "calendar"
  | "analytics"
  | "recent_emails"
  | "invoice_aging"
  | "import_summary"
  | "proposal_tracker"
  | "quick_actions";

export interface SectionPriority {
  section: DashboardSection;
  priority: number; // Lower = higher priority
  expanded: boolean;
  highlight: boolean;
}

/**
 * Calculate the overall health state from health factors.
 */
export function calculateHealthState(factors: HealthFactors): HealthAssessment {
  const concerns: string[] = [];
  let score = 0;

  // Proposals are #1 priority
  if (factors.ballWithUsOver7Days > 0) {
    score += factors.ballWithUsOver7Days * 10;
    concerns.push(
      `${factors.ballWithUsOver7Days} proposal${factors.ballWithUsOver7Days > 1 ? "s" : ""} waiting on us for 7+ days`
    );
  }
  if (factors.overdueFollowUps > 0) {
    score += factors.overdueFollowUps * 5;
    concerns.push(
      `${factors.overdueFollowUps} follow-up${factors.overdueFollowUps > 1 ? "s" : ""} overdue`
    );
  }
  if (factors.stalledProposals > 0) {
    score += factors.stalledProposals * 8;
    concerns.push(
      `${factors.stalledProposals} stalled proposal${factors.stalledProposals > 1 ? "s" : ""}`
    );
  }

  // Financial issues
  if (factors.overdueInvoices90 > 0) {
    score += factors.overdueInvoices90 * 15;
    concerns.push(`${factors.overdueInvoices90} invoice${factors.overdueInvoices90 > 1 ? "s" : ""} 90+ days overdue`);
  }
  if (factors.overdueInvoices60 > 0) {
    score += factors.overdueInvoices60 * 8;
  }
  if (factors.overdueInvoices30 > 0) {
    score += factors.overdueInvoices30 * 3;
  }

  // Operations
  if (factors.openRFIs > 3) {
    score += (factors.openRFIs - 3) * 2;
    concerns.push(`${factors.openRFIs} open RFIs need attention`);
  }
  if (factors.overdueDeliverables > 0) {
    score += factors.overdueDeliverables * 5;
    concerns.push(
      `${factors.overdueDeliverables} overdue deliverable${factors.overdueDeliverables > 1 ? "s" : ""}`
    );
  }

  // Communication gaps
  if (factors.silentProjects > 2) {
    score += (factors.silentProjects - 2) * 2;
  }

  // Determine state
  let state: HealthState;
  if (score > 50 || factors.overdueInvoices90 > 0 || factors.ballWithUsOver7Days > 2) {
    state = "critical";
  } else if (score > 20) {
    state = "needs_attention";
  } else {
    state = "healthy";
  }

  // Build section priority based on state
  const sectionPriority = buildSectionPriority(state, factors);

  return {
    state,
    score,
    primaryConcerns: concerns.slice(0, 3),
    sectionPriority,
  };
}

/**
 * Build the section priority ordering based on health state.
 */
function buildSectionPriority(
  state: HealthState,
  factors: HealthFactors
): SectionPriority[] {
  const hasProposalAlerts =
    factors.ballWithUsOver7Days > 0 ||
    factors.overdueFollowUps > 0 ||
    factors.stalledProposals > 0;
  const hasFinancialAlerts =
    factors.overdueInvoices30 > 0 ||
    factors.overdueInvoices60 > 0 ||
    factors.overdueInvoices90 > 0;

  if (state === "critical") {
    return [
      { section: "briefing", priority: 1, expanded: true, highlight: true },
      {
        section: "proposal_alerts",
        priority: 2,
        expanded: hasProposalAlerts,
        highlight: hasProposalAlerts,
      },
      {
        section: "financial_alerts",
        priority: 3,
        expanded: hasFinancialAlerts,
        highlight: hasFinancialAlerts,
      },
      { section: "kpis", priority: 4, expanded: true, highlight: false },
      { section: "hot_items", priority: 5, expanded: true, highlight: false },
      { section: "calendar", priority: 6, expanded: true, highlight: false },
      { section: "analytics", priority: 10, expanded: false, highlight: false },
      { section: "recent_emails", priority: 7, expanded: false, highlight: false },
      { section: "invoice_aging", priority: 8, expanded: false, highlight: false },
      { section: "import_summary", priority: 11, expanded: false, highlight: false },
      { section: "proposal_tracker", priority: 9, expanded: false, highlight: false },
      { section: "quick_actions", priority: 12, expanded: true, highlight: false },
    ];
  }

  if (state === "needs_attention") {
    return [
      { section: "briefing", priority: 1, expanded: true, highlight: false },
      { section: "kpis", priority: 2, expanded: true, highlight: false },
      {
        section: "proposal_alerts",
        priority: 3,
        expanded: hasProposalAlerts,
        highlight: hasProposalAlerts,
      },
      { section: "hot_items", priority: 4, expanded: true, highlight: false },
      { section: "calendar", priority: 5, expanded: true, highlight: false },
      {
        section: "financial_alerts",
        priority: 6,
        expanded: hasFinancialAlerts,
        highlight: hasFinancialAlerts,
      },
      { section: "analytics", priority: 7, expanded: true, highlight: false },
      { section: "recent_emails", priority: 8, expanded: true, highlight: false },
      { section: "invoice_aging", priority: 9, expanded: true, highlight: false },
      { section: "import_summary", priority: 10, expanded: false, highlight: false },
      { section: "proposal_tracker", priority: 11, expanded: true, highlight: false },
      { section: "quick_actions", priority: 12, expanded: true, highlight: false },
    ];
  }

  // Healthy - emphasize analytics and insights
  return [
    { section: "briefing", priority: 1, expanded: true, highlight: false },
    { section: "kpis", priority: 2, expanded: true, highlight: false },
    { section: "analytics", priority: 3, expanded: true, highlight: true },
    { section: "hot_items", priority: 4, expanded: true, highlight: false },
    { section: "calendar", priority: 5, expanded: true, highlight: false },
    { section: "proposal_tracker", priority: 6, expanded: true, highlight: false },
    { section: "recent_emails", priority: 7, expanded: true, highlight: false },
    { section: "invoice_aging", priority: 8, expanded: true, highlight: false },
    { section: "proposal_alerts", priority: 9, expanded: false, highlight: false },
    { section: "financial_alerts", priority: 10, expanded: false, highlight: false },
    { section: "import_summary", priority: 11, expanded: false, highlight: false },
    { section: "quick_actions", priority: 12, expanded: true, highlight: false },
  ];
}

/**
 * Get section configuration by name.
 */
export function getSectionConfig(
  assessment: HealthAssessment,
  section: DashboardSection
): SectionPriority | undefined {
  return assessment.sectionPriority.find((s) => s.section === section);
}

/**
 * Check if a section should be shown based on current health state.
 */
export function shouldShowSection(
  assessment: HealthAssessment,
  section: DashboardSection
): boolean {
  const config = getSectionConfig(assessment, section);
  if (!config) return true;

  // Always show high-priority sections
  if (config.priority <= 6) return true;

  // For lower priority sections, only show if expanded
  return config.expanded;
}

/**
 * Get the greeting message based on health state.
 */
export function getGreeting(state: HealthState, userName: string): string {
  const hour = new Date().getHours();
  const timeGreeting =
    hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";

  switch (state) {
    case "critical":
      return `${timeGreeting}, ${userName}. Some items need your attention.`;
    case "needs_attention":
      return `${timeGreeting}, ${userName}. A few things to review today.`;
    case "healthy":
      return `${timeGreeting}, ${userName}. Everything is running smoothly.`;
  }
}
