import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

const mockGet = vi.fn()
const mockPost = vi.fn()
const mockPut = vi.fn()
const mockDel = vi.fn()

vi.mock('@/api/request', () => ({
  get: (...args: any[]) => mockGet(...args),
  post: (...args: any[]) => mockPost(...args),
  put: (...args: any[]) => mockPut(...args),
  del: (...args: any[]) => mockDel(...args),
  getCsrfToken: vi.fn(() => Promise.resolve("test-csrf"))}))

vi.mock('@/utils/unwrapList', () => ({
  unwrapList: (res: any) => ({
    items: res?.items ?? res?.data?.items ?? [],
    total: res?.total ?? res?.data?.total ?? 0,
  }),
}))

import { useVillageStore } from '@/stores/village'

describe('useVillageStore', () => {
  let store: ReturnType<typeof useVillageStore>

  beforeEach(() => {
    vi.clearAllMocks()
    setActivePinia(createPinia())
    store = useVillageStore()
  })

  it('initializes with defaults', () => {
    expect(store.villages).toEqual([])
    expect(store.current).toBeNull()
    expect(store.loading).toBe(false)
    expect(store.total).toBe(0)
  })

  describe('fetchVillages', () => {
    it('成功时填充列表与总数并传入参数', async () => {
      mockGet.mockResolvedValueOnce({ items: [{ id: 1 }], total: 3 })
      await store.fetchVillages({ page: 2 })
      expect(mockGet).toHaveBeenCalledWith('/supported-villages', { page: 2 })
      expect(store.villages).toHaveLength(1)
      expect(store.total).toBe(3)
      expect(store.loading).toBe(false)
    })

    it('成功时兼容 data 包裹格式', async () => {
      mockGet.mockResolvedValueOnce({ data: { items: [{ id: 1 }], total: 1 } })
      await store.fetchVillages()
      expect(store.villages).toHaveLength(1)
      expect(store.total).toBe(1)
    })

    it('失败时静默并重置 loading', async () => {
      mockGet.mockRejectedValueOnce(new Error('network'))
      await store.fetchVillages()
      expect(store.villages).toEqual([])
      expect(store.loading).toBe(false)
    })
  })

  describe('fetchVillage', () => {
    it('成功时设置 current', async () => {
      mockGet.mockResolvedValueOnce({ data: { id: 2, name: 'V' } })
      await store.fetchVillage(2)
      expect(mockGet).toHaveBeenCalledWith('/supported-villages/2')
      expect(store.current).toEqual({ id: 2, name: 'V' })
      expect(store.loading).toBe(false)
    })

    it('响应无 data 时 current 置 null', async () => {
      mockGet.mockResolvedValueOnce({ code: 500 })
      await store.fetchVillage(2)
      expect(store.current).toBeNull()
      expect(store.loading).toBe(false)
    })

    it('失败时静默并重置 loading', async () => {
      mockGet.mockRejectedValueOnce(new Error('network'))
      await store.fetchVillage(1)
      expect(store.current).toBeNull()
      expect(store.loading).toBe(false)
    })
  })

  describe('createVillage', () => {
    it('POST 成功后重新加载列表并返回 res', async () => {
      mockPost.mockResolvedValueOnce({ code: 200, data: { id: 3 } })
      mockGet.mockResolvedValueOnce({ items: [{ id: 3 }], total: 1 })
      const r = await store.createVillage({ name: 'village-x' })
      expect(mockPost).toHaveBeenCalledWith('/supported-villages', { name: 'village-x' })
      expect(r).toEqual({ code: 200, data: { id: 3 } })
      expect(store.villages).toHaveLength(1)
    })
  })

  describe('updateVillage', () => {
    it('存在时乐观合并更新并返回 res', async () => {
      mockPut.mockResolvedValueOnce({ code: 200 })
      store.villages.push({ id: 1, name: 'old' } as any)
      const r = await store.updateVillage(1, { name: 'new' })
      expect(mockPut).toHaveBeenCalledWith('/supported-villages/1', { name: 'new' })
      expect(r).toEqual({ code: 200 })
      expect(store.villages[0].name).toBe('new')
    })

    it('不存在时跳过本地更新', async () => {
      mockPut.mockResolvedValueOnce({ code: 200 })
      await store.updateVillage(9, { name: 'x' })
      expect(store.villages).toEqual([])
    })
  })

  describe('deleteVillage', () => {
    it('删除匹配条目并减少 total', async () => {
      mockDel.mockResolvedValueOnce({ code: 200 })
      store.villages.push({ id: 1 } as any, { id: 2 } as any)
      store.total = 2
      await store.deleteVillage(1)
      expect(mockDel).toHaveBeenCalledWith('/supported-villages/1')
      expect(store.villages).toHaveLength(1)
      expect(store.villages[0].id).toBe(2)
      expect(store.total).toBe(1)
    })
  })
})
