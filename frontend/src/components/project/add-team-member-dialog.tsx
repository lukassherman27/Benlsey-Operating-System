"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { Loader2, Search } from "lucide-react";

interface AddTeamMemberDialogProps {
  projectCode: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function AddTeamMemberDialog({
  projectCode,
  open,
  onOpenChange,
}: AddTeamMemberDialogProps) {
  const queryClient = useQueryClient();
  const [selectedStaffId, setSelectedStaffId] = useState<string>("");
  const [selectedRole, setSelectedRole] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState("");

  // Fetch staff list
  const { data: staffData, isLoading: loadingStaff } = useQuery({
    queryKey: ["staff-list"],
    queryFn: () => api.getStaffList(),
    enabled: open,
  });

  // Add team member mutation
  const addMutation = useMutation({
    mutationFn: (data: { staff_id: number; role: string }) =>
      api.addProjectAssignment(projectCode, data),
    onSuccess: () => {
      toast.success("Team member added successfully");
      queryClient.invalidateQueries({ queryKey: ["project-assignments", projectCode] });
      handleClose();
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to add team member");
    },
  });

  const handleClose = () => {
    setSelectedStaffId("");
    setSelectedRole("");
    setSearchQuery("");
    onOpenChange(false);
  };

  const handleSubmit = () => {
    if (!selectedStaffId || !selectedRole) {
      toast.error("Please select a team member and role");
      return;
    }

    addMutation.mutate({
      staff_id: parseInt(selectedStaffId),
      role: selectedRole,
    });
  };

  // Filter staff based on search
  const filteredStaff = (staffData?.staff || []).filter((s) => {
    const query = searchQuery.toLowerCase();
    return (
      s.display_name.toLowerCase().includes(query) ||
      s.email?.toLowerCase().includes(query) ||
      s.department?.toLowerCase().includes(query)
    );
  });

  const roles = staffData?.roles || [
    "Project Lead",
    "Project Manager",
    "Designer",
    "Draftsperson",
    "Admin Support",
  ];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Add Team Member</DialogTitle>
          <DialogDescription>
            Assign a Bensley team member to this project
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <Input
              placeholder="Search by name, email, or department..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>

          {/* Staff Selection */}
          <div className="space-y-2">
            <Label>Team Member</Label>
            {loadingStaff ? (
              <div className="flex items-center gap-2 text-sm text-slate-500">
                <Loader2 className="h-4 w-4 animate-spin" />
                Loading staff...
              </div>
            ) : (
              <Select value={selectedStaffId} onValueChange={setSelectedStaffId}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a team member" />
                </SelectTrigger>
                <SelectContent className="max-h-60">
                  {filteredStaff.length === 0 ? (
                    <div className="p-2 text-center text-sm text-slate-500">
                      No matching staff found
                    </div>
                  ) : (
                    filteredStaff.map((staff) => (
                      <SelectItem key={staff.staff_id} value={String(staff.staff_id)}>
                        <div className="flex flex-col">
                          <span>{staff.display_name}</span>
                          {staff.department && (
                            <span className="text-xs text-slate-500">
                              {staff.department} - {staff.office}
                            </span>
                          )}
                        </div>
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
            )}
          </div>

          {/* Role Selection */}
          <div className="space-y-2">
            <Label>Role on Project</Label>
            <Select value={selectedRole} onValueChange={setSelectedRole}>
              <SelectTrigger>
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
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleClose}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!selectedStaffId || !selectedRole || addMutation.isPending}
          >
            {addMutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Adding...
              </>
            ) : (
              "Add Team Member"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
