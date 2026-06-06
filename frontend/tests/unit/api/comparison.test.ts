import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockRequest = vi.fn()

vi.mock('@/utils/request', () => ({
  default: (...args: any[]) => mockRequest(...args),
}))
vi.mock('@/api/request', () => ({
  default: (...args: any[]) => mockRequest(...args),
}))

import {
  getComparisonList,
  getComparisonDetail,
  createComparison,
  uploadComparisonImages,
  updateComparison,
  deleteComparison,
  getFeaturedComparisons,
  getComparisonStatistics,
  batchUpdateOrder,
  default as comparisonApi,
} from '@/api/comparison'

describe('api/comparison', () => {
  beforeEach(() => vi.clearAllMocks())

  it('getComparisonList GET /comparisons with params', () => {
    getComparisonList({ type: 'village', page: 1 })
    expect(mockRequest).toHaveBeenCalledWith({
      url: '/comparisons',
      method: 'get',
      params: { type: 'village', page: 1 },
    })
  })

  it('getComparisonDetail GET /comparisons/{id}', () => {
    getComparisonDetail(5)
    expect(mockRequest).toHaveBeenCalledWith({
      url: '/comparisons/5',
      method: 'get',
    })
  })

  it('createComparison POST /comparisons', () => {
    createComparison({ type: 'village', reference_id: 1, title: 'A', before_image: 'b', after_image: 'a' } as any)
    expect(mockRequest).toHaveBeenCalledWith({
      url: '/comparisons',
      method: 'post',
      data: expect.objectContaining({ title: 'A' }),
    })
  })

  it('uploadComparisonImages POST FormData', () => {
    const fd = new FormData()
    uploadComparisonImages(fd)
    expect(mockRequest).toHaveBeenCalledWith({
      url: '/comparisons/upload',
      method: 'post',
      data: fd,
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  })

  it('updateComparison PUT /comparisons/{id}', () => {
    updateComparison(3, { title: 'new' } as any)
    expect(mockRequest).toHaveBeenCalledWith({
      url: '/comparisons/3',
      method: 'put',
      data: { title: 'new' },
    })
  })

  it('deleteComparison DELETE /comparisons/{id}', () => {
    deleteComparison(3)
    expect(mockRequest).toHaveBeenCalledWith({
      url: '/comparisons/3',
      method: 'delete',
    })
  })

  it('getFeaturedComparisons 默认 limit=10', () => {
    getFeaturedComparisons()
    expect(mockRequest).toHaveBeenCalledWith({
      url: '/comparisons/featured/list',
      method: 'get',
      params: { type: undefined, limit: 10 },
    })
  })

  it('getFeaturedComparisons 自定义 type + limit', () => {
    getFeaturedComparisons('village', 5)
    expect(mockRequest).toHaveBeenCalledWith({
      url: '/comparisons/featured/list',
      method: 'get',
      params: { type: 'village', limit: 5 },
    })
  })

  it('getComparisonStatistics GET /comparisons/statistics/{type}/{refId}', () => {
    getComparisonStatistics('village', 5)
    expect(mockRequest).toHaveBeenCalledWith({
      url: '/comparisons/statistics/village/5',
      method: 'get',
    })
  })

  it('batchUpdateOrder POST /comparisons/batch/order', () => {
    batchUpdateOrder([{ id: 1, order: 2 }])
    expect(mockRequest).toHaveBeenCalledWith({
      url: '/comparisons/batch/order',
      method: 'post',
      data: [{ id: 1, order: 2 }],
    })
  })

  it('default export 包含所有方法', () => {
    expect(typeof comparisonApi.getComparisonList).toBe('function')
    expect(typeof comparisonApi.uploadComparisonImages).toBe('function')
    expect(typeof comparisonApi.batchUpdateOrder).toBe('function')
  })
})
