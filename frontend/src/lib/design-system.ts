/**
 * BENSLEY DESIGN SYSTEM
 * Single Source of Truth for UI consistency
 *
 * PHILOSOPHY: 80% grayscale foundation + 20% purposeful color accents
 * If you can't explain WHY a color is there, it should be grayscale.
 */

// =============================================================================
// FOUNDATION COLORS (Black & White - 80% of UI)
// =============================================================================
export const baseColors = {
  black: '#0A0A0A',         // Primary text, headers, emphasis
  charcoal: '#1A1A1A',      // Secondary text, body content
  graphite: '#333333',      // Tertiary elements
  silver: '#666666',        // Muted text, captions
  platinum: '#999999',      // Disabled, placeholders
  pearl: '#E5E5E5',         // Borders, dividers
  snow: '#F5F5F5',          // Subtle backgrounds, hover states
  white: '#FFFFFF',         // Cards, main background
} as const;

// =============================================================================
// ACCENT COLORS (Purposeful Color Pops - 20% of UI)
// Color = Information. These ONLY appear when they MEAN something.
// =============================================================================
export const accentColors = {
  // Primary Action - Deep Teal (sophisticated, not boring blue)
  primary: {
    DEFAULT: '#0D9488',       // teal-600: Primary buttons, links, focus rings
    hover: '#0F766E',         // teal-700: Hover state
    light: '#F0FDFA',         // teal-50: Light backgrounds
    ring: '#14B8A6',          // teal-500: Focus rings
  },

  // Status Colors - MUST have meaning
  success: {
    DEFAULT: '#059669',       // emerald-600: Paid, complete, healthy
    light: '#ECFDF5',         // emerald-50: Background
    text: '#047857',          // emerald-700: Text on light bg
  },
  warning: {
    DEFAULT: '#D97706',       // amber-600: Needs attention, 30-60 days
    light: '#FFFBEB',         // amber-50: Background
    text: '#B45309',          // amber-700: Text on light bg
  },
  danger: {
    DEFAULT: '#DC2626',       // red-600: Overdue, critical, error
    light: '#FEF2F2',         // red-50: Background
    text: '#B91C1C',          // red-700: Text on light bg
  },
  info: {
    DEFAULT: '#2563EB',       // blue-600: Informational, neutral status
    light: '#EFF6FF',         // blue-50: Background
    text: '#1D4ED8',          // blue-700: Text on light bg
  },
} as const;

// =============================================================================
// CHART COLORS (Consistent across all charts)
// =============================================================================
export const chartColors = {
  primary: '#3B82F6',       // blue-500: Primary metric
  success: '#22C55E',       // green-500: Positive/Paid
  warning: '#F59E0B',       // amber-500: Warning/Aging
  danger: '#EF4444',        // red-500: Danger/Overdue
  neutral: '#94A3B8',       // slate-400: Neutral/Other
} as const;

// =============================================================================
// DESIGN SYSTEM TOKENS (Tailwind Classes)
// =============================================================================
export const designSystem = {
  // Border Radius Scale
  borderRadius: {
    card: 'rounded-xl',       // 12px - Modern but not playful
    cardLarge: 'rounded-2xl', // 16px - Large cards and containers
    button: 'rounded-lg',     // 8px - Buttons
    input: 'rounded-lg',      // 8px - Inputs
    badge: 'rounded-md',      // 6px - Status badges (NOT pill-shaped for data)
    badgePill: 'rounded-full', // Only for decorative badges
    small: 'rounded-md',
  },

  // Spacing Scale
  spacing: {
    xs: 'p-1',         // 4px - Between icon and text
    sm: 'p-2',         // 8px - Inside buttons, badges
    md: 'p-4',         // 16px - Card padding, between elements
    lg: 'p-6',         // 24px - Between sections (standard card padding)
    xl: 'p-8',         // 32px - Page sections
    compact: 'p-3',
    normal: 'p-4',
    spacious: 'p-6',
    extraSpacious: 'p-8',
  },

  // Gap Scale
  gap: {
    tight: 'gap-2',
    normal: 'gap-3',
    relaxed: 'gap-4',
    loose: 'gap-6',
  },

  // Typography Scale
  typography: {
    // Page structure
    pageTitle: 'text-3xl font-bold text-slate-900',
    sectionHeader: 'text-2xl font-semibold text-slate-900',
    cardHeader: 'text-xl font-semibold text-slate-900',

    // Content
    heading1: 'text-3xl font-bold',
    heading2: 'text-2xl font-semibold',
    heading3: 'text-xl font-semibold',
    body: 'text-base font-normal',
    bodyBold: 'text-base font-semibold',
    bodySmall: 'text-sm text-slate-600',
    caption: 'text-sm text-slate-500',
    captionBold: 'text-sm font-semibold',

    // Special
    label: 'text-xs font-medium uppercase tracking-wide text-slate-500',
    labelWide: 'text-xs font-medium uppercase tracking-[0.3em] text-slate-400',
    metric: 'text-2xl font-bold tabular-nums',
    metricLarge: 'text-3xl font-bold tabular-nums',
    metricLabel: 'text-sm font-medium text-slate-500',
    metricValue: 'text-lg md:text-xl lg:text-2xl font-semibold',
    tiny: 'text-xs font-normal',
  },

  // Color Hierarchy for Text
  textColors: {
    primary: 'text-slate-900',      // Main headings, important text
    secondary: 'text-slate-600',    // Body text, descriptions
    tertiary: 'text-slate-500',     // Supporting text, captions
    muted: 'text-slate-400',        // Labels, placeholders
    inverse: 'text-white',
  },

  // Shadow Scale
  shadows: {
    sm: 'shadow-sm',         // Subtle depth
    md: 'shadow-md',         // Medium elevation
    lg: 'shadow-lg',         // High elevation (modals, dropdowns)
    none: 'shadow-none',
  },

  // Transition Patterns
  transitions: {
    base: 'transition-colors duration-200',
    all: 'transition-all duration-200',
    shadow: 'transition-shadow duration-200',
  },

  // Hover States (Consistent across all interactive elements)
  hover: {
    card: 'hover:bg-slate-50 hover:shadow-sm transition-all duration-200',
    button: 'hover:bg-slate-100 transition-colors duration-200',
    subtle: 'hover:bg-slate-50 transition-colors duration-200',
    row: 'hover:bg-snow transition-colors duration-150',
  },

  // Active States (Pressed feedback)
  active: {
    scale: 'active:scale-[0.98] active:shadow-sm',
    button: 'active:scale-[0.98]',
  },

  // Focus States (Accessibility)
  focus: {
    ring: 'focus-visible:ring-2 focus-visible:ring-teal-500 focus-visible:ring-offset-2 focus-visible:outline-none',
  },

  // Status Colors (Semantic - Tailwind classes)
  status: {
    success: {
      bg: 'bg-emerald-50',
      border: 'border-emerald-200',
      text: 'text-emerald-700',
      icon: 'text-emerald-600',
    },
    warning: {
      bg: 'bg-amber-50',
      border: 'border-amber-200',
      text: 'text-amber-700',
      icon: 'text-amber-600',
    },
    danger: {
      bg: 'bg-red-50',
      border: 'border-red-200',
      text: 'text-red-700',
      icon: 'text-red-600',
    },
    info: {
      bg: 'bg-blue-50',
      border: 'border-blue-200',
      text: 'text-blue-700',
      icon: 'text-blue-600',
    },
    neutral: {
      bg: 'bg-slate-50',
      border: 'border-slate-200',
      text: 'text-slate-700',
      icon: 'text-slate-600',
    },
  },

  // Card Styles
  cards: {
    default: 'bg-white border border-slate-200 rounded-xl shadow-sm',
    elevated: 'bg-white border border-slate-200 rounded-xl shadow-md',
    interactive: 'bg-white border border-slate-200 rounded-xl shadow-sm hover:shadow-md hover:border-slate-300 transition-all duration-200 cursor-pointer',
  },

  // Table Styles
  tables: {
    header: 'bg-slate-50 text-xs font-semibold uppercase tracking-wider text-slate-500',
    headerCell: 'px-4 py-3 text-left',
    headerCellRight: 'px-4 py-3 text-right',
    row: 'hover:bg-slate-50 transition-colors duration-150',
    cell: 'px-4 py-4 text-sm text-slate-900',
    cellMuted: 'px-4 py-4 text-sm text-slate-500',
    cellNumber: 'px-4 py-4 text-sm text-slate-900 text-right font-mono tabular-nums',
    divider: 'divide-y divide-slate-100',
  },

  // Button Variants
  buttons: {
    primary: 'bg-teal-600 text-white hover:bg-teal-700 rounded-lg px-4 py-2 font-medium transition-colors',
    secondary: 'bg-slate-50 text-slate-700 hover:bg-slate-100 border border-slate-200 rounded-lg px-4 py-2 font-medium transition-colors',
    ghost: 'text-slate-700 hover:text-slate-900 hover:bg-slate-50 rounded-lg px-4 py-2 font-medium transition-colors',
    danger: 'bg-white text-red-600 border border-red-200 hover:bg-red-50 rounded-lg px-4 py-2 font-medium transition-colors',
    disabled: 'bg-slate-50 text-slate-400 cursor-not-allowed rounded-lg px-4 py-2 font-medium',
  },

  // Badge Variants (Status indicators - THE place for color)
  badges: {
    default: 'bg-slate-50 text-slate-700 text-xs font-medium px-2.5 py-0.5 rounded-md border border-slate-200',
    success: 'bg-emerald-50 text-emerald-700 text-xs font-medium px-2.5 py-0.5 rounded-md border border-emerald-200',
    warning: 'bg-amber-50 text-amber-700 text-xs font-medium px-2.5 py-0.5 rounded-md border border-amber-200',
    danger: 'bg-red-50 text-red-700 text-xs font-medium px-2.5 py-0.5 rounded-md border border-red-200',
    info: 'bg-blue-50 text-blue-700 text-xs font-medium px-2.5 py-0.5 rounded-md border border-blue-200',
    neutral: 'bg-slate-50 text-slate-700 text-xs font-medium px-2.5 py-0.5 rounded-md border border-slate-200',
  },

  // Input Styles
  inputs: {
    default: 'bg-white border border-slate-200 text-slate-900 rounded-lg px-3 py-2 placeholder:text-slate-400 focus:ring-2 focus:ring-teal-500 focus:ring-opacity-50 focus:border-teal-500 transition-colors',
    error: 'bg-white border border-red-500 text-slate-900 rounded-lg px-3 py-2 ring-2 ring-red-500 ring-opacity-50',
  },

  // Navigation
  navigation: {
    inactive: 'text-slate-500 hover:text-slate-900 hover:bg-slate-50 rounded-lg px-3 py-2 transition-colors',
    active: 'text-slate-900 font-medium bg-slate-50 border-l-2 border-slate-900 rounded-lg px-3 py-2',
    activeTab: 'text-slate-900 font-medium border-b-2 border-slate-900 pb-2',
  },
} as const;

// =============================================================================
// BENSLEY VOICE & COPY
// Tone: Confident, witty, slightly irreverent. Like Bill at a cocktail party.
// =============================================================================
export const bensleyVoice = {
  // Empty States (where personality shines)
  emptyStates: {
    proposals: "The pipeline's looking thirsty. Time to make some calls?",
    suggestions: "All caught up! The AI is having a tea break.",
    emails: "Every email has a home. Impressive.",
    invoices: "Nothing overdue. Someone's been doing their job.",
    search: "Couldn't find that. Try different words, or blame the intern.",
    projects: "Suspiciously quiet. Is everyone on holiday?",
    default: "Nothing here yet. But give it time.",
  },

  // Loading Messages (rotate randomly)
  loadingMessages: [
    "Waking up the elephants...",
    "Consulting the design gods...",
    "Gathering intelligence...",
    "One moment, we're being thorough...",
    "Almost there, perfection takes time...",
    "Crunching the numbers...",
    "Fetching the good stuff...",
  ],

  // Success Toasts
  successMessages: {
    saved: "Saved. The cloud remembers everything.",
    emailLinked: "Connection made. The dots are connecting themselves.",
    suggestionApproved: "Approved! The AI is learning.",
    proposalCreated: "New opportunity logged. May the odds be ever in your favor.",
    invoicePaid: "Cha-ching! Another one bites the dust.",
    default: "Done! That was easy.",
  },

  // Error Messages (still helpful, slightly cheeky)
  errorMessages: {
    network: "The internet gremlins are at it again. Check your connection.",
    notFound: "This page has wandered off. Like a good design, it'll turn up somewhere unexpected.",
    server: "Something broke. Our fault, not yours. Try again?",
    timeout: "That took too long. The server's probably napping.",
    default: "Oops. Something went wrong. Try again?",
  },

  // Section Headers (optional flair)
  sectionHeaders: {
    dashboard: "Command Center",
    proposals: "The Pipeline",
    projects: "In the Wild",
    overdue: "The Naughty List",
    suggestions: "The Brain's Ideas",
    analytics: "The Numbers",
    finance: "Follow the Money",
  },

  // Tooltips
  tooltips: {
    healthScore: "How likely this proposal is to close. Higher = happier.",
    daysSinceContact: "Time flies when you're not following up.",
    aiConfidence: "How sure the robot is. Take with appropriate salt.",
    linkedEmails: "Emails we've matched to this project. Magic, basically.",
  },
} as const;

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

// Get loading message (static to avoid SSR hydration mismatch)
export function getLoadingMessage(): string {
  // Using static message - Math.random() causes server/client mismatch
  return bensleyVoice.loadingMessages[0];
}

// Get status badge class based on status
export function getStatusBadgeClass(status: 'success' | 'warning' | 'danger' | 'info' | 'neutral'): string {
  return designSystem.badges[status] || designSystem.badges.default;
}

// Get aging color based on days
export function getAgingColor(days: number): { bg: string; text: string; label: string } {
  if (days <= 30) return { bg: 'bg-slate-50', text: 'text-slate-700', label: 'Current' };
  if (days <= 60) return { bg: 'bg-amber-50', text: 'text-amber-700', label: 'Aging' };
  if (days <= 90) return { bg: 'bg-orange-50', text: 'text-orange-700', label: 'Overdue' };
  return { bg: 'bg-red-50', text: 'text-red-700', label: 'Critical' };
}

// Get activity color based on days since last activity
export function getActivityColor(days: number): { bg: string; text: string; label: string } {
  if (days <= 7) return { bg: 'bg-emerald-50', text: 'text-emerald-700', label: 'Active' };
  if (days <= 14) return { bg: 'bg-amber-50', text: 'text-amber-700', label: 'Needs attention' };
  return { bg: 'bg-red-50', text: 'text-red-700', label: 'Stalled' };
}

// =============================================================================
// PROPOSAL STATUS COLORS (Single source of truth)
// =============================================================================
export const proposalStatusColors: Record<string, { bg: string; fill: string; text: string }> = {
  "First Contact": { bg: "bg-blue-50", fill: "bg-blue-400", text: "text-blue-700" },
  "Meeting Held": { bg: "bg-sky-50", fill: "bg-sky-400", text: "text-sky-700" },
  "NDA Signed": { bg: "bg-indigo-50", fill: "bg-indigo-400", text: "text-indigo-700" },
  "Proposal Prep": { bg: "bg-yellow-50", fill: "bg-yellow-500", text: "text-yellow-700" },
  "Proposal Sent": { bg: "bg-amber-50", fill: "bg-amber-500", text: "text-amber-700" },
  "Negotiation": { bg: "bg-purple-50", fill: "bg-purple-500", text: "text-purple-700" },
  "MOU Signed": { bg: "bg-teal-50", fill: "bg-teal-500", text: "text-teal-700" },
  "On Hold": { bg: "bg-gray-100", fill: "bg-gray-400", text: "text-gray-600" },
  "Contract Signed": { bg: "bg-emerald-50", fill: "bg-emerald-500", text: "text-emerald-700" },
  "Lost": { bg: "bg-red-50", fill: "bg-red-400", text: "text-red-600" },
  "Declined": { bg: "bg-rose-50", fill: "bg-rose-400", text: "text-rose-600" },
  "Dormant": { bg: "bg-slate-100", fill: "bg-slate-400", text: "text-slate-500" },
};

// All valid proposal statuses (workflow order)
export const ALL_PROPOSAL_STATUSES = [
  "First Contact",
  "Meeting Held",
  "NDA Signed",
  "Proposal Prep",
  "Proposal Sent",
  "Negotiation",
  "MOU Signed",
  "On Hold",
  "Contract Signed",
  "Lost",
  "Declined",
  "Dormant",
] as const;

export type ProposalStatusType = typeof ALL_PROPOSAL_STATUSES[number];

// =============================================================================
// EXPORTS
// =============================================================================

// Shorthand export for convenience
export const ds = designSystem;

// Export individual color palettes
export const colors = {
  base: baseColors,
  accent: accentColors,
  chart: chartColors,
} as const;
