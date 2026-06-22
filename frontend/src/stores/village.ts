import { defineStore } from 'pinia'
import { ref } from 'vue'
import { get, post, put, del } from '@/api/request'
import { unwrapList } from '@/utils/unwrapList'

export const useVillageStore = defineStore('village', () => {
  const villages = ref<any[]>([])
  const current = ref<any>(null)
  const loading = ref(false)
  const total = ref(0)

  /** 展开单个对象响应 */
  function _unwrapSingle(res: any): any | null {
    return res?.data ?? null
  }

  async function fetchVillages(params?: any) {
    loading.value = true
    try {
      const res = await get<any>('/supported-villages', { params })
      const { items, total: t } = unwrapList(res)
      villages.value = items
      total.value = t
    } catch {
      /* silent */
    } finally {
      loading.value = false
    }
  }

  async function fetchVillage(id: number) {
    loading.value = true
    try {
      const res = await get<any>('/supported-villages/' + id)
      current.value = _unwrapSingle(res)
    } catch {
      /* silent */
    } finally {
      loading.value = false
    }
  }

  async function createVillage(data: any) {
    const res = await post<any>('/supported-villages', data)
    // POST 成功则重新加载列表（axios 会在非 2xx 时抛出异常）
    await fetchVillages()
    return res
  }

  async function updateVillage(id: number, data: any) {
    const res = await put<any>('/supported-villages/' + id, data)
    // PUT 成功后乐观更新本地状态
    const idx = villages.value.findIndex((v: any) => v.id === id)
    if (idx >= 0) villages.value[idx] = { ...villages.value[idx], ...data }
    return res
  }

  async function deleteVillage(id: number) {
    await del<any>('/supported-villages/' + id)
    villages.value = villages.value.filter((v: any) => v.id !== id)
    total.value--
  }

  return {
    villages,
    current,
    loading,
    total,
    fetchVillages,
    fetchVillage,
    createVillage,
    updateVillage,
    deleteVillage,
  }
})
