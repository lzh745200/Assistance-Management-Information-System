import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useMenuStore, type MenuItem } from '@/stores/menu'

describe('useMenuStore', () => {
  let store: ReturnType<typeof useMenuStore>
  beforeEach(() => {
    setActivePinia(createPinia())
    store = useMenuStore()
  })

  it('初始 menus=[] 和 activeMenu=""', () => {
    expect(store.menus).toEqual([])
    expect(store.activeMenu).toBe('')
  })

  it('setMenus 替换菜单列表', () => {
    const items: MenuItem[] = [
      { key: 'dashboard', label: '工作台', path: '/dashboard' },
      { key: 'village', label: '帮扶村', path: '/village' },
    ]
    store.setMenus(items)
    expect(store.menus).toEqual(items)
    expect(store.menus).toHaveLength(2)
  })

  it('setMenus 支持嵌套 children', () => {
    const items: MenuItem[] = [
      {
        key: 'data',
        label: '数据中心',
        children: [
          { key: 'data-village', label: '帮扶村数据', path: '/data/village' },
          { key: 'data-school', label: '学校数据', path: '/data/school' },
        ],
      },
    ]
    store.setMenus(items)
    expect(store.menus[0].children).toHaveLength(2)
  })

  it('setActive 修改 activeMenu', () => {
    store.setActive('dashboard')
    expect(store.activeMenu).toBe('dashboard')
    store.setActive('village')
    expect(store.activeMenu).toBe('village')
  })

  it('setMenus 可清空为 []', () => {
    store.setMenus([{ key: 'x', label: 'X' }])
    expect(store.menus).toHaveLength(1)
    store.setMenus([])
    expect(store.menus).toHaveLength(0)
  })
})
