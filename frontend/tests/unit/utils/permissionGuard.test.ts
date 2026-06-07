import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

const mockRbac = {
  hasPermission: vi.fn(),
  hasRole: vi.fn(),
  loadUserPermissions: vi.fn(),
}

const mockAuth = {
  user: { role: 'admin' },
}

vi.mock('@/stores/rbac', () => ({ useRbacStore: () => mockRbac }))
vi.mock('@/stores/auth', () => ({ useAuthStore: () => mockAuth }))

import {
  createPermissionGuard,
  createAsyncPermissionGuard,
  permissionDirective,
  roleDirective,
  permissionFilter,
  roleFilter,
} from '@/utils/permissionGuard'

describe('utils/permissionGuard', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  const mkRoute = (path: string, fullPath = path) => ({ path, fullPath } as any)

  describe('createPermissionGuard', () => {
    it('无权限要求 -> next()', () => {
      const guard = createPermissionGuard({ '/a': [] })
      const next = vi.fn()
      guard(mkRoute('/a', '/a'), mkRoute('/b'), next)
      expect(next).toHaveBeenCalledWith()
    })

    it('路由不存在于配置 -> next()', () => {
      const guard = createPermissionGuard({})
      const next = vi.fn()
      guard(mkRoute('/a'), mkRoute('/b'), next)
      expect(next).toHaveBeenCalledWith()
    })

    it('用户有权限 -> next()', () => {
      mockRbac.hasPermission.mockReturnValue(true)
      const guard = createPermissionGuard({ '/a': ['p1', 'p2'] })
      const next = vi.fn()
      guard(mkRoute('/a', '/a'), mkRoute('/b'), next)
      expect(next).toHaveBeenCalledWith()
    })

    it('用户无权限 -> /403', () => {
      mockRbac.hasPermission.mockReturnValue(false)
      const guard = createPermissionGuard({ '/a': ['p1'] })
      const next = vi.fn()
      guard(mkRoute('/a', '/a?q=1'), mkRoute('/b'), next)
      expect(next).toHaveBeenCalledWith({ path: '/403', query: { redirect: '/a?q=1' } })
    })

    it('任一权限满足 -> next()', () => {
      mockRbac.hasPermission.mockImplementation((_role: string, p: string) => p === 'p2')
      const guard = createPermissionGuard({ '/a': ['p1', 'p2'] })
      const next = vi.fn()
      guard(mkRoute('/a'), mkRoute('/b'), next)
      expect(next).toHaveBeenCalledWith()
    })
  })

  describe('createAsyncPermissionGuard', () => {
    it('等待 loadUserPermissions 后放行', async () => {
      mockRbac.loadUserPermissions.mockResolvedValue(undefined)
      mockRbac.hasPermission.mockReturnValue(true)
      const guard = createAsyncPermissionGuard({ '/a': ['p1'] })
      const next = vi.fn()
      await guard(mkRoute('/a'), mkRoute('/b'), next)
      expect(mockRbac.loadUserPermissions).toHaveBeenCalled()
      expect(next).toHaveBeenCalledWith()
    })

    it('无权限 -> /403', async () => {
      mockRbac.loadUserPermissions.mockResolvedValue(undefined)
      mockRbac.hasPermission.mockReturnValue(false)
      const guard = createAsyncPermissionGuard({ '/a': ['p1'] })
      const next = vi.fn()
      await guard(mkRoute('/a', '/a?x=1'), mkRoute('/b'), next)
      expect(next).toHaveBeenCalledWith({ path: '/403', query: { redirect: '/a?x=1' } })
    })

    it('空权限 -> 立即 next()', async () => {
      mockRbac.loadUserPermissions.mockResolvedValue(undefined)
      const guard = createAsyncPermissionGuard({ '/a': [] })
      const next = vi.fn()
      await guard(mkRoute('/a'), mkRoute('/b'), next)
      expect(next).toHaveBeenCalledWith()
    })
  })

  describe('permissionDirective', () => {
    it('mounted: 无 value -> 警告', () => {
      const el = document.createElement('div')
      const warn = vi.spyOn(console, 'warn').mockImplementation(() => {})
      permissionDirective.mounted(el, { value: null, arg: undefined } as any)
      expect(el.style.display).toBe('')
    })

    it('mounted: 有权限 -> 不变', () => {
      mockRbac.hasPermission.mockReturnValue(true)
      const el = document.createElement('div')
      permissionDirective.mounted(el, { value: 'p1', arg: undefined } as any)
      expect(el.style.display).toBe('')
    })

    it('mounted: 无权限, disabled arg', () => {
      mockRbac.hasPermission.mockReturnValue(false)
      const el = document.createElement('div')
      permissionDirective.mounted(el, { value: 'p1', arg: 'disabled' } as any)
      expect(el.getAttribute('disabled')).toBe('true')
      expect(el.classList.contains('permission-disabled')).toBe(true)
    })

    it('mounted: 无权限 -> 隐藏', () => {
      mockRbac.hasPermission.mockReturnValue(false)
      const el = document.createElement('div')
      permissionDirective.mounted(el, { value: 'p1' } as any)
      expect(el.style.display).toBe('none')
      expect(el.classList.contains('permission-hidden')).toBe(true)
    })

    it('updated: 无 value -> 提前返回', () => {
      const el = document.createElement('div')
      permissionDirective.updated(el, { value: null } as any)
      expect(el.style.display).toBe('')
    })

    it('updated: 权限满足 -> 清除样式', () => {
      mockRbac.hasPermission.mockReturnValue(true)
      const el = document.createElement('div')
      el.setAttribute('disabled', 'true')
      el.classList.add('permission-disabled')
      permissionDirective.updated(el, { value: 'p1' } as any)
      expect(el.getAttribute('disabled')).toBeNull()
      expect(el.classList.contains('permission-disabled')).toBe(false)
    })

    it('updated: 权限不满足 -> 隐藏', () => {
      mockRbac.hasPermission.mockReturnValue(false)
      const el = document.createElement('div')
      permissionDirective.updated(el, { value: 'p1' } as any)
      expect(el.style.display).toBe('none')
    })

    it('updated: 权限不满足 + disabled arg', () => {
      mockRbac.hasPermission.mockReturnValue(false)
      const el = document.createElement('div')
      permissionDirective.updated(el, { value: 'p1', arg: 'disabled' } as any)
      expect(el.getAttribute('disabled')).toBe('true')
    })
  })

  describe('roleDirective', () => {
    it('mounted: 无 value -> 警告', () => {
      const el = document.createElement('div')
      const warn = vi.spyOn(console, 'warn').mockImplementation(() => {})
      roleDirective.mounted(el, { value: null } as any)
      expect(el.style.display).toBe('')
    })

    it('mounted: 有角色 -> 不变', () => {
      mockRbac.hasRole.mockReturnValue(true)
      const el = document.createElement('div')
      roleDirective.mounted(el, { value: 'admin' } as any)
      expect(el.style.display).toBe('')
    })

    it('mounted: 无角色 -> 隐藏', () => {
      mockRbac.hasRole.mockReturnValue(false)
      const el = document.createElement('div')
      roleDirective.mounted(el, { value: 'admin' } as any)
      expect(el.style.display).toBe('none')
      expect(el.classList.contains('role-hidden')).toBe(true)
    })

    it('updated: 无 value', () => {
      const el = document.createElement('div')
      roleDirective.updated(el, { value: null } as any)
      expect(el.style.display).toBe('')
    })

    it('updated: 有角色 -> 清除', () => {
      mockRbac.hasRole.mockReturnValue(true)
      const el = document.createElement('div')
      el.classList.add('role-hidden')
      roleDirective.updated(el, { value: 'admin' } as any)
      expect(el.classList.contains('role-hidden')).toBe(false)
    })

    it('updated: 无角色 -> 隐藏', () => {
      mockRbac.hasRole.mockReturnValue(false)
      const el = document.createElement('div')
      roleDirective.updated(el, { value: 'admin' } as any)
      expect(el.style.display).toBe('none')
    })
  })

  describe('filters', () => {
    it('permissionFilter', () => {
      mockRbac.hasPermission.mockReturnValue(true)
      expect(permissionFilter('p1')).toBe(true)
    })

    it('roleFilter', () => {
      mockRbac.hasRole.mockReturnValue(true)
      expect(roleFilter('admin')).toBe(true)
    })
  })
})
