import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

const mockGet = vi.fn()

vi.mock('@/api/request', () => ({
  get: (...args: any[]) => mockGet(...args),
}))

import { useRbacStore } from '@/stores/rbac'

describe('useRbacStore', () => {
  let store: ReturnType<typeof useRbacStore>
  beforeEach(() => {
    vi.clearAllMocks()
    setActivePinia(createPinia())
    store = useRbacStore()
  })

  it('初始: roles=[], permissions=[], loading=false', () => {
    expect(store.roles).toEqual([])
    expect(store.permissions).toEqual([])
    expect(store.loading).toBe(false)
  })

  it('fetchRoles 成功时填充 roles', async () => {
    const roles = [
      { id: '1', name: 'admin', label: '管理员', permissions: ['*'] },
      { id: '2', name: 'viewer', label: '查看者', permissions: ['read'] },
    ]
    mockGet.mockResolvedValueOnce({ code: 200, data: roles })
    await store.fetchRoles()
    expect(mockGet).toHaveBeenCalledWith('/rbac/roles')
    expect(store.roles).toHaveLength(2)
    expect(store.loading).toBe(false)
  })

  it('fetchRoles 失败时静默 (loading 仍然被重置)', async () => {
    mockGet.mockRejectedValueOnce(new Error('boom'))
    await store.fetchRoles()
    expect(store.roles).toEqual([])
    expect(store.loading).toBe(false)
  })

  it('fetchRoles 非 200 状态码不更新 roles', async () => {
    mockGet.mockResolvedValueOnce({ code: 500, data: [] })
    await store.fetchRoles()
    expect(store.roles).toEqual([])
  })

  it('fetchPermissions 成功时填充 permissions', async () => {
    const perms = [
      { id: '1', name: 'read', label: '读', resource: 'village', action: 'read' },
    ]
    mockGet.mockResolvedValueOnce({ code: 200, data: perms })
    await store.fetchPermissions()
    expect(mockGet).toHaveBeenCalledWith('/rbac/permissions')
    expect(store.permissions).toHaveLength(1)
  })

  it('fetchPermissions 失败时静默', async () => {
    mockGet.mockRejectedValueOnce(new Error('boom'))
    await store.fetchPermissions()
    expect(store.permissions).toEqual([])
    expect(store.loading).toBe(false)
  })

  describe('hasPermission', () => {
    it('空 userRole 返回 false', () => {
      expect(store.hasPermission('', 'village.read')).toBe(false)
    })
    it('空 permission 返回 false', () => {
      expect(store.hasPermission('admin', '')).toBe(false)
    })
    it('super_admin 角色绕过所有检查', () => {
      expect(store.hasPermission('super_admin', 'any.permission')).toBe(true)
    })
    it('admin 角色 + 角色权限含 * 返回 true', () => {
      store.roles = [{ id: '1', name: 'admin', label: '管理员', permissions: ['*'] }]
      expect(store.hasPermission('admin', 'village.create')).toBe(true)
    })
    it('admin 角色 + 含具体权限返回 true', () => {
      store.roles = [{ id: '1', name: 'admin', label: '管理员', permissions: ['village.read'] }]
      expect(store.hasPermission('admin', 'village.read')).toBe(true)
    })
    it('admin 角色 + 不含权限返回 false', () => {
      store.roles = [{ id: '1', name: 'admin', label: '管理员', permissions: ['village.read'] }]
      expect(store.hasPermission('admin', 'village.delete')).toBe(false)
    })
    it('角色不在 roles 列表中返回 false', () => {
      store.roles = []
      expect(store.hasPermission('unknown_role', 'village.read')).toBe(false)
    })
  })
})
