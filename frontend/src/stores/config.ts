import { defineStore } from 'pinia'
import { ref } from 'vue'

/** 主题持久化 localStorage 键 */
export const THEME_STORAGE_KEY = 'theme'

/** 默认主题标识（军绿，对应 tokens.scss :root；DOM 上不设置 data-theme 属性） */
export const DEFAULT_THEME = 'default'

/** 主题选项（顶栏切换器与系统设置共用） */
export interface ThemeOption {
  value: string
  label: string
}

export const THEME_OPTIONS: ThemeOption[] = [
  { value: 'default', label: '军绿' },
  { value: 'light', label: '明亮' },
  { value: 'dark', label: '深色' },
  { value: 'military', label: '军旅' },
  { value: 'outdoor', label: '户外' },
  { value: 'high-contrast', label: '高对比' },
]

/**
 * 将主题应用到 DOM：
 * - 'default' → 移除 data-theme 属性（渲染 :root 军绿默认主题）
 * - 其他值 → 设置 data-theme，匹配 tokens.scss 的 [data-theme="..."]
 */
export function applyThemeToDom(theme: string): void {
  if (theme === DEFAULT_THEME) {
    document.documentElement.removeAttribute('data-theme')
  } else {
    document.documentElement.setAttribute('data-theme', theme)
  }
}

export const useConfigStore = defineStore('config', () => {
  const appName = ref('帮扶管理信息系统')
  const version = ref('1.5.0')
  const theme = ref(localStorage.getItem(THEME_STORAGE_KEY) || DEFAULT_THEME)

  function setTheme(t: string) {
    theme.value = t
    localStorage.setItem(THEME_STORAGE_KEY, t)
    applyThemeToDom(t)
  }

  return { appName, version, theme, setTheme }
})
