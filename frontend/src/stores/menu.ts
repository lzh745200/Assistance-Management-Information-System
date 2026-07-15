import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { get } from '@/api/request'
import { AuthStorage } from '@/utils/authStorage'

export interface MenuItem {
  key: string
  label: string
  path?: string
  icon?: string
  roles?: string[]
  children?: MenuItem[]
  order?: number
}

/** 从菜单树中提取所有 key（含子节点） */
function _extractAllKeys(items: MenuItem[]): Set<string> {
  const keys = new Set<string>()
  const walk = (list: MenuItem[]) => {
    for (const item of list) {
      keys.add(item.key)
      if (item.children?.length) walk(item.children)
    }
  }
  walk(items)
  return keys
}

export const useMenuStore = defineStore('menu', () => {
  const menus = ref<MenuItem[]>([])
  const activeMenu = ref('')
  const loaded = ref(false)
  const loading = ref(false)
  const loadFailed = ref(false)
  const allKeys = ref<Set<string>>(new Set())

  /** 可访问的菜单 key 集合 */
  const accessibleKeys = computed(() => allKeys.value)

  function setMenus(items: MenuItem[]) {
    menus.value = items
    allKeys.value = _extractAllKeys(items)
    loaded.value = true
    loading.value = false
    // Empty menu is valid — only fetchMenus catch sets loadFailed
    loadFailed.value = false
  }

  function setActive(key: string) {
    activeMenu.value = key
  }

  function canAccessMenu(menuKey: string): boolean {
    if (!loaded.value) return false
    return allKeys.value.has(menuKey)
  }

  /** 从后端加载当前用户可见菜单，更新 store */
  async function fetchMenus(): Promise<void> {
    if (loading.value) return // 防重复调用
    const token = AuthStorage.getToken()
    if (!token) return
    loading.value = true
    try {
      const res = await get('/menus/accessible')
      const data = res.data || res || []
      setMenus(Array.isArray(data) ? data : [])
    } catch {
      // 加载失败：保持 loaded=false 允许下次重试，标记失败状态
      loading.value = false
      loadFailed.value = true
    }
  }

  return {
    menus,
    activeMenu,
    loaded,
    loading,
    loadFailed,
    accessibleKeys,
    setMenus,
    setActive,
    canAccessMenu,
    fetchMenus,
  }
})
