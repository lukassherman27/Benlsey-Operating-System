'use client'

import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Users, ArrowRight, FolderOpen, Mail } from 'lucide-react'
import { cn } from '@/lib/utils'
import { ds } from '@/lib/design-system'
import Link from 'next/link'

/**
 * Contacts Page
 *
 * Redirects users to view contacts at the project level.
 * Contacts are derived from email communication and project assignments,
 * so they make more sense in the context of a specific project.
 *
 * Fix for #240 - Page was showing raw contact data with quality issues
 * (MIME-encoded strings, garbage data from email parsing).
 */
export default function ContactsPage() {
  return (
    <div className="space-y-6 w-full max-w-full overflow-x-hidden">
      {/* Header */}
      <div>
        <h1 className={cn(ds.typography.heading1, ds.textColors.primary)}>
          Contacts
        </h1>
        <p className={cn(ds.typography.body, ds.textColors.secondary, "mt-1")}>
          People connected to your projects
        </p>
      </div>

      {/* Redirect Card */}
      <Card className={cn(ds.borderRadius.card, "border-slate-200")}>
        <CardContent className="py-16 text-center">
          <div className="mx-auto w-20 h-20 rounded-full bg-teal-50 flex items-center justify-center mb-6">
            <Users className="h-10 w-10 text-teal-600" />
          </div>

          <h2 className={cn(ds.typography.heading2, ds.textColors.primary, "mb-3")}>
            Contacts are shown per project
          </h2>

          <p className={cn(ds.typography.body, ds.textColors.secondary, "max-w-lg mx-auto mb-8")}>
            Contacts are derived from email communications and project assignments.
            Open a project to see everyone involved - clients, collaborators, and team members.
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
              Where to find contacts
            </h3>
            <div className="flex flex-col items-center gap-2 text-sm text-slate-600">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-teal-100 text-teal-700 flex items-center justify-center text-xs font-bold">1</span>
                <span>Open a project from the Projects page</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-teal-100 text-teal-700 flex items-center justify-center text-xs font-bold">2</span>
                <span>View the Team or Contacts section</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-teal-100 text-teal-700 flex items-center justify-center text-xs font-bold">3</span>
                <span>See everyone who has communicated about that project</span>
              </div>
            </div>
          </div>

          <div className="mt-8 p-4 bg-blue-50 rounded-lg border border-blue-200 max-w-md mx-auto">
            <div className="flex items-center gap-2 text-blue-700">
              <Mail className="h-5 w-5" />
              <span className={ds.typography.bodyBold}>Tip</span>
            </div>
            <p className="text-sm text-blue-600 mt-1">
              Contacts are automatically discovered from email communications
              and linked to projects by the learning system.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
