import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('@/api/request', () => ({
  default: vi.fn(),
  get: vi.fn(),
}))

import { get } from '@/api/request'
import { useRbacStore } from '@/stores/rbac'

describe('stores/rbac', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('initial state', () => {
    it('roles/permissions/loading 初始值', () => {
      const s = useRbacStore()
      expect(s.roles).toEqual([])
      expect(s.permissions).toEqual([])
      expect(s.loading).toBe(false)
    })
  })

  describe('fetchRoles', () => {
    it('成功: 填充 roles', async () => {
      ;(get as any).mockResolvedValue({ code: 200, data: [{ id: '1', name: 'admin', label: 'Admin', permissions: ['*'] }] })
      const s = useRbacStore()
      await s.fetchRoles()
      expect(s.roles).toHaveLength(1)
    })

    it('code !== 200: roles 不变', async () => {
      ;(get as any).mockResolvedValue({ code: 500 })
      const s = useRbacStore()
      await s.fetchRoles()
      expect(s.roles).toEqual([])
    })

    it('data 缺失: roles 不变', async () => {
      ;(get as any).mockResolvedValue({ code: 200, data: null })
      const s = useRbacStore()
      await s.fetchRoles()
      expect(s.roles).toEqual([])
    })

    it('失败: silent + loading=false', async () => {
      ;(get as any).mockRejectedValue(new Error('boom'))
      const s = useRbacStore()
      await s.fetchRoles()
      expect(s.roles).toEqual([])
      expect(s.loading).toBe(false)
    })
  })

  describe('fetchPermissions', () => {
    it('成功', async () => {
      ;(get as any).mockResolvedValue({ code: 200, data: [{ id: '1', name: 'p1', label: 'P1', resource: 'r', action: 'a' }] })
      const s = useRbacStore()
      await s.fetchPermissions()
      expect(s.permissions).toHaveLength(1)
    })

    it('code !== 200', async () => {
      ;(get as any).mockResolvedValue({ code: 500 })
      const s = useRbacStore()
      await s.fetchPermissions()
      expect(s.permissions).toEqual([])
    })

    it('失败 silent', async () => {
      ;(get as any).mockRejectedValue(new Error())
      const s = useRbacStore()
      await s.fetchPermissions()
      expect(s.loading).toBe(false)
    })
  })

  describe('hasPermission', () => {
    it('空 role/permission 返回 false', () => {
      const s = useRbacStore()
      expect(s.hasPermission('', 'p1')).toBe(false)
      expect(s.hasPermission('admin', '')).toBe(false)
    })

    it('super_admin bypasses all', () => {
      const s = useRbacStore()
      expect(s.hasPermission('super_admin', 'any.thing')).toBe(true)
    })

    it('role.permissions 含 * 返回 true', () => {
      const s = useRbacStore()
      s.roles = [{ id: '1', name: 'admin', label: 'A', permissions: ['*'] }]
      expect(s.hasPermission('admin', 'whatever')).toBe(true)
    })

    it('role.permissions 含 exact permission', () => {
      const s = useRbacStore()
      s.roles = [{ id: '1', name: 'editor', label: 'E', permissions: ['edit.user'] }]
      expect(s.hasPermission('editor', 'edit.user')).toBe(true)
    })

    it('role.permissions 不含: false', () => {
      const s = useRbacStore()
      s.roles = [{ id: '1', name: 'viewer', label: 'V', permissions: ['view.user'] }]
      expect(s.hasPermission('viewer', 'edit.user')).toBe(false)
    })

    it('role 不存在: false', () => {
      const s = useRbacStore()
      expect(s.hasPermission('nonexistent', 'p1')).toBe(false)
    })
  })
})
