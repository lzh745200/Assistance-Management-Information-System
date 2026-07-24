import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockGet, mockPost, mockPut, mockDel } = vi.hoisted(() => ({
  mockGet: vi.fn(),
  mockPost: vi.fn(),
  mockPut: vi.fn(),
  mockDel: vi.fn(),
}))

// src/api/userManagement.ts 实际 import：import { get, post, put, del } from '@/api/request'
vi.mock('@/api/request', () => ({
  get: mockGet,
  post: mockPost,
  put: mockPut,
  del: mockDel,
}))

import {
  listUsers,
  createUser,
  updateUser,
  deleteUser,
  resetPassword,
  assignUserRole,
  generatePassword,
  listRoles,
} from '@/api/userManagement'

describe('api/userManagement', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('listUsers 调用 GET /user-management 并透传过滤参数', async () => {
    const body = { success: true, data: { items: [], total: 0 } }
    mockGet.mockResolvedValue(body)
    const params = { page: 2, page_size: 10, username: 'alice', role: 'admin' }
    const result = await listUsers(params)
    expect(mockGet).toHaveBeenCalledWith('/user-management', params)
    expect(result).toBe(body)
  })

  it('createUser 调用 POST /user-management 并透传载荷', async () => {
    const body = { success: true, data: { id: '1', username: 'alice', password: 'p' } }
    mockPost.mockResolvedValue(body)
    const data = { username: 'alice', full_name: 'Alice', role: 'admin' }
    const result = await createUser(data)
    expect(mockPost).toHaveBeenCalledWith('/user-management', data)
    expect(result).toBe(body)
  })

  it('updateUser 调用 PUT /user-management/{id}', async () => {
    const body = { success: true, message: 'ok' }
    mockPut.mockResolvedValue(body)
    const data = { full_name: 'Bob', is_active: false }
    const result = await updateUser(7, data)
    expect(mockPut).toHaveBeenCalledWith('/user-management/7', data)
    expect(result).toBe(body)
  })

  it('deleteUser 调用 DELETE /user-management/{id}', async () => {
    mockDel.mockResolvedValue({ success: true })
    await deleteUser(7)
    expect(mockDel).toHaveBeenCalledWith('/user-management/7')
  })

  it('resetPassword 调用 POST /user-management/{id}/reset-password 带 new_password', async () => {
    const body = { success: true, data: { username: 'alice', new_password: 'np' } }
    mockPost.mockResolvedValue(body)
    const result = await resetPassword(7, 'np')
    expect(mockPost).toHaveBeenCalledWith('/user-management/7/reset-password', {
      new_password: 'np',
    })
    expect(result).toBe(body)
  })

  it('assignUserRole 对 role_code 做 encodeURIComponent', async () => {
    mockPost.mockResolvedValue({ success: true })
    await assignUserRole(7, '系统管理员')
    expect(mockPost).toHaveBeenCalledWith(
      `/user-management/7/assign-role?role_code=${encodeURIComponent('系统管理员')}`
    )
  })

  it('generatePassword 带 length 时透传参数', async () => {
    const body = { success: true, data: { password: 'abc123' } }
    mockGet.mockResolvedValue(body)
    const result = await generatePassword(12)
    expect(mockGet).toHaveBeenCalledWith('/user-management/generate-password', { length: 12 })
    expect(result).toBe(body)
  })

  it('generatePassword 不带 length 时参数为 undefined', async () => {
    mockGet.mockResolvedValue({ success: true })
    await generatePassword()
    expect(mockGet).toHaveBeenCalledWith('/user-management/generate-password', undefined)
  })

  it('listRoles 调用 GET /user-management/roles', async () => {
    const body = { success: true, data: { items: [], total: 0 } }
    mockGet.mockResolvedValue(body)
    const result = await listRoles()
    expect(mockGet).toHaveBeenCalledWith('/user-management/roles')
    expect(result).toBe(body)
  })
})
