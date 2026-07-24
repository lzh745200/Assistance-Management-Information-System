import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockGet } = vi.hoisted(() => ({
  mockGet: vi.fn(),
}))

vi.mock('@/api/request', () => ({
  get: mockGet,
}))

import {
  getHelpCategories,
  getHelpArticles,
  getHelpArticle,
  searchHelp,
  getHelpSystemInfo,
  helpApi,
} from '@/api/help'

describe('api/help', () => {
  beforeEach(() => vi.clearAllMocks())

  it('getHelpCategories GET /system/help/categories', async () => {
    const body = { success: true, data: { categories: [] } }
    mockGet.mockResolvedValueOnce(body)
    const r = await getHelpCategories()
    expect(mockGet).toHaveBeenCalledWith('/system/help/categories')
    expect(r).toBe(body)
  })

  it('getHelpArticles 无参', async () => {
    const body = { success: true, data: { items: [], total: 0 } }
    mockGet.mockResolvedValueOnce(body)
    const r = await getHelpArticles()
    expect(mockGet).toHaveBeenCalledWith('/system/help/articles', undefined)
    expect(r).toBe(body)
  })

  it('getHelpArticles 带分类与分页参数', async () => {
    mockGet.mockResolvedValueOnce({ success: true })
    await getHelpArticles({ category: 'funds', keyword: '申请', page: 2, page_size: 10 })
    expect(mockGet).toHaveBeenCalledWith('/system/help/articles', {
      category: 'funds',
      keyword: '申请',
      page: 2,
      page_size: 10,
    })
  })

  it('getHelpArticle GET /system/help/articles/:id', async () => {
    const body = { success: true, data: { id: 5, title: '使用手册' } }
    mockGet.mockResolvedValueOnce(body)
    const r = await getHelpArticle(5)
    expect(mockGet).toHaveBeenCalledWith('/system/help/articles/5')
    expect(r).toBe(body)
  })

  it('searchHelp 默认 limit=10', async () => {
    const body = { success: true, data: { items: [], total: 0 } }
    mockGet.mockResolvedValueOnce(body)
    const r = await searchHelp('扶贫')
    expect(mockGet).toHaveBeenCalledWith('/system/help/search', { q: '扶贫', limit: 10 })
    expect(r).toBe(body)
  })

  it('searchHelp 自定义 limit', async () => {
    mockGet.mockResolvedValueOnce({ success: true })
    await searchHelp('项目', 5)
    expect(mockGet).toHaveBeenCalledWith('/system/help/search', { q: '项目', limit: 5 })
  })

  it('getHelpSystemInfo GET /system/help/system-info', async () => {
    const body = { success: true, data: { name: '系统', version: '1.0' } }
    mockGet.mockResolvedValueOnce(body)
    const r = await getHelpSystemInfo()
    expect(mockGet).toHaveBeenCalledWith('/system/help/system-info')
    expect(r).toBe(body)
  })

  it('helpApi 分组导出引用同一批函数', () => {
    expect(helpApi.getCategories).toBe(getHelpCategories)
    expect(helpApi.getArticles).toBe(getHelpArticles)
    expect(helpApi.getArticle).toBe(getHelpArticle)
    expect(helpApi.search).toBe(searchHelp)
    expect(helpApi.getSystemInfo).toBe(getHelpSystemInfo)
  })
})
