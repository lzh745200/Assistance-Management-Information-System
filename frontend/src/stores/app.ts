import { defineStore } from 'pinia'
export const useAppStore = defineStore('app', {
  state: () => ({ sidebarCollapsed: false, theme: 'light' }),
  actions: {
    toggleSidebar() {
      this.sidebarCollapsed = !this.sidebarCollapsed
    },
    setTheme(t: string) {
      this.theme = t
    },
  },
})
