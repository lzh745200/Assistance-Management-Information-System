import api from "./request";

export const rbacApi = {
  // ========== 权限检查 ==========
  checkPermission: (data: { permission?: string; resource?: string; action?: string }) =>
    api.post("/rbac/check", data),

  // ========== 角色管理 ==========
  getRoles: () => api.get("/rbac/roles"),
  getRole: (id: number) => api.get(`/rbac/roles/${id}`),
  createRole: (data: any) => api.post("/rbac/roles", data),
  updateRole: (id: number, data: any) =>
    api.put(`/rbac/roles/${id}`, data),
  deleteRole: (id: number) => api.delete(`/rbac/roles/${id}`),
  getRoleUsers: (roleId: number) =>
    api.get(`/rbac/roles/${roleId}/users`),

  // ========== 权限管理 ==========
  getPermissions: () => api.get("/rbac/permissions"),

  // ========== 用户权限 ==========
  getUserPermissions: (userId: number) =>
    api.get(`/rbac/user/${userId}/permissions`),
  getUserRoles: (userId: number) =>
    api.get(`/rbac/user/${userId}/roles`),

  // ========== 分配/撤销 ==========
  assignRole: (userId: number, roleId: number) =>
    api.post("/rbac/assign/role", { user_id: userId, role_id: roleId }),
  grantPermission: (data: { role_id: number; permission_id: number }) =>
    api.post("/rbac/grant/permission", data),
  revokeRole: (data: { user_id: number; role_id: number }) =>
    api.delete("/rbac/revoke/role", { data }),

  // ========== 当前用户权限（前端路由用）==========
  getCurrentUserPermissions: () =>
    api.get("/rbac/frontend/current-user-permissions"),
  getRoutePermissions: () =>
    api.get("/rbac/frontend/route-permissions"),
};
