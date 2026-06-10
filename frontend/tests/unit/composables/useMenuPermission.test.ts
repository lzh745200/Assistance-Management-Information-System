import { describe, it, expect } from 'vitest'
import { useMenuPermission } from '@/composables/useMenuPermission'

describe('composables/useMenuPermission', () => {
  it('hasPermission always returns true', () => {
    const p = useMenuPermission()
    expect(p.hasPermission('any_key')).toBe(true)
    expect(p.hasPermission('')).toBe(true)
  })
})
