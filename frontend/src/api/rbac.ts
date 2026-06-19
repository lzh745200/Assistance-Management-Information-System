import api from "./request";

export const rbacApi = {
  // ========== 权限检查 ==========
  checkPermission: (data: {
    permission?: string;
    resource?: string;
    action?: string;
  }) => api.post("/rbac/check", data),

  // ========== 角色管理 ==========
  getRoles: () => api.get("/rbac/roles"),
  getRole: (id: string) => api.get(`/rbac/roles/${id}`),
  createRole: (data: any) => api.post("/rbac/roles", data),
  updateRole: (id: string, data: any) => api.put(`/rbac/roles/${id}`, data),
  deleteRole: (id: string) => api.delete(`/rbac/roles/${id}`),
  getRoleUsers: (roleId: string) => api.get(`/rbac/roles/${roleId}/users`),

  // ========== 权限管理 ==========
  getPermissions: () => api.get("/rbac/permissions"),

  // ========== 用户权限 ==========
  getUserPermissions: (userId: number) =>
    api.get(`/rbac/user/${userId}/permissions`),
  getUserRoles: (userId: number) => api.get(`/rbac/user/${userId}/roles`),

  // ========== 分配/撤销 ==========
  assignRole: (userId: number, roleId: string) =>
    api.post("/rbac/assign/role", { user_id: userId, role_id: roleId }),
  grantPermission: (data: { user_id: number; permissions: string[] }) =>
    api.post("/rbac/grant/permission", data),
  revokePermission: (data: { user_id: number; permissions: string[] }) =>
    api.post("/rbac/revoke/permission", data),
  revokeRole: (data: { user_id: number; role_id: string }) =>
    api.delete("/rbac/revoke/role", { data }),

  // ========== 当前用户权限（前端路由用）==========
  getCurrentUserPermissions: () =>
    api.get("/rbac/frontend/current-user-permissions"),
  getRoutePermissions: () => api.get("/rbac/frontend/route-permissions"),
};
