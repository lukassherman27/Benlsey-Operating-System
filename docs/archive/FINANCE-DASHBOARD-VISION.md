# Finance Dashboard Vision
## Executive Financial Command Center for Bensley Design Studios

> **Bill opens the Finance Dashboard Monday morning. In 10 seconds he knows: total outstanding ($1.2M), cash runway (6.2 months), projects at risk (3), and actions needed (7 payment reminders ready to send).**

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [The Dashboard Bill Needs](#the-dashboard-bill-needs)
3. [Section 1: Executive Summary KPIs](#section-1-executive-summary-kpis)
4. [Section 2: Invoice Aging & Collections](#section-2-invoice-aging--collections)
5. [Section 3: Cash Flow View](#section-3-cash-flow-view)
6. [Section 4: Project Financials](#section-4-project-financials)
7. [Section 5: Work in Progress (WIP)](#section-5-work-in-progress-wip)
8. [Section 6: Alerts & Actions](#section-6-alerts--actions)
9. [Section 7: Standard Reports](#section-7-standard-reports)
10. [Data Sources & Integration](#data-sources--integration)
11. [Implementation Phases](#implementation-phases)
12. [Success Metrics](#success-metrics)

---

## Executive Summary

### The Problem

Bill currently tracks finances across:
- Manual Excel spreadsheets for invoices
- Email threads for payment confirmations
- Memory for which clients are slow payers
- Ad-hoc queries to accounting team for status

**Time Cost:** Answering "what's our cash position?" takes 30-60 minutes of spreadsheet compilation.

**Risk Cost:** Late payments go unnoticed. Overdue invoices aren't followed up. Project profitability is unknown until completion.

### The Solution

A real-time Finance Dashboard that answers Bill's three critical questions instantly:

1. **"Do we have enough money?"** → Cash flow view, runway, trending
2. **"Who owes us money?"** → Invoice aging, overdue amounts, collection priorities
3. **"Are projects profitable?"** → Per-project P&L, margin tracking, WIP status

### Industry Context

Architecture & engineering firms face unique financial challenges:
- **Net profit margins:** Top-quartile firms achieve 20-22% ([Monograph, 2025](https://monograph.com/blog/financial-kpis-architecture-engineering-firms-2025))
- **Days Sales Outstanding (DSO):** Healthy benchmark is 34 days; many firms hit 45-73 days ([Monograph, 2025](https://monograph.com/blog/financial-kpis-architecture-engineering-firms-2025))
- **Utilization rate:** Median for architecture firms is 61% ([Deltek Clarity A&E Study](https://www.deltek.com/en/architecture-and-engineering/architecture-project-management/kpis-for-architects))
- **Work in Progress (WIP):** Critical to track billable work not yet invoiced ([Projul](https://projul.com/blog/work-in-progress-understanding-wip/))

---

## The Dashboard Bill Needs

### Design Principles

1. **10-Second Overview** - Critical numbers visible without scrolling
2. **Click to Drill Down** - Summary numbers link to detailed views
3. **Action-Oriented** - Every alert has a draft action ready
4. **Real-Time** - No manual updates, data refreshes automatically
5. **Mobile-Ready** - Bill can check from anywhere

### Visual Layout (Top-Level View)

```
┌──────────────────────────────────────────────────────────────────────────┐
│  BENSLEY FINANCE DASHBOARD                        As of: Dec 22, 2025   │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐        │
│  │ TOTAL           │  │ OVERDUE         │  │ CASH            │        │
│  │ OUTSTANDING     │  │ INVOICES        │  │ RUNWAY          │        │
│  │                 │  │                 │  │                 │        │
│  │  $1,247,500     │  │   $485,000      │  │  6.2 months     │        │
│  │  ▲ 12% vs Q3    │  │   ⚠️ 5 clients  │  │  ⚠️ -0.8 mo.    │        │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘        │
│                                                                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐        │
│  │ AVG DAYS TO     │  │ NET PROFIT      │  │ UNBILLED        │        │
│  │ PAYMENT         │  │ MARGIN (Q4)     │  │ WIP             │        │
│  │                 │  │                 │  │                 │        │
│  │    52 days      │  │    18.5%        │  │   $892,300      │        │
│  │  ⚠️ +7 vs target│  │  ✅ On target   │  │  ℹ️ 23 projects │        │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘        │
│                                                                          │
├──────────────────────────────────────────────────────────────────────────┤
│  🔴 URGENT ACTIONS (3)                                                   │
│  ├─ BK-045: Invoice $264,600 now 67 days overdue [Draft Ready]          │
│  ├─ BK-033: Payment reminder needed (45 days) [Draft Ready]             │
│  └─ BK-028: Project over budget by 15% - margin at risk                 │
│                                                                          │
│  🟡 ATTENTION THIS WEEK (4)                                              │
│  ├─ 4 invoices approaching 30 days overdue                              │
│  ├─ BK-041: Ready to invoice Phase 3 completion ($125,000)              │
│  └─ Q4 cash flow trending below projection by 8%                        │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  [Invoice Aging Report] [Cash Flow Forecast] [Project P&L] [WIP Report] │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Section 1: Executive Summary KPIs

### The 6 Numbers Bill Sees First

Based on research into architecture firm best practices ([Monograph](https://monograph.com/blog/financial-kpis-architecture-engineering-firms-2025), [Scoro](https://www.scoro.com/blog/architecture-firm-kpis/), [Deltek](https://www.deltek.com/en/architecture-and-engineering/architecture-project-management/kpis-for-architects)), these are the critical KPIs for a design studio owner:

#### 1. Total Outstanding (Accounts Receivable)

**What it shows:** Total amount clients owe across all projects

**Calculation:** Sum of all unpaid invoices

**Display:**
```
┌─────────────────────────┐
│ TOTAL OUTSTANDING       │
│                         │
│   $1,247,500            │
│   ▲ 12% vs last quarter │
│                         │
│   Breakdown:            │
│   • Current: $762,500   │
│   • 30-60 days: $298K   │
│   • 60+ days: $187K     │
└─────────────────────────┘
```

**Click to:** Full invoice aging report

**Benchmark:** Should trend downward as collection processes improve

#### 2. Overdue Invoices

**What it shows:** Money owed past the due date (immediate action needed)

**Calculation:** Invoices where `current_date > due_date`

**Display:**
```
┌─────────────────────────┐
│ OVERDUE INVOICES        │
│                         │
│   $485,000              │
│   ⚠️ 5 clients, 12 inv. │
│                         │
│   Aging:                │
│   • 30-45 days: $210K   │
│   • 45-60 days: $148K   │
│   • 60+ days: $127K     │
└─────────────────────────┘
```

**Click to:** Overdue invoice list with draft payment reminders

**Alert Threshold:** Any invoice >45 days triggers draft reminder

#### 3. Cash Runway

**What it shows:** How many months of operating expenses are covered by cash + expected collections

**Calculation:** `(cash_on_hand + AR_expected_30_days) / average_monthly_expenses`

**Display:**
```
┌─────────────────────────┐
│ CASH RUNWAY             │
│                         │
│   6.2 months            │
│   ⚠️ -0.8 mo. vs Oct    │
│                         │
│   Trend:                │
│   Jul: 7.1  Aug: 6.8    │
│   Sep: 6.9  Oct: 7.0    │
│   Nov: 6.2              │
└─────────────────────────┘
```

**Click to:** Cash flow forecast (next 90 days)

**Alert Threshold:** <6 months triggers warning, <3 months critical

**Why This Matters:** Architecture firms often have lumpy revenue (big invoices arrive sporadically). Cash runway shows true financial health ([CloudZero CFO Dashboard Guide](https://www.cloudzero.com/blog/cfo-dashboards/)).

#### 4. Days Sales Outstanding (DSO)

**What it shows:** Average days from invoice to payment (efficiency of collections)

**Calculation:** `(Total AR / Total Revenue) × Number of Days`

**Display:**
```
┌─────────────────────────┐
│ AVG DAYS TO PAYMENT     │
│                         │
│   52 days               │
│   ⚠️ +7 vs 45-day goal  │
│                         │
│   By Client Tier:       │
│   • Repeat: 38 days     │
│   • New: 61 days        │
│   • International: 73   │
└─────────────────────────┘
```

**Click to:** Payment velocity by client

**Benchmark:** Healthy DSO for A&E firms is 34-40 days ([Monograph, 2025](https://monograph.com/blog/financial-kpis-architecture-engineering-firms-2025))

**Why This Matters:** High DSO = cash tied up in receivables = potential cash flow problems

#### 5. Net Profit Margin (Quarterly)

**What it shows:** How much profit the firm keeps after all expenses

**Calculation:** `(Total Revenue - Total Costs) / Total Revenue × 100`

**Display:**
```
┌─────────────────────────┐
│ NET PROFIT MARGIN (Q4)  │
│                         │
│   18.5%                 │
│   ✅ Target: 18-22%     │
│                         │
│   Quarterly Trend:      │
│   Q1: 16.2%  Q2: 17.8%  │
│   Q3: 19.1%  Q4: 18.5%  │
└─────────────────────────┘
```

**Click to:** Profit & loss breakdown

**Benchmark:** Top-quartile A&E firms achieve 20-22% ([Monograph, 2025](https://monograph.com/blog/financial-kpis-architecture-engineering-firms-2025))

**Why This Matters:** Anything below 10% means overhead is too high or fees are too low

#### 6. Unbilled Work in Progress (WIP)

**What it shows:** Revenue earned but not yet invoiced (work completed, invoice pending)

**Calculation:** Sum of completed milestone fees not yet invoiced

**Display:**
```
┌─────────────────────────┐
│ UNBILLED WIP            │
│                         │
│   $892,300              │
│   ℹ️ 23 active projects │
│                         │
│   Ready to Invoice:     │
│   • Phase complete: 8   │
│   • Milestone hit: 5    │
│   • Overdue: 2 ⚠️       │
└─────────────────────────┘
```

**Click to:** WIP aging report (what can be invoiced now)

**Alert Threshold:** WIP aging >60 days without invoice = revenue leakage

**Why This Matters:** High WIP = doing work without getting paid. Bill needs to send invoices! ([Phoenix Strategy Group](https://www.phoenixstrategy.group/blog/how-cash-flow-dashboards-help-manage-project-revenue))

---

## Section 2: Invoice Aging & Collections

### The Invoice Aging Matrix

Bill needs to see overdue invoices categorized by urgency:

```
┌────────────────────────────────────────────────────────────────────────┐
│  INVOICE AGING REPORT                          Total AR: $1,247,500   │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┬──────────┐ │
│  │ Current  │ 1-30     │ 31-60    │ 61-90    │ 90+      │ Total    │ │
│  │ (0-30)   │ days     │ days     │ days     │ days     │          │ │
│  ├──────────┼──────────┼──────────┼──────────┼──────────┼──────────┤ │
│  │ $762,500 │ $210,000 │ $148,000 │ $87,000  │ $40,000  │$1,247,500│ │
│  │ 61.1%    │ 16.8%    │ 11.9%    │  7.0%    │  3.2%    │  100%    │ │
│  │ ✅       │ ⚠️       │ 🔴       │ 🔴       │ 🚨       │          │ │
│  └──────────┴──────────┴──────────┴──────────┴──────────┴──────────┘ │
│                                                                        │
│  AGED INVOICES BY PROJECT (61+ days overdue)                          │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │ Project       Invoice#   Amount      Days    Status    Action    │ │
│  ├──────────────────────────────────────────────────────────────────┤ │
│  │ BK-045        INV-2024-089                                       │ │
│  │ Le Parque     Phase 3      $264,600   67   🔴 Overdue [Draft]   │ │
│  │                                                                  │ │
│  │ BK-033        INV-2024-103                                       │ │
│  │ Ritz-Carlton  Deposit      $125,000   51   🔴 Overdue [Draft]   │ │
│  │                                                                  │ │
│  │ BK-028        INV-2024-095                                       │ │
│  │ Bali Villa    Phase 2      $87,000    73   🚨 Critical [Draft]  │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│  [View All Invoices] [Export to Excel] [Bulk Send Reminders]          │
└────────────────────────────────────────────────────────────────────────┘
```

### Color Coding System

| Aging Bucket | Status | Action Required | Auto-Action |
|--------------|--------|----------------|-------------|
| **0-30 days** | ✅ Current | None | Track normally |
| **31-45 days** | ⚠️ Attention | Gentle reminder | Draft friendly follow-up |
| **46-60 days** | 🔴 Overdue | Firm reminder | Draft escalation email |
| **61-90 days** | 🔴 Critical | Urgent follow-up | Draft urgent reminder + flag for call |
| **90+ days** | 🚨 Severe | Collection action | Alert Bill + draft collection notice |

### Invoice Concentration Risk

Shows whether receivables are concentrated with a few clients (risk indicator):

```
┌────────────────────────────────────┐
│ RECEIVABLES CONCENTRATION          │
│                                    │
│ Top 5 Clients = 68% of Total AR   │
│ ⚠️ High concentration risk         │
│                                    │
│ 1. Four Seasons Bali:  $285,000   │
│ 2. Ritz-Carlton Maldives: $241K   │
│ 3. Le Parque Ahmedabad: $187K     │
│ 4. Anantara Phuket: $156K         │
│ 5. Private Villa Dubai: $124K     │
└────────────────────────────────────┘
```

**Why This Matters:** If 40% of AR is tied to one client and they have financial trouble, Bensley's cash flow is at risk ([Versapay AR Aging Guide](https://www.versapay.com/resources/ar-aging-reports-how-to-create)).

### Collection Efficiency Metrics

```
┌────────────────────────────────────────────┐
│ COLLECTION PERFORMANCE                     │
│                                            │
│ Collection Ratio (Q4):      96.2%          │
│ ✅ Target: 95-98%                          │
│                                            │
│ Payment Velocity by Client Type:           │
│ • Repeat Clients:    38 days (✅)          │
│ • New Clients:       61 days (⚠️)          │
│ • International:     73 days (🔴)          │
│                                            │
│ Reminder Effectiveness:                    │
│ • 1st reminder response rate: 67%          │
│ • 2nd reminder response rate: 84%          │
│ • 3rd reminder response rate: 92%          │
└────────────────────────────────────────────┘
```

**Why This Matters:** Healthy collection ratio is 95-98%. Below 90% = review client screening ([Digitek Solutions](https://digiteksolutions.com/blog/3-cash-flow-metrics-for-professional-service-organizations/)).

---

## Section 3: Cash Flow View

### Monthly Cash Flow Forecast (90 Days)

Bill needs to see projected cash position to make hiring/spending decisions:

```
┌──────────────────────────────────────────────────────────────────────┐
│  CASH FLOW FORECAST (Next 90 Days)              Updated: Dec 22     │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Starting Cash: $587,000                                             │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │        JAN 2026        │       FEB 2026        │   MAR 2026    │ │
│  ├────────────────────────┼───────────────────────┼───────────────┤ │
│  │ INFLOWS                                                         │ │
│  │ Expected Payments:     │                       │               │ │
│  │  • Current AR: $320K   │  • Current AR: $280K  │  $310K        │ │
│  │  • New invoices: $450K │  • New invoices:$520K │  $480K        │ │
│  │ ─────────────────────  │  ──────────────────   │  ───────────  │ │
│  │ Total In: $770,000     │  Total In: $800,000   │  $790,000     │ │
│  │                        │                       │               │ │
│  │ OUTFLOWS               │                       │               │ │
│  │  • Payroll: $340K      │  • Payroll: $340K     │  $340K        │ │
│  │  • Contractors: $125K  │  • Contractors: $145K │  $135K        │ │
│  │  • Rent/Utils: $45K    │  • Rent/Utils: $45K   │  $45K         │ │
│  │  • Other: $85K         │  • Other: $90K        │  $88K         │ │
│  │ ─────────────────────  │  ──────────────────   │  ───────────  │ │
│  │ Total Out: ($595,000)  │  Total Out: ($620K)   │  ($608K)      │ │
│  │                        │                       │               │ │
│  │ NET CHANGE: +$175,000  │  NET CHANGE: +$180K   │  +$182K       │ │
│  │                        │                       │               │ │
│  │ Ending Cash: $762,000  │  Ending Cash: $942K   │  $1,124K      │ │
│  │ Runway: 6.8 months ✅  │  Runway: 7.2 mo. ✅   │  7.5 mo. ✅   │ │
│  └────────────────────────┴───────────────────────┴───────────────┘ │
│                                                                      │
│  ⚠️ ASSUMPTIONS                                                      │
│  • Expected payment rate based on historical DSO (52 days)           │
│  • New invoices based on scheduled milestone completions             │
│  • If collections slow by 10%, Feb cash drops to $847K (6.4 mo.)    │
│                                                                      │
│  [Adjust Assumptions] [Scenario Planning] [Export Forecast]          │
└──────────────────────────────────────────────────────────────────────┘
```

### Cash Flow Variance (Actual vs. Projected)

```
┌────────────────────────────────────────┐
│ CASH FLOW VARIANCE (Q4 2024)          │
│                                        │
│ Projected Cash In:   $2,450,000       │
│ Actual Cash In:      $2,254,000       │
│ Variance:            -$196,000 (-8%)  │
│ ⚠️ Below projection                   │
│                                        │
│ Key Drivers:                           │
│ • 3 clients paid 20+ days late         │
│ • 2 milestone delays (client hold)     │
│ • 1 disputed invoice ($85K)            │
└────────────────────────────────────────┘
```

**Why This Matters:** Variance >10% means billing schedule or payment terms need attention ([Monograph, 2025](https://monograph.com/blog/financial-kpis-architecture-engineering-firms-2025)).

### Quarterly Revenue & Profit Trends

```
┌──────────────────────────────────────────────────────────────────┐
│  QUARTERLY FINANCIAL PERFORMANCE                                 │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│         Q1 2024    Q2 2024    Q3 2024    Q4 2024    Q1 2025     │
│  Revenue: $742K     $895K     $1.02M     $1.14M     $978K ⚠️   │
│  Profit:  $120K     $159K     $195K      $211K      $181K       │
│  Margin:  16.2%     17.8%     19.1%      18.5%      18.5%       │
│                                                                  │
│  Trend: Revenue dip in Q1 2025 (seasonal). Margin stable.       │
└──────────────────────────────────────────────────────────────────┘
```

---

## Section 4: Project Financials

### Per-Project Profit & Loss View

Bill needs to know which projects are profitable and which are bleeding money:

```
┌────────────────────────────────────────────────────────────────────────┐
│  PROJECT FINANCIAL SUMMARY (Active Projects)                          │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  Sort by: [Margin %] [Outstanding $] [Days Overdue] [Project Code]    │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │ Project    Contract  Invoiced  Paid    Outstanding  Margin  WIP  │ │
│  ├──────────────────────────────────────────────────────────────────┤ │
│  │ BK-045     $850,000  $585,000  $320K   $264,600      18.2%  $85K │ │
│  │ Le Parque           68.8%     37.7%    67d overdue   ✅     ⚠️   │ │
│  │ Phase: DD (75%)                        [Draft Reminder]           │ │
│  │                                                                  │ │
│  │ BK-033     $1.2M     $720,000  $595K   $125,000      21.5%  $195K│ │
│  │ Ritz-C NusaDua      60.0%     49.6%    51d overdue   ✅     ✅   │ │
│  │ Phase: CD (60%)                        [Draft Reminder]           │ │
│  │                                                                  │ │
│  │ BK-028     $485,000  $340,000  $253K   $87,000       9.8%   $42K │ │
│  │ Bali Villa          70.1%     52.2%    73d overdue   🔴     ⚠️   │ │
│  │ Phase: SD (85%)                        [Draft + Call] ⚠️ MARGIN  │ │
│  │                                                                  │ │
│  │ BK-041     $920,000  $545,000  $545K   $0            22.1%  $145K│ │
│  │ Anantara            59.2%     59.2%    Current       ✅     ✅   │ │
│  │ Phase: DD (65%)                        Ready to invoice $125K    │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│  PORTFOLIO SUMMARY                                                     │
│  • Total Contract Value: $38.4M (50 active projects)                  │
│  • Total Invoiced: $22.1M (57.6%)                                     │
│  • Total Outstanding: $1.25M                                          │
│  • Avg Project Margin: 18.9%                                          │
│  • Projects at Risk: 3 (margin <12% or overdue >60 days)              │
│                                                                        │
│  [Export to Excel] [Project Deep Dive] [Margin Analysis]              │
└────────────────────────────────────────────────────────────────────────┘
```

### Project Deep Dive View (Click on any project)

```
┌────────────────────────────────────────────────────────────────────────┐
│  BK-045: Le Parque Ahmedabad Villa                                    │
│  Client: Le Parque Developers  │  Status: Active - Design Development │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  FINANCIAL OVERVIEW                                                    │
│  Contract Value: $850,000                                              │
│  Invoiced to Date: $585,000 (68.8%)                                   │
│  Payments Received: $320,400 (37.7%)                                  │
│  Outstanding AR: $264,600 (67 days overdue) 🔴                        │
│  Remaining to Invoice: $265,000 (31.2%)                               │
│                                                                        │
│  PHASE BREAKDOWN                                                       │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │ Phase          Fee        Invoiced   Paid       Status           │ │
│  ├──────────────────────────────────────────────────────────────────┤ │
│  │ Mobilization   $85,000    $85,000    $85,000    ✅ Complete     │ │
│  │ Schematic      $170,000   $170,000   $170,000   ✅ Complete     │ │
│  │ Conceptual     $255,000   $255,000   $65,400    🔴 $189K due    │ │
│  │ Design Dev     $170,000   $75,000    $0         ⚠️ In progress  │ │
│  │ Construction   $85,000    $0         $0         ⏸️ Pending       │ │
│  │ Admin          $85,000    $0         $0         ⏸️ Pending       │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│  PROFITABILITY ANALYSIS                                                │
│  Direct Costs (hours logged): $425,000                                │
│  Allocated Overhead (35%): $148,750                                   │
│  Total Cost: $573,750                                                 │
│  Gross Profit: $276,250                                               │
│  Margin: 18.2% ✅ (Target: 18-22%)                                    │
│                                                                        │
│  ALERTS & ACTIONS                                                      │
│  🔴 Invoice $264,600 overdue by 67 days                               │
│     [Send Payment Reminder] [Schedule Call] [View Email History]      │
│                                                                        │
│  ✅ Phase 3 (DD) at 75% complete - ready to invoice next $95K         │
│     [Generate Invoice] [Draft Cover Email]                            │
│                                                                        │
│  RECENT ACTIVITY                                                       │
│  • Jan 12: Client meeting (approved facade change)                    │
│  • Jan 8: Email from client (additional bathroom request)             │
│  • Dec 18: Invoice #089 sent ($75,000 for DD progress)               │
│  • Nov 3: Payment received ($180,000)                                 │
│                                                                        │
│  [View All Emails] [View Invoices] [View Meetings] [Edit Project]     │
└────────────────────────────────────────────────────────────────────────┘
```

### Project Margin Analysis

```
┌────────────────────────────────────────────────────────────────┐
│  MARGIN ANALYSIS BY PROJECT TYPE                              │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Project Type      Avg Margin   Projects   Best      Worst    │
│  ───────────────────────────────────────────────────────────  │
│  Luxury Resort       21.3%         12      28.5%     14.2%    │
│  Private Villa       16.8%         18      24.1%     9.8% ⚠️  │
│  Hotel               19.4%         8       23.7%     17.1%    │
│  Restaurant/Bar      22.1%         7       26.3%     18.9%    │
│  Commercial          15.2%         5       19.4%     11.1%    │
│                                                                │
│  INSIGHT: Private villas showing lower margins. Investigate    │
│  scope creep and fee structures for this project type.         │
└────────────────────────────────────────────────────────────────┘
```

**Why This Matters:** Knowing which project types are most profitable helps Bill make strategic decisions about which opportunities to pursue ([Wrike Professional Services Guide](https://www.wrike.com/professional-services-guide/project-profitability/)).

---

## Section 5: Work in Progress (WIP)

### What is WIP?

**Work in Progress (WIP)** is billable work that has been completed but not yet invoiced. It represents revenue earned but not recognized on the books.

**Why It Matters:**
- High WIP = doing work without getting paid (cash flow problem)
- WIP aging shows what should be invoiced immediately
- Critical for architecture firms with milestone-based billing ([Projul WIP Guide](https://projul.com/blog/work-in-progress-understanding-wip/))

### WIP Dashboard View

```
┌────────────────────────────────────────────────────────────────────────┐
│  WORK IN PROGRESS (UNBILLED) REPORT                 Total: $892,300   │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  WIP AGING                                                             │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐            │
│  │ Current  │ 30-60    │ 61-90    │ 90+      │ Total    │            │
│  │ (0-30d)  │ days     │ days     │ days     │          │            │
│  ├──────────┼──────────┼──────────┼──────────┼──────────┤            │
│  │ $542,000 │ $215,000 │ $98,300  │ $37,000  │ $892,300 │            │
│  │ 60.7%    │ 24.1%    │ 11.0%    │  4.1%    │  100%    │            │
│  │ ✅       │ ⚠️       │ 🔴       │ 🚨       │          │            │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘            │
│                                                                        │
│  READY TO INVOICE (Phase Complete / Milestone Hit)                    │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │ Project         Phase          Amount      Days  Action          │ │
│  ├──────────────────────────────────────────────────────────────────┤ │
│  │ BK-041          Phase 3 Done   $125,000    12   [Generate Inv]  │ │
│  │ Anantara Phuket Design Dev     ✅ Complete       [Draft Email]   │ │
│  │                                                                  │ │
│  │ BK-045          DD 75%         $95,000     8    [Generate Inv]  │ │
│  │ Le Parque       Milestone      Eligible          [Draft Email]   │ │
│  │                                                                  │ │
│  │ BK-033          Phase 2 Done   $180,000    45   [Generate Inv]  │ │
│  │ Ritz-Carlton    Conceptual     ⚠️ Overdue        [Draft Email]   │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│  WIP LEAKAGE ALERT                                                     │
│  ⚠️ $135,300 in WIP aged >60 days without invoice                     │
│  • BK-028: $42,000 (85 days) - Phase 80% done but not invoiced       │
│  • BK-019: $56,000 (72 days) - Milestone hit but no invoice          │
│  • BK-007: $37,300 (94 days) - Project completed, final inv pending  │
│                                                                        │
│  ACTION: Review these projects and invoice immediately                │
│                                                                        │
│  [Generate All Invoices] [WIP Aging Detail] [Export Report]           │
└────────────────────────────────────────────────────────────────────────┘
```

### WIP by Project Manager

Shows which PMs are staying on top of billing:

```
┌────────────────────────────────────────────┐
│ WIP BY PROJECT MANAGER                     │
│                                            │
│ PM Name          Total WIP    Avg Age      │
│ ──────────────────────────────────────     │
│ Sarah Chen       $245,000     28 days ✅   │
│ Michael Torres   $387,000     52 days ⚠️   │
│ Lisa Wong        $198,000     31 days ✅   │
│ David Kim        $62,300      67 days 🔴   │
│                                            │
│ INSIGHT: Michael has high WIP aging.       │
│ Review project milestones and billing.     │
└────────────────────────────────────────────┘
```

**Why This Matters:** WIP aging by PM identifies training needs or process bottlenecks ([Haile Solutions WIP Guide](https://hailesolutions.com/work-in-progress-project-management-wip/)).

---

## Section 6: Alerts & Actions

### Alert Priority System

Alerts are organized by urgency with **draft actions ready** for each:

```
┌────────────────────────────────────────────────────────────────────────┐
│  FINANCE ALERTS & ACTIONS                              7 items total  │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  🔴 URGENT - Action Needed Today (3)                                   │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │ 1. BK-045: Invoice $264,600 now 67 days overdue                  │ │
│  │    Last contact: Nov 3 (payment received)                        │ │
│  │    [📧 Draft Payment Reminder Ready] [📞 Schedule Call]          │ │
│  │                                                                  │ │
│  │ 2. BK-033: Payment $125,000 now 51 days overdue                  │ │
│  │    Last contact: Dec 1 (gentle reminder sent)                    │ │
│  │    [📧 Draft Escalation Email Ready] [📞 Schedule Call]          │ │
│  │                                                                  │ │
│  │ 3. BK-028: Project margin at 9.8% (target: 18%+)                 │ │
│  │    Issue: 25 hours over budget on Phase 2                        │ │
│  │    [📊 View Cost Breakdown] [🔔 Alert PM] [📝 Review Scope]     │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│  🟡 ATTENTION - This Week (4)                                          │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │ 4. 4 invoices approaching 30-day overdue threshold               │ │
│  │    Total: $287,000 across BK-041, BK-019, BK-012, BK-007         │ │
│  │    [📧 Draft Gentle Reminders] [📊 View Details]                │ │
│  │                                                                  │ │
│  │ 5. BK-041: Phase 3 complete - ready to invoice $125,000          │ │
│  │    Completion date: Jan 10 (12 days ago)                         │ │
│  │    [📄 Generate Invoice] [📧 Draft Cover Email]                 │ │
│  │                                                                  │ │
│  │ 6. Q1 2025 cash flow trending 8% below projection                │ │
│  │    Cause: 3 milestone delays + slower collections                │ │
│  │    [📊 View Forecast] [📝 Adjust Assumptions]                   │ │
│  │                                                                  │ │
│  │ 7. WIP aging: $135,300 unbilled for >60 days                     │ │
│  │    3 projects with completed work not invoiced                   │ │
│  │    [📊 View WIP Report] [📧 Alert PMs] [📄 Bulk Invoice]        │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│  🟢 GOOD NEWS (Recent Positive Events)                                 │
│  • BK-041: Payment received $180,000 (Jan 20)                         │
│  • BK-052: New contract signed $1.1M (Jan 18)                         │
│  • Q4 2024 margin: 18.5% (on target)                                  │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### Alert Configuration

Bill can customize alert thresholds:

```
┌────────────────────────────────────────────┐
│ ALERT SETTINGS                             │
│                                            │
│ Invoice Overdue Alerts:                    │
│ • Gentle reminder:     30 days             │
│ • Firm reminder:       45 days             │
│ • Urgent follow-up:    60 days             │
│ • Critical/collection: 90 days             │
│                                            │
│ Cash Flow Alerts:                          │
│ • Low runway warning:  <6 months           │
│ • Critical runway:     <3 months           │
│ • Variance alert:      >10% vs projection  │
│                                            │
│ Project Margin Alerts:                     │
│ • Low margin warning:  <15%                │
│ • Critical margin:     <12%                │
│ • Over budget:         >110% hours used    │
│                                            │
│ WIP Alerts:                                │
│ • Ready to invoice:    Milestone complete  │
│ • WIP aging:           >60 days unbilled   │
│ • WIP leakage:         >90 days unbilled   │
│                                            │
│ [Save Settings] [Reset to Defaults]        │
└────────────────────────────────────────────┘
```

### Draft Actions (AI-Generated)

Every alert includes a **draft action** ready for Bill's review:

**Example: Payment Reminder (67 days overdue)**

```
┌────────────────────────────────────────────────────────────────────┐
│  DRAFT PAYMENT REMINDER - BK-045 Le Parque                        │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  To: accounts@leparque.com                                         │
│  Cc: rajesh.sharma@leparque.com                                    │
│  Subject: Payment Reminder - Invoice #089 for Le Parque Villa     │
│                                                                    │
│  ─────────────────────────────────────────────────────────────    │
│                                                                    │
│  Dear Rajesh,                                                      │
│                                                                    │
│  I hope this email finds you well.                                │
│                                                                    │
│  I wanted to follow up on Invoice #089 for $264,600 (Phase 3      │
│  - Design Development) dated November 15, 2024. As of today,      │
│  this invoice is 67 days past the net-30 due date.                │
│                                                                    │
│  We greatly value our partnership on the Le Parque Ahmedabad      │
│  Villa project and would appreciate your assistance in            │
│  processing this payment at your earliest convenience.            │
│                                                                    │
│  If there are any questions regarding this invoice or if there    │
│  is anything we need to address to facilitate payment, please     │
│  don't hesitate to reach out.                                     │
│                                                                    │
│  Invoice Details:                                                  │
│  • Invoice Number: INV-2024-089                                   │
│  • Amount: $264,600                                               │
│  • Invoice Date: November 15, 2024                                │
│  • Due Date: December 15, 2024                                    │
│                                                                    │
│  Thank you for your attention to this matter.                     │
│                                                                    │
│  Best regards,                                                     │
│  Bill Bensley                                                      │
│  Bensley Design Studios                                           │
│                                                                    │
│  ─────────────────────────────────────────────────────────────    │
│                                                                    │
│  AI Generated based on:                                            │
│  • Similar past reminders (67% response rate after 1st reminder)  │
│  • Client payment history (typically pays after 2nd reminder)     │
│  • Relationship type (repeat client, friendly tone)               │
│                                                                    │
│  [Edit Draft] [Approve & Send] [Schedule for Later] [Dismiss]     │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

**The AI learns:** If Bill edits the tone, the system adjusts future drafts for this client.

---

## Section 7: Standard Reports

### Exportable Reports Bill Needs

Architecture firms typically need these standard financial reports ([Coupler.io Financial Dashboard Examples](https://blog.coupler.io/financial-dashboards/)):

#### 1. Accounts Receivable Aging Report

**Frequency:** Weekly

**Format:** Excel export

**Contents:**
- All open invoices organized by aging bucket (0-30, 31-60, 61-90, 90+)
- Total AR by client
- Payment history and trends
- Collection priority ranking

**Use Case:** Board meetings, bank reporting, internal reviews

#### 2. Cash Flow Statement

**Frequency:** Monthly

**Format:** PDF or Excel

**Contents:**
- Operating cash flow (revenue - expenses)
- Investing cash flow (equipment, software)
- Financing cash flow (loans, dividends)
- Net change in cash position
- Beginning and ending cash balances

**Use Case:** Financial planning, investor reporting

#### 3. Project Profitability Report

**Frequency:** Quarterly

**Format:** Excel with pivot tables

**Contents:**
- Revenue by project
- Direct costs by project
- Allocated overhead
- Gross profit and margin %
- Comparison to budget
- Margin trend analysis

**Use Case:** Identifying profitable project types, strategic planning

#### 4. WIP Aging Report

**Frequency:** Monthly (or on-demand)

**Format:** Excel

**Contents:**
- Unbilled work by project
- WIP aging buckets
- Ready-to-invoice items
- Revenue recognition status
- Variance from expected billing schedule

**Use Case:** Revenue forecasting, invoice preparation

#### 5. Collections Performance Report

**Frequency:** Monthly

**Format:** PDF dashboard

**Contents:**
- Days Sales Outstanding (DSO) trend
- Collection ratio
- Overdue invoices by client
- Payment velocity by client type
- Reminder effectiveness metrics

**Use Case:** Evaluating collection processes, identifying problem clients

#### 6. Budget vs. Actual (P&L)

**Frequency:** Monthly

**Format:** Excel

**Contents:**
- Revenue budget vs. actual
- Expense budget vs. actual
- Variance analysis ($ and %)
- Year-to-date comparison
- Forecast to year-end

**Use Case:** Financial control, board meetings

#### 7. Client Payment Analysis

**Frequency:** Quarterly

**Format:** Excel

**Contents:**
- Average days to payment by client
- Total revenue per client (YTD)
- Outstanding AR per client
- Payment history and trends
- Risk scoring (based on payment behavior)

**Use Case:** Client relationship management, credit decisions

---

## Data Sources & Integration

### Where Financial Data Comes From

```
┌────────────────────────────────────────────────────────────────────┐
│  DATA INTEGRATION ARCHITECTURE                                     │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  PRIMARY DATA SOURCES                                              │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                                                             │  │
│  │  1. BENSLEY DATABASE (bensley_master.db)                    │  │
│  │     Tables: projects, invoices, contract_phases,            │  │
│  │             project_fee_breakdown, invoice_aging            │  │
│  │     Status: ✅ Already exists                               │  │
│  │     Freshness: Real-time (manual entry + email parsing)     │  │
│  │                                                             │  │
│  │  2. EMAIL SYNC (lukas@bensley.com)                          │  │
│  │     Source: Gmail API                                       │  │
│  │     Extracts: Payment confirmations, client communications  │  │
│  │     Status: ✅ Active (hourly sync)                         │  │
│  │                                                             │  │
│  │  3. ACCOUNTING SOFTWARE (Future)                            │  │
│  │     Options: QuickBooks, Xero, or manual CSV import         │  │
│  │     Provides: Bank transactions, expense tracking           │  │
│  │     Status: ⏸️ Not yet integrated                           │  │
│  │                                                             │  │
│  │  4. PROJECT MANAGEMENT (Manual Entry + AI Parse)            │  │
│  │     Source: Meeting transcripts, email updates              │  │
│  │     Extracts: Milestone completions, scope changes          │  │
│  │     Status: ⚠️ Partial (needs improvement)                  │  │
│  │                                                             │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  DERIVED METRICS (Calculated by Dashboard)                         │
│  • Days Sales Outstanding = (Total AR / Revenue) × Days           │
│  • Cash Runway = (Cash + AR_30d) / Avg Monthly Expenses           │
│  • Net Profit Margin = (Revenue - Costs) / Revenue × 100          │
│  • WIP Aging = Current Date - Milestone Completion Date           │
│  • Collection Ratio = Payments Received / Invoices Sent           │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### Data Freshness & Accuracy

| Data Type | Update Frequency | Source | Accuracy |
|-----------|------------------|--------|----------|
| **Invoice data** | Real-time (manual entry) | Database | High (human-verified) |
| **Payment received** | Daily (email parsing + manual) | Gmail sync + DB | Medium (needs confirmation) |
| **Project phases** | Weekly (manual + AI parse) | Meetings + emails | Medium (AI suggestions) |
| **Costs (hours)** | Manual entry | Project tracking | Variable (depends on discipline) |
| **Cash position** | Manual entry | Bank statements | High (when entered) |
| **Budget data** | Quarterly | Manual entry | High |

### Integration Roadmap

**Phase 1 (Now - Q1 2026):** Use existing database + email parsing
- No external integrations needed
- Manual entry for invoices, payments, milestones
- AI assists with parsing meeting notes and emails

**Phase 2 (Q2 2026):** Automate payment tracking
- Email parsing for payment confirmations (already built)
- Auto-update `invoices.payment_date` and `payment_amount`
- Reduce manual entry by 60%

**Phase 3 (Q3 2026):** Bank statement integration
- Import bank CSV or connect to bank API
- Auto-reconcile payments to invoices
- True real-time cash position

**Phase 4 (Q4 2026):** Accounting software integration
- Connect to QuickBooks/Xero (if Bensley uses one)
- Bi-directional sync (invoices out, payments in)
- Expense tracking from accounting system

---

## Implementation Phases

### Phase 1: MVP Finance Dashboard (4 weeks)

**Goal:** Bill can see top 6 KPIs and invoice aging instantly

**Deliverables:**
- [ ] Dashboard UI with 6 KPI cards (Section 1)
- [ ] Invoice aging matrix (Section 2)
- [ ] Basic alert system (overdue invoices)
- [ ] Draft payment reminder emails
- [ ] Excel export for aging report

**Data Requirements:**
- `invoices` table (already exists)
- `projects` table (already exists)
- Manual entry: cash position, monthly expenses

**Success Metric:** Bill can answer "what's outstanding?" in <30 seconds

---

### Phase 2: Cash Flow Forecasting (3 weeks)

**Goal:** Bill knows if cash flow is healthy for next 90 days

**Deliverables:**
- [ ] 90-day cash flow forecast (Section 3)
- [ ] Variance tracking (budget vs. actual)
- [ ] Cash runway calculation and trend
- [ ] Scenario planning tool (adjust assumptions)

**Data Requirements:**
- Historical payment data (calculate average DSO)
- Expected milestone dates (from `contract_phases`)
- Monthly expense baseline

**Success Metric:** Cash flow forecast accuracy within 15% of actual

---

### Phase 3: Project Profitability (4 weeks)

**Goal:** Bill knows which projects are profitable and which are bleeding money

**Deliverables:**
- [ ] Per-project P&L view (Section 4)
- [ ] Project margin tracking
- [ ] Project deep dive view
- [ ] Margin analysis by project type
- [ ] Alert for projects <12% margin

**Data Requirements:**
- Direct costs per project (hours logged × rates)
- Overhead allocation methodology
- Phase completion tracking

**Success Metric:** Identify 3+ projects with margin issues in Q1 2026

---

### Phase 4: WIP Management (3 weeks)

**Goal:** No revenue leakage - all completed work gets invoiced promptly

**Deliverables:**
- [ ] WIP dashboard (Section 5)
- [ ] WIP aging report
- [ ] "Ready to invoice" queue
- [ ] Auto-draft invoice cover emails
- [ ] WIP by PM view

**Data Requirements:**
- Milestone completion tracking
- Phase progress percentages
- Last invoice date per project

**Success Metric:** WIP aged >60 days drops to <$50K

---

### Phase 5: Advanced Reporting (2 weeks)

**Goal:** Exportable reports for board meetings, banks, internal reviews

**Deliverables:**
- [ ] All 7 standard reports (Section 7)
- [ ] One-click Excel/PDF export
- [ ] Report scheduling (auto-email weekly/monthly)
- [ ] Historical report archive

**Success Metric:** Weekly AR aging report auto-generated and emailed

---

## Success Metrics

### Primary Success Metrics

| Metric | Current State | Target (Q2 2026) | How Measured |
|--------|---------------|------------------|--------------|
| **Time to answer "what's outstanding?"** | 30-60 min | <30 seconds | Dashboard load time |
| **Overdue invoice follow-up rate** | Unknown (things slip) | 100% within 5 days | Alert response logs |
| **Days Sales Outstanding (DSO)** | Unknown | <45 days | Calculated from AR/revenue |
| **WIP aged >60 days** | Unknown | <$50,000 | WIP aging report |
| **Collection ratio** | Unknown | >95% | Payments received / invoiced |
| **Project margin visibility** | Unknown until project ends | Real-time for all active | Dashboard query frequency |

### Secondary Success Metrics

| Metric | What It Tells Us |
|--------|------------------|
| **Draft approval rate** | Are payment reminders effective? (Target: >80% approved) |
| **Cash flow forecast accuracy** | Is forecasting model reliable? (Target: ±15%) |
| **Projects flagged for margin risk** | Are we catching problems early? (Target: 100% of <12% margin projects) |
| **Invoice generation time** | How fast can Bill create invoices? (Target: <10 min per invoice) |
| **Report export frequency** | Is Bill using reports for decision-making? (Target: weekly AR aging) |

### North Star Metric

**Bill's Monday Morning Finance Review:**
1. Open Finance Dashboard: 10 seconds
2. Review KPIs and alerts: 3 minutes
3. Approve/send payment reminders: 2 minutes
4. Check cash flow forecast: 1 minute
5. Review flagged projects: 2 minutes
6. **Total time: <8 minutes** (vs. current 60+ minutes)

**ROI Calculation:**
- Time saved per week: ~4 hours
- Time saved per year: ~200 hours
- Value of Bill's time: $300/hour (conservative)
- **Annual value: $60,000** in reclaimed executive time

---

## Appendix: Visual Mockups

### Mobile View (For Bill on the Go)

```
┌─────────────────────────┐
│  BENSLEY FINANCE        │
│  Dec 22, 2025           │
├─────────────────────────┤
│                         │
│  💰 OUTSTANDING         │
│  $1,247,500             │
│  ▲ 12% vs Q3            │
│                         │
│  ⚠️ OVERDUE             │
│  $485,000 (5 clients)   │
│                         │
│  📊 CASH RUNWAY         │
│  6.2 months             │
│  ⚠️ -0.8 mo. vs Oct     │
│                         │
├─────────────────────────┤
│  🔴 URGENT (3)          │
│                         │
│  BK-045: $264K overdue  │
│  67 days                │
│  [Reminder Ready]       │
│                         │
│  BK-033: $125K overdue  │
│  51 days                │
│  [Reminder Ready]       │
│                         │
│  BK-028: Margin 9.8%    │
│  Below target           │
│  [Review Project]       │
│                         │
├─────────────────────────┤
│  [Full Dashboard]       │
│  [Invoices] [Projects]  │
│  [Reports] [Settings]   │
└─────────────────────────┘
```

---

## Conclusion

This Finance Dashboard transforms Bill's financial management from **reactive spreadsheet hunting** to **proactive executive command**.

**Key Benefits:**
1. **Instant Visibility** - Critical numbers at a glance
2. **Proactive Alerts** - Problems flagged before they become crises
3. **Action-Ready** - Draft payment reminders, invoices, and reports ready for approval
4. **Strategic Insight** - Know which project types are most profitable
5. **Cash Flow Confidence** - 90-day forecast shows if runway is safe

**The Decision Bill Can Make:**

> "I know exactly where we stand financially. I know which clients to call today. I know which projects need attention. I can make hiring and spending decisions with confidence because I see our true cash position and 90-day forecast."

**Next Steps:**
1. Review this vision with Bill and finance team
2. Prioritize features (start with Phase 1 MVP)
3. Define data entry workflows (who enters what, when)
4. Build dashboard incrementally (ship Phase 1 in 4 weeks)
5. Iterate based on Bill's usage and feedback

---

**Sources:**
- [12 Financial KPIs A&E Firm Leaders Must Track in 2025 - Monograph](https://monograph.com/blog/financial-kpis-architecture-engineering-firms-2025)
- [20 Key CFO Dashboards And KPIs: What Matters Most In 2025 - CloudZero](https://www.cloudzero.com/blog/cfo-dashboards/)
- [11 Architecture Firm KPIs You Need to Track - Scoro](https://www.scoro.com/blog/architecture-firm-kpis/)
- [8 Key Performance Indicators for Architecture Firms - Deltek](https://www.deltek.com/en/architecture-and-engineering/architecture-project-management/kpis-for-architects)
- [How Cash Flow Dashboards Help Manage Project Revenue - Phoenix Strategy Group](https://www.phoenixstrategy.group/blog/how-cash-flow-dashboards-help-manage-project-revenue)
- [Accounts Receivable Aging Report Guide - Versapay](https://www.versapay.com/resources/ar-aging-reports-how-to-create)
- [3 Cash Flow Metrics for Professional Service Organizations - Digitek Solutions](https://digiteksolutions.com/blog/3-cash-flow-metrics-for-professional-service-organizations/)
- [Work in Progress - Understanding WIP - Projul](https://projul.com/blog/work-in-progress-understanding-wip/)
- [Measuring Project Profitability for Professional Services - Wrike](https://www.wrike.com/professional-services-guide/project-profitability/)
- [Understanding Work in Progress in Project Management - Haile Solutions](https://hailesolutions.com/work-in-progress-project-management-wip/)
- [Top 26 Financial Dashboard Examples - Coupler.io](https://blog.coupler.io/financial-dashboards/)
