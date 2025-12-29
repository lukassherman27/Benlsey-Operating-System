"use client"

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Search } from 'lucide-react'
import { useCurrentUser } from "@/hooks/useCurrentUser"

interface EmailLinkDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  emailId: number | null
  onSuccess?: () => void
}

export function EmailLinkDialog({ open, onOpenChange, emailId, onSuccess }: EmailLinkDialogProps) {
  const [selectedProject, setSelectedProject] = useState('')
  const [reason, setReason] = useState('')
  const [searchQuery, setSearchQuery] = useState('')

  const queryClient = useQueryClient()
  const { email: currentUserEmail } = useCurrentUser()

  // Get all projects
  const { data: projectsData, isLoading: loadingProjects } = useQuery({
    queryKey: ['projects-linking-list'],
    queryFn: () => api.getProjectsForLinking(500),
    enabled: open
  })

  const projects = projectsData?.projects || []

  // Filter projects by search query
  const filteredProjects = projects.filter(project => {
    if (!searchQuery) return true
    const query = searchQuery.toLowerCase()
    return (
      project.code?.toLowerCase().includes(query) ||
      project.name?.toLowerCase().includes(query)
    )
  })

  // Update link mutation
  const updateLink = useMutation({
    mutationFn: ({ emailId, projectCode, reason }: { emailId: number; projectCode: string; reason: string }) =>
      api.updateEmailLink(emailId, {
        project_code: projectCode,
        reason,
        updated_by: currentUserEmail || 'user'
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['email-validation-queue'] })
      queryClient.invalidateQueries({ queryKey: ['email-details'] })
      onOpenChange(false)
      setSelectedProject('')
      setReason('')
      setSearchQuery('')
      onSuccess?.()
    }
  })

  const handleSubmit = () => {
    if (!selectedProject || !reason || !emailId) {
      return
    }

    updateLink.mutate({
      emailId,
      projectCode: selectedProject,
      reason
    })
  }

  const handleClose = () => {
    onOpenChange(false)
    setSelectedProject('')
    setReason('')
    setSearchQuery('')
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-lg max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle>Link Email to Project</DialogTitle>
          <DialogDescription>
            Select the correct project for this email. Your correction trains the AI!
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 flex-1 overflow-hidden flex flex-col">
          {/* Search Projects */}
          <div>
            <Label htmlFor="project-search">Search Projects</Label>
            <div className="relative mt-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                id="project-search"
                placeholder="Search by code or name..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>
          </div>

          {/* Project List */}
          <div className="flex-1 overflow-hidden">
            <Label>Select Project</Label>
            <div className="border rounded-md mt-1 max-h-[200px] overflow-y-auto">
              {loadingProjects ? (
                <div className="p-4 text-center text-muted-foreground">
                  Loading projects...
                </div>
              ) : filteredProjects.length === 0 ? (
                <div className="p-4 text-center text-muted-foreground">
                  No projects found
                </div>
              ) : (
                filteredProjects.slice(0, 50).map((project) => (
                  <button
                    key={project.code}
                    onClick={() => setSelectedProject(project.code)}
                    className={`w-full p-3 text-left border-b last:border-b-0 transition-colors ${
                      selectedProject === project.code
                        ? 'bg-blue-50 border-blue-200'
                        : 'hover:bg-gray-50'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-medium text-blue-600">{project.code}</div>
                        <div className="text-sm text-muted-foreground truncate">{project.name}</div>
                      </div>
                      <div className="flex items-center gap-2">
                        {project.is_active_project === 1 && (
                          <Badge variant="default" className="text-xs bg-green-600">Active</Badge>
                        )}
                        <Badge variant="outline" className="text-xs">{project.status}</Badge>
                      </div>
                    </div>
                  </button>
                ))
              )}
            </div>
            {filteredProjects.length > 50 && (
              <p className="text-xs text-muted-foreground mt-1">
                Showing first 50 results. Refine your search for more.
              </p>
            )}
          </div>

          {/* Selected Project Display */}
          {selectedProject && (
            <div className="p-2 bg-blue-50 rounded-md">
              <span className="text-sm font-medium">Selected: </span>
              <span className="text-sm text-blue-600">{selectedProject}</span>
            </div>
          )}

          {/* Reason */}
          <div>
            <Label htmlFor="reason">
              Why this project? <span className="text-red-500">*</span>
            </Label>
            <Textarea
              id="reason"
              placeholder="E.g., Email discusses branding work, not resort design"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={3}
              className="mt-1"
            />
            <p className="text-xs text-muted-foreground mt-1">
              This explanation helps train the AI to make better links in the future.
            </p>
          </div>
        </div>

        <DialogFooter className="mt-4">
          <Button variant="outline" onClick={handleClose}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!selectedProject || !reason || updateLink.isPending}
          >
            {updateLink.isPending ? 'Linking...' : 'Link Email'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
