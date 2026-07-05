/**
 * 用户权限管理 API
 * 提供用户-组织关联、角色分配、权限管理等功能
 */

import { get, post, del, apiRequest } from './request'

// ==================== 类型定义 ====================

/** 用户组织关联 */
export interface UserOrganization {
  user_id: number
  organization_id: number
  role: string
}

/** 用户角色 */
export interface UserRole {
  user_id: number
  role_id: string
}

/** 用户权限 */
export interface UserPermission {
  user_id: number
  permission: string
}

/** 组织树节点 */
export interface OrganizationTreeNode {
  id: number
  name: string
  children?: OrganizationTreeNode[]
}

// ==================== 用户-组织管理 ====================

/** 将用户分配到组织 */
export async function assignUserToOrganization(data: {
  user_id: number
  organization_id: number
  role?: string
  is_primary?: boolean
}): Promise<{ success: boolean; message: string; data: UserOrganization }> {
  return post('/user-permissions/assign-organization', data)
}

/** 将用户从组织中移除 */
export async function removeUserFromOrganization(
  userId: number,
  organizationId: number
): Promise<{ success: boolean; message: string }> {
  return del(
    `/user-permissions/remove-organization?user_id=${userId}&organization_id=${organizationId}`
  )
}

/** 获取用户所属的所有组织 */
export async function getUserOrganizations(
  userId: number
): Promise<{ success: boolean; data: any[]; count: number }> {
  return get(`/user-permissions/user-organizations/${userId}`)
}

/** 获取组织下的所有用户 */
export async function getOrganizationUsers(
  organizationId: number,
  includeChildren?: boolean
): Promise<{ success: boolean; data: any[]; count: number }> {
  return get(
    `/user-permissions/organization-users/${organizationId}`,
    includeChildren ? { include_children: true } : undefined
  )
}

// ==================== 角色管理 ====================

/** 获取所有角色列表 */
export async function listRoles(params?: {
  skip?: number
  limit?: number
}): Promise<{ success: boolean; data: any[]; total: number }> {
  return get('/rbac/roles', params)
}

/** 为用户分配角色 */
export async function assignRoleToUser(data: {
  user_id: number
  role_id: string
  expires_at?: string
}): Promise<{ success: boolean; message: string; data: UserRole }> {
  return post('/rbac/assign/role', data)
}

/** 移除用户的角色 */
export async function removeRoleFromUser(
  userId: number,
  roleId: string
): Promise<{ success: boolean; message: string }> {
  return apiRequest({
    method: 'DELETE',
    url: '/rbac/revoke/role',
    data: { user_id: userId, role_id: roleId },
  })
}

/** 获取用户的所有角色 */
export async function getUserRoles(
  userId: number
): Promise<{ success: boolean; data: any[]; count: number }> {
  return get(`/rbac/user/${userId}/roles`)
}

// ==================== 权限管理 ====================

/** 直接授予用户权限 */
export async function grantPermission(data: {
  user_id: number
  permission: string
  expires_at?: string
}): Promise<{ success: boolean; message: string; data: UserPermission }> {
  return post('/user-permissions/grant-permission', data)
}

/** 撤销用户的权限 */
export async function revokePermission(
  userId: number,
  permission: string
): Promise<{ success: boolean; message: string }> {
  return del(
    `/user-permissions/revoke-permission?user_id=${userId}&permission=${encodeURIComponent(permission)}`
  )
}

/** 获取用户的所有权限 */
export async function getUserPermissions(
  userId: number
): Promise<{ success: boolean; data: string[]; count: number }> {
  return get(`/user-permissions/user-permissions/${userId}`)
}

/** 检查用户是否拥有指定权限 */
export async function checkUserPermission(data: {
  user_id: number
  permission: string
}): Promise<{ success: boolean; has_permission: boolean }> {
  return post('/user-permissions/check-permission', data)
}

// ==================== 组织树管理 ====================

/** 获取组织树 */
export async function getOrganizationTree(
  parentId?: number
): Promise<{ success: boolean; data: OrganizationTreeNode[] }> {
  return get('/user-permissions/organization-tree', parentId ? { parent_id: parentId } : undefined)
}

/** 获取当前用户可访问的所有组织ID */
export async function getAccessibleOrganizations(): Promise<{
  success: boolean
  data: number[]
  count: number
}> {
  return get('/user-permissions/accessible-organizations')
}

// ==================== 分组导出 ====================

export const userPermissionsApi = {
  // 用户-组织
  assignOrganization: assignUserToOrganization,
  removeOrganization: removeUserFromOrganization,
  getUserOrganizations,
  getOrganizationUsers,
  // 角色
  listRoles,
  assignRole: assignRoleToUser,
  removeRole: removeRoleFromUser,
  getUserRoles,
  // 权限
  grantPermission,
  revokePermission,
  getUserPermissions,
  checkPermission: checkUserPermission,
  // 组织树
  getOrganizationTree,
  getAccessibleOrganizations,
}
