import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useConfigStore = defineStore('config', () => {
  const appName = ref('帮扶管理信息系统')
  const version = ref('1.2.0')
  const theme = ref(localStorage.getItem('theme') || 'light')

  function setTheme(t: string) {
    theme.value = t
    localStorage.setItem('theme', t)
  }

  return { appName, version, theme, setTheme }
})
