import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useRuralWorkStore = defineStore('ruralWork', () => {
  const works = ref<any[]>([])
  const currentWork = ref<any>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchWorks(_params?: any) {
    loading.value = true
    error.value = null
    try {
      // Stub
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  return { works, currentWork, loading, error, fetchWorks }
})
