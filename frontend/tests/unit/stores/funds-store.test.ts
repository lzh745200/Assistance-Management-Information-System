import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('@/api/request', () => ({
  default: vi.fn(),
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  del: vi.fn(),
  apiRequest: vi.fn(),
}))

vi.mock('@/utils/unwrapList', () => ({
  unwrapList: vi.fn((r: any) => ({ items: r?.items ?? [], total: r?.total ?? 0 })),
}))

import { post, put, del, apiRequest } from '@/api/request'
import { useFundsStore } from '@/stores/funds'

describe('stores/funds', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('initial state', () => {
    it('fundList/current/loading/total 初始值', () => {
      const s = useFundsStore()
      expect(s.fundList).toEqual([])
      expect(s.current).toBeNull()
      expect(s.loading).toBe(false)
      expect(s.total).toBe(0)
    })
  })

  describe('fetchFunds', () => {
    it('成功: 填充 list + total', async () => {
      ;(apiRequest as any).mockResolvedValue({ items: [{ id: 1 }], total: 1 })
      const s = useFundsStore()
      await s.fetchFunds()
      expect(s.fundList).toEqual([{ id: 1 }])
      expect(s.total).toBe(1)
    })

    it('失败: 清空', async () => {
      ;(apiRequest as any).mockRejectedValue(new Error('fail'))
      const s = useFundsStore()
      await s.fetchFunds()
      expect(s.fundList).toEqual([])
      expect(s.total).toBe(0)
      expect(s.loading).toBe(false)
    })
  })

  describe('createFund', () => {
    it('POST + refetch', async () => {
      ;(post as any).mockResolvedValue({ code: 200 })
      ;(apiRequest as any).mockResolvedValue({ items: [{ id: 99 }], total: 1 })
      const s = useFundsStore()
      await s.createFund({ name: 'X' })
      expect(post).toHaveBeenCalledWith('/funds', { name: 'X' })
      expect(s.fundList).toEqual([{ id: 99 }])
    })
  })

  describe('updateFund', () => {
    it('PUT + 更新本地项', async () => {
      ;(put as any).mockResolvedValue({ code: 200 })
      const s = useFundsStore()
      s.fundList = [{ id: 1, name: 'A', amount: 100 }]
      await s.updateFund(1, { amount: 200 })
      expect(put).toHaveBeenCalledWith('/funds/1', { amount: 200 })
      expect(s.fundList[0].amount).toBe(200)
      expect(s.fundList[0].name).toBe('A')  // preserved
    })

    it('id 不在列表: 不报错', async () => {
      ;(put as any).mockResolvedValue({ code: 200 })
      const s = useFundsStore()
      await s.updateFund(99, { amount: 1 })
      expect(s.fundList).toEqual([])
    })
  })

  describe('deleteFund', () => {
    it('DEL + 移除 + total--', async () => {
      ;(del as any).mockResolvedValue({ code: 200 })
      const s = useFundsStore()
      s.fundList = [{ id: 1 }, { id: 2 }]
      s.total = 2
      await s.deleteFund(1)
      expect(del).toHaveBeenCalledWith('/funds/1')
      expect(s.fundList).toEqual([{ id: 2 }])
      expect(s.total).toBe(1)
    })
  })

  describe('getSummary', () => {
    it('成功: 返回 res.data', async () => {
      ;(apiRequest as any).mockResolvedValue({ data: { total_amount: 1000 } })
      const s = useFundsStore()
      const r = await s.getSummary()
      expect(r).toEqual({ total_amount: 1000 })
    })

    it('无 data: 返回 res 本身', async () => {
      ;(apiRequest as any).mockResolvedValue({ total_amount: 500 })
      const s = useFundsStore()
      const r = await s.getSummary()
      expect(r).toEqual({ total_amount: 500 })
    })

    it('失败: 默认结构', async () => {
      ;(apiRequest as any).mockRejectedValue(new Error('fail'))
      const s = useFundsStore()
      const r = await s.getSummary()
      expect(r).toEqual({ total_amount: 0, total_allocated: 0, total_count: 0, by_status: {} })
    })
  })

  describe('approveFund', () => {
    it('POST + 设置 status=approved', async () => {
      ;(post as any).mockResolvedValue({ code: 200 })
      const s = useFundsStore()
      s.fundList = [{ id: 1, status: 'pending' }]
      await s.approveFund(1)
      expect(post).toHaveBeenCalledWith('/funds/1/approve', {})
      expect(s.fundList[0].status).toBe('approved')
    })

    it('id 不在: POST 但不修改', async () => {
      ;(post as any).mockResolvedValue({ code: 200 })
      const s = useFundsStore()
      await s.approveFund(99)
      expect(post).toHaveBeenCalled()
    })
  })
})
