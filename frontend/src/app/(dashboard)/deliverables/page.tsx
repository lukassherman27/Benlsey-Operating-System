'use client'

import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Package, ArrowRight, FolderOpen } from 'lucide-react'
import { cn } from '@/lib/utils'
import { ds } from '@/lib/design-system'
import Link from 'next/link'

/**
 * Deliverables Page
 *
 * Redirects users to manage deliverables at the project level.
 * Deliverables are project-specific, not standalone entities.
 *
 * Fix for #239 - Page was showing confusing PM Workload data
 * when deliverables table is empty.
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
          Track project deliverables by phase
        </p>
      </div>

      {/* Redirect Card */}
      <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
        <CardContent className="py-16 text-center">
          <div className="mx-auto w-20 h-20 rounded-full bg-teal-50 flex items-center justify-center mb-6">
            <Package className="h-10 w-10 text-teal-600" />
          </div>

          <h2 className={cn(ds.typography.heading2, ds.textColors.primary, "mb-3")}>
            Deliverables are managed per project
          </h2>

          <p className={cn(ds.typography.body, ds.textColors.secondary, "max-w-lg mx-auto mb-8")}>
            Deliverables like drawings, presentations, and reports belong to specific projects.
            Open a project to view, add, and track its deliverables.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button asChild size="lg" className="bg-teal-600 hover:bg-teal-700 text-white">
              <Link href="/projects">
                <FolderOpen className="h-5 w-5 mr-2" />
                Go to Projects
                <ArrowRight className="h-4 w-4 ml-2" />
              </Link>
            </Button>
          </div>

          <div className="mt-8 pt-8 border-t border-slate-100">
            <h3 className={cn(ds.typography.bodyBold, ds.textColors.primary, "mb-3")}>
              Where to find deliverables
            </h3>
            <div className="flex flex-col items-center gap-2 text-sm text-slate-600">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-teal-100 text-teal-700 flex items-center justify-center text-xs font-bold">1</span>
                <span>Open a project from the Projects page</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-teal-100 text-teal-700 flex items-center justify-center text-xs font-bold">2</span>
                <span>Click the Deliverables tab</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-teal-100 text-teal-700 flex items-center justify-center text-xs font-bold">3</span>
                <span>Add and track deliverables for that project</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
