import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockGet, mockPost, mockDel, mockApiRequest } = vi.hoisted(() => ({
  mockGet: vi.fn(),
  mockPost: vi.fn(),
  mockDel: vi.fn(),
  mockApiRequest: vi.fn(),
}))

// src/api/userPermissions.ts 实际 import：import { get, post, del, apiRequest } from '@/api/request'
vi.mock('@/api/request', () => ({
  get: mockGet,
  post: mockPost,
  del: mockDel,
  apiRequest: mockApiRequest,
  getCsrfToken: vi.fn(() => Promise.resolve("test-csrf"))}))

import {
  assignUserToOrganization,
  removeUserFromOrganization,
  getUserOrganizations,
  getOrganizationUsers,
  listRoles,
  assignRoleToUser,
  removeRoleFromUser,
  getUserRoles,
  grantPermission,
  revokePermission,
  getUserPermissions,
  checkUserPermission,
  getOrganizationTree,
  getAccessibleOrganizations,
} from '@/api/userPermissions'

describe('api/userPermissions', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('assignUserToOrganization 调用 POST /user-permissions/assign-organization', async () => {
    const body = { success: true, message: 'ok', data: { user_id: 1 } }
    mockPost.mockResolvedValue(body)
    const data = { user_id: 1, organization_id: 2, role: 'member' }
    const result = await assignUserToOrganization(data)
    expect(mockPost).toHaveBeenCalledWith('/user-permissions/assign-organization', data)
    expect(result).toBe(body)
  })

  it('removeUserFromOrganization 将参数拼进 DELETE URL 查询串', async () => {
    mockDel.mockResolvedValue({ success: true })
    await removeUserFromOrganization(1, 2)
    expect(mockDel).toHaveBeenCalledWith(
      '/user-permissions/remove-organization?user_id=1&organization_id=2'
    )
  })

  it('getUserOrganizations 调用 GET /user-permissions/user-organizations/{userId}', async () => {
    const body = { success: true, data: [], count: 0 }
    mockGet.mockResolvedValue(body)
    const result = await getUserOrganizations(1)
    expect(mockGet).toHaveBeenCalledWith('/user-permissions/user-organizations/1')
    expect(result).toBe(body)
  })

  it('getOrganizationUsers includeChildren=true 时传 include_children 参数', async () => {
    mockGet.mockResolvedValue({ success: true })
    await getOrganizationUsers(2, true)
    expect(mockGet).toHaveBeenCalledWith('/user-permissions/organization-users/2', {
      include_children: true,
    })
  })

  it('getOrganizationUsers 不带 includeChildren 时参数为 undefined', async () => {
    mockGet.mockResolvedValue({ success: true })
    await getOrganizationUsers(2)
    expect(mockGet).toHaveBeenCalledWith('/user-permissions/organization-users/2', undefined)
  })

  it('listRoles 调用 GET /rbac/roles 并透传分页参数', async () => {
    const body = { success: true, data: [], total: 0 }
    mockGet.mockResolvedValue(body)
    const result = await listRoles({ skip: 0, limit: 10 })
    expect(mockGet).toHaveBeenCalledWith('/rbac/roles', { skip: 0, limit: 10 })
    expect(result).toBe(body)
  })

  it('assignRoleToUser 调用 POST /rbac/assign/role', async () => {
    const body = { success: true, message: 'ok', data: { user_id: 1, role_id: 'r1' } }
    mockPost.mockResolvedValue(body)
    const data = { user_id: 1, role_id: 'r1' }
    const result = await assignRoleToUser(data)
    expect(mockPost).toHaveBeenCalledWith('/rbac/assign/role', data)
    expect(result).toBe(body)
  })

  it('removeRoleFromUser 通过 apiRequest 发起带 body 的 DELETE', async () => {
    const body = { success: true, message: 'ok' }
    mockApiRequest.mockResolvedValue(body)
    const result = await removeRoleFromUser(1, 'r1')
    expect(mockApiRequest).toHaveBeenCalledWith({
      method: 'DELETE',
      url: '/rbac/revoke/role',
      data: { user_id: 1, role_id: 'r1' },
    })
    expect(result).toBe(body)
  })

  it('getUserRoles 调用 GET /rbac/user/{userId}/roles', async () => {
    const body = { success: true, data: [], count: 0 }
    mockGet.mockResolvedValue(body)
    const result = await getUserRoles(1)
    expect(mockGet).toHaveBeenCalledWith('/rbac/user/1/roles')
    expect(result).toBe(body)
  })

  it('grantPermission 调用 POST /user-permissions/grant-permission', async () => {
    const body = { success: true, message: 'ok', data: { user_id: 1, permission: 'read' } }
    mockPost.mockResolvedValue(body)
    const data = { user_id: 1, permission: 'read' }
    const result = await grantPermission(data)
    expect(mockPost).toHaveBeenCalledWith('/user-permissions/grant-permission', data)
    expect(result).toBe(body)
  })

  it('revokePermission 对 permission 做 encodeURIComponent 后拼进 DELETE URL', async () => {
    mockDel.mockResolvedValue({ success: true })
    await revokePermission(1, 'data:导出')
    expect(mockDel).toHaveBeenCalledWith(
      `/user-permissions/revoke-permission?user_id=1&permission=${encodeURIComponent('data:导出')}`
    )
  })

  it('getUserPermissions 调用 GET /user-permissions/user-permissions/{userId}', async () => {
    const body = { success: true, data: ['read'], count: 1 }
    mockGet.mockResolvedValue(body)
    const result = await getUserPermissions(1)
    expect(mockGet).toHaveBeenCalledWith('/user-permissions/user-permissions/1')
    expect(result).toBe(body)
  })

  it('checkUserPermission 调用 POST /user-permissions/check-permission', async () => {
    const body = { success: true, has_permission: true }
    mockPost.mockResolvedValue(body)
    const data = { user_id: 1, permission: 'read' }
    const result = await checkUserPermission(data)
    expect(mockPost).toHaveBeenCalledWith('/user-permissions/check-permission', data)
    expect(result).toBe(body)
  })

  it('getOrganizationTree 带 parentId 时传 parent_id 参数', async () => {
    mockGet.mockResolvedValue({ success: true })
    await getOrganizationTree(5)
    expect(mockGet).toHaveBeenCalledWith('/user-permissions/organization-tree', { parent_id: 5 })
  })

  it('getOrganizationTree 不带 parentId 时参数为 undefined', async () => {
    const body = { success: true, data: [] }
    mockGet.mockResolvedValue(body)
    const result = await getOrganizationTree()
    expect(mockGet).toHaveBeenCalledWith('/user-permissions/organization-tree', undefined)
    expect(result).toBe(body)
  })

  it('getAccessibleOrganizations 调用 GET /user-permissions/accessible-organizations', async () => {
    const body = { success: true, data: [1, 2], count: 2 }
    mockGet.mockResolvedValue(body)
    const result = await getAccessibleOrganizations()
    expect(mockGet).toHaveBeenCalledWith('/user-permissions/accessible-organizations')
    expect(result).toBe(body)
  })
})
