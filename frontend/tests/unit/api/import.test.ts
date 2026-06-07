import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockGet = vi.fn()
const mockPost = vi.fn()

vi.mock('@/utils/request', () => ({
  default: {
    get: (...args: any[]) => mockGet(...args),
    post: (...args: any[]) => mockPost(...args),
  },
}))

vi.mock('@/api/request', () => ({
  default: {
    get: (...args: any[]) => mockGet(...args),
    post: (...args: any[]) => mockPost(...args),
  },
}))

import {
  downloadImportTemplate,
  importVillages,
  getImportHistory,
  formatImportStatus,
} from '@/api/import'

describe('api/import', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('downloadImportTemplate GET /import/template with entity_type', async () => {
    const blob = new Blob(['test'])
    mockGet.mockResolvedValueOnce({ data: blob })
    const result = await downloadImportTemplate('village')
    expect(mockGet).toHaveBeenCalledWith('/import/template', {
      params: { entity_type: 'village' },
      responseType: 'blob',
    })
    expect(result).toBe(blob)
  })

  it('importVillages POST /import/entities with FormData (default entity_type=supported_village)', async () => {
    mockPost.mockResolvedValueOnce({
      data: { success: true, total_rows: 10, success_rows: 10, failed_rows: 0, skipped_rows: 0 },
    })
    const file = new File(['test'], 'villages.xlsx')
    const result = await importVillages(file)
    expect(mockPost).toHaveBeenCalled()
    const [url, formData, config] = mockPost.mock.calls[0]
    expect(url).toBe('/import/entities')
    expect(formData).toBeInstanceOf(FormData)
    expect(formData.get('file')).toBe(file)
    expect(formData.get('entity_type')).toBe('supported_village')
    expect(formData.get('mode')).toBe('incremental')
    expect(config.headers['Content-Type']).toBe('multipart/form-data')
    expect(config.timeout).toBe(120000)
    expect(result.success).toBe(true)
  })

  it('importVillages mode=overwrite', async () => {
    mockPost.mockResolvedValueOnce({
      data: { success: true, total_rows: 5, success_rows: 5, failed_rows: 0, skipped_rows: 0 },
    })
    const file = new File(['test'], 'data.xlsx')
    await importVillages(file, 'overwrite')
    const formData = mockPost.mock.calls[0][1]
    expect(formData.get('mode')).toBe('overwrite')
  })

  it('getImportHistory 默认 page=1, pageSize=10', async () => {
    mockGet.mockResolvedValueOnce({ data: { items: [], total: 0 } })
    await getImportHistory()
    expect(mockGet).toHaveBeenCalledWith('/import/history', {
      params: { page: 1, page_size: 10 },
    })
  })

  it('getImportHistory 自定义 page + pageSize', async () => {
    mockGet.mockResolvedValueOnce({ data: { items: [], total: 0 } })
    await getImportHistory(2, 25)
    expect(mockGet).toHaveBeenCalledWith('/import/history', {
      params: { page: 2, page_size: 25 },
    })
  })

  describe('formatImportStatus', () => {
    it('pending -> 等待中 / info', () => {
      expect(formatImportStatus('pending')).toEqual({ text: '等待中', type: 'info' })
    })
    it('processing -> 处理中 / warning', () => {
      expect(formatImportStatus('processing')).toEqual({ text: '处理中', type: 'warning' })
    })
    it('completed -> 已完成 / success', () => {
      expect(formatImportStatus('completed')).toEqual({ text: '已完成', type: 'success' })
    })
    it('failed -> 失败 / danger', () => {
      expect(formatImportStatus('failed')).toEqual({ text: '失败', type: 'danger' })
    })
    it('未知状态回退', () => {
      expect(formatImportStatus('xyz')).toEqual({ text: 'xyz', type: 'info' })
    })
  })
})
