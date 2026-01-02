# Dashboard Improvements Plan

## Issue: #293 - Dashboard UI Improvements for Bill's Monday View

## Research Summary

**Dashboard best practices for executive views:**
1. Show most critical metrics at a glance (top of page)
2. Group related information together
3. Use color to indicate status (red=danger, amber=warning, green=good)
4. Keep loading states visible to avoid "stuck" feeling
5. Provide quick actions from the dashboard

## Current State Analysis

The dashboard currently has:
- Key metrics strip (Pipeline, Stale, Overdue, Projects)
- Proposals needing action (stale >14 days)
- Money owed widget
- Calendar widget
- Projects with issues
- Quick links

## What's Missing (Requirements)

1. **Proposals by status breakdown** - Bill needs to see at a glance how many proposals are in each stage
2. **Recently sent proposals** - What went out in the last 7 days
3. **Invoice aging buckets** - 30/60/90+ day aging categories
4. **Loading states** - Ensure they don't get stuck

## Approach

### Adding Status Breakdown
- Add a compact visual showing counts per status (First Contact, Proposal Sent, Negotiation, etc.)
- Use badges with colors matching the status
- Place in the left column near proposals

### Adding Recently Sent Section
- Query proposals where `proposal_sent_date` is within last 7 days
- Show as a simple list with project name and sent date
- Place below or as tab in proposals section

### Invoice Aging Improvement
- API already returns `aging_breakdown` with under_30, 30_to_90, over_90
- Display as a visual bar or pill breakdown showing amounts
- Make the warning level increase with age

## What I'm NOT Doing
- Not changing the overall layout (works well)
- Not adding new API endpoints (using existing data)
- Not adding charts/visualizations (keep it simple for Bill)

## Execution

1. Update imports and queries
2. Add status breakdown widget
3. Add recently sent section
4. Improve invoice aging display
5. Test loading states
6. Commit and create PR
