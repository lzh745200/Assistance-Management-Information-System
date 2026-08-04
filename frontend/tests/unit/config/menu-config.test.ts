import { describe, it, expect } from 'vitest'
import { MENU_CONFIG, getAllMenuKeys } from '@/config/menu-config'
import type { MenuItem } from '@/config/menu-config'

describe('config/menu-config', () => {
  it('菜单配置非空且为数组', () => {
    expect(Array.isArray(MENU_CONFIG)).toBe(true)
    expect(MENU_CONFIG.length).toBeGreaterThan(0)
  })

  it('顶层菜单项数量为 15', () => {
    expect(MENU_CONFIG.length).toBe(15)
  })

  it('顶层 key 唯一', () => {
    const keys = MENU_CONFIG.map((m) => m.key)
    expect(new Set(keys).size).toBe(keys.length)
  })

  it('顶层 order 唯一且为数字', () => {
    const orders = MENU_CONFIG.map((m) => m.order)
    expect(new Set(orders).size).toBe(orders.length)
    for (const o of orders) expect(typeof o).toBe('number')
  })

  it('每个顶层项均含 key/label', () => {
    for (const item of MENU_CONFIG) {
      expect(item.key).toBeTruthy()
      expect(item.label).toBeTruthy()
    }
  })

  it('getAllMenuKeys 返回全部 key 且无重复', () => {
    const keys = getAllMenuKeys()
    expect(new Set(keys).size).toBe(keys.length)
    expect(keys).toHaveLength(52)
    expect(keys).toContain('dashboard')
    expect(keys).toContain('system-overview')
    expect(keys).toContain('batch-import')
    expect(keys).toContain('analytics-map')
    expect(keys).toContain('data-package-version')
  })

  it('getAllMenuKeys 覆盖所有顶层 key', () => {
    const keys = getAllMenuKeys()
    for (const item of MENU_CONFIG) {
      expect(keys).toContain(item.key)
    }
  })

  it('funds-admin 角色白名单', () => {
    const funds = MENU_CONFIG.find((m) => m.key === 'funds-admin')!
    expect(funds.path).toBe('/funds')
    expect(funds.roles).toEqual(['admin', 'super_admin', 'manager'])
  })

  it('funds-user 角色白名单', () => {
    const fundsUser = MENU_CONFIG.find((m) => m.key === 'funds-user')!
    expect(fundsUser.roles).toEqual(['operator', 'viewer', 'approval_leader'])
  })

  it('approval 角色白名单', () => {
    const approval = MENU_CONFIG.find((m) => m.key === 'approval')!
    expect(approval.roles).toEqual(['admin', 'super_admin', 'approval_leader', 'manager'])
  })

  it('system-security 含 19 个子项且角色受限', () => {
    const sys = MENU_CONFIG.find((m) => m.key === 'system-security')!
    expect(sys.children).toHaveLength(19)
    expect(sys.roles).toEqual(['admin', 'super_admin'])
    for (const child of sys.children!) {
      expect(child.key).toBeTruthy()
      expect(child.label).toBeTruthy()
    }
  })

  it('helpData 含 8 个子项', () => {
    const help = MENU_CONFIG.find((m) => m.key === 'helpData')!
    expect(help.children).toHaveLength(8)
    expect(help.roles).toEqual(['admin', 'super_admin', 'manager', 'operator'])
  })

  it('analytics 含 6 个子项', () => {
    const analytics = MENU_CONFIG.find((m) => m.key === 'analytics')!
    expect(analytics.children).toHaveLength(6)
  })

  it('data-upload 含 4 个子项', () => {
    const upload = MENU_CONFIG.find((m) => m.key === 'data-upload')!
    expect(upload.children).toHaveLength(4)
  })

  it('嵌套子项 key 结构完整（仅叶子项有 path）', () => {
    const walk = (items: MenuItem[], leaf: boolean): void => {
      for (const item of items) {
        expect(item.key).toBeTruthy()
        expect(item.label).toBeTruthy()
        if (leaf) expect(typeof item.path).toBe('string')
        if (item.children) walk(item.children, true)
      }
    }
    walk(MENU_CONFIG, false)
  })
})
