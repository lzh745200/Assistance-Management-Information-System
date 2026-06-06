import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

const mockApiRequest = vi.fn()

vi.mock('@/api/request', () => ({
  apiRequest: (...args: any[]) => mockApiRequest(...args),
}))

vi.mock('@/utils/unwrapList', () => ({
  unwrapList: (res: any) => {
    if (Array.isArray(res)) return { items: res, total: res.length }
    if (res?.data?.items) return { items: res.data.items, total: res.data.total ?? res.data.items.length }
    return { items: [], total: 0 }
  },
}))

import { useDataReportStore } from '@/stores/dataReport'

describe('useDataReportStore', () => {
  let store: ReturnType<typeof useDataReportStore>
  beforeEach(() => {
    vi.clearAllMocks()
    setActivePinia(createPinia())
    store = useDataReportStore()
  })

  it('初始: reports=[], receivedReports=[]', () => {
    expect(store.reports).toEqual([])
    expect(store.receivedReports).toEqual([])
    expect(store.receivedTotal).toBe(0)
  })

  it('fetchReceivedReports 成功时填充 receivedReports + total', async () => {
    mockApiRequest.mockResolvedValueOnce({
      data: { items: [{ id: 1 }, { id: 2 }], total: 2 },
    })
    await store.fetchReceivedReports({ page: 1 })
    expect(mockApiRequest).toHaveBeenCalledWith(expect.objectContaining({
      method: 'GET',
      url: '/data-reports/received',
      params: { page: 1 },
    }))
    expect(store.receivedReports).toHaveLength(2)
    expect(store.receivedTotal).toBe(2)
  })

  it('fetchReceivedReports 失败时清空 + 设置 error', async () => {
    mockApiRequest.mockRejectedValueOnce(new Error('boom'))
    await store.fetchReceivedReports()
    expect(store.receivedReports).toEqual([])
    expect(store.error).toBe('boom')
  })

  it('fetchReceivedReports axios 错误格式', async () => {
    mockApiRequest.mockRejectedValueOnce({ response: { data: { message: '服务器错误' } } })
    await store.fetchReceivedReports()
    expect(store.error).toBe('服务器错误')
  })

  it('fetchReports 成功时填充 reports', async () => {
    mockApiRequest.mockResolvedValueOnce({
      data: { items: [{ id: 1 }] },
    })
    await store.fetchReports()
    expect(store.reports).toHaveLength(1)
  })

  it('fetchReports 失败时设置 error', async () => {
    mockApiRequest.mockRejectedValueOnce(new Error('network'))
    await store.fetchReports()
    expect(store.error).toBe('network')
  })

  it('previewReport 调用 GET /data-reports/{id}', async () => {
    mockApiRequest.mockResolvedValueOnce({ data: { id: 5, content: 'x' } })
    await store.previewReport(5)
    expect(mockApiRequest).toHaveBeenCalledWith(expect.objectContaining({
      method: 'GET',
      url: '/data-reports/5',
    }))
  })

  it('receiveReport 调用 POST /data-reports/{id}/approve', async () => {
    mockApiRequest.mockResolvedValueOnce({})
    await store.receiveReport(3)
    expect(mockApiRequest).toHaveBeenCalledWith(expect.objectContaining({
      method: 'POST',
      url: '/data-reports/3/approve',
    }))
  })

  it('rejectReport 调用 POST /data-reports/{id}/review with decision=reject', async () => {
    mockApiRequest.mockResolvedValueOnce({})
    await store.rejectReport(3, '数据不完整')
    expect(mockApiRequest).toHaveBeenCalledWith(expect.objectContaining({
      method: 'POST',
      url: '/data-reports/3/review',
      data: { decision: 'reject', comment: '数据不完整' },
    }))
  })

  it('downloadReport 调用 GET /data-reports/{id}/package', async () => {
    mockApiRequest.mockResolvedValueOnce({ data: { url: 'http://x' } })
    await store.downloadReport(7)
    expect(mockApiRequest).toHaveBeenCalledWith(expect.objectContaining({
      method: 'GET',
      url: '/data-reports/7/package',
    }))
  })

  it('submitReport 调用 POST /data-reports', async () => {
    mockApiRequest.mockResolvedValueOnce({})
    await store.submitReport({ content: 'new' })
    expect(mockApiRequest).toHaveBeenCalledWith(expect.objectContaining({
      method: 'POST',
      url: '/data-reports',
      data: { content: 'new' },
    }))
  })
})
