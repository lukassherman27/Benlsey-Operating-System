"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";
import { Users, Plus, MoreHorizontal, Pencil, Trash2 } from "lucide-react";
import { AddTeamMemberDialog } from "./add-team-member-dialog";

interface BensleyTeamCardProps {
  projectCode: string;
}

interface Assignment {
  assignment_id: number;
  staff_id: number;
  first_name: string;
  last_name: string | null;
  display_name: string;
  role: string | null;
  department: string | null;
  office: string | null;
}

export function BensleyTeamCard({ projectCode }: BensleyTeamCardProps) {
  const queryClient = useQueryClient();
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedAssignment, setSelectedAssignment] = useState<Assignment | null>(null);
  const [editRole, setEditRole] = useState("");

  // Fetch project assignments
  const { data, isLoading, error } = useQuery({
    queryKey: ["project-assignments", projectCode],
    queryFn: () => api.getProjectAssignments(projectCode),
    staleTime: 1000 * 60 * 5,
  });

  // Update role mutation
  const updateMutation = useMutation({
    mutationFn: ({ assignmentId, role }: { assignmentId: number; role: string }) =>
      api.updateProjectAssignment(projectCode, assignmentId, { role }),
    onSuccess: () => {
      toast.success("Role updated successfully");
      queryClient.invalidateQueries({ queryKey: ["project-assignments", projectCode] });
      setEditDialogOpen(false);
      setSelectedAssignment(null);
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to update role");
    },
  });

  // Remove assignment mutation
  const removeMutation = useMutation({
    mutationFn: (assignmentId: number) =>
      api.removeProjectAssignment(projectCode, assignmentId),
    onSuccess: () => {
      toast.success("Team member removed");
      queryClient.invalidateQueries({ queryKey: ["project-assignments", projectCode] });
      setDeleteDialogOpen(false);
      setSelectedAssignment(null);
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to remove team member");
    },
  });

  const handleEditClick = (assignment: Assignment) => {
    setSelectedAssignment(assignment);
    setEditRole(assignment.role || "");
    setEditDialogOpen(true);
  };

  const handleDeleteClick = (assignment: Assignment) => {
    setSelectedAssignment(assignment);
    setDeleteDialogOpen(true);
  };

  const handleEditSubmit = () => {
    if (selectedAssignment && editRole) {
      updateMutation.mutate({
        assignmentId: selectedAssignment.assignment_id,
        role: editRole,
      });
    }
  };

  const handleDeleteConfirm = () => {
    if (selectedAssignment) {
      removeMutation.mutate(selectedAssignment.assignment_id);
    }
  };

  const roles = data?.roles || [
    "Project Lead",
    "Project Manager",
    "Designer",
    "Draftsperson",
    "Admin Support",
  ];

  if (isLoading) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-base">
            <Users className="h-4 w-4 text-blue-600" />
            Bensley Team
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  const assignments = data?.assignments || [];

  return (
    <>
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-base">
              <Users className="h-4 w-4 text-blue-600" />
              Bensley Team
            </CardTitle>
            <div className="flex items-center gap-2">
              <Badge variant="secondary">{assignments.length} assigned</Badge>
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7"
                onClick={() => setAddDialogOpen(true)}
              >
                <Plus className="h-4 w-4" />
                <span className="sr-only">Add team member</span>
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="pt-0">
          {assignments.length === 0 ? (
            <div className="text-center py-6">
              <p className="text-sm text-slate-500 mb-3">
                No team members assigned yet
              </p>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setAddDialogOpen(true)}
              >
                <Plus className="mr-2 h-4 w-4" />
                Add First Team Member
              </Button>
            </div>
          ) : (
            <div className="space-y-2">
              {assignments.map((assignment) => (
                <div
                  key={assignment.assignment_id}
                  className="flex items-center justify-between p-2 rounded-lg bg-slate-50 hover:bg-slate-100 transition-colors group"
                >
                  <div className="flex items-center gap-3">
                    <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 font-medium text-sm">
                      {assignment.first_name.charAt(0)}
                    </div>
                    <div>
                      <p className="font-medium text-sm text-slate-900">
                        {assignment.display_name}
                      </p>
                      {assignment.department && (
                        <p className="text-xs text-slate-500">
                          {assignment.department}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {assignment.role && (
                      <Badge variant="outline" className="text-xs">
                        {assignment.role}
                      </Badge>
                    )}
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7 opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          <MoreHorizontal className="h-4 w-4" />
                          <span className="sr-only">Actions</span>
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => handleEditClick(assignment)}>
                          <Pencil className="mr-2 h-4 w-4" />
                          Edit Role
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          className="text-red-600"
                          onClick={() => handleDeleteClick(assignment)}
                        >
                          <Trash2 className="mr-2 h-4 w-4" />
                          Remove
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Add Team Member Dialog */}
      <AddTeamMemberDialog
        projectCode={projectCode}
        open={addDialogOpen}
        onOpenChange={setAddDialogOpen}
      />

      {/* Edit Role Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>Edit Role</DialogTitle>
            <DialogDescription>
              Update role for {selectedAssignment?.display_name}
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Label>Role on Project</Label>
            <Select value={editRole} onValueChange={setEditRole}>
              <SelectTrigger className="mt-2">
                <SelectValue placeholder="Select a role" />
              </SelectTrigger>
              <SelectContent>
                {roles.map((role) => (
                  <SelectItem key={role} value={role}>
                    {role}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleEditSubmit} disabled={updateMutation.isPending}>
              {updateMutation.isPending ? "Saving..." : "Save"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Remove Team Member?</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to remove {selectedAssignment?.display_name} from
              this project? This action can be undone by adding them again.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteConfirm}
              className="bg-red-600 hover:bg-red-700"
            >
              {removeMutation.isPending ? "Removing..." : "Remove"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
