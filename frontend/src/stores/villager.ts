import { defineStore } from 'pinia'
import { ref } from 'vue'

/** 村民管理 store — 后端 /villagers 模块尚未实现 */
export const useVillagerStore = defineStore('villager', () => {
  const villagerList = ref<any[]>([])
  const current = ref<any>(null)
  const loading = ref(false)
  const total = ref(0)

  async function fetchVillagers(_params?: any) {
    loading.value = false
  }
  async function fetchVillager(_id: number) {
    loading.value = false
  }
  async function createVillager(_data: any) {
    return { code: 200 }
  }
  async function updateVillager(_id: number, _data: any) {
    return { code: 200 }
  }
  async function deleteVillager(_id: number) {
    return { code: 200 }
  }

  return {
    villagerList,
    current,
    loading,
    total,
    fetchVillagers,
    fetchVillager,
    createVillager,
    updateVillager,
    deleteVillager,
  }
})
