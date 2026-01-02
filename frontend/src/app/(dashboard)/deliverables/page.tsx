'use client'

import { cn } from '@/lib/utils'
import { ds } from '@/lib/design-system'
import { DeliverablesDashboard } from '@/components/dashboard/deliverables-dashboard'

/**
 * Deliverables Page
 *
 * Cross-project view of all deliverables with filtering by:
 * - Status (overdue, pending, in progress, delivered, approved)
 * - PM assignment
 * - Search (name, project code, project name)
 *
 * Issue #313 - PM Dashboard feature
 */
export default function DeliverablesPage() {
  return (
    <div className="space-y-6 w-full max-w-full overflow-x-hidden">
      {/* Header */}
      <div>
        <h1 className={cn(ds.typography.heading1, ds.textColors.primary)}>
          Deliverables
        </h1>
        <p className={cn(ds.typography.body, ds.textColors.secondary, "mt-1")}>
          Track all project deliverables across the organization
        </p>
      </div>

      {/* Dashboard */}
      <DeliverablesDashboard />
    </div>
  )
}
