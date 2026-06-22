/**
 * 响应式侧边栏 Composable
 *
 * 功能：
 * - 根据窗口宽度自动折叠/展开侧边栏
 * - 持久化折叠状态到 localStorage
 * - 提供手动切换方法
 */

import { ref, onMounted, onUnmounted } from 'vue'

/** 移动端断点（px） */
const MOBILE_BREAKPOINT = 768
/** 平板断点（px） */
const TABLET_BREAKPOINT = 1024
/** localStorage 键 */
const STORAGE_KEY = 'sidebar_collapsed'

export function useResponsiveSidebar() {
  const isCollapsed = ref(false)
  const isMobile = ref(false)

  /** 从 localStorage 恢复状态 */
  function restoreState() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (saved !== null) {
        isCollapsed.value = saved === 'true'
      }
    } catch {
      // localStorage 不可用时忽略
    }
  }

  /** 持久化状态 */
  function persistState() {
    try {
      localStorage.setItem(STORAGE_KEY, String(isCollapsed.value))
    } catch {
      // localStorage 不可用时忽略
    }
  }

  /** 切换折叠状态 */
  function toggleCollapse() {
    isCollapsed.value = !isCollapsed.value
    persistState()
  }

  /** 设置折叠状态 */
  function setCollapsed(value: boolean) {
    isCollapsed.value = value
    persistState()
  }

  /** 根据窗口宽度自动调整 */
  function handleResize() {
    const width = window.innerWidth
    isMobile.value = width < MOBILE_BREAKPOINT

    // 移动端和平板自动折叠
    if (width < TABLET_BREAKPOINT) {
      isCollapsed.value = true
    }
  }

  onMounted(() => {
    restoreState()
    handleResize()
    window.addEventListener('resize', handleResize)
  })

  onUnmounted(() => {
    window.removeEventListener('resize', handleResize)
  })

  return {
    isCollapsed,
    isMobile,
    toggleCollapse,
    setCollapsed,
  }
}
