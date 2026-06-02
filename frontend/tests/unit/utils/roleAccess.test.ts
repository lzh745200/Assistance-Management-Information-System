import { describe, it, expect } from 'vitest'
import {
  ROLE_PRIORITY,
  normalizeRole,
  getEffectiveRoles,
  hasAllowedRole,
  hasMinRole,
  canAccessMenu,
  getRoleFromLocalStorage,
} from '@/utils/roleAccess'

describe('roleAccess utility', () => {
  it('ROLE_PRIORITY includes expected roles', () => {
    expect(ROLE_PRIORITY.super_admin).toBe(0)
    expect(ROLE_PRIORITY.admin).toBe(1)
    expect(ROLE_PRIORITY.approval_leader).toBe(2)
    expect(ROLE_PRIORITY.manager).toBe(2)
    expect(ROLE_PRIORITY.operator).toBe(3)
    expect(ROLE_PRIORITY.viewer).toBe(4)
  })

  it('normalizeRole returns viewer when role is empty', () => {
    expect(normalizeRole(undefined)).toBe('viewer')
    expect(normalizeRole(null)).toBe('viewer')
    expect(normalizeRole('')).toBe('viewer')
  })

  it('normalizeRole keeps valid role', () => {
    expect(normalizeRole('admin')).toBe('admin')
  })

  it('getEffectiveRoles maps super_admin to include admin', () => {
    expect(getEffectiveRoles('super_admin')).toEqual(['super_admin', 'admin'])
  })

  it('getEffectiveRoles keeps non-super_admin as single role', () => {
    expect(getEffectiveRoles('manager')).toEqual(['manager'])
  })

  it('hasAllowedRole passes when no allowedRoles', () => {
    expect(hasAllowedRole('viewer')).toBe(true)
    expect(hasAllowedRole('viewer', [])).toBe(true)
  })

  it('hasAllowedRole supports super_admin compatible admin config', () => {
    expect(hasAllowedRole('super_admin', ['admin'])).toBe(true)
  })

  it('hasAllowedRole rejects role not in allowed list', () => {
    expect(hasAllowedRole('viewer', ['admin', 'manager'])).toBe(false)
  })

  it('hasMinRole works with same or higher privilege', () => {
    expect(hasMinRole('admin', 'admin')).toBe(true)
    expect(hasMinRole('super_admin', 'admin')).toBe(true)
    expect(hasMinRole('manager', 'operator')).toBe(true)
  })

  it('hasMinRole rejects lower privilege', () => {
    expect(hasMinRole('viewer', 'operator')).toBe(false)
    expect(hasMinRole('operator', 'manager')).toBe(false)
  })

  it('hasMinRole passes when minRole is undefined', () => {
    expect(hasMinRole('viewer', undefined)).toBe(true)
  })

  it('canAccessMenu supports combined roles + minRole', () => {
    expect(canAccessMenu('admin', { roles: ['admin'], minRole: 'manager' })).toBe(true)
    expect(canAccessMenu('viewer', { roles: ['viewer'], minRole: 'operator' })).toBe(false)
    expect(canAccessMenu('operator', { roles: ['manager', 'admin'], minRole: 'viewer' })).toBe(false)
  })

  it('getRoleFromLocalStorage returns default when no user', () => {
    sessionStorage.clear()
    expect(getRoleFromLocalStorage()).toBe('viewer')
    expect(getRoleFromLocalStorage('operator')).toBe('operator')
  })

  it('getRoleFromLocalStorage reads sessionStorage auth_user', () => {
    sessionStorage.clear()
    sessionStorage.setItem('auth_user', JSON.stringify({ role: 'manager' }))
    expect(getRoleFromLocalStorage()).toBe('manager')
  })

  it('getRoleFromLocalStorage handles invalid json', () => {
    sessionStorage.clear()
    sessionStorage.setItem('auth_user', '{invalid')
    expect(getRoleFromLocalStorage()).toBe('viewer')
  })
})
