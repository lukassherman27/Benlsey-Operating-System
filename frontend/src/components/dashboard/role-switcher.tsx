"use client";

import { useEffect, useState } from "react";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { User, Briefcase, DollarSign } from "lucide-react";

export type DashboardRole = "executive" | "pm" | "finance";

interface RoleSwitcherProps {
  onRoleChange: (role: DashboardRole) => void;
  defaultRole?: DashboardRole;
}

const ROLES: Array<{ value: DashboardRole; label: string; icon: React.ReactNode }> = [
  { value: "executive", label: "Executive", icon: <User className="h-4 w-4" /> },
  { value: "pm", label: "PM", icon: <Briefcase className="h-4 w-4" /> },
  { value: "finance", label: "Finance", icon: <DollarSign className="h-4 w-4" /> },
];

const STORAGE_KEY = "dashboard_role";

export function RoleSwitcher({ onRoleChange, defaultRole = "executive" }: RoleSwitcherProps) {
  const [selectedRole, setSelectedRole] = useState<DashboardRole>(defaultRole);
  const [mounted, setMounted] = useState(false);

  // Load saved role from localStorage on mount
  useEffect(() => {
    setMounted(true);
    const saved = localStorage.getItem(STORAGE_KEY) as DashboardRole | null;
    if (saved && ROLES.find((r) => r.value === saved)) {
      setSelectedRole(saved);
      onRoleChange(saved);
    }
  }, [onRoleChange]);

  const handleRoleChange = (value: string) => {
    const role = value as DashboardRole;
    setSelectedRole(role);
    onRoleChange(role);
    if (mounted) {
      localStorage.setItem(STORAGE_KEY, role);
    }
  };

  return (
    <Tabs value={selectedRole} onValueChange={handleRoleChange}>
      <TabsList className="grid w-full grid-cols-3 max-w-md">
        {ROLES.map((role) => (
          <TabsTrigger
            key={role.value}
            value={role.value}
            className="flex items-center gap-2"
          >
            {role.icon}
            <span>{role.label}</span>
          </TabsTrigger>
        ))}
      </TabsList>
    </Tabs>
  );
}

/**
 * Hook to access current dashboard role with localStorage persistence
 */
export function useDashboardRole(defaultRole: DashboardRole = "executive"): [
  DashboardRole,
  (role: DashboardRole) => void
] {
  const [role, setRole] = useState<DashboardRole>(defaultRole);

  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY) as DashboardRole | null;
    if (saved && ROLES.find((r) => r.value === saved)) {
      setRole(saved);
    }
  }, []);

  const updateRole = (newRole: DashboardRole) => {
    setRole(newRole);
    localStorage.setItem(STORAGE_KEY, newRole);
  };

  return [role, updateRole];
}
