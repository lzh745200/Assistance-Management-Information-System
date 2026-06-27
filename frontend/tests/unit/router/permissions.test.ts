import { describe, it, expect } from 'vitest'
import { rolePermissions, routePermissions } from '@/router/permissions'

describe('rolePermissions', () => {
  it('super_admin has wildcard', () => {
    expect(rolePermissions.super_admin).toEqual(['*'])
  })

  it('admin has read/write/delete', () => {
    expect(rolePermissions.admin).toContain('read')
    expect(rolePermissions.admin).toContain('write')
    expect(rolePermissions.admin).toContain('delete')
  })

  it('manager has read/write', () => {
    expect(rolePermissions.manager).toEqual(['read', 'write'])
  })

  it('viewer has read only', () => {
    expect(rolePermissions.viewer).toEqual(['read'])
  })

  it('approval_leader has read/approve', () => {
    expect(rolePermissions.approval_leader).toContain('approve')
    expect(rolePermissions.approval_leader).toContain('read')
  })

  it('all roles exist and have permissions', () => {
    const roles = ['super_admin', 'admin', 'manager', 'operator', 'viewer', 'approval_leader']
    for (const role of roles) {
      expect(rolePermissions[role]).toBeDefined()
      expect(rolePermissions[role].length).toBeGreaterThan(0)
    }
  })
})

describe('routePermissions', () => {
  it('dashboard requires read', () => {
    expect(routePermissions['/dashboard']).toContain('read')
  })

  it('approval requires read and approve', () => {
    expect(routePermissions['/approval']).toContain('approve')
    expect(routePermissions['/approval']).toContain('read')
  })

  it('all routes have at least one permission', () => {
    for (const [path, perms] of Object.entries(routePermissions)) {
      expect(perms.length).toBeGreaterThan(0)
    }
  })

  it('all routes contain read', () => {
    for (const perms of Object.values(routePermissions)) {
      expect(perms).toContain('read')
    }
  })
})
