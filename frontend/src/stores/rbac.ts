import { defineStore } from "pinia";
import { ref } from "vue";
import { get } from "@/api/request";

export interface Role {
  id: string;
  name: string;
  label: string;
  permissions: string[];
}

export interface Permission {
  id: string;
  name: string;
  label: string;
  resource: string;
  action: string;
}

export const useRbacStore = defineStore("rbac", () => {
  const roles = ref<Role[]>([]);
  const permissions = ref<Permission[]>([]);
  const loading = ref(false);

  async function fetchRoles() {
    loading.value = true;
    try {
      const res = await get<{ code: number; data: Role[] }>("/rbac/roles");
      if (res.code === 200 && res.data) roles.value = res.data;
    } catch {
      /* silent */
    } finally {
      loading.value = false;
    }
  }

  async function fetchPermissions() {
    loading.value = true;
    try {
      const res = await get<{ code: number; data: Permission[] }>(
        "/rbac/permissions",
      );
      if (res.code === 200 && res.data) permissions.value = res.data;
    } catch {
      /* silent */
    } finally {
      loading.value = false;
    }
  }

  function hasPermission(userRole: string, permission: string): boolean {
    if (!userRole || !permission) return false;
    // Super admin bypasses all checks
    if (userRole === "super_admin") return true;
    // Check role-level permissions
    const role = roles.value.find((r) => r.name === userRole);
    if (
      role?.permissions.includes("*") ||
      role?.permissions.includes(permission)
    )
      return true;
    return false;
  }

  return {
    roles,
    permissions,
    loading,
    fetchRoles,
    fetchPermissions,
    hasPermission,
  };
});
