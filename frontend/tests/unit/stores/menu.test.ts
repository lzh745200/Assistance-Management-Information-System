import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

import { useMenuStore } from '@/stores/menu'

describe('useMenuStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('initial state: menus 是空数组, activeMenu 是空字符串', () => {
    const store = useMenuStore()
    expect(store.menus).toEqual([])
    expect(store.activeMenu).toBe('')
  })

  it('setMenus 写入菜单列表', () => {
    const store = useMenuStore()
    const items = [
      { key: 'dashboard', label: '仪表盘', path: '/dashboard' },
      { key: 'villages', label: '帮扶村', path: '/villages' },
    ]
    store.setMenus(items)
    expect(store.menus).toEqual(items)
  })

  it('setActive 修改当前激活菜单', () => {
    const store = useMenuStore()
    store.setActive('villages')
    expect(store.activeMenu).toBe('villages')
  })

  it('多次 setActive 后保持最后一个值', () => {
    const store = useMenuStore()
    store.setActive('a')
    store.setActive('b')
    store.setActive('c')
    expect(store.activeMenu).toBe('c')
  })

  it('setMenus 替换为新数组', () => {
    const store = useMenuStore()
    store.setMenus([{ key: 'a', label: 'A' }])
    store.setMenus([{ key: 'b', label: 'B' }])
    expect(store.menus).toHaveLength(1)
    expect(store.menus[0].key).toBe('b')
  })
})
